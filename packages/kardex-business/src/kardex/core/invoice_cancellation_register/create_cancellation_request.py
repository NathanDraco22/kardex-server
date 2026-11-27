from pymongo.errors import DuplicateKeyError

from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.invoice_cancellation_requests import (
    CreateInvoiceCancellationRequest,
    InvoiceCancellationRequestInDb,
)
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.services.mongo_collections.v1 import (
    InvoiceCancellationRequestsCollection,
    InvoicesCollection,
)
from kardex.tools import InvalidOperation, TimeTools, UuidTool

from .validate_invoice_cancellable import validate_invoice_cancellable


async def create_cancellation_request(
    body: CreateInvoiceCancellationRequest,
) -> InvoiceCancellationRequestInDb:
    """Crea una solicitud de anulación de factura en estado `pending`."""
    reason = body.reason.strip()
    if len(reason) < 3:
        raise InvalidOperation("El motivo de anulación debe tener al menos 3 caracteres.")

    invoices_col = InvoicesCollection.get_instance()
    requests_col = InvoiceCancellationRequestsCollection.get_instance()

    raw_invoice = await invoices_col.fetch_invoice_by_id(body.invoiceId)
    if raw_invoice is None:
        raise InvalidOperation("La factura solicitada no existe.")

    invoice = InvoiceInDb.model_validate(raw_invoice)
    await validate_invoice_cancellable(invoice)

    existing_pending = await requests_col.fetch_pending_by_invoice_id(invoice.id)
    if existing_pending is not None:
        raise InvalidOperation(
            "Ya existe una solicitud de anulación pendiente para esta factura."
        )

    now = TimeTools.get_now_in_milliseconds()
    doc_number = await CounterManager().next_invoice_cancellation_request_number()
    request_model = InvoiceCancellationRequestInDb(
        id=UuidTool.generate_uuid(),
        docNumber=doc_number,
        branchId=invoice.branchId,
        invoiceId=invoice.id,
        invoiceDocNumber=invoice.docNumber,
        invoiceTotal=invoice.total,
        invoicePaymentType=invoice.paymentType,
        invoiceStatus=invoice.status,
        invoiceShiftId=invoice.shiftId,
        clientId=invoice.clientId,
        clientInfo=invoice.clientInfo,
        reason=reason,
        requestedBy=body.requestedBy,
        status="pending",
        createdAt=now,
    )

    try:
        await requests_col.create_request(request_model.model_dump())
    except DuplicateKeyError as exc:
        raise InvalidOperation(
            "Ya existe una solicitud de anulación pendiente para esta factura."
        ) from exc

    return request_model
