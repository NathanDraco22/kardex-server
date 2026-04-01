from typing import Any
from pydantic import BaseModel
from repos.v1.product_accounts import ProductAccountInDb

from services.mongo_collections.v1 import (
    ProductAccountsCollection,
)


class InsufficientBalanceError(Exception):
    pass


class InventoryExitBatchItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int  # Siempre positivo
    # No necesitamos cost de entrada, porque el costo lo dicta el sistema (AverageCost)


class ExitBatchResult(BaseModel):
    # La lista de pares (id, qty) que espera tu función bulk_substract
    stock_subtractions: list[tuple[str, int]]

    # Lista de costos asignados en el mismo orden de los items de entrada
    # (Útil para que el orquestador actualice el documento original con el costo real de salida)
    assigned_costs: list[int]


def prepare_inventory_exit_batch(
    branch_id: str,
    items: list[InventoryExitBatchItem],
    existing_accounts_dict: dict[str, ProductAccountInDb],
    document_id: str,
    doc_number: str,
    is_order_fulfillment: bool = False,
) -> ExitBatchResult:
    # 1. Consolidar y Crear Mapa de Nombres
    consolidated_req: dict[str, int] = {}
    id_name_map: dict[str, str] = {}  # <--- Mapa para errores

    for item in items:
        consolidated_req[item.product_id] = (
            consolidated_req.get(item.product_id, 0) + item.quantity
        )
        # Guardamos el nombre para usarlo si hay error
        if item.product_id not in id_name_map:
            id_name_map[item.product_id] = item.product_name

    # 2. Validaciones
    pair_op: list[tuple[str, int]] = []

    for p_id, total_qty_needed in consolidated_req.items():
        # Obtenemos el nombre amigable
        p_name = id_name_map.get(p_id, "Producto Desconocido")

        if p_id not in existing_accounts_dict:
            raise InsufficientBalanceError(
                f"El producto '{p_name}' no tiene cuenta en esta sucursal."
            )

        account = existing_accounts_dict[p_id]

        # Lógica del Interruptor (Pedido vs Venta)
        promise_stock = account.promiseStock if account.promiseStock else 0
        limit_stock = account.currentStock

        if not is_order_fulfillment:
            limit_stock = account.currentStock - promise_stock

        if total_qty_needed > limit_stock:
            stock_type_msg = "FÍSICO" if is_order_fulfillment else "DISPONIBLE"
            raise InsufficientBalanceError(
                f"Stock {stock_type_msg} insuficiente para '{p_name}'. "
                f"Requerido: {total_qty_needed}, "
                f"Disponible: {limit_stock}"
            )

        pair_op.append((p_id, total_qty_needed))

    # 3. Generar Transacciones (Igual que antes...)
    assigned_costs: list[int] = []

    for item in items:
        current_account = existing_accounts_dict[item.product_id]
        cost_at_exit = current_account.averageCost
        assigned_costs.append(cost_at_exit)
        new_stock_level = current_account.currentStock - item.quantity
        current_account.currentStock = new_stock_level

    return ExitBatchResult(
        stock_subtractions=pair_op,
        assigned_costs=assigned_costs,
    )


async def execute_inventory_exit_db_operations(
    branch_id: str,
    batch_result: ExitBatchResult,
    session: Any,
    # Inyección de dependencias
    account_col: ProductAccountsCollection,
) -> None:
    """
    Ejecuta la resta de inventario.
    """

    # 1. Restar Stock (Bulk)
    # Usa tu función existente que tiene la protección $gte
    if batch_result.stock_subtractions:
        await account_col.bulk_substract_product_account_data(
            branch_id=branch_id,
            bulk_to_substrack=batch_result.stock_subtractions,
            session=session,
        )
