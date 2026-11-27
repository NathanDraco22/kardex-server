import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.composite.composite_controller import CompositeController
from kardex.core.devolution_register import process_devolution as proc_dev_mod
from kardex.core.receipt_register import process_receipt as proc_rec_mod
from kardex.core.receipt_register import reverse_receipt as rev_rec_mod
from kardex.core.report_manager.report_manager import ReportManager
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.devolutions import DevolutionInDb
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.receipts import (
    AppliedDevolution,
    AppliedInvoice,
    CreateReceipt,
    ReceiptInDb,
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


def _sample_devolution(*, bon_quantity: int = 0) -> DevolutionInDb:
    return DevolutionInDb(
        id="dev-1",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente"),
        docNumber="DEV-001",
        originalInvoiceId="inv-1",
        originalInvoiceDocNumber="FAC-001",
        originalInvoicePaymentType="credit",
        returnedItems=[
            SaleItem(
                product=ProductItem(
                    id="prod-1",
                    name="Producto 1",
                    unitName="Unidad",
                    brandName="Marca",
                ),
                quantity=5,
                bonQuantity=bon_quantity,
                cost=50,
                price=100,
                subTotal=500,
                total=500,
                invoiceItemIndex=0,
            )
        ],
        description="Devolución con bonificación",
        status="open",
        totalCost=350,
        total=500,
        createdBy=UserInfo(id="user-1", name="Usuario"),
        createdAt=1000,
    )


def _sample_receipt(
    *,
    client_id: str = "client-1",
    devolutions: list[AppliedDevolution] | None = None,
    total: int = 0,
    invoice_amount: int = 500,
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
        appliedCreditNotes=[],
        paymentMethod="cash",
        total=total,
        createdBy=UserInfo(id="user-1", name="Cajero"),
    )


def test_process_devolution_reenters_quantity_plus_bon_quantity(monkeypatch):
    dev = _sample_devolution(bon_quantity=2)
    update_stock_mock = AsyncMock(
        return_value={
            "id": "pa-1",
            "productId": "prod-1",
            "branchId": "branch-1",
            "currentStock": 17,
            "promiseStock": 0,
            "averageCost": 50,
            "lastCost": 50,
            "createdAt": 1000,
        }
    )
    tx_mock = AsyncMock()
    dev_col = SimpleNamespace(
        update_devolution_status_by_id=AsyncMock(
            return_value={**dev.model_dump(), "status": "confirmed"}
        )
    )
    prd_acc_col = SimpleNamespace(update_product_account_balance_data=update_stock_mock)
    prd_tx_col = SimpleNamespace(create_many_product_transactions_with_session=tx_mock)

    monkeypatch.setattr(proc_dev_mod, "MongoService", lambda: _FakeMongoService())
    monkeypatch.setattr(
        proc_dev_mod, "fetch_product_types_map", AsyncMock(return_value={"prod-1": "item"})
    )
    monkeypatch.setattr(
        proc_dev_mod,
        "DevolutionsCollection",
        SimpleNamespace(get_instance=lambda: dev_col),
    )
    monkeypatch.setattr(
        proc_dev_mod,
        "ProductAccountsCollection",
        SimpleNamespace(get_instance=lambda: prd_acc_col),
    )
    monkeypatch.setattr(
        proc_dev_mod,
        "ProductTransactionsCollection",
        SimpleNamespace(get_instance=lambda: prd_tx_col),
    )

    confirmed = asyncio.run(proc_dev_mod.process_devolution(dev))
    assert confirmed.status == "confirmed"
    assert update_stock_mock.await_args.kwargs["add_to_current_stock"] == 7
    created_txs = tx_mock.await_args.args[0]
    assert created_txs[0]["quantity"] == 7


@pytest.mark.parametrize(
    "dev_doc,expected_match",
    [
        (None, "no encontrada"),
        (
            {
                "id": "dev-1",
                "docNumber": "DEV-001",
                "status": "open",
                "clientId": "client-1",
                "originalInvoicePaymentType": "credit",
                "total": 500,
            },
            "no está confirmada",
        ),
        (
            {
                "id": "dev-1",
                "docNumber": "DEV-001",
                "status": "confirmed",
                "clientId": "other-client",
                "originalInvoicePaymentType": "credit",
                "total": 500,
            },
            "otro cliente",
        ),
        (
            {
                "id": "dev-1",
                "docNumber": "DEV-001",
                "status": "confirmed",
                "clientId": "client-1",
                "originalInvoicePaymentType": "cash",
                "total": 500,
            },
            "factura de contado",
        ),
    ],
)
def test_process_receipt_rejects_invalid_applied_devolution(
    monkeypatch, dev_doc, expected_match
):
    receipt = _sample_receipt(
        devolutions=[
            AppliedDevolution(devolutionId="dev-1", docNumber="DEV-001", amountApplied=500)
        ]
    )
    dev_col = SimpleNamespace(
        fetch_devolution_by_id=AsyncMock(return_value=dev_doc),
    )
    monkeypatch.setattr(proc_rec_mod, "MongoService", lambda: _FakeMongoService())
    monkeypatch.setattr(
        proc_rec_mod, "ReceiptsCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod, "InvoicesCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod, "DevolutionsCollection", SimpleNamespace(get_instance=lambda: dev_col)
    )
    monkeypatch.setattr(
        proc_rec_mod, "CreditNotesCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod, "ClientTransactionsCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod, "ClientsCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod,
        "CounterManager",
        lambda: SimpleNamespace(next_receipt_number=AsyncMock(return_value="REC-001")),
    )

    with pytest.raises(InvalidOperation, match=expected_match):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_process_receipt_rejects_invoice_with_open_devolution(monkeypatch):
    receipt = _sample_receipt(total=500, invoice_amount=500)
    invoice_doc = {
        "id": "inv-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": {"name": "Cliente"},
        "docNumber": "FAC-001",
        "saleItems": [],
        "totalCost": 200,
        "total": 500,
        "amountPaid": 0,
        "status": "open",
        "paymentType": "credit",
        "createdBy": {"id": "u-1", "name": "Cajero"},
        "createdAt": 1000,
    }
    receipt_col = SimpleNamespace(
        create_receipt_with_session=AsyncMock(
            side_effect=lambda data, session=None: data
        )
    )
    invoice_col = SimpleNamespace(
        fetch_invoice_by_id_with_session=AsyncMock(return_value=invoice_doc),
    )
    dev_col = SimpleNamespace(
        fetch_devolutions_by_invoice_id=AsyncMock(
            return_value=[{"id": "dev-open", "status": "open"}]
        )
    )

    monkeypatch.setattr(proc_rec_mod, "MongoService", lambda: _FakeMongoService())
    monkeypatch.setattr(
        proc_rec_mod, "ReceiptsCollection", SimpleNamespace(get_instance=lambda: receipt_col)
    )
    monkeypatch.setattr(
        proc_rec_mod, "InvoicesCollection", SimpleNamespace(get_instance=lambda: invoice_col)
    )
    monkeypatch.setattr(
        proc_rec_mod, "DevolutionsCollection", SimpleNamespace(get_instance=lambda: dev_col)
    )
    monkeypatch.setattr(
        proc_rec_mod, "CreditNotesCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod, "ClientTransactionsCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod, "ClientsCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        proc_rec_mod,
        "CounterManager",
        lambda: SimpleNamespace(next_receipt_number=AsyncMock(return_value="REC-001")),
    )

    with pytest.raises(InvalidOperation, match="pendiente de confirmar"):
        asyncio.run(proc_rec_mod.process_receipt(receipt))


def test_reverse_receipt_restores_devolution_to_confirmed(monkeypatch):
    receipt = ReceiptInDb(
        id="rec-1",
        branchId="branch-1",
        clientInfo=ClientInfo(name="Cliente"),
        clientId="client-1",
        docNumber="REC-001",
        appliedInvoices=[
            AppliedInvoice(invoiceId="inv-1", docNumber="FAC-001", amountApplied=300)
        ],
        appliedDevolutions=[
            AppliedDevolution(devolutionId="dev-1", docNumber="DEV-001", amountApplied=300)
        ],
        appliedCreditNotes=[],
        paymentMethod="cash",
        total=0,
        createdBy=UserInfo(id="u-1", name="Cajero"),
        createdAt=1000,
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
        "amountPaid": 300,
        "status": "partiallyPaid",
        "paymentType": "credit",
        "createdBy": {"id": "u-1", "name": "Cajero"},
        "createdAt": 1000,
    }
    update_dev_mock = AsyncMock(return_value={"id": "dev-1", "status": "confirmed"})
    receipt_col = SimpleNamespace(
        delete_receipt_by_id_with_session=AsyncMock(return_value=receipt.model_dump())
    )
    invoice_col = SimpleNamespace(
        fetch_invoice_by_id_with_session=AsyncMock(return_value=invoice_doc),
        subtract_from_amount_paid=AsyncMock(),
    )
    dev_col = SimpleNamespace(update_devolution_status_by_id=update_dev_mock)
    client_col = SimpleNamespace(
        add_to_client_balance=AsyncMock(
            return_value={"id": "client-1", "name": "Cliente", "balance": 500, "createdAt": 1000}
        )
    )
    client_tx_col = SimpleNamespace(create_client_transaction_with_session=AsyncMock())

    monkeypatch.setattr(rev_rec_mod, "MongoService", lambda: _FakeMongoService())
    monkeypatch.setattr(
        rev_rec_mod, "ReceiptsCollection", SimpleNamespace(get_instance=lambda: receipt_col)
    )
    monkeypatch.setattr(
        rev_rec_mod, "InvoicesCollection", SimpleNamespace(get_instance=lambda: invoice_col)
    )
    monkeypatch.setattr(
        rev_rec_mod, "DevolutionsCollection", SimpleNamespace(get_instance=lambda: dev_col)
    )
    monkeypatch.setattr(
        rev_rec_mod, "CreditNotesCollection", SimpleNamespace(get_instance=lambda: SimpleNamespace())
    )
    monkeypatch.setattr(
        rev_rec_mod,
        "ClientTransactionsCollection",
        SimpleNamespace(get_instance=lambda: client_tx_col),
    )
    monkeypatch.setattr(
        rev_rec_mod, "ClientsCollection", SimpleNamespace(get_instance=lambda: client_col)
    )

    asyncio.run(rev_rec_mod.reverse_receipt(receipt))
    assert update_dev_mock.await_args.kwargs["status"] == "confirmed"


def test_composite_fetches_all_branches_and_counts_only_confirmed_devolutions():
    captured_params = []

    async def _fake_get_active_devs(params):
        captured_params.append(params)
        return [
            _sample_devolution().model_copy(update={"id": "dev-conf", "status": "confirmed", "total": 200}),
            _sample_devolution().model_copy(update={"id": "dev-open", "status": "open", "total": 300}),
        ]

    pending_invoice = InvoiceInDb(
        id="inv-1",
        branchId="branch-A",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente"),
        docNumber="FAC-001",
        saleItems=[],
        totalCost=400,
        total=1000,
        amountPaid=0,
        status="open",
        paymentType="credit",
        createdBy=UserInfo(id="u-1", name="Cajero"),
        createdAt=1000,
    )
    controller = CompositeController(
        invoices_repo=SimpleNamespace(
            get_pending_to_paid_invoices=AsyncMock(return_value=[pending_invoice])
        ),
        devolutions_repo=SimpleNamespace(get_all_active_devolutions=_fake_get_active_devs),
        credit_notes_repo=SimpleNamespace(get_credit_notes_by_client_id=AsyncMock(return_value=[])),
    )

    res = asyncio.run(controller.get_client_pending_invoices("client-1", "branch-B"))
    assert captured_params[0].branchId is None
    assert len(res.devolutions) == 2
    assert res.summary.totalDevolutions == 200
    assert res.summary.netTotalPayable == 800


def test_report_manager_uses_total_receipts_for_total_receipt_cash():
    manager = ReportManager.__new__(ReportManager)
    manager.branches_repo = SimpleNamespace(
        get_all_commerce_branches=AsyncMock(return_value=[SimpleNamespace(id="branch-1")])
    )
    manager.invoices_repo = SimpleNamespace(get_invoice_summary=AsyncMock(return_value=[]))
    manager.receipts_repo = SimpleNamespace(
        get_branch_receipt_amounts_summary=AsyncMock(
            return_value=[
                SimpleNamespace(
                    branchId="branch-1",
                    totalAppliedInvoices=1000,
                    totalAppliedDevolutions=700,
                    totalReceipts=300,
                    receiptCount=1,
                )
            ]
        )
    )
    manager.devolutions_repo = SimpleNamespace(
        get_confirmed_devolutions_total=AsyncMock(return_value=0)
    )

    summary = asyncio.run(manager.get_invoice_summary(startDate=100, endDate=200))
    assert summary is not None
    assert summary.totalReceiptCash == 300
    assert summary.totalReceipts == 300
