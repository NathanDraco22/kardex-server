import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from kardex.core.credit_note_register.credit_note_register import CreditNoteRegister
from kardex.core.credit_note_register.process_credit_note import (
    sum_previously_returned_from_devolutions,
)
from kardex.core.default_values import SALE_CLIENT_ID
from kardex.core.devolution_register.devolution_register import DevolutionRegister
from kardex.core.report_manager.report_manager import ReportManager
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.credit_notes import CreateCreditNote
from kardex.repos.v1.devolutions import CreateDevolution, DevolutionInDb
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


def _make_devolution_register(
    invoice,
    *,
    prev_devolutions=None,
    prev_credit_notes=None,
) -> DevolutionRegister:
    devolutions_repo = SimpleNamespace(
        create_devolution=AsyncMock(
            side_effect=lambda body: DevolutionInDb(
                **body.model_dump(),
                id="dev-created",
                createdAt=1000,
            )
        )
    )
    branches_repo = SimpleNamespace(get_branch_by_id=AsyncMock(return_value=SimpleNamespace(id="branch-1")))
    products_repo = SimpleNamespace(get_product_by_ids=AsyncMock(return_value=[SimpleNamespace(id="prod-1")]))
    clients_repo = SimpleNamespace(get_client_by_id=AsyncMock(return_value=SimpleNamespace(id="client-1")))
    invoices_repo = SimpleNamespace(get_invoice_by_id=AsyncMock(return_value=invoice))
    devolutions_col = SimpleNamespace(
        fetch_devolutions_by_invoice_id=AsyncMock(return_value=prev_devolutions or [])
    )
    credit_notes_col = SimpleNamespace(
        fetch_credit_notes_by_invoice_id=AsyncMock(return_value=prev_credit_notes or [])
    )
    return DevolutionRegister(
        devolutions_repo=devolutions_repo,
        branches_repo=branches_repo,
        products_repo=products_repo,
        clients_repo=clients_repo,
        invoices_repo=invoices_repo,
        credit_notes_col=credit_notes_col,
        devolutions_col=devolutions_col,
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


def test_devolution_accepts_unpaid_credit_invoice():
    register = _make_devolution_register(
        SimpleNamespace(id="inv-1", status="open", paymentType="credit", amountPaid=0)
    )
    dev = _sample_devolution(client_id="client-1")
    asyncio.run(register._validate_document(dev))
    assert dev.originalInvoicePaymentType == "credit"


def test_devolution_create_sets_original_payment_type_for_unpaid_credit():
    register = _make_devolution_register(
        SimpleNamespace(id="inv-1", status="open", paymentType="credit", amountPaid=0)
    )
    body = CreateDevolution(
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente"),
        originalInvoiceId="inv-1",
        originalInvoiceDocNumber="FAC-001",
        returnedItems=[_sample_item()],
        description="Devolución de crédito sin abonos",
        totalCost=50,
        total=100,
        createdBy=UserInfo(id="user-1", name="Usuario"),
    )
    created = asyncio.run(register.create_devolution(body))
    assert created.originalInvoicePaymentType == "credit"


def test_devolution_rejects_partially_paid_credit_invoice():
    register = _make_devolution_register(
        SimpleNamespace(
            id="inv-1", status="partiallyPaid", paymentType="credit", amountPaid=50
        )
    )
    with pytest.raises(InvalidOperation, match="abonos o pagadas"):
        asyncio.run(register._validate_document(_sample_devolution(client_id="client-1")))


def test_devolution_rejects_paid_credit_invoice():
    register = _make_devolution_register(
        SimpleNamespace(id="inv-1", status="paid", paymentType="credit", amountPaid=100)
    )
    with pytest.raises(InvalidOperation, match="abonos o pagadas"):
        asyncio.run(register._validate_document(_sample_devolution(client_id="client-1")))


def test_sum_previously_returned_from_devolutions_counts_indexed_and_legacy_and_skips_cancelled():
    sale_items = [
        _sample_item().model_copy(update={"quantity": 3}),
        _sample_item().model_copy(
            update={
                "product": ProductItem(
                    id="prod-2",
                    name="Producto 2",
                    unitName="Unidad",
                    brandName="Marca",
                ),
                "quantity": 2,
            }
        ),
    ]
    devolutions = [
        {
            "id": "dev-1",
            "status": "confirmed",
            "returnedItems": [
                {"invoiceItemIndex": 0, "product": {"id": "prod-1"}, "quantity": 1}
            ],
        },
        {
            "id": "dev-2",
            "status": "open",
            "returnedItems": [{"product": {"id": "prod-1"}, "quantity": 1}],
        },
        {
            "id": "dev-cancelled",
            "status": "cancelled",
            "returnedItems": [
                {"invoiceItemIndex": 0, "product": {"id": "prod-1"}, "quantity": 3}
            ],
        },
    ]

    assert sum_previously_returned_from_devolutions(sale_items, devolutions, 0) == 2
    assert sum_previously_returned_from_devolutions(sale_items, devolutions, 1) == 0


def test_devolution_rejects_item_already_returned_in_credit_note():
    sale_item = _sample_item().model_copy(update={"quantity": 2})
    invoice = SimpleNamespace(
        id="inv-1",
        status="open",
        paymentType="credit",
        amountPaid=0,
        invoiceDiscount=0,
        saleItems=[sale_item],
    )
    prev_credit_notes = [
        {
            "status": "approved",
            "returnedItems": [
                {"invoiceItemIndex": 0, "product": {"id": "prod-1"}, "quantity": 2}
            ],
        }
    ]
    register = _make_devolution_register(invoice, prev_credit_notes=prev_credit_notes)
    with pytest.raises(InvalidOperation, match="saldo disponible"):
        asyncio.run(register._validate_document(_sample_devolution(client_id="client-1")))


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
