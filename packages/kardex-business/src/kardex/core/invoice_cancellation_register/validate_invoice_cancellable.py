from typing import Any, cast

from kardex.core.policies import CancellationDecision
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    DevolutionsCollection,
    ShiftsCollection,
)
from kardex.tools import InvalidOperation
from kardex.tools.app_settings_tool import AppSettingsTool

from .invoice_cancellation_policy import InvoiceCancellationPolicy


def _ensure_allowed(decision: CancellationDecision) -> None:
    if decision.allowed:
        return
    raise InvalidOperation(cast(str, decision.reason))


async def validate_invoice_cancellable(
    invoice: InvoiceInDb,
    session: Any = None,
) -> None:
    """Valida que una factura cumpla todas las reglas de negocio para ser anulada."""
    policy = InvoiceCancellationPolicy(invoice)

    _ensure_allowed(policy.header_decision())

    if invoice.shiftId:
        shift_data = await ShiftsCollection.get_instance().fetch_shift_by_id(
            invoice.shiftId, session=session
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

    devolutions = await DevolutionsCollection.get_instance().fetch_devolutions_by_invoice_id(
        invoice_id=invoice.id,
        client_id=None,
        session=session,
    )
    _ensure_allowed(policy.devolutions_decision(devolutions))

    credit_notes = (
        await CreditNotesCollection.get_instance().fetch_credit_notes_by_invoice_id(
            invoice_id=invoice.id,
            session=session,
        )
    )
    _ensure_allowed(policy.credit_notes_decision(credit_notes))
