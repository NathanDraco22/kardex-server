from pydantic import BaseModel, Field

from kardex.repos.v1.app_settings.models.app_setting_model import CurrencyCode


class PaymentDetail(BaseModel):
    """Detalle del pago recibido en una factura o recibo.

    Permite registrar pagos en moneda primaria o secundaria conservando la
    tasa de cambio congelada al momento de la transacción y el vuelto en
    centavos de la moneda primaria.
    """

    paidCurrency: CurrencyCode
    tenderedAmount: int = Field(ge=0)
    exchangeRate: float = Field(gt=0)
    changeAmount: int = Field(default=0, ge=0)
