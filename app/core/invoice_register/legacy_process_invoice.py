from tools import UuidTool, TimeTools
from repos.v1.invoices import CreateInvoice, InvoiceInDb
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb

from core.inventory import (
    execute_inventory_exit_db_operations,
    prepare_inventory_exit_batch,
    InventoryExitBatchItem,
)

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
                if create_invoice.orderNumber and create_invoice.status == "open":
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
                        f"Stock insuficiente para {invoice_item.product.name}"
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

            if create_invoice.status == "draft":
                create_invoice.status = "open"

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
    Procesa una factura anónima (venta de mostrador) utilizando el motor de inventario unificado.
    """
    mongo_client = MongoService().client

    # Colecciones
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()
    invoice_col = InvoicesCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_invoice_doc_id = UuidTool.generate_uuid()
            current_time = TimeTools.get_now_in_milliseconds()

            # 1. PREPARAR DATOS DE SALIDA (Mapeo a InventoryExitBatchItem)
            # REGLA DE NEGOCIO: En ventas, descontamos Cantidad + Bonificación
            batch_items = []
            for item in create_invoice.saleItems:
                total_to_dispatch = abs(item.quantity + item.bonQuantity)

                batch_items.append(
                    InventoryExitBatchItem(
                        product_id=item.product.id,  # Accedemos al ID dentro del objeto product
                        quantity=total_to_dispatch,
                    )
                )

            # 2. OBTENER CUENTAS ACTUALES (Snapshot Read)
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=create_invoice.branchId,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            # 3. EJECUTAR LÓGICA PURA REUTILIZABLE 🧠
            # Valida stock, calcula costos de salida y prepara transacciones
            batch_result = prepare_inventory_exit_batch(
                branch_id=create_invoice.branchId,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                # Metadata de la Factura
                document_id=new_invoice_doc_id,
                doc_number=create_invoice.docNumber,
                # Tipo de Transacción
                tx_type="exit",
                tx_subtype="invoice",  # "invoice"
            )

            # 4. ENRIQUECER ITEMS DE LA FACTURA CON EL COSTO REAL
            # Asignamos el Costo Promedio calculado al momento de la salida
            # Nota: Asumimos que el orden de create_invoice.saleItems coincide con batch_items
            for i, invoice_item in enumerate(create_invoice.saleItems):
                invoice_item.cost = batch_result.assigned_costs[i]

            # 5. PERSISTENCIA MASIVA EN BD 💾
            await execute_inventory_exit_db_operations(
                branch_id=create_invoice.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                transaction_col=prd_transaction_col,
            )

            # 6. GUARDAR LA FACTURA
            new_invoice_data = create_invoice.model_dump()
            new_invoice_data.update(
                {
                    "id": new_invoice_doc_id,
                    "createdAt": current_time,
                    "paidAt": current_time,  # Al ser anónima/contado, se paga al instante
                    "amountPaid": create_invoice.total,
                    # Guardamos los items ya con su campo 'cost' actualizado en el paso 4
                    "saleItems": [
                        item.model_dump() for item in create_invoice.saleItems
                    ],
                }
            )

            insert_result = await invoice_col.create_invoice_with_session(
                new_invoice_data,
                session=session,
            )

            new_invoice_in_db = InvoiceInDb.model_validate(insert_result)

            # 7. PREPARAR RETORNO (Cuentas actualizadas)
            # Filtramos del diccionario las cuentas que fueron tocadas
            updated_accounts = []
            for item in batch_items:
                if item.product_id in accounts_dict:
                    updated_accounts.append(accounts_dict[item.product_id])

            return new_invoice_in_db, updated_accounts
