from kardex.tools import UuidTool, TimeTools, BranchesTool
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryEntryBatchItem,
    InventoryEngine,
)
from kardex.repos.v1.adjust_entries import AdjustEntryInDb, CreateAdjustEntry
from kardex.repos.v1.product_accounts import ProductAccountInDb

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    AdjustEntriesCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
)
from kardex.core.counter_manager.counter_manager import CounterManager


async def process_adjust_entry(
    adjust_entry: CreateAdjustEntry,
) -> AdjustEntryInDb:
    mongo_client = MongoService().client

    # Colecciones
    adjust_col = AdjustEntriesCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()
    product_account_col = ProductAccountsCollection.get_instance()
    product_stats_col = ProductStatsCollection.get_instance()
    product_prof_col = ProductSaleProfilesCollection.get_instance()

    # Tools
    branches_tool = BranchesTool()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            if not adjust_entry.docNumber:
                adjust_entry.docNumber = await CounterManager().next_adjust_number(
                    session
                )

            # 1. CREAR DOCUMENTO DE AJUSTE
            new_adjust_data = adjust_entry.model_dump()
            new_adjust_data["id"] = UuidTool.generate_uuid()
            new_adjust_data["createdAt"] = now_in_milliseconds

            # Insertar en BD
            await adjust_col.create_adjust_entry_with_session(
                new_adjust_data,
                session=session,
            )
            new_adjust_in_db = AdjustEntryInDb.model_validate(new_adjust_data)

            # 2. VALIDAR BRANCH (Para saber si crear Stats)
            current_branch_in_db = branches_tool.get_branch_by_id(adjust_entry.branchId)
            if current_branch_in_db is None:
                raise Exception(
                    f"Branch {adjust_entry.branchId} not found processing Adjust Entry"
                )

            # 3. PREPARAR DATOS (Mapeo a InventoryEntryBatchItem)
            batch_items = [
                InventoryEntryBatchItem(
                    product_id=item.productId,  # Ojo: En AdjustEntry suele ser 'productId'
                    quantity=item.quantity,
                    unit_cost=item.cost,
                )
                for item in adjust_entry.items
            ]

            # 4. OBTENER CUENTAS ACTUALES (Snapshot Read)
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=adjust_entry.branchId,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            # 5. EJECUTAR LÓGICA PURA REUTILIZABLE 🧠
            # Usa la misma lógica de entrada que Compras y Traslados
            batch_result = InventoryBatchTransformer.prepare_entry(
                branch_id=adjust_entry.branchId,
                is_commerce_branch=current_branch_in_db.isCommerce,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                # Metadata
                document_id=new_adjust_in_db.id,
                doc_number=new_adjust_in_db.docNumber,
                # Tipos
                tx_type="entry",
                tx_subtype="adjustment",  # Subtipo específico "adjustment"
            )

            # 6. PERSISTENCIA MASIVA 💾
            await InventoryEngine.execute_entry(
                branch_id=adjust_entry.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                profile_col=product_prof_col,
                stats_col=product_stats_col,
                transaction_col=prd_transaction_col,
            )

            return new_adjust_in_db
