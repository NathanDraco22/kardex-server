from typing import Any

import pytest

from kardex.core.credit_note_register.credit_note_policy import CreditNotePolicy
from kardex.core.default_values import SALE_CLIENT_ID
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.credit_notes import CreateCreditNote, CreditNoteInDb
from kardex.repos.v1.invoices import InvoiceInDb

APPROVAL_REASON = (
    "Solo se pueden aprobar notas de crédito en estado emitida. "
    "Estado actual: {status}."
)
REJECTION_REASON = (
    "Solo se pueden rechazar notas de crédito en estado emitida. "
    "Estado actual: {status}."
)


def _sale_item() -> SaleItem:
    return SaleItem(
        product=ProductItem(id="product-1", name="Producto", unitName="Unidad"),
        quantity=1,
        cost=500,
        price=1000,
        subTotal=1000,
        total=1000,
    )


def _create_credit_note(**overrides: Any) -> CreateCreditNote:
    data: dict[str, Any] = {
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "type": "amount",
        "amount": 100,
        "description": "Motivo detallado",
        "createdBy": UserInfo(id="user-1", name="Cajero"),
    }
    data.update(overrides)
    return CreateCreditNote(**data)


def _credit_note(**overrides: Any) -> CreditNoteInDb:
    data: dict[str, Any] = {
        "id": "cn-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "type": "amount",
        "amount": 100,
        "description": "Motivo detallado",
        "status": "emitted",
        "createdBy": UserInfo(id="user-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return CreditNoteInDb(**data)


def _invoice(**overrides: Any) -> InvoiceInDb:
    data: dict[str, Any] = {
        "id": "invoice-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "saleItems": [_sale_item()],
        "status": "open",
        "paymentType": "credit",
        "totalCost": 500,
        "total": 1000,
        "createdBy": UserInfo(id="user-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return InvoiceInDb(**data)


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({}, None),
        (
            {"clientId": SALE_CLIENT_ID},
            "Credit notes by amount require a registered client.",
        ),
        ({"amount": 0}, "Credit note amount must be greater than 0."),
        ({"amount": -100}, "Credit note amount must be greater than 0."),
        (
            {"description": ""},
            "A detailed reason/description is required for credit notes by amount.",
        ),
        (
            {"description": "   "},
            "A detailed reason/description is required for credit notes by amount.",
        ),
    ],
)
def test_amount_request_decision(
    overrides: dict[str, Any], expected_reason: str | None
) -> None:
    decision = CreditNotePolicy().amount_request_decision(
        _create_credit_note(**overrides), sale_client_id=SALE_CLIENT_ID
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_amount_request_decision_checks_client_before_amount_and_description():
    doc = _create_credit_note(
        clientId=SALE_CLIENT_ID,
        amount=0,
        description="",
    )

    decision = CreditNotePolicy().amount_request_decision(
        doc, sale_client_id=SALE_CLIENT_ID
    )

    assert decision.reason == "Credit notes by amount require a registered client."


@pytest.mark.parametrize(
    ("original_invoice_id", "expected_reason"),
    [
        (
            "",
            "Devolution credit notes require an original invoice.",
        ),
        ("invoice-1", None),
    ],
)
def test_devolution_request_decision(
    original_invoice_id: str, expected_reason: str | None
) -> None:
    doc = _create_credit_note(
        type="devolution", originalInvoiceId=original_invoice_id
    )

    decision = CreditNotePolicy().devolution_request_decision(doc)

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({}, None),
        (
            {"status": "cancelled"},
            "Cannot create a credit note for a cancelled invoice.",
        ),
        (
            {"paymentType": "cash"},
            "Credit notes by devolution only apply to credit invoices. "
            "Use devolutions for cash invoices.",
        ),
    ],
)
def test_devolution_invoice_decision(
    overrides: dict[str, Any], expected_reason: str | None
) -> None:
    decision = CreditNotePolicy().devolution_invoice_decision(_invoice(**overrides))

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_devolution_invoice_decision_checks_cancelled_before_payment_type():
    invoice = _invoice(status="cancelled", paymentType="cash")

    decision = CreditNotePolicy().devolution_invoice_decision(invoice)

    assert decision.reason == "Cannot create a credit note for a cancelled invoice."


@pytest.mark.parametrize(
    ("returned_items", "expected_reason"),
    [
        (
            [],
            "Devolution credit notes must include returned items.",
        ),
        ([_sale_item()], None),
    ],
)
def test_devolution_items_decision(
    returned_items: list[SaleItem], expected_reason: str | None
) -> None:
    doc = _create_credit_note(type="devolution", returnedItems=returned_items)

    decision = CreditNotePolicy().devolution_items_decision(doc)

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        ("emitted", None),
        ("open", APPROVAL_REASON.format(status="open")),
        ("approved", APPROVAL_REASON.format(status="approved")),
        ("confirmed", APPROVAL_REASON.format(status="confirmed")),
        ("rejected", APPROVAL_REASON.format(status="rejected")),
        ("cancelled", APPROVAL_REASON.format(status="cancelled")),
        ("applied", APPROVAL_REASON.format(status="applied")),
    ],
)
def test_approval_decision(status: str, expected_reason: str | None) -> None:
    decision = CreditNotePolicy().approval_decision(_credit_note(status=status))

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        ("emitted", None),
        ("open", REJECTION_REASON.format(status="open")),
        ("approved", REJECTION_REASON.format(status="approved")),
        ("confirmed", REJECTION_REASON.format(status="confirmed")),
        ("rejected", REJECTION_REASON.format(status="rejected")),
        ("cancelled", REJECTION_REASON.format(status="cancelled")),
        ("applied", REJECTION_REASON.format(status="applied")),
    ],
)
def test_rejection_decision(status: str, expected_reason: str | None) -> None:
    decision = CreditNotePolicy().rejection_decision(_credit_note(status=status))

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        (
            "applied",
            "No se puede eliminar una nota de crédito que ya fue aplicada "
            "en un recibo de pago.",
        ),
        ("emitted", None),
        ("open", None),
        ("approved", None),
        ("confirmed", None),
        ("rejected", None),
        ("cancelled", None),
    ],
)
def test_reversal_decision(status: str, expected_reason: str | None) -> None:
    decision = CreditNotePolicy().reversal_decision(_credit_note(status=status))

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("total", "expected_reason"),
    [
        (1, None),
        (1000, None),
        (0, "Credit note total must be greater than 0."),
        (-1, "Credit note total must be greater than 0."),
    ],
)
def test_recalculated_total_decision(total: int, expected_reason: str | None) -> None:
    decision = CreditNotePolicy().recalculated_total_decision(total)

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason
