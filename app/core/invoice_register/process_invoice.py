from tools import UuidTool, TimeTools
from repos.v1.invoices import CreateInvoice, InvoiceInDb
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb


from repos.v1.client_transactions import ClientTransactionInDb
from repos.v1.client_accounts import ClientAccountInDb

from services import MongoService

from services.mongo_collections.v1 import (
    InvoicesCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ClientAccountsCollection,
    ClientTransactionsCollection,
)


class InsufficientBalanceError(Exception):
    pass


async def process_invoice(
    create_invoice: CreateInvoice,
) -> tuple[InvoiceInDb, ClientAccountInDb]:
    mongo_client = MongoService().client

    prd_transaction_col = ProductTransactionsCollection()
    prd_account_col = ProductAccountsCollection()

    client_transaction_col = ClientTransactionsCollection()
    client_account_col = ClientAccountsCollection()

    invoice_col = InvoicesCollection()

    invoice_items = create_invoice.saleItems

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_invoice_doc_id = UuidTool.generate_uuid()

            updated_product_accounts: list[ProductAccountInDb] = []

            created_transactions: list[ProductTransactionInDb] = []

            for _, invoice_item in enumerate(invoice_items):
                total_to_substract = invoice_item.quantity + invoice_item.bonQuantity
                result = await prd_account_col.substract_product_account_data(
                    invoice_item.product.id,
                    create_invoice.branchId,
                    total_to_substract,
                    session=session,
                )

                if result is None:
                    raise InsufficientBalanceError()

                updated_product_account = ProductAccountInDb.model_validate(result)

                invoice_item.cost = updated_product_account.averageCost

                updated_product_accounts.append(updated_product_account)

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_invoice_doc_id,
                    type="SALE",
                    productId=invoice_item.product.id,
                    branchId=create_invoice.branchId,
                    quantity=total_to_substract,
                    averageCost=updated_product_account.averageCost,
                    createdAt=TimeTools.get_now_utc(),
                )

                created_transactions.append(new_transaction)

            new_invoice_date = create_invoice.model_dump()
            new_invoice_date["id"] = new_invoice_doc_id
            new_invoice_date["createdAt"] = TimeTools.get_now_utc()

            insert_result = await invoice_col.create_invoice_with_session(
                new_invoice_date,
                session=session,
            )

            created_transactions_data = [
                transaction.model_dump() for transaction in created_transactions
            ]

            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            new_invoice_in_db = InvoiceInDb.model_validate(insert_result)

            new_client_transaction = ClientTransactionInDb(
                id=UuidTool.generate_uuid(),
                clientId=create_invoice.clientId,
                documentId=new_invoice_in_db.id,
                amount=new_invoice_in_db.total,
                type="DEBIT",
                createdAt=TimeTools.get_now_utc(),
            )

            new_client_transaction_data = new_client_transaction.model_dump()

            await client_transaction_col.create_client_transaction_with_session(
                new_client_transaction_data,
                session=session,
            )

            client_account_data = await client_account_col.add_to_client_account(
                create_invoice.clientId,
                new_invoice_in_db.total,
                session=session,
            )

            if new_invoice_in_db.paymentType == "CASH":
                await invoice_col.add_to_amount_paid(
                    new_invoice_in_db.id,
                    new_invoice_in_db.total,
                    session=session,
                )

                new_client_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_invoice.clientId,
                    documentId=new_invoice_in_db.id,
                    amount=new_invoice_in_db.total,
                    type="CREDIT",
                    createdAt=TimeTools.get_now_utc(),
                )

                new_client_transaction_data = new_client_transaction.model_dump()

                await client_transaction_col.create_client_transaction_with_session(
                    new_client_transaction_data,
                    session=session,
                )

                client_account_data = (
                    await client_account_col.substract_from_client_account(
                        create_invoice.clientId,
                        new_invoice_in_db.total,
                        session=session,
                    )
                )

            client_account = ClientAccountInDb.model_validate(client_account_data)

            return new_invoice_in_db, client_account
