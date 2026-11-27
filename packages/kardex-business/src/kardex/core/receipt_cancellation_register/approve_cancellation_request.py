from kardex.repos.v1.client_transactions import ClientTransactionInDb
from kardex.repos.v1.clients import ClientInDb
from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.receipt_cancellation_requests import (
    ReceiptCancellationRequestInDb,
)
from kardex.repos.v1.receipts import ReceiptInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ClientTransactionsCollection,
    ClientsCollection,
    InvoicesCollection,
    ReceiptCancellationRequestsCollection,
    ReceiptsCollection,
)
from kardex.tools import (
    InvalidOperation,
    ReceiptCancellationRequestNotFound,
    TimeTools,
    UuidTool,
)

from .validate_receipt_cancellable import validate_receipt_cancellable


async def approve_receipt_cancellation_request(
    request_id: str,
    reviewed_by: UserInfo,
    review_notes: str = "",
) -> ReceiptCancellationRequestInDb:
    """Aprueba una solicitud de anulación de recibo y revierte sus efectos de forma atómica."""
    requests_col = ReceiptCancellationRequestsCollection.get_instance()
    receipt_col = ReceiptsCollection.get_instance()
    invoice_col = InvoicesCollection.get_instance()
    client_tx_col = ClientTransactionsCollection.get_instance()
    client_col = ClientsCollection.get_instance()
    mongo_client = MongoService().client

    now = TimeTools.get_now_in_milliseconds()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            transitioned = await requests_col.transition_request_status(
                request_id=request_id,
                update_data={
                    "status": "approved",
                    "reviewedBy": reviewed_by.model_dump(),
                    "reviewedAt": now,
                    "reviewNotes": review_notes.strip(),
                    "updatedAt": now,
                },
                session=session,
            )

            if transitioned is None:
                existing = await requests_col.fetch_request_by_id_with_session(
                    request_id, session
                )
                if existing is None:
                    raise ReceiptCancellationRequestNotFound(
                        f"ReceiptCancellationRequest {request_id} not found",
                        request_id=request_id,
                    )
                raise InvalidOperation(
                    f"La solicitud ya fue procesada (estado: {existing.get('status')})."
                )

            request_model = ReceiptCancellationRequestInDb.model_validate(transitioned)

            raw_receipt = await receipt_col.get_receipt_by_id_with_session(
                receipt_id=request_model.receiptId,
                session=session,
            )
            if raw_receipt is None:
                raise InvalidOperation("El recibo asociado no existe.")

            receipt = ReceiptInDb.model_validate(raw_receipt)
            await validate_receipt_cancellable(receipt, session=session)

            for applied_invoice in receipt.appliedInvoices:
                await invoice_col.subtract_from_amount_paid(
                    invoice_id=applied_invoice.invoiceId,
                    amount_paid=applied_invoice.amountApplied,
                    session=session,
                )

            if receipt.total > 0:
                updated_client_data = await client_col.add_to_client_balance(
                    client_id=receipt.clientId,
                    amount=receipt.total,
                    timestamp=now,
                    session=session,
                )
                client_account = ClientInDb.model_validate(updated_client_data)
                payment_tx = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=receipt.clientId,
                    documentId=receipt.id,
                    docNumber=receipt.docNumber,
                    amount=abs(receipt.total),
                    type="debit",
                    subtype="receipt",
                    resultBalance=client_account.balance,
                    createdAt=now,
                )
                await client_tx_col.create_client_transaction_with_session(
                    payment_tx.model_dump(), session=session
                )

            await receipt_col.mark_receipt_cancelled_with_session(
                receipt_id=receipt.id,
                update_data={
                    "isDeleted": True,
                    "deletedAt": now,
                    "cancelledAt": now,
                    "cancelledBy": reviewed_by.model_dump(),
                    "cancellationReason": request_model.reason,
                    "cancellationRequestId": request_model.id,
                    "updatedAt": now,
                },
                session=session,
            )

            return request_model
