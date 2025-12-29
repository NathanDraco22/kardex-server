from repos.v1.transfers import TransferInDb, CancelTransferIntent
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb

from tools import UuidTool, TimeTools

from services import MongoService
from services.mongo_collections.v1 import (
    TransfersCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


async def process_cancel_transfer(
    transfer_id: str,
    intent: CancelTransferIntent,
) -> tuple[TransferInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    transfers_col = TransfersCollection()
    product_account_col = ProductAccountsCollection()
    prd_transaction_col = ProductTransactionsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # 1. OBTENER EL TRASLADO EXISTENTE
            existing_transfer_dict = (
                await transfers_col.fetch_transfer_by_id_with_session(
                    transfer_id, session=session
                )
            )

            if not existing_transfer_dict:
                raise Exception(f"Traslado {transfer_id} no encontrado")

            transfer_doc = TransferInDb.model_validate(existing_transfer_dict)

            # 2. VALIDAR ESTADO (Solo se puede cancelar si está en tránsito)
            if transfer_doc.status != "inTransit":
                raise Exception(
                    f"No se puede cancelar un traslado con estado: {transfer_doc.status}"
                )

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            # NOTA CRUCIAL: En cancelación, el inventario vuelve al ORIGEN
            target_branch = transfer_doc.origin
            items_to_return = transfer_doc.items

            updated_origin_accounts: list[ProductAccountInDb] = []
            created_transactions: list[ProductTransactionInDb] = []

            # 3. DEVOLVER ITEMS AL STOCK DE ORIGEN
            for item in items_to_return:
                # A. Sumar al Stock del ORIGEN
                # Usamos update_product_account_balance_data porque es una ENTRADA de inventario
                result = await product_account_col.update_product_account_balance_data(
                    product_id=item.id,
                    branch_id=target_branch,  # Vuelve a casa
                    add_to_current_stock=item.quantity,  # Cantidad Positiva (Reingreso)
                    last_cost=item.cost,  # Mismo costo con el que salió
                    session=session,
                )

                updated_account = ProductAccountInDb.model_validate(result)
                updated_origin_accounts.append(updated_account)

                # B. Crear Transacción de REVERSA (Cancelación)
                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=transfer_doc.id,
                    docNumber=transfer_doc.docNumber,
                    # Tipo Entry: Porque estamos recuperando el stock
                    type="entry",
                    subtype="transfer",  # Subtipo específico para auditoría
                    productId=item.id,
                    branchId=target_branch,
                    # REGLA: Entrada = Positivo
                    quantity=item.quantity,
                    averageCost=updated_account.averageCost,
                    createdAt=now_in_milliseconds,
                    resultStock=updated_account.currentStock,
                )
                created_transactions.append(new_transaction)

            # 4. ACTUALIZAR EL DOCUMENTO DE TRASLADO A "CANCELLED"
            update_data = intent.model_dump()

            updated_transfer_dict = (
                await transfers_col.update_transfer_status_with_session(
                    transfer_id=transfer_id, update_data=update_data, session=session
                )
            )

            updated_transfer_in_db = TransferInDb.model_validate(updated_transfer_dict)

            # 5. INSERTAR TRANSACCIONES
            created_transactions_data = [t.model_dump() for t in created_transactions]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            return updated_transfer_in_db, updated_origin_accounts
