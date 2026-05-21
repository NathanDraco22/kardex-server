from typing import Tuple
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ReceiptsCollection,
    InvoicesCollection,
    ClientTransactionsCollection,
    ClientsCollection,
    DevolutionsCollection,
)
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.receipts import ReceiptInDb
from kardex.repos.v1.client_transactions import ClientTransactionInDb
from kardex.repos.v1.clients import ClientInDb
from kardex.tools import UuidTool, TimeTools, InvalidOperation


async def reverse_receipt(
    receipt: ReceiptInDb,
) -> Tuple[ReceiptInDb, ClientInDb]:
    """
    Revierte un recibo eliminado, restaurando el balance del cliente,
    revertiendo los pagos de facturas y creando transacciones inversas.
    Solo permite revertir si las facturas involucradas están en estado 'partiallyPaid'.
    """
    mongo_client = MongoService().client
    receipt_col = ReceiptsCollection.get_instance()
    invoice_col = InvoicesCollection.get_instance()
    devolution_col = DevolutionsCollection.get_instance()
    client_transaction_col = ClientTransactionsCollection.get_instance()
    client_account_col = ClientsCollection.get_instance()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            for applied_invoice in receipt.appliedInvoices:
                current_invoice_data = (
                    await invoice_col.fetch_invoice_by_id_with_session(
                        invoice_id=applied_invoice.invoiceId, session=session
                    )
                )

                if current_invoice_data is None:
                    raise InvalidOperation(f"Invoice {applied_invoice.invoiceId} not found")

                current_invoice = InvoiceInDb.model_validate(current_invoice_data)

                if current_invoice.status == "paid":
                    raise InvalidOperation(f"Invoice {current_invoice.docNumber} is already paid, cannot reverse")

                if current_invoice.status == "cancelled":
                    raise InvalidOperation(f"Invoice {current_invoice.docNumber} is cancelled, cannot reverse")

                if current_invoice.status == "draft":
                    raise InvalidOperation(f"Invoice {current_invoice.docNumber} is still in draft, cannot reverse")

                await invoice_col.subtract_from_amount_paid(
                    invoice_id=applied_invoice.invoiceId,
                    amount_paid=applied_invoice.amountApplied,
                    session=session,
                )

            final_client_account = None

            for applied_devolution in receipt.appliedDevolutions:
                await devolution_col.update_devolution_status_by_id(
                    devolution_id=applied_devolution.devolutionId,
                    status="available",
                    session=session,
                )

                updated_client_data = await client_account_col.add_to_client_balance(
                    client_id=receipt.clientId,
                    amount=applied_devolution.amountApplied,
                    timestamp=now_in_milliseconds,
                    session=session,
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                devolution_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=receipt.clientId,
                    documentId=applied_devolution.devolutionId,
                    docNumber=applied_devolution.docNumber,
                    amount=abs(applied_devolution.amountApplied),
                    type="debit",
                    subtype="devolution",
                    resultBalance=final_client_account.balance,
                    createdAt=now_in_milliseconds,
                )
                await client_transaction_col.create_client_transaction_with_session(
                    devolution_transaction.model_dump(), session=session
                )

            if receipt.total > 0:
                updated_client_data = await client_account_col.add_to_client_balance(
                    client_id=receipt.clientId,
                    amount=receipt.total,
                    timestamp=now_in_milliseconds,
                    session=session,
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                payment_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=receipt.clientId,
                    documentId=receipt.id,
                    docNumber=receipt.docNumber,
                    amount=abs(receipt.total),
                    type="debit",
                    subtype="receipt",
                    resultBalance=final_client_account.balance,
                    createdAt=now_in_milliseconds,
                )
                await client_transaction_col.create_client_transaction_with_session(
                    payment_transaction.model_dump(), session=session
                )

            if final_client_account is None:
                client_data = await client_account_col.fetch_client_by_id(
                    receipt.clientId
                )
                final_client_account = ClientInDb.model_validate(client_data)

            deleted_receipt_data = await receipt_col.delete_receipt_by_id_with_session(
                receipt_id=receipt.id,
                deleted_at=now_in_milliseconds,
                session=session,
            )
            deleted_receipt = ReceiptInDb.model_validate(deleted_receipt_data)

            return deleted_receipt, final_client_account
