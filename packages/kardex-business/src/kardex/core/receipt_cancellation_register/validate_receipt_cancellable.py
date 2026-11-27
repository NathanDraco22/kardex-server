from typing import Any

from kardex.repos.v1.receipts import ReceiptInDb
from kardex.services.mongo_collections.v1 import (
    InvoicesCollection,
    ShiftsCollection,
)
from kardex.tools import InvalidOperation
from kardex.tools.app_settings_tool import AppSettingsTool


async def validate_receipt_cancellable(
    receipt: ReceiptInDb,
    session: Any = None,
) -> None:
    """Valida que un recibo cumpla las reglas de negocio para ser anulado."""
    if receipt.isDeleted:
        raise InvalidOperation("El recibo ya se encuentra anulado.")

    if receipt.appliedDevolutions or receipt.appliedCreditNotes:
        raise InvalidOperation(
            "No se puede anular un recibo que tiene devoluciones o notas de crédito aplicadas."
        )

    if receipt.shiftId:
        shift_data = await ShiftsCollection.get_instance().fetch_shift_by_id(
            receipt.shiftId, session=session
        )
        if shift_data is not None and shift_data.get("status") != "open":
            settings = await AppSettingsTool().get_current_app_settings()
            if not settings.allowCancellationsOutsideShift:
                raise InvalidOperation(
                    "No se puede anular un recibo perteneciente a un turno ya cerrado."
                )

    invoices_col = InvoicesCollection.get_instance()
    for applied_invoice in receipt.appliedInvoices:
        inv_data = await invoices_col.fetch_invoice_by_id_with_session(
            invoice_id=applied_invoice.invoiceId,
            session=session,
        )
        if inv_data is None:
            raise InvalidOperation(
                f"La factura aplicada {applied_invoice.docNumber} no existe."
            )
        inv_status = inv_data.get("status")
        if inv_status in ("cancelled", "draft"):
            raise InvalidOperation(
                f"La factura {applied_invoice.docNumber} está en estado '{inv_status}' y no permite revertir el recibo."
            )
