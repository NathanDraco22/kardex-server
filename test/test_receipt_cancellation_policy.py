from typing import Any

import pytest

from kardex.core.policies import CancellationDecision
from kardex.core.receipt_cancellation_register.receipt_cancellation_policy import (
    ReceiptCancellationPolicy,
)
from kardex.repos.v1.app_settings import AppSettingInDb
from kardex.repos.v1.common.models import ClientInfo, UserInfo
from kardex.repos.v1.receipts import (
    AppliedCreditNote,
    AppliedDevolution,
    AppliedInvoice,
    ReceiptInDb,
)


def _receipt(**overrides: Any) -> ReceiptInDb:
    data: dict[str, Any] = {
        "id": "rec-1",
        "branchId": "b-1",
        "clientId": "c-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "paymentMethod": "cash",
        "total": 1000,
        "createdBy": UserInfo(id="u-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return ReceiptInDb(**data)


def _settings(allow_outside_shift: bool = False) -> AppSettingInDb:
    return AppSettingInDb(
        id="Default",
        createdAt=0,
        allowCancellationsOutsideShift=allow_outside_shift,
    )


def test_header_rejects_deleted_receipt():
    decision = ReceiptCancellationPolicy(_receipt(isDeleted=True)).header_decision()

    assert decision.allowed is False
    assert decision.reason == "El recibo ya se encuentra anulado."


def test_header_rejects_applied_devolutions():
    receipt = _receipt(
        appliedDevolutions=[
            AppliedDevolution(
                devolutionId="dev-1",
                docNumber="D-0001",
                amountApplied=200,
            )
        ]
    )

    decision = ReceiptCancellationPolicy(receipt).header_decision()

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular un recibo que tiene devoluciones o notas de crédito aplicadas."
    )


def test_header_rejects_applied_credit_notes():
    receipt = _receipt(
        appliedCreditNotes=[
            AppliedCreditNote(
                creditNoteId="cn-1",
                docNumber="NC-0001",
                amountApplied=200,
            )
        ]
    )

    decision = ReceiptCancellationPolicy(receipt).header_decision()

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular un recibo que tiene devoluciones o notas de crédito aplicadas."
    )


@pytest.mark.parametrize("allow_outside_shift", [False, True])
def test_shift_decision_closed_shift(allow_outside_shift: bool):
    policy = ReceiptCancellationPolicy(_receipt())

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
            == "No se puede anular un recibo perteneciente a un turno ya cerrado."
        )


def test_shift_decision_allows_open_shift():
    policy = ReceiptCancellationPolicy(_receipt())

    decision = policy.shift_decision(None, shift_status="open")

    assert decision == CancellationDecision(allowed=True)


def test_shift_decision_allows_missing_shift():
    policy = ReceiptCancellationPolicy(_receipt())

    decision = policy.shift_decision(None, shift_status=None)

    assert decision == CancellationDecision(allowed=True)


def test_shift_decision_closed_shift_without_settings_is_rejected():
    policy = ReceiptCancellationPolicy(_receipt())

    decision = policy.shift_decision(None, shift_status="closed")

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se puede anular un recibo perteneciente a un turno ya cerrado."
    )


def test_applied_invoice_rejects_missing_invoice():
    policy = ReceiptCancellationPolicy(_receipt())

    decision = policy.applied_invoice_decision("F-0001", None)

    assert decision.allowed is False
    assert decision.reason == "La factura aplicada F-0001 no existe."


@pytest.mark.parametrize("status", ["cancelled", "draft"])
def test_applied_invoice_rejects_non_reversible_status(status: str):
    policy = ReceiptCancellationPolicy(_receipt())

    decision = policy.applied_invoice_decision(
        "F-0001",
        {"id": "inv-1", "status": status},
    )

    assert decision.allowed is False
    assert (
        decision.reason
        == f"La factura F-0001 está en estado '{status}' y no permite revertir el recibo."
    )


@pytest.mark.parametrize("status", ["open", "paid", "partiallyPaid"])
def test_applied_invoice_allows_reversible_status(status: str):
    policy = ReceiptCancellationPolicy(_receipt())

    decision = policy.applied_invoice_decision(
        "F-0001",
        {"id": "inv-1", "status": status},
    )

    assert decision == CancellationDecision(allowed=True)


def test_all_decisions_allow_cancellable_receipt():
    receipt = _receipt(
        shiftId="shift-1",
        appliedInvoices=[
            AppliedInvoice(
                invoiceId="inv-1",
                docNumber="F-0001",
                amountApplied=1000,
            )
        ],
    )
    policy = ReceiptCancellationPolicy(receipt)

    assert policy.header_decision() == CancellationDecision(allowed=True)
    assert policy.shift_decision(
        _settings(allow_outside_shift=True),
        shift_status="closed",
    ) == CancellationDecision(allowed=True)
    assert policy.applied_invoice_decision(
        "F-0001",
        {"id": "inv-1", "status": "paid"},
    ) == CancellationDecision(allowed=True)


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_denied_decision_requires_reason(reason: str | None):
    with pytest.raises(ValueError, match="requiere un motivo"):
        CancellationDecision(allowed=False, reason=reason)


def test_denied_decision_accepts_valid_reason():
    decision = CancellationDecision(allowed=False, reason="Motivo válido")

    assert decision.allowed is False
    assert decision.reason == "Motivo válido"
