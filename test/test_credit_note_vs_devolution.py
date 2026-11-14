import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from kardex.core.credit_note_register.credit_note_register import CreditNoteRegister
from kardex.core.default_values import SALE_CLIENT_ID
from kardex.core.devolution_register.devolution_register import DevolutionRegister
from kardex.core.report_manager.report_manager import ReportManager
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.credit_notes import CreateCreditNote
from kardex.repos.v1.devolutions import DevolutionInDb
from kardex.tools import InvalidOperation


def _sample_item() -> SaleItem:
    return SaleItem(
        product=ProductItem(
            id="prod-1",
            name="Producto 1",
            unitName="Unidad",
            brandName="Marca",
        ),
        quantity=1,
        cost=50,
        price=100,
        subTotal=100,
        total=100,
    )


def _sample_credit_note(invoice_id: str = "inv-1") -> CreateCreditNote:
    return CreateCreditNote(
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente"),
        type="devolution",
        originalInvoiceId=invoice_id,
        originalInvoiceDocNumber="FAC-001",
        returnedItems=[_sample_item()],
        amount=100,
        createdBy=UserInfo(id="user-1", name="Usuario"),
    )


def _sample_devolution(
    client_id: str = SALE_CLIENT_ID, invoice_id: str = "inv-1"
) -> DevolutionInDb:
    return DevolutionInDb(
        id="dev-1",
        branchId="branch-1",
        clientId=client_id,
        clientInfo=ClientInfo(name="Cliente"),
        docNumber="DEV-001",
        originalInvoiceId=invoice_id,
        originalInvoiceDocNumber="FAC-001",
        returnedItems=[_sample_item()],
        description="Devolución",
        status="open",
        totalCost=50,
        total=100,
        createdBy=UserInfo(id="user-1", name="Usuario"),
        createdAt=1000,
    )


def _make_credit_note_register(invoice) -> CreditNoteRegister:
    branches_repo = SimpleNamespace(get_branch_by_id=AsyncMock(return_value=SimpleNamespace(id="branch-1")))
    clients_repo = SimpleNamespace(get_client_by_id=AsyncMock(return_value=SimpleNamespace(id="client-1")))
    invoices_repo = SimpleNamespace(get_invoice_by_id=AsyncMock(return_value=invoice))
    return CreditNoteRegister(
        branches_repo=branches_repo,
        clients_repo=clients_repo,
        invoices_repo=invoices_repo,
    )


def _make_devolution_register(invoice) -> DevolutionRegister:
    devolutions_repo = SimpleNamespace()
    branches_repo = SimpleNamespace(get_branch_by_id=AsyncMock(return_value=SimpleNamespace(id="branch-1")))
    products_repo = SimpleNamespace(get_product_by_ids=AsyncMock(return_value=[SimpleNamespace(id="prod-1")]))
    clients_repo = SimpleNamespace(get_client_by_id=AsyncMock(return_value=SimpleNamespace(id="client-1")))
    invoices_repo = SimpleNamespace(get_invoice_by_id=AsyncMock(return_value=invoice))
    return DevolutionRegister(
        devolutions_repo=devolutions_repo,
        branches_repo=branches_repo,
        products_repo=products_repo,
        clients_repo=clients_repo,
        invoices_repo=invoices_repo,
    )


def test_credit_note_rejects_cash_invoice():
    register = _make_credit_note_register(
        SimpleNamespace(id="inv-1", status="paid", paymentType="cash")
    )
    with pytest.raises(InvalidOperation, match="credit invoices"):
        asyncio.run(register._validate_credit_note(_sample_credit_note()))


def test_credit_note_rejects_cancelled_invoice():
    register = _make_credit_note_register(
        SimpleNamespace(id="inv-1", status="cancelled", paymentType="credit")
    )
    with pytest.raises(InvalidOperation, match="cancelled"):
        asyncio.run(register._validate_credit_note(_sample_credit_note()))


def test_credit_note_accepts_paid_credit_invoice():
    register = _make_credit_note_register(
        SimpleNamespace(id="inv-1", status="paid", paymentType="credit")
    )
    asyncio.run(register._validate_credit_note(_sample_credit_note()))


def test_devolution_rejects_credit_invoice():
    register = _make_devolution_register(
        SimpleNamespace(id="inv-1", status="open", paymentType="credit", amountPaid=0)
    )
    with pytest.raises(InvalidOperation, match="cash invoices"):
        asyncio.run(register._validate_document(_sample_devolution()))


def test_devolution_accepts_cash_invoice_for_registered_client():
    register = _make_devolution_register(
        SimpleNamespace(id="inv-1", status="paid", paymentType="cash", amountPaid=100)
    )
    asyncio.run(register._validate_document(_sample_devolution(client_id="client-1")))


def test_devolution_accepts_cash_invoice_for_anon_client():
    register = _make_devolution_register(
        SimpleNamespace(id="inv-1", status="paid", paymentType="transfer", amountPaid=100)
    )
    asyncio.run(register._validate_document(_sample_devolution(client_id=SALE_CLIENT_ID)))


def test_report_manager_includes_total_cash_devolutions():
    manager = ReportManager.__new__(ReportManager)
    manager.branches_repo = SimpleNamespace(
        get_all_commerce_branches=AsyncMock(return_value=[SimpleNamespace(id="branch-1")])
    )
    manager.invoices_repo = SimpleNamespace(get_invoice_summary=AsyncMock(return_value=[]))
    manager.receipts_repo = SimpleNamespace(
        get_branch_receipt_amounts_summary=AsyncMock(return_value=[])
    )
    manager.devolutions_repo = SimpleNamespace(
        get_confirmed_devolutions_total=AsyncMock(return_value=3500)
    )

    summary = asyncio.run(manager.get_invoice_summary(startDate=100, endDate=200))
    assert summary is not None
    assert summary.totalCashDevolutions == 3500
