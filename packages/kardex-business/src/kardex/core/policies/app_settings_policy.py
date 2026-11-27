from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kardex.repos.v1.app_settings import AppSettingInDb


class ConvertedOrderShiftPolicy(str, Enum):
    """Política de turno aplicada al convertir una orden en factura."""

    NEVER = "never"
    OPTIONAL = "optional"
    REQUIRED = "required"

    @property
    def links_to_shift(self) -> bool:
        """Indica si la factura convertida debe cargarse a un turno."""
        return self is not ConvertedOrderShiftPolicy.NEVER

    @property
    def requires_open_shift(self) -> bool:
        """Indica si la conversión se bloquea cuando no llega un turno."""
        return self is ConvertedOrderShiftPolicy.REQUIRED


class AppSettingsPolicy:
    """Lectura tipada de las banderas de configuración, sin IO.

    Centraliza la interpretación de combinaciones de banderas para que los
    procesos de dominio no repitan cascadas de condiciones. Si no hay
    configuración disponible se aplican los valores conservadores.
    """

    def __init__(self, settings: AppSettingInDb | None) -> None:
        self._settings = settings

    @property
    def converted_order_shift_policy(self) -> ConvertedOrderShiftPolicy:
        """Resuelve cómo interactúa la conversión de órdenes con los turnos."""
        if self._settings is None or not self._settings.useShifts:
            return ConvertedOrderShiftPolicy.NEVER
        if not self._settings.chargeConvertedOrdersToShift:
            return ConvertedOrderShiftPolicy.NEVER
        if self._settings.requireShiftForConvertedOrders:
            return ConvertedOrderShiftPolicy.REQUIRED
        return ConvertedOrderShiftPolicy.OPTIONAL

    @property
    def round_up_invoice_totals(self) -> bool:
        """Indica si las facturas nuevas redondean sus totales hacia arriba."""
        if self._settings is None:
            return False
        return self._settings.roundUpInvoiceTotals

    @property
    def allows_cancellations_outside_shift(self) -> bool:
        """Indica si se permite anular documentos de turnos ya cerrados."""
        if self._settings is None:
            return False
        return self._settings.allowCancellationsOutsideShift
