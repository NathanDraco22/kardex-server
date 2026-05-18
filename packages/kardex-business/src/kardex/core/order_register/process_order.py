from typing import Tuple, List
from kardex.services.mongo_collections.v1 import (
    OrdersCollection,
    ProductAccountsCollection,
)
from kardex.repos.v1.orders import CreateOrder, OrderInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.tools import UuidTool, TimeTools, InsufficientBalanceError
from kardex.services import MongoService


async def process_order(
    create_order: CreateOrder,
) -> Tuple[OrderInDb, List[ProductAccountInDb]]:
    mongo_client = MongoService().client
    prd_account_col = ProductAccountsCollection()
    order_col = OrdersCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # ==========================================
            # 1. PREPARACIÓN DE DATOS
            # ==========================================
            # Agrupamos por ID para saber la cantidad total a reservar por producto
            consolidated_reservation: dict[str, int] = {}
            # Mapa para obtener nombres rápido en caso de error
            id_name_map: dict[str, str] = {}

            for item in create_order.saleItems:
                qty_to_reserve = abs(item.quantity + item.bonQuantity)
                consolidated_reservation[item.product.id] = (
                    consolidated_reservation.get(item.product.id, 0) + qty_to_reserve
                )
                id_name_map[item.product.id] = item.product.name

            # ==========================================
            # 2. OBTENER CUENTAS (SNAPSHOT READ)
            # ==========================================
            product_ids = list(consolidated_reservation.keys())
            accounts_data = await prd_account_col.get_accounts_by_branch_id(
                branch_id=create_order.branchId,
                product_ids=product_ids,
                session=session,
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in accounts_data
            }

            # ==========================================
            # 3. VALIDACIÓN EN MEMORIA Y ASIGNACIÓN DE COSTOS
            # ==========================================
            bulk_reserve_data: list[tuple[str, int]] = []
            updated_product_accounts: List[ProductAccountInDb] = []

            for p_id, qty_needed in consolidated_reservation.items():
                p_name = id_name_map.get(p_id, "Producto Desconocido")

                if p_id not in accounts_dict:
                    raise InsufficientBalanceError(
                        f"El producto '{p_name}' no tiene cuenta en esta sucursal.",
                        product_id=p_id,
                        product_name=p_name,
                    )

                account = accounts_dict[p_id]

                # Cálculo de Stock Disponible Real
                current = account.currentStock
                promised = account.promiseStock if account.promiseStock else 0
                available = current - promised

                # Validación: ¿Hay suficiente "espacio libre" para reservar?
                if qty_needed > available:
                    raise InsufficientBalanceError(
                        f"Stock insuficiente para reservar '{p_name}'. "
                        f"Requerido: {qty_needed}, "
                        f"Físico: {current}, "
                        f"Comprometido: {promised}, "
                        f"Disponible: {available}",
                        product_id=p_id,
                        product_name=p_name,
                    )

                # Preparamos datos para el Bulk Write
                bulk_reserve_data.append((p_id, qty_needed))

                # Simulamos la actualización en memoria para el retorno
                # (Incrementamos el promiseStock)
                account.promiseStock = promised + qty_needed
                updated_product_accounts.append(account)

            # ASIGNAR COSTOS A LOS ITEMS DEL PEDIDO
            # Es importante guardar el costo promedio al momento de crear el pedido
            for item in create_order.saleItems:
                if item.product.id in accounts_dict:
                    item.cost = accounts_dict[item.product.id].averageCost

            # ==========================================
            # 4. RESERVA MASIVA (PERSISTENCIA)
            # ==========================================
            # Usamos la función optimizada que creamos en el paso anterior
            await prd_account_col.bulk_add_to_promise_stock(
                branch_id=create_order.branchId,
                bulk_data=bulk_reserve_data,
                session=session,
            )

            # ==========================================
            # 5. GUARDAR PEDIDO
            # ==========================================
            new_order_data = create_order.model_dump()
            new_order_data.update(
                {
                    "id": UuidTool.generate_uuid(),
                    "createdAt": TimeTools.get_now_in_milliseconds(),
                    # Guardamos los items con el costo actualizado
                    "saleItems": [item.model_dump() for item in create_order.saleItems],
                }
            )

            insert_result = await order_col.create_order_with_session(
                new_order_data,
                session=session,
            )
            new_order_in_db = OrderInDb.model_validate(insert_result)

            return new_order_in_db, updated_product_accounts
