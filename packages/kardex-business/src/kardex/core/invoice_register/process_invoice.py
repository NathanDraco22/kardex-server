from typing import Any

from kardex.tools import UuidTool, TimeTools
from kardex.kardex_config import KardexConfig
from kardex.repos.v1.invoices import CreateInvoice, InvoiceInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryExitBatchItem,
    InventoryEngine,
    calculate_line_amount,
    fetch_product_types_and_price_factors_map,
)
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.core.finance import ClientFinanceEngine, FinanceTransactionRequest
from kardex.repos.v1.clients import ClientInDb

from kardex.services import MongoService

from kardex.services.mongo_collections.v1 import (
    InvoicesCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ClientsCollection,
    ClientTransactionsCollection,
    OrdersCollection,
)

from .invoice_rounding_policy import InvoiceRoundingPolicy


async def _prepare_and_execute_invoice_inventory(
    create_invoice: CreateInvoice,
    invoice_id: str,
    session: Any,
    product_account_col: ProductAccountsCollection,
    prd_transaction_col: ProductTransactionsCollection,
    is_order_fulfillment: bool = False,
) -> dict[str, ProductAccountInDb]:
    """Procesa la salida de inventario únicamente para ítems inventariables (`productType == 'item'`)."""
    product_ids = list({item.product.id for item in create_invoice.saleItems})
    product_types, price_unit_factors = (
        await fetch_product_types_and_price_factors_map(product_ids)
    )

    accounts_data = await product_account_col.get_accounts_by_branch_id(
        branch_id=create_invoice.branchId,
        product_ids=product_ids,
        session=session,
    )
    accounts_dict = {
        acc["productId"]: ProductAccountInDb.model_validate(acc)
        for acc in accounts_data
    }

    inventory_indices: list[int] = []
    batch_items: list[InventoryExitBatchItem] = []

    for idx, item in enumerate(create_invoice.saleItems):
        resolved_type = product_types.get(item.product.id, item.product.productType)
        item.product.productType = resolved_type
        item.priceUnitFactor = price_unit_factors.get(
            item.product.id, max(item.priceUnitFactor, 1)
        )

        if resolved_type == "item":
            total_qty = abs(item.quantity + item.bonQuantity)
            inventory_indices.append(idx)
            batch_items.append(
                InventoryExitBatchItem(
                    product_id=item.product.id,
                    quantity=total_qty,
                    product_name=item.product.name,
                )
            )
        else:
            account = accounts_dict.get(item.product.id)
            item.cost = account.averageCost if account is not None else 0

    if batch_items:
        batch_result = InventoryBatchTransformer.prepare_exit(
            branch_id=create_invoice.branchId,
            items=batch_items,
            existing_accounts_dict=accounts_dict,
            document_id=invoice_id,
            doc_number=create_invoice.docNumber,
            tx_type="exit",
            tx_subtype="invoice",
            is_order_fulfillment=is_order_fulfillment,
        )

        for batch_pos, item_idx in enumerate(inventory_indices):
            create_invoice.saleItems[item_idx].cost = batch_result.assigned_costs[
                batch_pos
            ]

        if is_order_fulfillment:
            await product_account_col.bulk_dispatch_promise_stock(
                branch_id=create_invoice.branchId,
                bulk_data=batch_result.stock_subtractions,
                session=session,
            )
            created_transactions_data = [
                t.model_dump() for t in batch_result.transactions
            ]
            if created_transactions_data:
                await prd_transaction_col.create_many_product_transactions_with_session(
                    created_transactions_data, session=session
                )
        else:
            await InventoryEngine.execute_exit(
                branch_id=create_invoice.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                transaction_col=prd_transaction_col,
                allow_negative=KardexConfig().letInvoiceWithNegative,
            )

    create_invoice.totalCost = sum(
        calculate_line_amount(
            item.cost,
            item.quantity + item.bonQuantity,
            item.priceUnitFactor,
        )
        for item in create_invoice.saleItems
    )

    return accounts_dict


def normalize_invoice_discounts(
    create_invoice: CreateInvoice, *, round_up: bool = False
) -> None:
    """Valida y normaliza los subtotales y descuentos por ítem y el descuento global de la factura.

    Con `round_up=True` los subtotales de línea se redondean hacia arriba y los
    descuentos hacia abajo para que subtotal, descuentos y total queden en
    unidades enteras de la moneda, manteniendo la igualdad
    ``subtotal - descuentos = total``.
    """
    rounding = InvoiceRoundingPolicy(round_up)
    for item in create_invoice.saleItems:
        if item.price > 0 and item.quantity > 0:
            item.subTotal = calculate_line_amount(
                item.price,
                item.quantity,
                max(item.priceUnitFactor, 1),
            )
        else:
            item.subTotal = max(0, item.subTotal)
        item.subTotal = rounding.line_subtotal(item.subTotal)
        if item.discountType == "percentage":
            pct = max(0, min(100, item.discountPercentage))
            item.discountPercentage = pct
            item.totalDiscount = round(item.subTotal * pct / 100)
        elif item.discountType == "amount":
            item.discountPercentage = 0
            item.totalDiscount = max(0, min(item.subTotal, item.totalDiscount))
        else:
            if item.discountPercentage > 0:
                pct = min(100, item.discountPercentage)
                item.discountType = "percentage"
                item.discountPercentage = pct
                item.totalDiscount = round(item.subTotal * pct / 100)
            elif item.totalDiscount > 0:
                item.discountType = "amount"
                item.discountPercentage = 0
                item.totalDiscount = min(item.subTotal, item.totalDiscount)
            else:
                item.discountPercentage = 0
                item.totalDiscount = 0
        item.totalDiscount = max(0, min(item.subTotal, item.totalDiscount))
        item.totalDiscount = rounding.line_discount(item.totalDiscount)
        item.total = max(0, item.subTotal - item.totalDiscount)

    items_net_total = sum(item.total for item in create_invoice.saleItems)
    create_invoice.itemDiscounts = sum(
        item.totalDiscount for item in create_invoice.saleItems
    )

    if create_invoice.discountType == "percentage":
        pct = max(0, min(100, create_invoice.discountValue))
        create_invoice.discountValue = pct
        create_invoice.invoiceDiscount = round(items_net_total * pct / 100)
        create_invoice.invoiceDiscount = rounding.invoice_discount(
            create_invoice.invoiceDiscount
        )
    elif create_invoice.discountType == "amount":
        amt = max(0, min(items_net_total, create_invoice.discountValue))
        amt = rounding.invoice_discount(amt)
        create_invoice.discountValue = amt
        create_invoice.invoiceDiscount = amt
    else:
        create_invoice.discountType = None
        create_invoice.discountValue = 0
        create_invoice.invoiceDiscount = 0

    create_invoice.total = max(0, items_net_total - create_invoice.invoiceDiscount)


async def process_invoice(
    create_invoice: CreateInvoice, *, round_up: bool = False
) -> tuple[InvoiceInDb, ClientInDb]:
    mongo_client = MongoService().client

    prd_transaction_col = ProductTransactionsCollection.get_instance()
    product_account_col = ProductAccountsCollection.get_instance()
    invoice_col = InvoicesCollection.get_instance()
    order_col = OrdersCollection.get_instance()
    client_col = ClientsCollection.get_instance()
    client_tx_col = ClientTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            new_invoice_id = UuidTool.generate_uuid()
            current_time = TimeTools.get_now_in_milliseconds()

            if len(create_invoice.docNumber) == 0:
                create_invoice.docNumber = await CounterManager().next_invoice_number(
                    session=session
                )

            is_order_fulfillment = bool(
                create_invoice.orderNumber and create_invoice.status == "open"
            )

            await _prepare_and_execute_invoice_inventory(
                create_invoice=create_invoice,
                invoice_id=new_invoice_id,
                session=session,
                product_account_col=product_account_col,
                prd_transaction_col=prd_transaction_col,
                is_order_fulfillment=is_order_fulfillment,
            )

            normalize_invoice_discounts(create_invoice, round_up=round_up)

            if create_invoice.status == "draft":
                create_invoice.status = "open"

            new_invoice_data = create_invoice.model_dump()
            new_invoice_data.update(
                {
                    "id": new_invoice_id,
                    "createdAt": current_time,
                    "status": "paid"
                    if create_invoice.paymentType != "credit"
                    else "open",
                    "amountPaid": create_invoice.total
                    if create_invoice.paymentType != "credit"
                    else 0,
                    "paidAt": current_time
                    if create_invoice.paymentType != "credit"
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
            client_account = await ClientFinanceEngine.process_movement(
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
            if new_invoice_in_db.paymentType != "credit":
                client_account = await ClientFinanceEngine.process_movement(
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
    create_invoice: CreateInvoice, *, round_up: bool = False
) -> tuple[InvoiceInDb, list[ProductAccountInDb]]:
    """
    Procesa una factura anónima (venta de mostrador) utilizando el motor de inventario unificado.
    """
    mongo_client = MongoService().client

    prd_transaction_col = ProductTransactionsCollection.get_instance()
    product_account_col = ProductAccountsCollection.get_instance()
    invoice_col = InvoicesCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            new_invoice_doc_id = UuidTool.generate_uuid()
            current_time = TimeTools.get_now_in_milliseconds()
            if len(create_invoice.docNumber) == 0:
                create_invoice.docNumber = await CounterManager().next_invoice_number(
                    session=session
                )

            accounts_dict = await _prepare_and_execute_invoice_inventory(
                create_invoice=create_invoice,
                invoice_id=new_invoice_doc_id,
                session=session,
                product_account_col=product_account_col,
                prd_transaction_col=prd_transaction_col,
                is_order_fulfillment=False,
            )

            normalize_invoice_discounts(create_invoice, round_up=round_up)

            # 6. GUARDAR LA FACTURA
            new_invoice_data = create_invoice.model_dump()
            new_invoice_data.update(
                {
                    "id": new_invoice_doc_id,
                    "createdAt": current_time,
                    "paidAt": current_time,  # Al ser anónima/contado, se paga al instante
                    "amountPaid": create_invoice.total,
                    # Guardamos los items ya con su campo 'cost' actualizado
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
            updated_accounts = list(accounts_dict.values())

            return new_invoice_in_db, updated_accounts
