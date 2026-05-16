from kardex.tools import BranchesTool
from kardex.core.inventory import (
    execute_inventory_entry_db_operations,
    InventoryEntryBatchItem,
    prepare_inventory_entry_batch,
)
from kardex.repos.v1.transfers import TransferInDb, CancelTransferIntent
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    TransfersCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
)


class TransferNotFoundError(Exception):
    pass


class TransferInvalidStatusError(Exception):
    pass


async def process_cancel_transfer(
    transfer_id: str,
    intent: CancelTransferIntent,
) -> TransferInDb:
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

            # 2. VALIDAR ESTADO (Solo 'inTransit' se puede cancelar)
            if transfer_doc.status != "inTransit":
                raise TransferInvalidStatusError(
                    f"No se puede cancelar un traslado con estado: {transfer_doc.status}"
                )

            # 3. OBTENER DATOS DE LA SUCURSAL DE ORIGEN (A donde vuelve la mercadería)
            origin_branch_id = transfer_doc.origin

            origin_branch_in_db = branches_tool.get_branch_by_id(origin_branch_id)
            if origin_branch_in_db is None:
                raise Exception("Sucursal de Origen no encontrada para retorno")

            # 4. PREPARAR ITEMS PARA EL RETORNO
            # Mapeamos los items del traslado a InventoryEntryBatchItem
            # Nota: Usamos el costo original con el que salieron para que el reingreso sea contablemente neutro
            batch_items = [
                InventoryEntryBatchItem(
                    product_id=item.id, quantity=item.quantity, unit_cost=item.cost
                )
                for item in transfer_doc.items
            ]

            # 5. OBTENER CUENTAS ACTUALES EN ORIGEN (Snapshot Read)
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=origin_branch_id,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            # 6. EJECUTAR LÓGICA PURA REUTILIZABLE 🧠
            # Usamos la misma lógica que una entrada normal, porque el stock está entrando de vuelta.
            batch_result = prepare_inventory_entry_batch(
                branch_id=origin_branch_id,
                is_commerce_branch=origin_branch_in_db.isCommerce,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                # Metadata
                document_id=transfer_doc.id,
                doc_number=transfer_doc.docNumber,
                # Definimos el tipo de movimiento en el Kardex
                tx_type="entry",  # Es una entrada (retorno)
                tx_subtype="transfer",  # O podrías crear TransactionSubType.CANCEL_RETURN
            )

            # 7. PERSISTENCIA MASIVA 💾
            await execute_inventory_entry_db_operations(
                branch_id=origin_branch_id,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                profile_col=product_prof_col,
                stats_col=product_stats_col,
                transaction_col=prd_transaction_col,
            )

            # 8. ACTUALIZAR ESTADO DEL TRASLADO A "CANCELLED"
            update_data = intent.model_dump()

            updated_transfer_dict = (
                await transfers_col.update_transfer_status_with_session(
                    transfer_id=transfer_id, update_data=update_data, session=session
                )
            )

            updated_transfer_in_db = TransferInDb.model_validate(updated_transfer_dict)

            return updated_transfer_in_db
