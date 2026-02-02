from tools import BranchesTool
from core.inventory import (
    execute_inventory_entry_db_operations,
    InventoryEntryBatchItem,
    prepare_inventory_entry_batch,
)

from repos.v1.transfers import TransferInDb, ReceiveTransferIntent
from repos.v1.product_accounts import ProductAccountInDb

from services import MongoService
from services.mongo_collections.v1 import (
    TransfersCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
)


class TransferNotFoundError(Exception):
    pass


class TransferAlreadyProcessedError(Exception):
    pass


async def process_incoming_transfer(
    transfer_id: str,
    intent: ReceiveTransferIntent,
) -> tuple[TransferInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    # Colecciones
    transfers_col = TransfersCollection()
    product_account_col = ProductAccountsCollection()
    product_stats_col = ProductStatsCollection()
    product_prof_col = ProductSaleProfilesCollection()
    prd_transaction_col = ProductTransactionsCollection()

    # Tools
    branches_tool = BranchesTool()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # 1. OBTENER Y VALIDAR TRASLADO
            existing_transfer_dict = (
                await transfers_col.fetch_transfer_by_id_with_session(
                    transfer_id, session=session
                )
            )

            if not existing_transfer_dict:
                raise TransferNotFoundError(f"Traslado {transfer_id} no encontrado")

            transfer_doc = TransferInDb.model_validate(existing_transfer_dict)

            if transfer_doc.status != "inTransit":
                raise TransferAlreadyProcessedError(
                    "Este traslado ya fue procesado anteriormente"
                )

            # Validar Sucursal Destino
            destination_branch_in_db = branches_tool.get_branch_by_id(
                transfer_doc.destination
            )
            if destination_branch_in_db is None:
                raise Exception("Sucursal de Destino no encontrada")

            destination_branch = transfer_doc.destination

            # 2. PREPARAR DATOS DE ENTRADA (Mapeo a tu nuevo modelo InventoryEntryBatchItem)
            # Convertimos los items del traslado al formato genérico que espera tu función lógica
            batch_items = [
                InventoryEntryBatchItem(
                    product_id=item.id, quantity=item.quantity, unit_cost=item.cost
                )
                for item in transfer_doc.items
            ]

            # 3. OBTENER CUENTAS ACTUALES (Snapshot Read)
            # Solo buscamos las cuentas de los productos involucrados
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=destination_branch,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            # 4. EJECUTAR LÓGICA PURA (Tu función prepare_inventory_entry_batch)
            # Aquí obtenemos el objeto EntryBatchResult fuertemente tipado
            batch_result = prepare_inventory_entry_batch(
                branch_id=destination_branch,
                is_commerce_branch=destination_branch_in_db.isCommerce,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                document_id=transfer_doc.id,
                doc_number=transfer_doc.docNumber,
                tx_type="entry",  # Usando literal o Enum TransactionType.ENTRY
                tx_subtype="transfer",  # Usando literal o Enum TransactionSubType.TRANSFER
            )

            # 5. PERSISTENCIA EN BD (Usando la función que te di arriba)
            await execute_inventory_entry_db_operations(
                branch_id=destination_branch,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                profile_col=product_prof_col,
                stats_col=product_stats_col,
                transaction_col=prd_transaction_col,
            )

            # 6. ACTUALIZAR ESTADO DEL TRASLADO
            update_data = intent.model_dump()
            updated_transfer_dict = (
                await transfers_col.update_transfer_status_with_session(
                    transfer_id=transfer_id, update_data=update_data, session=session
                )
            )
            updated_transfer_in_db = TransferInDb.model_validate(updated_transfer_dict)

            # Retornamos el traslado actualizado y las cuentas simuladas que generó tu lógica
            return updated_transfer_in_db, batch_result.simulated_accounts
