from typing import Any

import pytest

from kardex.core.invoice_cancellation_register.invoice_cancellation_policy import (
    InvoiceCancellationPolicy,
)
from kardex.core.policies import CancellationDecision
from kardex.repos.v1.app_settings import AppSettingInDb
from kardex.repos.v1.common.models import (
    ClientInfo,
    ProductItem,
    SaleItem,
    UserInfo,
)
from kardex.repos.v1.invoices import InvoiceInDb

ACTIVE_DEVOLUTION_STATUSES = ["open", "confirmed", "applied"]
ACTIVE_CREDIT_NOTE_STATUSES = [
    "emitted",
    "open",
    "approved",
    "confirmed",
    "applied",
]


def _sale_item() -> SaleItem:
    return SaleItem(
        product=ProductItem(
            id="p-1",
            name="Producto Test",
            unitName="Unidad",
        ),
        quantity=1,
        cost=500,
        price=1000,
        subTotal=1000,
        total=1000,
    )


def _invoice(**overrides: Any) -> InvoiceInDb:
    data: dict[str, Any] = {
        "id": "inv-1",
        "branchId": "b-1",
        "clientId": "c-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "saleItems": [_sale_item()],
        "status": "paid",
        "paymentType": "cash",
        "totalCost": 500,
        "total": 1000,
        "createdBy": UserInfo(id="u-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return InvoiceInDb(**data)


def _settings(allow_outside_shift: bool = False) -> AppSettingInDb:
    return AppSettingInDb(
        id="Default",
        createdAt=0,
        allowCancellationsOutsideShift=allow_outside_shift,
    )


def test_header_rejects_cancelled_invoice():
    decision = InvoiceCancellationPolicy(_invoice(status="cancelled")).header_decision()

    assert decision.allowed is False
    assert decision.reason == "La factura ya se encuentra anulada."


def test_header_rejects_draft_invoice():
    decision = InvoiceCancellationPolicy(_invoice(status="draft")).header_decision()

    assert decision.allowed is False
    assert decision.reason == "No se puede anular una factura en borrador."


def test_header_rejects_paid_credit_invoice():
    invoice = _invoice(paymentType="credit", status="paid", amountPaid=1000)

    decision = InvoiceCancellationPolicy(invoice).header_decision()

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular una factura a crédito que ya tiene abonos o está pagada."
    )


def test_header_rejects_credit_invoice_with_payments():
    invoice = _invoice(paymentType="credit", status="open", amountPaid=100)

    decision = InvoiceCancellationPolicy(invoice).header_decision()

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular una factura a crédito que ya tiene abonos o está pagada."
    )


def test_header_rejects_partially_paid_credit_invoice_without_payments():
    invoice = _invoice(paymentType="credit", status="partiallyPaid", amountPaid=0)

    decision = InvoiceCancellationPolicy(invoice).header_decision()

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular una factura a crédito que ya tiene abonos o está pagada."
    )


def test_header_allows_open_credit_invoice_without_payments():
    invoice = _invoice(paymentType="credit", status="open", amountPaid=0)

    decision = InvoiceCancellationPolicy(invoice).header_decision()

    assert decision == CancellationDecision(allowed=True)


def test_header_allows_cash_invoice_with_payments():
    invoice = _invoice(paymentType="cash", status="paid", amountPaid=1000)

    decision = InvoiceCancellationPolicy(invoice).header_decision()

    assert decision == CancellationDecision(allowed=True)


@pytest.mark.parametrize("allow_outside_shift", [False, True])
def test_shift_decision_closed_shift(allow_outside_shift: bool):
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.shift_decision(
        _settings(allow_outside_shift),
        shift_status="closed",
    )

    if allow_outside_shift:
        assert decision == CancellationDecision(allowed=True)
    else:
        assert decision.allowed is False
        assert (
            decision.reason
            == "No se puede anular una factura perteneciente a un turno ya cerrado."
        )


def test_shift_decision_allows_open_shift():
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.shift_decision(None, shift_status="open")

    assert decision == CancellationDecision(allowed=True)


def test_shift_decision_allows_missing_shift():
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.shift_decision(None, shift_status=None)

    assert decision == CancellationDecision(allowed=True)


def test_shift_decision_closed_shift_without_settings_is_rejected():
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.shift_decision(None, shift_status="closed")

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular una factura perteneciente a un turno ya cerrado."
    )


@pytest.mark.parametrize("status", ACTIVE_DEVOLUTION_STATUSES)
def test_devolutions_decision_rejects_active_status(status: str):
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.devolutions_decision([{"id": "dev-1", "status": status}])

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular una factura que tiene devoluciones activas o confirmadas."
    )


@pytest.mark.parametrize("status", ["cancelled", "pending", None])
def test_devolutions_decision_allows_inactive_status(status: str | None):
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.devolutions_decision([{"id": "dev-1", "status": status}])

    assert decision == CancellationDecision(allowed=True)


@pytest.mark.parametrize("status", ACTIVE_CREDIT_NOTE_STATUSES)
def test_credit_notes_decision_rejects_active_status(status: str):
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.credit_notes_decision([{"id": "cn-1", "status": status}])

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular una factura que tiene notas de crédito activas o aplicadas."
    )


@pytest.mark.parametrize("status", ["rejected", "cancelled", None])
def test_credit_notes_decision_allows_inactive_status(status: str | None):
    policy = InvoiceCancellationPolicy(_invoice())

    decision = policy.credit_notes_decision([{"id": "cn-1", "status": status}])

    assert decision == CancellationDecision(allowed=True)


def test_all_decisions_allow_cancellable_invoice():
    policy = InvoiceCancellationPolicy(_invoice(shiftId="shift-1"))

    assert policy.header_decision() == CancellationDecision(allowed=True)
    assert policy.shift_decision(
        _settings(allow_outside_shift=True),
        shift_status="closed",
    ) == CancellationDecision(allowed=True)
    assert policy.devolutions_decision([]) == CancellationDecision(allowed=True)
    assert policy.credit_notes_decision([]) == CancellationDecision(allowed=True)


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_denied_decision_requires_reason(reason: str | None):
    with pytest.raises(ValueError, match="requiere un motivo"):
        CancellationDecision(allowed=False, reason=reason)


def test_denied_decision_accepts_valid_reason():
    decision = CancellationDecision(allowed=False, reason="Motivo válido")

    assert decision.allowed is False
    assert decision.reason == "Motivo válido"
