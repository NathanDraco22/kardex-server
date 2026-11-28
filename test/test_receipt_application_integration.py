import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from kardex.core.receipt_register import process_receipt as proc_rec_mod
from kardex.repos.v1.common.models import ClientInfo, UserInfo
from kardex.repos.v1.receipts import (
    AppliedCreditNote,
    AppliedDevolution,
    AppliedInvoice,
    CreateReceipt,
)
from kardex.tools import InvalidOperation


class _FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    async def start_transaction(self):
        return _FakeTx()


class _FakeMongoService:
    def __init__(self):
        self.client = SimpleNamespace(start_session=self._start_session)

    @asynccontextmanager
    async def _start_session(self):
        yield _FakeSession()


def _sample_receipt(
    *,
    client_id: str = "client-1",
    total: int = 0,
    invoice_amount: int = 500,
    credit_notes: list[AppliedCreditNote] | None = None,
    devolutions: list[AppliedDevolution] | None = None,
) -> CreateReceipt:
    return CreateReceipt(
        branchId="branch-1",
        clientInfo=ClientInfo(name="Cliente"),
        clientId=client_id,
        appliedInvoices=[
            AppliedInvoice(
                invoiceId="inv-1",
                docNumber="FAC-001",
                amountApplied=invoice_amount,
            )
        ],
        appliedDevolutions=devolutions or [],
        appliedCreditNotes=credit_notes or [],
        paymentMethod="cash",
        total=total,
        createdBy=UserInfo(id="user-1", name="Cajero"),
    )


def _patch_collections(monkeypatch, **overrides):
    defaults = {
        "ReceiptsCollection": SimpleNamespace(get_instance=lambda: SimpleNamespace()),
        "InvoicesCollection": SimpleNamespace(get_instance=lambda: SimpleNamespace()),
        "DevolutionsCollection": SimpleNamespace(
            get_instance=lambda: SimpleNamespace()
        ),
        "CreditNotesCollection": SimpleNamespace(
            get_instance=lambda: SimpleNamespace()
        ),
        "ClientTransactionsCollection": SimpleNamespace(
            get_instance=lambda: SimpleNamespace()
        ),
        "ClientsCollection": SimpleNamespace(get_instance=lambda: SimpleNamespace()),
    }
    defaults.update(overrides)
    monkeypatch.setattr(proc_rec_mod, "MongoService", lambda: _FakeMongoService())
    for name, value in defaults.items():
        monkeypatch.setattr(proc_rec_mod, name, value)
    monkeypatch.setattr(
        proc_rec_mod,
        "CounterManager",
        lambda: SimpleNamespace(
            next_receipt_number=AsyncMock(return_value="REC-001")
        ),
    )


def test_process_receipt_rejects_funds_discrepancy(monkeypatch):
    receipt = _sample_receipt(total=100, invoice_amount=500)
    _patch_collections(monkeypatch)

    with pytest.raises(InvalidOperation, match="Discrepancy Error"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_rejects_unapproved_credit_note(monkeypatch):
    receipt = _sample_receipt(
        invoice_amount=100,
        credit_notes=[
            AppliedCreditNote(
                creditNoteId="cn-1",
                docNumber="CN-001",
                amountApplied=100,
            )
        ],
    )
    credit_note_col = SimpleNamespace(
        fetch_credit_note_by_id=AsyncMock(
            return_value={
                "id": "cn-1",
                "docNumber": "CN-001",
                "status": "emitted",
                "clientId": "client-1",
                "amount": 100,
            }
        )
    )
    _patch_collections(
        monkeypatch,
        CreditNotesCollection=SimpleNamespace(
            get_instance=lambda: credit_note_col
        ),
    )

    with pytest.raises(InvalidOperation, match="no está aprobada"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_rejects_invoice_overpayment(monkeypatch):
    receipt = _sample_receipt(total=500, invoice_amount=500)
    receipt_col = SimpleNamespace(
        create_receipt_with_session=AsyncMock(
            side_effect=lambda data, session=None: data
        )
    )
    invoice_doc = {
        "id": "inv-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": {"name": "Cliente"},
        "docNumber": "FAC-001",
        "saleItems": [],
        "totalCost": 200,
        "total": 500,
        "amountPaid": 200,
        "status": "partiallyPaid",
        "paymentType": "credit",
        "createdBy": {"id": "u-1", "name": "Cajero"},
        "createdAt": 1000,
    }
    invoice_col = SimpleNamespace(
        fetch_invoice_by_id_with_session=AsyncMock(return_value=invoice_doc),
    )
    devolution_col = SimpleNamespace(
        fetch_devolutions_by_invoice_id=AsyncMock(return_value=[]),
    )
    _patch_collections(
        monkeypatch,
        ReceiptsCollection=SimpleNamespace(get_instance=lambda: receipt_col),
        InvoicesCollection=SimpleNamespace(get_instance=lambda: invoice_col),
        DevolutionsCollection=SimpleNamespace(
            get_instance=lambda: devolution_col
        ),
    )

    with pytest.raises(InvalidOperation, match="Overpayment Error"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_rejects_missing_invoice(monkeypatch):
    receipt = _sample_receipt(total=500, invoice_amount=500)
    receipt_col = SimpleNamespace(
        create_receipt_with_session=AsyncMock(
            side_effect=lambda data, session=None: data
        )
    )
    invoice_col = SimpleNamespace(
        fetch_invoice_by_id_with_session=AsyncMock(return_value=None),
        add_to_amount_paid=AsyncMock(),
    )
    _patch_collections(
        monkeypatch,
        ReceiptsCollection=SimpleNamespace(get_instance=lambda: receipt_col),
        InvoicesCollection=SimpleNamespace(get_instance=lambda: invoice_col),
    )

    with pytest.raises(InvalidOperation, match="Invoice inv-1 not found"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))

    invoice_col.add_to_amount_paid.assert_not_awaited()


def test_process_receipt_checks_funds_before_credit_notes(monkeypatch):
    receipt = _sample_receipt(
        total=100,
        invoice_amount=500,
        credit_notes=[
            AppliedCreditNote(
                creditNoteId="cn-1",
                docNumber="CN-001",
                amountApplied=100,
            )
        ],
    )
    _patch_collections(monkeypatch)

    with pytest.raises(InvalidOperation, match="Discrepancy Error"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_checks_credit_notes_before_devolutions(monkeypatch):
    receipt = _sample_receipt(
        total=0,
        invoice_amount=500,
        credit_notes=[
            AppliedCreditNote(
                creditNoteId="cn-1",
                docNumber="CN-001",
                amountApplied=250,
            )
        ],
        devolutions=[
            AppliedDevolution(
                devolutionId="dev-1",
                docNumber="DEV-001",
                amountApplied=250,
            )
        ],
    )
    credit_note_col = SimpleNamespace(
        fetch_credit_note_by_id=AsyncMock(
            return_value={
                "id": "cn-1",
                "docNumber": "CN-001",
                "status": "emitted",
                "clientId": "client-1",
                "amount": 250,
            }
        )
    )
    _patch_collections(
        monkeypatch,
        CreditNotesCollection=SimpleNamespace(
            get_instance=lambda: credit_note_col
        ),
    )

    with pytest.raises(InvalidOperation, match="no está aprobada"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_checks_devolutions_before_invoices(monkeypatch):
    receipt = _sample_receipt(
        total=0,
        invoice_amount=500,
        devolutions=[
            AppliedDevolution(
                devolutionId="dev-1",
                docNumber="DEV-001",
                amountApplied=500,
            )
        ],
    )
    devolution_col = SimpleNamespace(
        fetch_devolution_by_id=AsyncMock(
            return_value={
                "id": "dev-1",
                "docNumber": "DEV-001",
                "status": "open",
                "clientId": "client-1",
                "originalInvoicePaymentType": "credit",
                "total": 500,
            }
        )
    )
    _patch_collections(
        monkeypatch,
        DevolutionsCollection=SimpleNamespace(
            get_instance=lambda: devolution_col
        ),
    )

    with pytest.raises(InvalidOperation, match="no está confirmada"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_applies_cash_devolution_and_credit_note(monkeypatch):
    receipt = _sample_receipt(
        total=100,
        invoice_amount=500,
        credit_notes=[
            AppliedCreditNote(
                creditNoteId="cn-1",
                docNumber="CN-001",
                amountApplied=200,
            )
        ],
        devolutions=[
            AppliedDevolution(
                devolutionId="dev-1",
                docNumber="DEV-001",
                amountApplied=200,
            )
        ],
    )
    receipt_col = SimpleNamespace(
        create_receipt_with_session=AsyncMock(
            side_effect=lambda data, session=None: data
        )
    )
    invoice_col = SimpleNamespace(
        fetch_invoice_by_id_with_session=AsyncMock(
            return_value={
                "id": "inv-1",
                "branchId": "branch-1",
                "clientId": "client-1",
                "clientInfo": {"name": "Cliente"},
                "docNumber": "FAC-001",
                "saleItems": [],
                "totalCost": 200,
                "total": 1000,
                "amountPaid": 500,
                "status": "partiallyPaid",
                "paymentType": "credit",
                "createdBy": {"id": "u-1", "name": "Cajero"},
                "createdAt": 1000,
            }
        ),
        add_to_amount_paid=AsyncMock(),
    )
    devolution_col = SimpleNamespace(
        fetch_devolution_by_id=AsyncMock(
            return_value={
                "id": "dev-1",
                "docNumber": "DEV-001",
                "status": "confirmed",
                "clientId": "client-1",
                "originalInvoicePaymentType": "credit",
                "total": 200,
            }
        ),
        fetch_devolutions_by_invoice_id=AsyncMock(return_value=[]),
        update_devolution_status_by_id=AsyncMock(),
    )
    credit_note_col = SimpleNamespace(
        fetch_credit_note_by_id=AsyncMock(
            return_value={
                "id": "cn-1",
                "docNumber": "CN-001",
                "status": "approved",
                "clientId": "client-1",
                "amount": 200,
            }
        ),
        update_credit_note_status_by_id=AsyncMock(),
    )
    client_col = SimpleNamespace(
        substract_from_client_balance=AsyncMock(
            return_value={
                "id": "client-1",
                "name": "Cliente",
                "balance": 0,
                "createdAt": 1000,
            }
        )
    )
    client_tx_col = SimpleNamespace(
        create_client_transaction_with_session=AsyncMock()
    )
    _patch_collections(
        monkeypatch,
        ReceiptsCollection=SimpleNamespace(get_instance=lambda: receipt_col),
        InvoicesCollection=SimpleNamespace(get_instance=lambda: invoice_col),
        DevolutionsCollection=SimpleNamespace(
            get_instance=lambda: devolution_col
        ),
        CreditNotesCollection=SimpleNamespace(
            get_instance=lambda: credit_note_col
        ),
        ClientsCollection=SimpleNamespace(get_instance=lambda: client_col),
        ClientTransactionsCollection=SimpleNamespace(
            get_instance=lambda: client_tx_col
        ),
    )

    saved_receipt, _ = asyncio.run(proc_rec_mod.process_receipt(receipt))

    assert saved_receipt.docNumber == "REC-001"
    invoice_col.add_to_amount_paid.assert_awaited_once()
    assert invoice_col.add_to_amount_paid.await_args.kwargs["amount_paid"] == 500
    devolution_col.update_devolution_status_by_id.assert_awaited_once()
    assert (
        devolution_col.update_devolution_status_by_id.await_args.kwargs["status"]
        == "applied"
    )
    credit_note_col.update_credit_note_status_by_id.assert_awaited_once()
    assert (
        credit_note_col.update_credit_note_status_by_id.await_args.kwargs["status"]
        == "applied"
    )

    assert client_col.substract_from_client_balance.await_count == 3
    amounts = [
        call.kwargs["amount"]
        for call in client_col.substract_from_client_balance.await_args_list
    ]
    assert amounts == [200, 200, 100]
    subtypes = [
        call.args[0]["subtype"]
        for call in client_tx_col.create_client_transaction_with_session.await_args_list
    ]
    assert subtypes == ["devolution", "credit_note", "receipt"]
