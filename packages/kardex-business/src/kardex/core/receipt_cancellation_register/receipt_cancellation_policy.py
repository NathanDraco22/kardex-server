from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from kardex.core.policies.app_settings_policy import AppSettingsPolicy
from kardex.core.policies.cancellation_decision import CancellationDecision

if TYPE_CHECKING:
    from kardex.repos.v1.app_settings import AppSettingInDb
    from kardex.repos.v1.receipts import ReceiptInDb


class ReceiptCancellationPolicy:
    """Evalúa si un recibo cumple las reglas de negocio para ser anulado.

    No consulta repositorios ni configuración: recibe el recibo y los datos
    de las facturas aplicadas ya resueltos por el orquestador.
    """

    def __init__(self, receipt: ReceiptInDb) -> None:
        self._receipt = receipt

    def header_decision(self) -> CancellationDecision:
        """Valida el estado del recibo y sus aplicaciones."""
        receipt = self._receipt
        if receipt.isDeleted:
            return CancellationDecision(
                allowed=False,
                reason="El recibo ya se encuentra anulado.",
            )
        if receipt.appliedDevolutions or receipt.appliedCreditNotes:
            return CancellationDecision(
                allowed=False,
                reason=(
                    "No se puede anular un recibo que tiene devoluciones o "
                    "notas de crédito aplicadas."
                ),
            )
        return CancellationDecision(allowed=True)

    def shift_decision(
        self,
        settings: AppSettingInDb | None,
        *,
        shift_status: str | None,
    ) -> CancellationDecision:
        """Valida si el recibo pertenece a un turno cerrado."""
        if shift_status is None or shift_status == "open":
            return CancellationDecision(allowed=True)
        if AppSettingsPolicy(settings).allows_cancellations_outside_shift:
            return CancellationDecision(allowed=True)
        return CancellationDecision(
            allowed=False,
            reason=(
                "No se puede anular un recibo perteneciente a un turno ya "
                "cerrado."
            ),
        )

    def applied_invoice_decision(
        self,
        doc_number: str,
        invoice_data: Mapping[str, Any] | None,
    ) -> CancellationDecision:
        """Valida que una factura aplicada exista y permita revertir el recibo."""
        if invoice_data is None:
            return CancellationDecision(
                allowed=False,
                reason=f"La factura aplicada {doc_number} no existe.",
            )
        status = invoice_data.get("status")
        if status in ("cancelled", "draft"):
            return CancellationDecision(
                allowed=False,
                reason=(
                    f"La factura {doc_number} está en estado '{status}' y no "
                    "permite revertir el recibo."
                ),
            )
        return CancellationDecision(allowed=True)
