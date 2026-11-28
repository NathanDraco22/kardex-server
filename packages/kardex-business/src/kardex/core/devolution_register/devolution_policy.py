from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from kardex.core.policies.policy_decision import PolicyDecision

if TYPE_CHECKING:
    from kardex.repos.v1.devolutions import DevolutionInDb
    from kardex.repos.v1.invoices import InvoiceInDb


class DevolutionPolicy:
    """Evalúa las reglas de cabecera, estados y transiciones de una devolución.

    No consulta repositorios: recibe el documento y los datos ya resueltos por
    el orquestador.
    """

    def items_decision(self, returned_items: Sequence[Any]) -> PolicyDecision:
        """Valida que la devolución incluya al menos un producto."""
        if not returned_items:
            return PolicyDecision(
                allowed=False,
                reason="La devolución debe incluir al menos un producto.",
            )
        return PolicyDecision(allowed=True)

    def invoice_decision(self, invoice: InvoiceInDb) -> PolicyDecision:
        """Valida que la factura original admita una devolución por producto."""
        if invoice.status == "cancelled":
            return PolicyDecision(
                allowed=False,
                reason="Cannot create a devolution for a cancelled invoice.",
            )
        if getattr(invoice, "invoiceDiscount", 0) > 0:
            return PolicyDecision(
                allowed=False,
                reason=(
                    "No se permiten devoluciones por producto en facturas con "
                    "descuento global."
                ),
            )
        if invoice.paymentType == "credit" and (
            invoice.amountPaid > 0 or invoice.status in ("partiallyPaid", "paid")
        ):
            return PolicyDecision(
                allowed=False,
                reason=(
                    "No se permiten devoluciones sobre facturas a crédito con "
                    "abonos o pagadas."
                ),
            )
        return PolicyDecision(allowed=True)

    def confirmation_client_decision(
        self, devolution: DevolutionInDb, *, anonymous: bool, sale_client_id: str
    ) -> PolicyDecision:
        """Valida que la devolución se confirme por el endpoint correcto."""
        if not anonymous and devolution.clientId == sale_client_id:
            return PolicyDecision(
                allowed=False,
                reason="Use the anonymous devolution endpoint for this client.",
            )
        if anonymous and devolution.clientId != sale_client_id:
            return PolicyDecision(
                allowed=False,
                reason="Invalid client ID for anonymous devolution.",
            )
        return PolicyDecision(allowed=True)

    def status_decision(self, devolution: DevolutionInDb) -> PolicyDecision:
        """Valida que la devolución siga abierta antes de confirmarla."""
        if devolution.status != "open":
            return PolicyDecision(
                allowed=False,
                reason="Devolution is not open.",
            )
        return PolicyDecision(allowed=True)
