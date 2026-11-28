from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, AbstractSet, Any

from kardex.core.policies.decisions.policy_decision import PolicyDecision

if TYPE_CHECKING:
    from kardex.repos.v1.invoices import InvoiceInDb
    from kardex.repos.v1.receipts import (
        AppliedCreditNote,
        AppliedDevolution,
        AppliedInvoice,
    )


class ReceiptApplicationPolicy:
    """Evalúa las reglas de aplicación de fondos de un recibo.

    No consulta repositorios: recibe los documentos y los datos ya resueltos
    por el orquestador y devuelve una decisión pura.
    """

    def funds_decision(
        self, *, total_funds: int, total_applied: int
    ) -> PolicyDecision:
        """Valida que los fondos del recibo cubran exactamente lo aplicado."""
        if total_funds == total_applied:
            return PolicyDecision(allowed=True)
        return PolicyDecision(
            allowed=False,
            reason=(
                f"Discrepancy Error: Total Funds ({total_funds}) "
                f"does not match Total Applied to Invoices ({total_applied})."
            ),
        )

    def credit_note_duplicate_decision(
        self, credit_note_id: str, seen_ids: AbstractSet[str]
    ) -> PolicyDecision:
        """Valida que la nota de crédito no se repita dentro del recibo."""
        if credit_note_id in seen_ids:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Nota de crédito duplicada en el recibo: {credit_note_id}."
                ),
            )
        return PolicyDecision(allowed=True)

    def applied_credit_note_decision(
        self,
        applied: AppliedCreditNote,
        credit_note: Mapping[str, Any] | None,
        *,
        client_id: str,
    ) -> PolicyDecision:
        """Valida una nota de crédito aplicada al recibo."""
        if not credit_note:
            return PolicyDecision(
                allowed=False,
                reason=f"Nota de crédito {applied.creditNoteId} no encontrada.",
            )

        doc_number = credit_note.get("docNumber", "")
        status = credit_note.get("status")
        if status not in ("approved", "confirmed"):
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"La nota de crédito #{doc_number} no está aprobada "
                    f"(estado: {status})."
                ),
            )
        if credit_note.get("clientId") != client_id:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"La nota de crédito #{doc_number} pertenece a otro cliente."
                ),
            )

        cn_amount = int(credit_note.get("amount") or 0)
        if applied.amountApplied <= 0 or applied.amountApplied > cn_amount:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"El monto aplicado ({applied.amountApplied}) de la nota de "
                    f"crédito #{doc_number} es inválido (total: {cn_amount})."
                ),
            )
        return PolicyDecision(allowed=True)

    def devolution_duplicate_decision(
        self, devolution_id: str, seen_ids: AbstractSet[str]
    ) -> PolicyDecision:
        """Valida que la devolución no se repita dentro del recibo."""
        if devolution_id in seen_ids:
            return PolicyDecision(
                allowed=False,
                reason=f"Devolución duplicada en el recibo: {devolution_id}.",
            )
        return PolicyDecision(allowed=True)

    def applied_devolution_decision(
        self,
        applied: AppliedDevolution,
        devolution: Mapping[str, Any] | None,
        *,
        client_id: str,
    ) -> PolicyDecision:
        """Valida una devolución aplicada al recibo."""
        if not devolution:
            return PolicyDecision(
                allowed=False,
                reason=f"Devolución {applied.devolutionId} no encontrada.",
            )

        doc_number = devolution.get("docNumber", "")
        status = devolution.get("status")
        if status != "confirmed":
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"La devolución #{doc_number} no está confirmada "
                    f"(estado: {status})."
                ),
            )
        if devolution.get("clientId") != client_id:
            return PolicyDecision(
                allowed=False,
                reason=f"La devolución #{doc_number} pertenece a otro cliente.",
            )
        if devolution.get("originalInvoicePaymentType") not in ("credit", None):
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"La devolución #{doc_number} proviene de una factura de "
                    "contado y no puede aplicarse en recibos."
                ),
            )

        dev_total = int(devolution.get("total") or 0)
        if applied.amountApplied <= 0 or applied.amountApplied > dev_total:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"El monto aplicado ({applied.amountApplied}) de la "
                    f"devolución #{doc_number} es inválido (total: {dev_total})."
                ),
            )
        return PolicyDecision(allowed=True)

    def applied_invoice_decision(
        self,
        applied: AppliedInvoice,
        invoice: InvoiceInDb | None,
        *,
        has_open_devolution: bool = False,
    ) -> PolicyDecision:
        """Valida la aplicación de un pago sobre una factura."""
        if invoice is None:
            return PolicyDecision(
                allowed=False,
                reason=f"Invoice {applied.invoiceId} not found",
            )
        if has_open_devolution:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"La factura #{invoice.docNumber} tiene una devolución "
                    "pendiente de confirmar."
                ),
            )

        pending_balance = invoice.total - invoice.amountPaid
        if applied.amountApplied > pending_balance:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Overpayment Error: Payment of {applied.amountApplied} "
                    f"exceeds pending balance of {pending_balance} "
                    f"for Invoice {invoice.docNumber}"
                ),
            )
        return PolicyDecision(allowed=True)
