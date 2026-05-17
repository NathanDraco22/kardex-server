from kardex.tools import UuidTool, TimeTools, BranchesTool
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryExitBatchItem,
    InventoryEngine,
)

from kardex.repos.v1.adjust_exits import AdjustExitInDb, CreateAdjustExit
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import TransactionSubType

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    AdjustExitsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)
from kardex.core.counter_manager.counter_manager import CounterManager


async def process_adjust_exit(
    adjust_exit: CreateAdjustExit,
) -> tuple[AdjustExitInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    # Colecciones
    adjust_col = AdjustExitsCollection()
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()

    # Tools
    branches_tool = BranchesTool()

    # Determinar el Subtipo de Transacción
    # Mapeamos el string del input al Enum del sistema
    tx_subtype: TransactionSubType = "adjustment"
    if adjust_exit.type == "devolution":
        tx_subtype = "devolution"
    elif adjust_exit.type == "loss":
        tx_subtype = "loss"

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_adjust_id = UuidTool.generate_uuid()
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            if not adjust_exit.docNumber:
                adjust_exit.docNumber = await CounterManager().next_adjust_number(
                    session
                )

            # 1. VALIDAR BRANCH
            current_branch_in_db = branches_tool.get_branch_by_id(adjust_exit.branchId)
            if current_branch_in_db is None:
                raise Exception(
                    f"Branch {adjust_exit.branchId} not found processing Adjust Exit"
                )

            # 2. PREPARAR DATOS (Mapeo a InventoryExitBatchItem)
            batch_items = [
                InventoryExitBatchItem(
                    product_id=item.productId,  # Ojo: En AdjustExit suele ser 'productId'
                    quantity=item.quantity,
                    product_name=item.productName,
                )
                for item in adjust_exit.items
            ]

            # 3. OBTENER CUENTAS ACTUALES (Snapshot Read)
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=adjust_exit.branchId,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            # 4. EJECUTAR LÓGICA PURA REUTILIZABLE 🧠
            # Valida stock insuficiente y calcula costos de salida
            batch_result = InventoryBatchTransformer.prepare_exit(
                branch_id=adjust_exit.branchId,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                # Metadata
                document_id=new_adjust_id,
                doc_number=adjust_exit.docNumber,
                # Tipos
                tx_type="exit",
                tx_subtype=tx_subtype,  # "adjustment", "loss", "devolution"
            )

            # 5. ACTUALIZAR COSTOS EN EL DOCUMENTO ORIGINAL
            # Asignamos el Costo Promedio al momento de la salida a cada item
            for i, item in enumerate(adjust_exit.items):
                item.cost = batch_result.assigned_costs[i]

            # 6. PERSISTENCIA MASIVA 💾
            await InventoryEngine.execute_exit(
                branch_id=adjust_exit.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                transaction_col=prd_transaction_col,
            )

            # 7. CREAR DOCUMENTO DE AJUSTE
            new_adjust_data = adjust_exit.model_dump()
            new_adjust_data.update(
                {
                    "id": new_adjust_id,
                    "createdAt": now_in_milliseconds,
                    # Guardamos items con el costo actualizado
                    "items": [item.model_dump() for item in adjust_exit.items],
                }
            )

            await adjust_col.create_adjust_exit_with_session(
                new_adjust_data,
                session=session,
            )

            new_adjust_in_db = AdjustExitInDb.model_validate(new_adjust_data)

            # Para retornar las cuentas simuladas (estado final tras la resta)
            # Reconstruimos las cuentas basadas en el resultado en memoria
            updated_accounts_simulated = []
            for item in batch_items:
                if item.product_id in accounts_dict:
                    # accounts_dict ya fue modificado en memoria por prepare_inventory_exit_batch
                    updated_accounts_simulated.append(accounts_dict[item.product_id])

            return new_adjust_in_db, updated_accounts_simulated
