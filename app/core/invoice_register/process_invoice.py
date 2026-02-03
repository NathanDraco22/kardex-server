from tools import UuidTool, TimeTools
from repos.v1.invoices import CreateInvoice, InvoiceInDb
from repos.v1.product_accounts import ProductAccountInDb
from core.inventory import (
    execute_inventory_exit_db_operations,
    prepare_inventory_exit_batch,
    InventoryExitBatchItem,
)

from core.finance import process_client_financial_movement, FinanceTransactionRequest
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

    # Colecciones
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()
    invoice_col = InvoicesCollection()
    order_col = OrdersCollection()
    client_col = ClientsCollection()
    client_tx_col = ClientTransactionsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_invoice_id = UuidTool.generate_uuid()
            current_time = TimeTools.get_now_in_milliseconds()

            # ==========================================
            # 1. PREPARACIÓN DE INVENTARIO
            # ==========================================
            batch_items: list[InventoryExitBatchItem] = []
            for item in create_invoice.saleItems:
                total_qty = abs(item.quantity + item.bonQuantity)
                batch_items.append(
                    InventoryExitBatchItem(
                        product_id=item.product.id, quantity=total_qty
                    )
                )

            # Obtener Cuentas
            product_ids = [item.product_id for item in batch_items]
            accounts_data = await product_account_col.get_accounts_by_branch_id(
                branch_id=create_invoice.branchId,
                product_ids=product_ids,
                session=session,
            )
            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in accounts_data
            }

            # Ejecutar cálculos (Validación de stock físico + Costos + Kardex)
            batch_result = prepare_inventory_exit_batch(
                branch_id=create_invoice.branchId,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                document_id=new_invoice_id,
                doc_number=create_invoice.docNumber,
                tx_type="exit",
                tx_subtype="invoice",
            )

            # Asignar Costos Reales a la Factura
            for i, item in enumerate(create_invoice.saleItems):
                item.cost = batch_result.assigned_costs[i]

            # ==========================================
            # 2. PERSISTENCIA DE INVENTARIO (DIFERENCIADA)
            # ==========================================
            is_order_fulfillment = (
                create_invoice.orderNumber and create_invoice.status == "open"
            )

            if is_order_fulfillment:
                # CAMINO A: ES UN PEDIDO -> Usamos bulk_dispatch_promise_stock
                await product_account_col.bulk_dispatch_promise_stock(
                    branch_id=create_invoice.branchId,
                    bulk_data=batch_result.stock_subtractions,
                    session=session,
                )

                # Guardar Kardex manualmente (porque no usamos execute_inventory_exit...)
                created_transactions_data = [
                    t.model_dump() for t in batch_result.transactions
                ]
                await prd_transaction_col.create_many_product_transactions_with_session(
                    created_transactions_data, session=session
                )

            else:
                # CAMINO B: VENTA DIRECTA -> Usamos el método estándar
                await execute_inventory_exit_db_operations(
                    branch_id=create_invoice.branchId,
                    batch_result=batch_result,
                    session=session,
                    account_col=product_account_col,
                    transaction_col=prd_transaction_col,
                )

            # ==========================================
            # 3. GUARDAR FACTURA
            # ==========================================
            if create_invoice.status == "draft":
                create_invoice.status = "open"

            new_invoice_data = create_invoice.model_dump()
            new_invoice_data.update(
                {
                    "id": new_invoice_id,
                    "createdAt": current_time,
                    "amountPaid": create_invoice.total
                    if create_invoice.paymentType == "cash"
                    else 0,
                    "paidAt": current_time
                    if create_invoice.paymentType == "cash"
                    else None,
                    "saleItems": [
                        item.model_dump() for item in create_invoice.saleItems
                    ],
                }
            )

            await invoice_col.create_invoice_with_session(
                new_invoice_data, session=session
            )
            new_invoice_in_db = InvoiceInDb.model_validate(new_invoice_data)

            # ==========================================
            # 4. ACTUALIZAR PEDIDO (USANDO TU MÉTODO EXISTENTE)
            # ==========================================
            if create_invoice.orderNumber:
                # Preparamos el diccionario de actualización
                order_update_payload = {
                    "invoiceId": new_invoice_id,
                    "status": "completed",  # O el estado que marque cierre
                    "updatedAt": current_time,
                }

                await order_col.update_order_by_doc_number(
                    doc_number=create_invoice.orderNumber,
                    order=order_update_payload,  # <--- Pasamos el dict aquí
                    session=session,
                )

            # ==========================================
            # 5. GESTIÓN FINANCIERA
            # ==========================================

            # A. Cargo (Deuda)
            client_account = await process_client_financial_movement(
                request=FinanceTransactionRequest(
                    client_id=create_invoice.clientId,
                    amount=new_invoice_in_db.total,
                    document_id=new_invoice_id,
                    doc_number=new_invoice_in_db.docNumber,
                    subtype="invoice",
                ),
                session=session,
                client_col=client_col,
                client_tx_col=client_tx_col,
            )

            # B. Pago Contado (Abono)
            if new_invoice_in_db.paymentType == "cash":
                client_account = await process_client_financial_movement(
                    request=FinanceTransactionRequest(
                        client_id=create_invoice.clientId,
                        amount=-(new_invoice_in_db.total),
                        document_id=new_invoice_id,
                        doc_number=new_invoice_in_db.docNumber,
                        subtype="invoice",
                    ),
                    session=session,
                    client_col=client_col,
                    client_tx_col=client_tx_col,
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
