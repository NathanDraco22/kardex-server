from typing import Any

import pytest

from kardex.core.policies import ReceiptApplicationPolicy
from kardex.repos.v1.common.models import ClientInfo, UserInfo
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.receipts import (
    AppliedCreditNote,
    AppliedDevolution,
    AppliedInvoice,
)


def _applied_credit_note(amount_applied: int = 500) -> AppliedCreditNote:
    return AppliedCreditNote(
        creditNoteId="cn-1",
        docNumber="CN-001",
        amountApplied=amount_applied,
    )


def _credit_note(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "docNumber": "CN-001",
        "status": "approved",
        "clientId": "client-1",
        "amount": 500,
    }
    data.update(overrides)
    return data


def _applied_devolution(amount_applied: int = 500) -> AppliedDevolution:
    return AppliedDevolution(
        devolutionId="dev-1",
        docNumber="DEV-001",
        amountApplied=amount_applied,
    )


def _devolution(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "docNumber": "DEV-001",
        "status": "confirmed",
        "clientId": "client-1",
        "originalInvoicePaymentType": "credit",
        "total": 500,
    }
    data.update(overrides)
    return data


def _applied_invoice(
    invoice_id: str = "inv-1", amount_applied: int = 500
) -> AppliedInvoice:
    return AppliedInvoice(
        invoiceId=invoice_id,
        docNumber="FAC-001",
        amountApplied=amount_applied,
    )


def _invoice(**overrides: Any) -> InvoiceInDb:
    data: dict[str, Any] = {
        "id": "inv-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "docNumber": "FAC-001",
        "saleItems": [],
        "totalCost": 0,
        "total": 500,
        "amountPaid": 100,
        "status": "open",
        "paymentType": "credit",
        "createdBy": UserInfo(id="user-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return InvoiceInDb(**data)


@pytest.mark.parametrize(
    ("total_funds", "total_applied", "expected_reason"),
    [
        (500, 500, None),
        (
            500,
            400,
            "Discrepancy Error: Total Funds (500) does not match "
            "Total Applied to Invoices (400).",
        ),
        (
            400,
            500,
            "Discrepancy Error: Total Funds (400) does not match "
            "Total Applied to Invoices (500).",
        ),
    ],
)
def test_funds_decision(
    total_funds: int, total_applied: int, expected_reason: str | None
) -> None:
    decision = ReceiptApplicationPolicy().funds_decision(
        total_funds=total_funds, total_applied=total_applied
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("seen_ids", "expected_reason"),
    [
        (set(), None),
        (
            {"cn-1"},
            "Nota de crédito duplicada en el recibo: cn-1.",
        ),
    ],
)
def test_credit_note_duplicate_decision(
    seen_ids: set[str], expected_reason: str | None
) -> None:
    before = set(seen_ids)

    decision = ReceiptApplicationPolicy().credit_note_duplicate_decision(
        "cn-1", seen_ids
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason
    assert seen_ids == before


@pytest.mark.parametrize("credit_note", [None, {}])
def test_applied_credit_note_decision_missing(
    credit_note: dict[str, Any] | None,
) -> None:
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(), credit_note, client_id="client-1"
    )

    assert decision.allowed is False
    assert decision.reason == "Nota de crédito cn-1 no encontrada."


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        ("approved", None),
        ("confirmed", None),
        (
            "emitted",
            "La nota de crédito #CN-001 no está aprobada (estado: emitted).",
        ),
        ("open", "La nota de crédito #CN-001 no está aprobada (estado: open)."),
        (
            "rejected",
            "La nota de crédito #CN-001 no está aprobada (estado: rejected).",
        ),
        (
            "cancelled",
            "La nota de crédito #CN-001 no está aprobada (estado: cancelled).",
        ),
        (
            "applied",
            "La nota de crédito #CN-001 no está aprobada (estado: applied).",
        ),
    ],
)
def test_applied_credit_note_decision_status(
    status: str, expected_reason: str | None
) -> None:
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(),
        _credit_note(status=status),
        client_id="client-1",
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_applied_credit_note_decision_other_client() -> None:
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(),
        _credit_note(clientId="other-client"),
        client_id="client-1",
    )

    assert decision.allowed is False
    assert decision.reason == (
        "La nota de crédito #CN-001 pertenece a otro cliente."
    )


def test_applied_credit_note_decision_checks_status_before_client_and_amount():
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(amount_applied=0),
        _credit_note(status="emitted", clientId="other-client", amount=0),
        client_id="client-1",
    )

    assert decision.reason == (
        "La nota de crédito #CN-001 no está aprobada (estado: emitted)."
    )


def test_applied_credit_note_decision_checks_client_before_amount():
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(amount_applied=0),
        _credit_note(clientId="other-client", amount=0),
        client_id="client-1",
    )

    assert decision.reason == (
        "La nota de crédito #CN-001 pertenece a otro cliente."
    )


@pytest.mark.parametrize(
    ("amount_applied", "credit_note", "expected_reason"),
    [
        (500, _credit_note(), None),
        (
            0,
            _credit_note(),
            "El monto aplicado (0) de la nota de crédito #CN-001 es inválido "
            "(total: 500).",
        ),
        (
            -10,
            _credit_note(),
            "El monto aplicado (-10) de la nota de crédito #CN-001 es inválido "
            "(total: 500).",
        ),
        (
            501,
            _credit_note(),
            "El monto aplicado (501) de la nota de crédito #CN-001 es inválido "
            "(total: 500).",
        ),
        (
            100,
            _credit_note(amount=None),
            "El monto aplicado (100) de la nota de crédito #CN-001 es inválido "
            "(total: 0).",
        ),
    ],
)
def test_applied_credit_note_decision_amount(
    amount_applied: int,
    credit_note: dict[str, Any],
    expected_reason: str | None,
) -> None:
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(amount_applied),
        credit_note,
        client_id="client-1",
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_applied_credit_note_decision_handles_missing_optional_fields():
    decision = ReceiptApplicationPolicy().applied_credit_note_decision(
        _applied_credit_note(amount_applied=100),
        {"status": "approved", "clientId": "client-1"},
        client_id="client-1",
    )

    assert decision.reason == (
        "El monto aplicado (100) de la nota de crédito # es inválido (total: 0)."
    )


@pytest.mark.parametrize(
    ("seen_ids", "expected_reason"),
    [
        (set(), None),
        (
            {"dev-1"},
            "Devolución duplicada en el recibo: dev-1.",
        ),
    ],
)
def test_devolution_duplicate_decision(
    seen_ids: set[str], expected_reason: str | None
) -> None:
    before = set(seen_ids)

    decision = ReceiptApplicationPolicy().devolution_duplicate_decision(
        "dev-1", seen_ids
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason
    assert seen_ids == before


@pytest.mark.parametrize("devolution", [None, {}])
def test_applied_devolution_decision_missing(
    devolution: dict[str, Any] | None,
) -> None:
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(), devolution, client_id="client-1"
    )

    assert decision.allowed is False
    assert decision.reason == "Devolución dev-1 no encontrada."


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        ("confirmed", None),
        ("open", "La devolución #DEV-001 no está confirmada (estado: open)."),
        (
            "applied",
            "La devolución #DEV-001 no está confirmada (estado: applied).",
        ),
        (
            "cancelled",
            "La devolución #DEV-001 no está confirmada (estado: cancelled).",
        ),
    ],
)
def test_applied_devolution_decision_status(
    status: str, expected_reason: str | None
) -> None:
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(),
        _devolution(status=status),
        client_id="client-1",
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_applied_devolution_decision_other_client() -> None:
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(),
        _devolution(clientId="other-client"),
        client_id="client-1",
    )

    assert decision.allowed is False
    assert decision.reason == "La devolución #DEV-001 pertenece a otro cliente."


def test_applied_devolution_decision_checks_status_before_client_and_amount():
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(amount_applied=0),
        _devolution(
            status="open",
            clientId="other-client",
            originalInvoicePaymentType="cash",
            total=0,
        ),
        client_id="client-1",
    )

    assert decision.reason == (
        "La devolución #DEV-001 no está confirmada (estado: open)."
    )


def test_applied_devolution_decision_checks_client_before_payment_and_amount():
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(amount_applied=0),
        _devolution(
            clientId="other-client",
            originalInvoicePaymentType="cash",
            total=0,
        ),
        client_id="client-1",
    )

    assert decision.reason == "La devolución #DEV-001 pertenece a otro cliente."


@pytest.mark.parametrize(
    ("payment_type", "expected_reason"),
    [
        ("credit", None),
        (None, None),
        (
            "cash",
            "La devolución #DEV-001 proviene de una factura de contado y no "
            "puede aplicarse en recibos.",
        ),
    ],
)
def test_applied_devolution_decision_payment_type(
    payment_type: str | None, expected_reason: str | None
) -> None:
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(),
        _devolution(originalInvoicePaymentType=payment_type),
        client_id="client-1",
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("amount_applied", "devolution", "expected_reason"),
    [
        (500, _devolution(), None),
        (
            0,
            _devolution(),
            "El monto aplicado (0) de la devolución #DEV-001 es inválido "
            "(total: 500).",
        ),
        (
            -10,
            _devolution(),
            "El monto aplicado (-10) de la devolución #DEV-001 es inválido "
            "(total: 500).",
        ),
        (
            501,
            _devolution(),
            "El monto aplicado (501) de la devolución #DEV-001 es inválido "
            "(total: 500).",
        ),
        (
            100,
            _devolution(total=None),
            "El monto aplicado (100) de la devolución #DEV-001 es inválido "
            "(total: 0).",
        ),
    ],
)
def test_applied_devolution_decision_amount(
    amount_applied: int,
    devolution: dict[str, Any],
    expected_reason: str | None,
) -> None:
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(amount_applied),
        devolution,
        client_id="client-1",
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_applied_devolution_decision_checks_payment_type_before_amount():
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(amount_applied=0),
        _devolution(originalInvoicePaymentType="cash", total=0),
        client_id="client-1",
    )

    assert decision.reason == (
        "La devolución #DEV-001 proviene de una factura de contado y no "
        "puede aplicarse en recibos."
    )


def test_applied_devolution_decision_handles_missing_optional_fields():
    decision = ReceiptApplicationPolicy().applied_devolution_decision(
        _applied_devolution(amount_applied=100),
        {"status": "confirmed", "clientId": "client-1"},
        client_id="client-1",
    )

    assert decision.reason == (
        "El monto aplicado (100) de la devolución # es inválido (total: 0)."
    )


def test_applied_invoice_decision_missing_takes_precedence() -> None:
    decision = ReceiptApplicationPolicy().applied_invoice_decision(
        _applied_invoice(invoice_id="inv-missing"),
        None,
        has_open_devolution=True,
    )

    assert decision.allowed is False
    assert decision.reason == "Invoice inv-missing not found"


def test_applied_invoice_decision_rejects_open_devolution() -> None:
    decision = ReceiptApplicationPolicy().applied_invoice_decision(
        _applied_invoice(),
        _invoice(),
        has_open_devolution=True,
    )

    assert decision.allowed is False
    assert decision.reason == (
        "La factura #FAC-001 tiene una devolución pendiente de confirmar."
    )


def test_applied_invoice_decision_rejects_overpayment() -> None:
    decision = ReceiptApplicationPolicy().applied_invoice_decision(
        _applied_invoice(amount_applied=500),
        _invoice(total=500, amountPaid=100),
    )

    assert decision.allowed is False
    assert decision.reason == (
        "Overpayment Error: Payment of 500 exceeds pending balance of 400 "
        "for Invoice FAC-001"
    )


def test_applied_invoice_decision_allows_exact_pending_balance() -> None:
    decision = ReceiptApplicationPolicy().applied_invoice_decision(
        _applied_invoice(amount_applied=400),
        _invoice(total=500, amountPaid=100),
    )

    assert decision.allowed is True
    assert decision.reason is None


def test_applied_invoice_decision_allows_zero_with_positive_pending() -> None:
    decision = ReceiptApplicationPolicy().applied_invoice_decision(
        _applied_invoice(amount_applied=0),
        _invoice(total=500, amountPaid=100),
    )

    assert decision.allowed is True
    assert decision.reason is None


def test_applied_invoice_decision_rejects_zero_with_paid_over_total() -> None:
    decision = ReceiptApplicationPolicy().applied_invoice_decision(
        _applied_invoice(amount_applied=0),
        _invoice(total=500, amountPaid=700),
    )

    assert decision.allowed is False
    assert decision.reason == (
        "Overpayment Error: Payment of 0 exceeds pending balance of -200 "
        "for Invoice FAC-001"
    )
