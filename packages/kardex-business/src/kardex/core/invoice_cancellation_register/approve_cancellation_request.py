from kardex.core.finance import ClientFinanceEngine, FinanceTransactionRequest
from kardex.core.inventory import fetch_product_types_map
from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.invoice_cancellation_requests import (
    InvoiceCancellationRequestInDb,
)
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import ProductTransactionInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ClientTransactionsCollection,
    ClientsCollection,
    InvoiceCancellationRequestsCollection,
    InvoicesCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.tools import (
    InvalidOperation,
    InvoiceCancellationRequestNotFound,
    TimeTools,
    UuidTool,
)

from .validate_invoice_cancellable import validate_invoice_cancellable


async def approve_cancellation_request(
    request_id: str,
    reviewed_by: UserInfo,
    review_notes: str = "",
) -> InvoiceCancellationRequestInDb:
    """Aprueba una solicitud de anulación de factura de forma atómica."""
    requests_col = InvoiceCancellationRequestsCollection.get_instance()
    invoices_col = InvoicesCollection.get_instance()
    prd_account_col = ProductAccountsCollection.get_instance()
    prd_tx_col = ProductTransactionsCollection.get_instance()
    client_col = ClientsCollection.get_instance()
    client_tx_col = ClientTransactionsCollection.get_instance()
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
                    raise InvoiceCancellationRequestNotFound(
                        f"InvoiceCancellationRequest {request_id} not found",
                        request_id=request_id,
                    )
                raise InvalidOperation(
                    f"La solicitud ya fue procesada (estado: {existing.get('status')})."
                )

            request_model = InvoiceCancellationRequestInDb.model_validate(transitioned)

            raw_invoice = await invoices_col.fetch_invoice_by_id_with_session(
                request_model.invoiceId, session
            )
            if raw_invoice is None:
                raise InvalidOperation("La factura asociada no existe.")

            invoice = InvoiceInDb.model_validate(raw_invoice)
            await validate_invoice_cancellable(invoice, session=session)

            if invoice.saleItems:
                product_types = await fetch_product_types_map(
                    [item.product.id for item in invoice.saleItems]
                )
                created_transactions: list[ProductTransactionInDb] = []

                for item in invoice.saleItems:
                    resolved_type = product_types.get(
                        item.product.id, item.product.productType
                    )
                    if resolved_type != "item":
                        continue

                    qty_to_return = abs(item.quantity + item.bonQuantity)
                    if qty_to_return == 0:
                        continue

                    updated_account_data = (
                        await prd_account_col.update_product_account_balance_data(
                            product_id=item.product.id,
                            branch_id=invoice.branchId,
                            add_to_current_stock=qty_to_return,
                            last_cost=item.cost,
                            session=session,
                        )
                    )
                    updated_account = ProductAccountInDb.model_validate(
                        updated_account_data
                    )

                    created_transactions.append(
                        ProductTransactionInDb(
                            id=UuidTool.generate_uuid(),
                            documentId=invoice.id,
                            docNumber=invoice.docNumber,
                            type="entry",
                            subtype="invoice_cancellation",
                            productId=item.product.id,
                            branchId=invoice.branchId,
                            quantity=qty_to_return,
                            averageCost=updated_account.averageCost,
                            resultStock=updated_account.currentStock,
                            createdAt=now,
                        )
                    )

                if created_transactions:
                    await prd_tx_col.create_many_product_transactions_with_session(
                        [t.model_dump() for t in created_transactions],
                        session=session,
                    )

            if invoice.paymentType == "credit" and invoice.clientId:
                await ClientFinanceEngine.process_movement(
                    request=FinanceTransactionRequest(
                        client_id=invoice.clientId,
                        amount=-invoice.total,
                        document_id=invoice.id,
                        doc_number=invoice.docNumber,
                        subtype="invoice_cancellation",
                    ),
                    session=session,
                    client_col=client_col,
                    client_tx_col=client_tx_col,
                )

            await invoices_col.update_invoice_by_id_with_session(
                invoice_id=invoice.id,
                invoice={
                    "status": "cancelled",
                    "cancelledAt": now,
                    "cancelledBy": reviewed_by.model_dump(),
                    "cancellationReason": request_model.reason,
                    "cancellationRequestId": request_model.id,
                    "updatedAt": now,
                },
                session=session,
            )

            return request_model
