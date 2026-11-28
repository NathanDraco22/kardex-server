from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kardex.repos.v1.app_settings import AppSettingInDb
    from kardex.repos.v1.receipts import CreateReceipt


@dataclass(frozen=True, slots=True)
class ReceiptPaymentDecision:
    """Resultado de evaluar la coherencia del pago de un recibo."""

    allowed: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.allowed and not (self.reason or "").strip():
            raise ValueError(
                "Una decisión de pago rechazada requiere un motivo."
            )


def _round_half_up(value: float) -> int:
    """Redondea al entero más cercano con el criterio de Dart (mitad hacia arriba)."""
    return math.floor(value + 0.5)


class ReceiptPaymentPolicy:
    """Evalúa si el pago de un recibo es coherente antes de persistirlo.

    La UI calcula estos valores, pero la API debe rechazar combinaciones
    incoherentes que afectarían el arqueo o el comprobante impreso.
    """

    def __init__(self, settings: AppSettingInDb | None) -> None:
        self._settings = settings

    def evaluate(self, receipt: CreateReceipt) -> ReceiptPaymentDecision:
        """Devuelve la decisión de pago; no lanza excepciones de dominio."""
        if receipt.total < 0:
            return ReceiptPaymentDecision(
                allowed=False,
                reason="El total del recibo no puede ser negativo.",
            )

        for applied_invoice in receipt.appliedInvoices:
            if applied_invoice.amountApplied < 0:
                return ReceiptPaymentDecision(
                    allowed=False,
                    reason=(
                        f"El monto aplicado a la factura "
                        f"{applied_invoice.docNumber} no puede ser negativo."
                    ),
                )

        for applied_devolution in receipt.appliedDevolutions:
            if applied_devolution.amountApplied < 0:
                return ReceiptPaymentDecision(
                    allowed=False,
                    reason=(
                        f"El monto aplicado a la devolución "
                        f"{applied_devolution.docNumber} no puede ser negativo."
                    ),
                )

        for applied_credit_note in receipt.appliedCreditNotes:
            if applied_credit_note.amountApplied < 0:
                return ReceiptPaymentDecision(
                    allowed=False,
                    reason=(
                        f"El monto aplicado a la nota de crédito "
                        f"{applied_credit_note.docNumber} no puede ser negativo."
                    ),
                )

        if receipt.paymentMethod in ("card", "transfer") and not (
            receipt.bankReference.strip()
        ):
            return ReceiptPaymentDecision(
                allowed=False,
                reason=(
                    "Los pagos con tarjeta o transferencia requieren una "
                    "referencia bancaria."
                ),
            )

        detail = receipt.paymentDetail
        if detail is None:
            return ReceiptPaymentDecision(allowed=True)

        settings = self._settings
        if settings is None:
            return ReceiptPaymentDecision(
                allowed=False,
                reason="No se pudo validar la configuración de moneda del pago.",
            )

        if receipt.paymentMethod != "cash":
            return ReceiptPaymentDecision(
                allowed=False,
                reason="El detalle de pago solo aplica a pagos en efectivo.",
            )

        if receipt.total <= 0:
            return ReceiptPaymentDecision(
                allowed=False,
                reason=(
                    "No se espera detalle de pago para un recibo sin cobro "
                    "en efectivo."
                ),
            )

        allowed_currencies = {settings.currency, settings.secondaryCurrency}
        if detail.paidCurrency not in allowed_currencies:
            return ReceiptPaymentDecision(
                allowed=False,
                reason=(
                    "La moneda del pago no coincide con la configuración de "
                    "la empresa."
                ),
            )

        if detail.paidCurrency != settings.currency:
            if not settings.allowSecondaryCurrencyPayment:
                return ReceiptPaymentDecision(
                    allowed=False,
                    reason=(
                        "El pago en moneda secundaria no está habilitado en la "
                        "configuración."
                    ),
                )
            if settings.exchangeRate <= 0:
                return ReceiptPaymentDecision(
                    allowed=False,
                    reason=(
                        "No hay una tasa de cambio válida configurada para la "
                        "moneda secundaria."
                    ),
                )
            # Se acepta la tasa congelada del detalle para respetar el cobro al
            # momento de la captura; solo se exige que la moneda secundaria esté
            # habilitada y que exista una tasa configurada válida.

        if detail.paidCurrency == settings.currency:
            converted_tendered = detail.tenderedAmount
        else:
            converted_tendered = _round_half_up(
                detail.tenderedAmount * detail.exchangeRate
            )

        if converted_tendered < receipt.total:
            return ReceiptPaymentDecision(
                allowed=False,
                reason="El monto recibido no cubre el total del recibo.",
            )

        expected_change = converted_tendered - receipt.total
        if detail.changeAmount != expected_change:
            return ReceiptPaymentDecision(
                allowed=False,
                reason="El cambio registrado no coincide con el monto recibido.",
            )

        return ReceiptPaymentDecision(allowed=True)
