from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

from kardex.core.policies.app_settings_policy import AppSettingsPolicy
from kardex.core.policies.cancellation_decision import CancellationDecision

if TYPE_CHECKING:
    from kardex.repos.v1.app_settings import AppSettingInDb
    from kardex.repos.v1.invoices import InvoiceInDb

ACTIVE_DEVOLUTION_STATUSES = frozenset({"open", "confirmed", "applied"})
ACTIVE_CREDIT_NOTE_STATUSES = frozenset(
    {"emitted", "open", "approved", "confirmed", "applied"}
)


class InvoiceCancellationPolicy:
    """Evalúa si una factura cumple las reglas de negocio para ser anulada.

    No consulta repositorios ni configuración: recibe la factura, los
    documentos relacionados y los settings ya resueltos por el orquestador.
    """

    def __init__(self, invoice: InvoiceInDb) -> None:
        self._invoice = invoice

    def header_decision(self) -> CancellationDecision:
        """Valida el estado de la factura y su condición de pago."""
        invoice = self._invoice
        if invoice.status == "cancelled":
            return CancellationDecision(
                allowed=False,
                reason="La factura ya se encuentra anulada.",
            )
        if invoice.status == "draft":
            return CancellationDecision(
                allowed=False,
                reason="No se puede anular una factura en borrador.",
            )
        if invoice.paymentType == "credit" and (
            invoice.status != "open" or invoice.amountPaid > 0
        ):
            return CancellationDecision(
                allowed=False,
                reason=(
                    "No se puede anular una factura a crédito que ya tiene "
                    "abonos o está pagada."
                ),
            )
        return CancellationDecision(allowed=True)

    def shift_decision(
        self,
        settings: AppSettingInDb | None,
        *,
        shift_status: str | None,
    ) -> CancellationDecision:
        """Valida si la factura pertenece a un turno cerrado."""
        if shift_status is None or shift_status == "open":
            return CancellationDecision(allowed=True)
        if AppSettingsPolicy(settings).allows_cancellations_outside_shift:
            return CancellationDecision(allowed=True)
        return CancellationDecision(
            allowed=False,
            reason=(
                "No se puede anular una factura perteneciente a un turno ya "
                "cerrado."
            ),
        )

    def devolutions_decision(
        self,
        devolutions: Iterable[Mapping[str, Any]],
    ) -> CancellationDecision:
        """Valida que la factura no tenga devoluciones activas."""
        if any(
            devolution.get("status") in ACTIVE_DEVOLUTION_STATUSES
            for devolution in devolutions
        ):
            return CancellationDecision(
                allowed=False,
                reason=(
                    "No se puede anular una factura que tiene devoluciones "
                    "activas o confirmadas."
                ),
            )
        return CancellationDecision(allowed=True)

    def credit_notes_decision(
        self,
        credit_notes: Iterable[Mapping[str, Any]],
    ) -> CancellationDecision:
        """Valida que la factura no tenga notas de crédito activas."""
        if any(
            credit_note.get("status") in ACTIVE_CREDIT_NOTE_STATUSES
            for credit_note in credit_notes
        ):
            return CancellationDecision(
                allowed=False,
                reason=(
                    "No se puede anular una factura que tiene notas de crédito "
                    "activas o aplicadas."
                ),
            )
        return CancellationDecision(allowed=True)
