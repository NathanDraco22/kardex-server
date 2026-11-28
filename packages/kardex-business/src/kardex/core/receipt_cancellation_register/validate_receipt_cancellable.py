from typing import Any, cast

from kardex.core.policies import CancellationDecision, ReceiptCancellationPolicy
from kardex.repos.v1.receipts import ReceiptInDb
from kardex.services.mongo_collections.v1 import (
    InvoicesCollection,
    ShiftsCollection,
)
from kardex.tools import InvalidOperation
from kardex.tools.app_settings_tool import AppSettingsTool


def _ensure_allowed(decision: CancellationDecision) -> None:
    if decision.allowed:
        return
    raise InvalidOperation(cast(str, decision.reason))


async def validate_receipt_cancellable(
    receipt: ReceiptInDb,
    session: Any = None,
) -> None:
    """Valida que un recibo cumpla las reglas de negocio para ser anulado."""
    policy = ReceiptCancellationPolicy(receipt)

    _ensure_allowed(policy.header_decision())

    if receipt.shiftId:
        shift_data = await ShiftsCollection.get_instance().fetch_shift_by_id(
            receipt.shiftId, session=session
        )
        if shift_data is not None and shift_data.get("status") != "open":
            settings = await AppSettingsTool().get_current_app_settings()
            # Un turno sin `status` se trataba como cerrado en el validador original.
            _ensure_allowed(
                policy.shift_decision(
                    settings,
                    shift_status=shift_data.get("status") or "closed",
                )
            )

    invoices_col = InvoicesCollection.get_instance()
    for applied_invoice in receipt.appliedInvoices:
        inv_data = await invoices_col.fetch_invoice_by_id_with_session(
            invoice_id=applied_invoice.invoiceId,
            session=session,
        )
        _ensure_allowed(
            policy.applied_invoice_decision(
                doc_number=applied_invoice.docNumber,
                invoice_data=inv_data,
            )
        )
