from typing import Any
from pydantic import BaseModel
from repos.v1.product_transactions import (
    ProductTransactionInDb,
    TransactionType,
    TransactionSubType,
)
from repos.v1.product_accounts import ProductAccountInDb
from tools import UuidTool, TimeTools


from services.mongo_collections.v1 import (
    ProductAccountsCollection,
    ProductTransactionsCollection,
)


class InsufficientBalanceError(Exception):
    pass


class InventoryExitBatchItem(BaseModel):
    product_id: str
    quantity: int  # Siempre positivo
    # No necesitamos cost de entrada, porque el costo lo dicta el sistema (AverageCost)


class ExitBatchResult(BaseModel):
    # La lista de pares (id, qty) que espera tu función bulk_substract
    stock_subtractions: list[tuple[str, int]]

    # Las transacciones generadas (una por cada item de salida)
    transactions: list[ProductTransactionInDb]

    # Lista de costos asignados en el mismo orden de los items de entrada
    # (Útil para que el orquestador actualice el documento original con el costo real de salida)
    assigned_costs: list[int]


def prepare_inventory_exit_batch(
    branch_id: str,
    items: list[InventoryExitBatchItem],
    existing_accounts_dict: dict[str, ProductAccountInDb],
    # Metadata para el Kardex
    document_id: str,
    doc_number: str,
    tx_type: TransactionType,  # ej: TransactionType.EXIT
    tx_subtype: TransactionSubType,  # ej: TransactionSubType.TRANSFER
) -> ExitBatchResult:
    now = TimeTools.get_now_in_milliseconds()

    # 1. Consolidar para validar Stock Total (Fail Fast)
    consolidated_req: dict[str, int] = {}
    for item in items:
        consolidated_req[item.product_id] = (
            consolidated_req.get(item.product_id, 0) + item.quantity
        )

    # 2. Validaciones de Stock (Sin tocar BD, solo memoria)
    # Validamos contra lo que consolidamos para asegurar que alcanza para TODO el lote
    pair_op: list[tuple[str, int]] = []

    for p_id, total_qty_needed in consolidated_req.items():
        if p_id not in existing_accounts_dict:
            raise InsufficientBalanceError(f"Producto {p_id} no encontrado en origen")

        account = existing_accounts_dict[p_id]

        if total_qty_needed > account.currentStock:
            raise InsufficientBalanceError(
                f"Stock insuficiente para {p_id}. "
                f"Requerido: {total_qty_needed}, Disponible: {account.currentStock}"
            )

        # Preparamos la tupla para el bulk_substract
        pair_op.append((p_id, total_qty_needed))

    # 3. Generar Transacciones y Asignar Costos
    transactions: list[ProductTransactionInDb] = []
    assigned_costs: list[int] = []

    # Iteramos sobre los items ORIGINALES (no los consolidados) para mantener el detalle del documento
    for item in items:
        current_account = existing_accounts_dict[item.product_id]

        # El costo de salida es el Costo Promedio actual
        cost_at_exit = current_account.averageCost
        assigned_costs.append(cost_at_exit)

        # Calculamos el stock resultante simulado
        # (Restamos en memoria para que si el item se repite, el resultStock baje progresivamente)
        new_stock_level = current_account.currentStock - item.quantity

        new_tx = ProductTransactionInDb(
            id=UuidTool.generate_uuid(),
            documentId=document_id,
            docNumber=doc_number,
            type=tx_type,
            subtype=tx_subtype,
            productId=item.product_id,
            branchId=branch_id,
            quantity=-abs(item.quantity),  # Negativo para salida
            averageCost=cost_at_exit,
            createdAt=now,
            resultStock=new_stock_level,
        )
        transactions.append(new_tx)

        # Actualizamos la referencia en memoria para la siguiente iteración del bucle
        current_account.currentStock = new_stock_level

    return ExitBatchResult(
        stock_subtractions=pair_op,
        transactions=transactions,
        assigned_costs=assigned_costs,
    )


async def execute_inventory_exit_db_operations(
    branch_id: str,
    batch_result: ExitBatchResult,
    session: Any,
    # Inyección de dependencias
    account_col: ProductAccountsCollection,
    transaction_col: ProductTransactionsCollection,
) -> None:
    """
    Ejecuta la resta de inventario y creación de historial de salida.
    """

    # 1. Restar Stock (Bulk)
    # Usa tu función existente que tiene la protección $gte
    if batch_result.stock_subtractions:
        await account_col.bulk_substract_product_account_data(
            branch_id=branch_id,
            bulk_to_substrack=batch_result.stock_subtractions,
            session=session,
        )

    # 2. Insertar Transacciones (Bulk)
    if batch_result.transactions:
        raw_txs = [t.model_dump() for t in batch_result.transactions]
        await transaction_col.create_many_product_transactions_with_session(
            raw_txs, session=session
        )
