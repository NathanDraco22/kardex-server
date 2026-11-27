from typing import Any

import pytest

from kardex.core.receipt_register.receipt_payment_policy import (
    ReceiptPaymentDecision,
    ReceiptPaymentPolicy,
)
from kardex.repos.v1.app_settings import AppSettingInDb
from kardex.repos.v1.app_settings.models.app_setting_model import CurrencyCode
from kardex.repos.v1.common.models import ClientInfo, PaymentDetail, UserInfo
from kardex.repos.v1.receipts import (
    AppliedCreditNote,
    AppliedDevolution,
    AppliedInvoice,
    CreateReceipt,
)


def _settings(
    currency: CurrencyCode = "NIO",
    secondary_currency: CurrencyCode = "USD",
    exchange_rate: float = 36.0,
    allow_secondary_currency_payment: bool = False,
) -> AppSettingInDb:
    return AppSettingInDb(
        id="Default",
        createdAt=0,
        currency=currency,
        secondaryCurrency=secondary_currency,
        exchangeRate=exchange_rate,
        allowSecondaryCurrencyPayment=allow_secondary_currency_payment,
    )


def _receipt(**overrides: Any) -> CreateReceipt:
    data: dict[str, Any] = {
        "branchId": "b1",
        "clientId": "c1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "paymentMethod": "cash",
        "total": 1000,
        "createdBy": UserInfo(id="u1", name="Cajero"),
        "appliedInvoices": [
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=1000)
        ],
    }
    data.update(overrides)
    return CreateReceipt(**data)


def _detail(
    paid_currency: CurrencyCode = "NIO",
    tendered_amount: int = 1500,
    exchange_rate: float = 1.0,
    change_amount: int = 500,
) -> PaymentDetail:
    return PaymentDetail(
        paidCurrency=paid_currency,
        tenderedAmount=tendered_amount,
        exchangeRate=exchange_rate,
        changeAmount=change_amount,
    )


def test_evaluate_allows_primary_cash_with_change():
    receipt = _receipt(paymentDetail=_detail())

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision == ReceiptPaymentDecision(allowed=True)
    assert decision.reason is None


def test_evaluate_allows_legacy_cash_without_detail():
    decision = ReceiptPaymentPolicy(_settings()).evaluate(_receipt())

    assert decision.allowed is True


def test_evaluate_allows_legacy_cash_without_settings():
    decision = ReceiptPaymentPolicy(None).evaluate(_receipt())

    assert decision.allowed is True


@pytest.mark.parametrize("payment_method", ["card", "transfer"])
def test_evaluate_allows_bank_payment_with_reference(payment_method: str):
    receipt = _receipt(
        paymentMethod=payment_method,
        bankReference="BAC - 12345",
        paymentDetail=None,
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is True


def test_evaluate_allows_secondary_cash_with_half_up_rounding():
    receipt = _receipt(
        total=111,
        appliedInvoices=[
            AppliedInvoice(
                invoiceId="inv1",
                docNumber="F-1",
                amountApplied=111,
            )
        ],
        paymentDetail=_detail(
            paid_currency="USD",
            tendered_amount=221,
            exchange_rate=0.5,
            change_amount=0,
        ),
    )

    decision = ReceiptPaymentPolicy(
        _settings(allow_secondary_currency_payment=True)
    ).evaluate(receipt)

    assert decision.allowed is True


def test_evaluate_rejects_negative_total():
    decision = ReceiptPaymentPolicy(_settings()).evaluate(_receipt(total=-1))

    assert decision.allowed is False
    assert decision.reason == "El total del recibo no puede ser negativo."


def test_evaluate_rejects_negative_applied_invoice():
    receipt = _receipt(
        appliedInvoices=[
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=-1)
        ]
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "El monto aplicado a la factura F-1 no puede ser negativo."
    )


def test_evaluate_rejects_negative_applied_devolution():
    receipt = _receipt(
        appliedDevolutions=[
            AppliedDevolution(
                devolutionId="dev1",
                docNumber="DEV-1",
                amountApplied=-1,
            )
        ]
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "El monto aplicado a la devolución DEV-1 no puede ser negativo."
    )


def test_evaluate_rejects_negative_applied_credit_note():
    receipt = _receipt(
        appliedCreditNotes=[
            AppliedCreditNote(
                creditNoteId="cn1",
                docNumber="NC-1",
                amountApplied=-1,
            )
        ]
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "El monto aplicado a la nota de crédito NC-1 no puede ser negativo."
    )


@pytest.mark.parametrize("payment_method", ["card", "transfer"])
def test_evaluate_rejects_bank_payment_without_reference(payment_method: str):
    receipt = _receipt(paymentMethod=payment_method, bankReference="")

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "Los pagos con tarjeta o transferencia requieren una referencia bancaria."
    )


@pytest.mark.parametrize("payment_method", ["card", "transfer"])
def test_evaluate_rejects_bank_payment_with_whitespace_reference(
    payment_method: str,
):
    receipt = _receipt(paymentMethod=payment_method, bankReference="   ")

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "Los pagos con tarjeta o transferencia requieren una referencia bancaria."
    )


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_denied_decision_requires_reason(reason: str | None):
    with pytest.raises(ValueError, match="requiere un motivo"):
        ReceiptPaymentDecision(allowed=False, reason=reason)


def test_evaluate_rejects_detail_without_settings():
    receipt = _receipt(paymentDetail=_detail())

    decision = ReceiptPaymentPolicy(None).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se pudo validar la configuración de moneda del pago."
    )


def test_evaluate_rejects_detail_on_non_cash_payment():
    receipt = _receipt(
        paymentMethod="transfer",
        bankReference="BAC - 12345",
        paymentDetail=_detail(),
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert decision.reason == "El detalle de pago solo aplica a pagos en efectivo."


def test_evaluate_rejects_detail_on_zero_total():
    receipt = _receipt(
        total=0,
        appliedInvoices=[],
        paymentDetail=_detail(tendered_amount=0, change_amount=0),
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "No se espera detalle de pago para un recibo sin cobro en efectivo."
    )


def test_evaluate_rejects_currency_outside_settings():
    receipt = _receipt(paymentDetail=_detail(paid_currency="EUR"))

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "La moneda del pago no coincide con la configuración de la empresa."
    )


def test_evaluate_rejects_secondary_currency_disabled():
    receipt = _receipt(
        paymentDetail=_detail(
            paid_currency="USD",
            tendered_amount=28,
            exchange_rate=36.0,
            change_amount=8,
        )
    )

    decision = ReceiptPaymentPolicy(
        _settings(allow_secondary_currency_payment=False)
    ).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "El pago en moneda secundaria no está habilitado en la configuración."
    )


def test_evaluate_rejects_invalid_configured_exchange_rate():
    receipt = _receipt(
        paymentDetail=_detail(
            paid_currency="USD",
            tendered_amount=28,
            exchange_rate=36.0,
            change_amount=8,
        )
    )

    decision = ReceiptPaymentPolicy(
        _settings(
            exchange_rate=0.0,
            allow_secondary_currency_payment=True,
        )
    ).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "No hay una tasa de cambio válida configurada para la moneda secundaria."
    )


def test_evaluate_rejects_tendered_amount_below_total():
    receipt = _receipt(
        paymentDetail=_detail(tendered_amount=900, change_amount=0)
    )

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert decision.reason == "El monto recibido no cubre el total del recibo."


def test_evaluate_rejects_change_mismatch():
    receipt = _receipt(paymentDetail=_detail(change_amount=400))

    decision = ReceiptPaymentPolicy(_settings()).evaluate(receipt)

    assert decision.allowed is False
    assert (
        decision.reason
        == "El cambio registrado no coincide con el monto recibido."
    )
