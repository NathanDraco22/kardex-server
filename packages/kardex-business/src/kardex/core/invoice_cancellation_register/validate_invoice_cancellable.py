from typing import Any

from kardex.repos.v1.invoices import InvoiceInDb
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    DevolutionsCollection,
    ShiftsCollection,
)
from kardex.tools import InvalidOperation
from kardex.tools.app_settings_tool import AppSettingsTool

ACTIVE_DEVOLUTION_STATUSES = {"open", "confirmed", "applied"}
ACTIVE_CREDIT_NOTE_STATUSES = {
    "emitted",
    "open",
    "approved",
    "confirmed",
    "applied",
}


async def validate_invoice_cancellable(
    invoice: InvoiceInDb,
    session: Any = None,
) -> None:
    """Valida que una factura cumpla todas las reglas de negocio para ser anulada."""
    if invoice.status == "cancelled":
        raise InvalidOperation("La factura ya se encuentra anulada.")

    if invoice.status == "draft":
        raise InvalidOperation("No se puede anular una factura en borrador.")

    if invoice.paymentType == "credit":
        if invoice.status != "open" or invoice.amountPaid > 0:
            raise InvalidOperation(
                "No se puede anular una factura a crédito que ya tiene abonos o está pagada."
            )

    if invoice.shiftId:
        shift_data = await ShiftsCollection.get_instance().fetch_shift_by_id(
            invoice.shiftId, session=session
        )
        if shift_data is not None and shift_data.get("status") != "open":
            settings = await AppSettingsTool().get_current_app_settings()
            if not settings.allowCancellationsOutsideShift:
                raise InvalidOperation(
                    "No se puede anular una factura perteneciente a un turno ya cerrado."
                )

    devolutions = await DevolutionsCollection.get_instance().fetch_devolutions_by_invoice_id(
        invoice_id=invoice.id,
        client_id=None,
        session=session,
    )
    if any(dev.get("status") in ACTIVE_DEVOLUTION_STATUSES for dev in devolutions):
        raise InvalidOperation(
            "No se puede anular una factura que tiene devoluciones activas o confirmadas."
        )

    credit_notes = (
        await CreditNotesCollection.get_instance().fetch_credit_notes_by_invoice_id(
            invoice_id=invoice.id,
            session=session,
        )
    )
    if any(cn.get("status") in ACTIVE_CREDIT_NOTE_STATUSES for cn in credit_notes):
        raise InvalidOperation(
            "No se puede anular una factura que tiene notas de crédito activas o aplicadas."
        )
