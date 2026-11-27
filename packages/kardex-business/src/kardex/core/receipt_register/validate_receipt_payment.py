import math

from kardex.repos.v1.app_settings import AppSettingInDb
from kardex.repos.v1.receipts import CreateReceipt
from kardex.tools import InvalidOperation


def _round_half_up(value: float) -> int:
    """Redondea al entero más cercano con el criterio de Dart (mitad hacia arriba)."""
    return math.floor(value + 0.5)


def validate_receipt_payment(
    receipt: CreateReceipt,
    settings: AppSettingInDb | None,
) -> None:
    """Valida la coherencia del pago de un recibo antes de persistirlo.

    La UI calcula estos valores, pero la API debe rechazar combinaciones
    incoherentes que afectarían el arqueo o el comprobante impreso.
    """
    if receipt.total < 0:
        raise InvalidOperation("El total del recibo no puede ser negativo.")

    for applied_invoice in receipt.appliedInvoices:
        if applied_invoice.amountApplied < 0:
            raise InvalidOperation(
                f"El monto aplicado a la factura {applied_invoice.docNumber} "
                "no puede ser negativo."
            )

    for applied_devolution in receipt.appliedDevolutions:
        if applied_devolution.amountApplied < 0:
            raise InvalidOperation(
                f"El monto aplicado a la devolución {applied_devolution.docNumber} "
                "no puede ser negativo."
            )

    for applied_credit_note in receipt.appliedCreditNotes:
        if applied_credit_note.amountApplied < 0:
            raise InvalidOperation(
                f"El monto aplicado a la nota de crédito "
                f"{applied_credit_note.docNumber} no puede ser negativo."
            )

    if receipt.paymentMethod in ("card", "transfer") and not (
        receipt.bankReference.strip()
    ):
        raise InvalidOperation(
            "Los pagos con tarjeta o transferencia requieren una referencia bancaria."
        )

    detail = receipt.paymentDetail
    if detail is None:
        return

    if settings is None:
        raise InvalidOperation(
            "No se pudo validar la configuración de moneda del pago."
        )

    if receipt.paymentMethod != "cash":
        raise InvalidOperation(
            "El detalle de pago solo aplica a pagos en efectivo."
        )

    if receipt.total <= 0:
        raise InvalidOperation(
            "No se espera detalle de pago para un recibo sin cobro en efectivo."
        )

    allowed_currencies = {settings.currency, settings.secondaryCurrency}
    if detail.paidCurrency not in allowed_currencies:
        raise InvalidOperation(
            "La moneda del pago no coincide con la configuración de la empresa."
        )

    if detail.paidCurrency != settings.currency:
        if not settings.allowSecondaryCurrencyPayment:
            raise InvalidOperation(
                "El pago en moneda secundaria no está habilitado en la configuración."
            )
        if settings.exchangeRate <= 0:
            raise InvalidOperation(
                "No hay una tasa de cambio válida configurada para la moneda secundaria."
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
        raise InvalidOperation(
            "El monto recibido no cubre el total del recibo."
        )

    expected_change = converted_tendered - receipt.total
    if detail.changeAmount != expected_change:
        raise InvalidOperation(
            "El cambio registrado no coincide con el monto recibido."
        )
