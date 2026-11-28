from __future__ import annotations

from typing import TYPE_CHECKING

from kardex.core.policies.policy_decision import PolicyDecision

if TYPE_CHECKING:
    from kardex.repos.v1.credit_notes import CreateCreditNote, CreditNoteInDb
    from kardex.repos.v1.invoices import InvoiceInDb


class CreditNotePolicy:
    """Evalúa las reglas de cabecera, estados y transiciones de una nota de crédito.

    No consulta repositorios: recibe el documento y, cuando aplica, los datos
    ya resueltos por el orquestador.
    """

    def amount_request_decision(
        self, doc: CreateCreditNote, *, sale_client_id: str
    ) -> PolicyDecision:
        """Valida una solicitud de nota de crédito por monto."""
        if doc.clientId == sale_client_id:
            return PolicyDecision(
                allowed=False,
                reason="Credit notes by amount require a registered client.",
            )
        if doc.amount <= 0:
            return PolicyDecision(
                allowed=False,
                reason="Credit note amount must be greater than 0.",
            )
        if not doc.description.strip():
            return PolicyDecision(
                allowed=False,
                reason=(
                    "A detailed reason/description is required for credit notes "
                    "by amount."
                ),
            )
        return PolicyDecision(allowed=True)

    def devolution_request_decision(self, doc: CreateCreditNote) -> PolicyDecision:
        """Valida que una solicitud de devolución referencie su factura original."""
        if not doc.originalInvoiceId:
            return PolicyDecision(
                allowed=False,
                reason="Devolution credit notes require an original invoice.",
            )
        return PolicyDecision(allowed=True)

    def devolution_invoice_decision(self, invoice: InvoiceInDb) -> PolicyDecision:
        """Valida que la factura original admita una nota de crédito por devolución."""
        if invoice.status == "cancelled":
            return PolicyDecision(
                allowed=False,
                reason="Cannot create a credit note for a cancelled invoice.",
            )
        if invoice.paymentType != "credit":
            return PolicyDecision(
                allowed=False,
                reason=(
                    "Credit notes by devolution only apply to credit invoices. "
                    "Use devolutions for cash invoices."
                ),
            )
        return PolicyDecision(allowed=True)

    def devolution_items_decision(self, doc: CreateCreditNote) -> PolicyDecision:
        """Valida que la devolución incluya sus productos retornados."""
        if not doc.returnedItems:
            return PolicyDecision(
                allowed=False,
                reason="Devolution credit notes must include returned items.",
            )
        return PolicyDecision(allowed=True)

    def approval_decision(self, credit_note: CreditNoteInDb) -> PolicyDecision:
        """Valida que la nota pueda aprobarse."""
        if credit_note.status != "emitted":
            return PolicyDecision(
                allowed=False,
                reason=(
                    "Solo se pueden aprobar notas de crédito en estado emitida. "
                    f"Estado actual: {credit_note.status}."
                ),
            )
        return PolicyDecision(allowed=True)

    def rejection_decision(self, credit_note: CreditNoteInDb) -> PolicyDecision:
        """Valida que la nota pueda rechazarse."""
        if credit_note.status != "emitted":
            return PolicyDecision(
                allowed=False,
                reason=(
                    "Solo se pueden rechazar notas de crédito en estado emitida. "
                    f"Estado actual: {credit_note.status}."
                ),
            )
        return PolicyDecision(allowed=True)

    def reversal_decision(self, credit_note: CreditNoteInDb) -> PolicyDecision:
        """Valida que la nota pueda revertirse y eliminarse."""
        if credit_note.status == "applied":
            return PolicyDecision(
                allowed=False,
                reason=(
                    "No se puede eliminar una nota de crédito que ya fue aplicada "
                    "en un recibo de pago."
                ),
            )
        return PolicyDecision(allowed=True)

    def recalculated_total_decision(self, total: int) -> PolicyDecision:
        """Valida el total recalculado de una devolución."""
        if total <= 0:
            return PolicyDecision(
                allowed=False,
                reason="Credit note total must be greater than 0.",
            )
        return PolicyDecision(allowed=True)
