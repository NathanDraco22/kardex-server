from __future__ import annotations


def _round_up_whole_unit(value: int) -> int:
    """Redondea centavos hacia arriba al siguiente entero de la moneda."""
    if value <= 0:
        return 0
    return ((value + 99) // 100) * 100


def _round_down_whole_unit(value: int) -> int:
    """Redondea centavos hacia abajo al entero anterior de la moneda."""
    if value <= 0:
        return 0
    return (value // 100) * 100


class InvoiceRoundingPolicy:
    """Aplica el redondeo de importes a unidades enteras de la moneda."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    def line_subtotal(self, value: int) -> int:
        """Redondea un subtotal de línea hacia arriba cuando está habilitado."""
        if not self._enabled:
            return value
        return _round_up_whole_unit(value)

    def line_discount(self, value: int) -> int:
        """Redondea un descuento de línea hacia abajo cuando está habilitado."""
        if not self._enabled:
            return value
        return _round_down_whole_unit(value)

    def invoice_discount(self, value: int) -> int:
        """Redondea el descuento global hacia abajo cuando está habilitado."""
        if not self._enabled:
            return value
        return _round_down_whole_unit(value)
