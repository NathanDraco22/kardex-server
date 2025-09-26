from typing import Tuple
from services.mongo_collections.v1 import (
    ReceiptsCollection,
    InvoicesCollection,
    ClientTransactionsCollection,
    ClientsCollection,
)
from repos.v1.receipts import CreateReceipt, ReceiptInDb
from repos.v1.client_transactions import ClientTransactionInDb
from repos.v1.clients import ClientInDb
from tools import UuidTool, TimeTools
from services import MongoService


async def process_receipt(
    create_receipt: CreateReceipt,
) -> Tuple[ReceiptInDb, ClientInDb]:
    """
    Procesa un recibo de pago de forma atómica.
    1. Guarda el nuevo documento de recibo.
    2. Aplica el monto a las facturas correspondientes.
    3. Crea una transacción de CRÉDITO para el cliente.
    4. Actualiza el saldo de la cuenta del cliente.
    """
    mongo_client = MongoService().client
    receipt_col = ReceiptsCollection()
    invoice_col = InvoicesCollection()
    client_transaction_col = ClientTransactionsCollection()
    client_account_col = ClientsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_receipt_data = create_receipt.model_dump()
            new_receipt_data["id"] = UuidTool.generate_uuid()
            new_receipt_data["createdAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await receipt_col.create_receipt_with_session(
                new_receipt_data,
                session=session,
            )
            new_receipt_in_db = ReceiptInDb.model_validate(insert_result)

            for applied_invoice in create_receipt.appliedInvoices:
                await invoice_col.add_to_amount_paid(
                    invoice_id=applied_invoice.invoiceId,
                    amount_paid=applied_invoice.amountApplied,
                    session=session,
                )

            updated_client_account_data = (
                await client_account_col.substract_from_client_balance(
                    client_id=create_receipt.clientId,
                    amount=create_receipt.total,
                    session=session,
                )
            )

            final_client_account = ClientInDb.model_validate(
                updated_client_account_data
            )

            new_client_transaction = ClientTransactionInDb(
                id=UuidTool.generate_uuid(),
                clientId=create_receipt.clientId,
                documentId=new_receipt_in_db.id,
                amount=-abs(create_receipt.total),
                type="credit",
                createdAt=TimeTools.get_now_in_milliseconds(),
                resultBalance=final_client_account.balance,
            )
            await client_transaction_col.create_client_transaction_with_session(
                new_client_transaction.model_dump(),
                session=session,
            )

            return new_receipt_in_db, final_client_account
