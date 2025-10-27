from tools import UuidTool, TimeTools
from repos.v1.invoices import CreateInvoice, InvoiceInDb
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb

from repos.v1.client_transactions import ClientTransactionInDb
from repos.v1.clients import ClientInDb

from services import MongoService

from services.mongo_collections.v1 import (
    InvoicesCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ClientsCollection,
    ClientTransactionsCollection,
    OrdersCollection,
)


class InsufficientBalanceError(Exception):
    pass


async def process_invoice(
    create_invoice: CreateInvoice,
) -> tuple[InvoiceInDb, ClientInDb]:
    mongo_client = MongoService().client

    prd_transaction_col = ProductTransactionsCollection()
    prd_account_col = ProductAccountsCollection()

    order_col = OrdersCollection()

    client_transaction_col = ClientTransactionsCollection()
    client_account_col = ClientsCollection()

    invoice_col = InvoicesCollection()

    order_col = OrdersCollection()

    invoice_items = create_invoice.saleItems

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_invoice_doc_id = UuidTool.generate_uuid()

            updated_product_accounts: list[ProductAccountInDb] = []

            created_transactions: list[ProductTransactionInDb] = []

            for _, invoice_item in enumerate(invoice_items):
                total_to_dispatch = abs(
                    invoice_item.quantity + invoice_item.bonQuantity
                )
                if create_invoice.orderNumber:
                    result = await prd_account_col.dispatch_promise_stock(
                        invoice_item.product.id,
                        create_invoice.branchId,
                        total_to_dispatch,
                        session=session,
                    )
                else:
                    result = await prd_account_col.dispatch_direct_stock(
                        invoice_item.product.id,
                        create_invoice.branchId,
                        total_to_dispatch,
                        session=session,
                    )

                if result is None:
                    raise InsufficientBalanceError(
                        f"Stock insuficiente para {invoice_item.product.id}"
                    )

                updated_product_account = ProductAccountInDb.model_validate(result)

                invoice_item.cost = updated_product_account.averageCost

                updated_product_accounts.append(updated_product_account)

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_invoice_doc_id,
                    docNumber=create_invoice.docNumber,
                    type="exit",
                    subtype="invoice",
                    productId=invoice_item.product.id,
                    branchId=create_invoice.branchId,
                    quantity=-total_to_dispatch,
                    averageCost=updated_product_account.averageCost,
                    resultStock=updated_product_account.currentStock,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                )

                created_transactions.append(new_transaction)

            new_invoice_date = create_invoice.model_dump()
            new_invoice_date["id"] = new_invoice_doc_id
            new_invoice_date["createdAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await invoice_col.create_invoice_with_session(
                new_invoice_date,
                session=session,
            )

            await order_col.update_order_by_doc_number(
                create_invoice.orderNumber,
                {"invoiceId": new_invoice_doc_id},
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

            client_account_data = await client_account_col.add_to_client_balance(
                create_invoice.clientId,
                new_invoice_in_db.total,
                session=session,
            )

            client_account = ClientInDb.model_validate(client_account_data)

            new_client_transaction = ClientTransactionInDb(
                id=UuidTool.generate_uuid(),
                clientId=create_invoice.clientId,
                documentId=new_invoice_in_db.id,
                docNumber=new_invoice_in_db.docNumber,
                amount=new_invoice_in_db.total,
                type="debit",
                subtype="invoice",
                createdAt=TimeTools.get_now_in_milliseconds(),
                resultBalance=client_account.balance,
            )

            new_client_transaction_data = new_client_transaction.model_dump()

            await client_transaction_col.create_client_transaction_with_session(
                new_client_transaction_data,
                session=session,
            )

            if new_invoice_in_db.paymentType == "cash":
                await invoice_col.add_to_amount_paid(
                    new_invoice_in_db.id,
                    new_invoice_in_db.total,
                    session=session,
                )

                client_account_data = (
                    await client_account_col.substract_from_client_balance(
                        create_invoice.clientId,
                        new_invoice_in_db.total,
                        session=session,
                    )
                )

                client_account = ClientInDb.model_validate(client_account_data)

                new_client_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_invoice.clientId,
                    documentId=new_invoice_in_db.id,
                    docNumber=new_invoice_in_db.docNumber,
                    amount=-(new_invoice_in_db.total),
                    type="credit",
                    subtype="invoice",
                    createdAt=TimeTools.get_now_in_milliseconds(),
                    resultBalance=client_account.balance,
                )

                new_client_transaction_data = new_client_transaction.model_dump()

                await client_transaction_col.create_client_transaction_with_session(
                    new_client_transaction_data,
                    session=session,
                )

            if new_invoice_in_db.orderNumber:
                await order_col.update_order_status_by_doc_number(
                    doc_number=new_invoice_in_db.orderNumber,
                    status="completed",
                    session=session,
                )

            return new_invoice_in_db, client_account


async def process_anon_invoice(
    create_invoice: CreateInvoice,
) -> tuple[InvoiceInDb, list[ProductAccountInDb]]:
    """
    Procesa una factura anónima (venta de mostrador).
    1. Afecta el inventario (venta directa).
    2. Enriquece los items con su costo.
    3. Guarda la factura.
    4. Guarda las transacciones de producto.
    """
    mongo_client = MongoService().client
    prd_transaction_col = ProductTransactionsCollection()
    prd_account_col = ProductAccountsCollection()
    invoice_col = InvoicesCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_invoice_doc_id = UuidTool.generate_uuid()

            updated_product_accounts: list[ProductAccountInDb] = []
            created_transactions: list[ProductTransactionInDb] = []

            for invoice_item in create_invoice.saleItems:
                total_to_dispatch = abs(
                    invoice_item.quantity + invoice_item.bonQuantity
                )

                result = await prd_account_col.dispatch_direct_stock(
                    invoice_item.product.id,
                    create_invoice.branchId,
                    total_to_dispatch,
                    session=session,
                )

                if result is None:
                    raise InsufficientBalanceError(
                        f"Stock insuficiente para {invoice_item.product.id}"
                    )

                updated_product_account = ProductAccountInDb.model_validate(result)
                invoice_item.cost = updated_product_account.averageCost
                updated_product_accounts.append(updated_product_account)

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_invoice_doc_id,
                    docNumber=create_invoice.docNumber,
                    type="exit",
                    subtype="invoice",
                    productId=invoice_item.product.id,
                    branchId=create_invoice.branchId,
                    quantity=-(total_to_dispatch),
                    averageCost=updated_product_account.averageCost,
                    resultStock=updated_product_account.currentStock,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                )
                created_transactions.append(new_transaction)

            new_invoice_data = create_invoice.model_dump()
            new_invoice_data["id"] = new_invoice_doc_id
            new_invoice_data["createdAt"] = TimeTools.get_now_in_milliseconds()
            new_invoice_data["amountPaid"] = create_invoice.total
            new_invoice_data["paidAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await invoice_col.create_invoice_with_session(
                new_invoice_data,
                session=session,
            )

            created_transactions_data = [t.model_dump() for t in created_transactions]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            new_invoice_in_db = InvoiceInDb.model_validate(insert_result)

            return new_invoice_in_db, updated_product_accounts
