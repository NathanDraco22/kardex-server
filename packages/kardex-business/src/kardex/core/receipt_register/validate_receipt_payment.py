from typing import cast

from kardex.repos.v1.app_settings import AppSettingInDb
from kardex.repos.v1.receipts import CreateReceipt
from kardex.tools import InvalidOperation

from kardex.core.policies import ReceiptPaymentPolicy


def validate_receipt_payment(
    receipt: CreateReceipt,
    settings: AppSettingInDb | None,
) -> None:
    """Valida la coherencia del pago de un recibo antes de persistirlo.

    La UI calcula estos valores, pero la API debe rechazar combinaciones
    incoherentes que afectarían el arqueo o el comprobante impreso.
    """
    decision = ReceiptPaymentPolicy(settings).evaluate(receipt)
    if not decision.allowed:
        raise InvalidOperation(cast(str, decision.reason))
