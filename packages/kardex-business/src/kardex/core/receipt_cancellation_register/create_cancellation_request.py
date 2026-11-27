from pymongo.errors import DuplicateKeyError

from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.receipt_cancellation_requests import (
    CreateReceiptCancellationRequest,
    ReceiptCancellationRequestInDb,
)
from kardex.repos.v1.receipts import ReceiptInDb
from kardex.services.mongo_collections.v1 import (
    ReceiptCancellationRequestsCollection,
    ReceiptsCollection,
)
from kardex.tools import InvalidOperation, TimeTools, UuidTool

from .validate_receipt_cancellable import validate_receipt_cancellable


async def create_receipt_cancellation_request(
    body: CreateReceiptCancellationRequest,
) -> ReceiptCancellationRequestInDb:
    """Crea una solicitud de anulación de recibo en estado `pending`."""
    reason = body.reason.strip()
    if len(reason) < 3:
        raise InvalidOperation("El motivo de anulación debe tener al menos 3 caracteres.")

    receipts_col = ReceiptsCollection.get_instance()
    requests_col = ReceiptCancellationRequestsCollection.get_instance()

    raw_receipt = await receipts_col.fetch_receipt_by_id(body.receiptId)
    if raw_receipt is None:
        raise InvalidOperation("El recibo solicitado no existe.")

    receipt = ReceiptInDb.model_validate(raw_receipt)
    await validate_receipt_cancellable(receipt)

    existing_pending = await requests_col.fetch_pending_by_receipt_id(receipt.id)
    if existing_pending is not None:
        raise InvalidOperation(
            "Ya existe una solicitud de anulación pendiente para este recibo."
        )

    now = TimeTools.get_now_in_milliseconds()
    doc_number = await CounterManager().next_receipt_cancellation_request_number()
    request_model = ReceiptCancellationRequestInDb(
        id=UuidTool.generate_uuid(),
        docNumber=doc_number,
        branchId=receipt.branchId,
        receiptId=receipt.id,
        receiptDocNumber=receipt.docNumber,
        receiptTotal=receipt.total,
        receiptPaymentMethod=receipt.paymentMethod,
        receiptShiftId=receipt.shiftId,
        clientId=receipt.clientId,
        clientInfo=receipt.clientInfo,
        reason=reason,
        requestedBy=body.requestedBy,
        status="pending",
        createdAt=now,
    )

    try:
        await requests_col.create_request(request_model.model_dump())
    except DuplicateKeyError as exc:
        raise InvalidOperation(
            "Ya existe una solicitud de anulación pendiente para este recibo."
        ) from exc

    return request_model
