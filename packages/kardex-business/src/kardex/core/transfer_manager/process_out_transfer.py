from kardex.tools import UuidTool, TimeTools
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryExitBatchItem,
    InventoryEngine,
)

from kardex.repos.v1.transfers import TransferInDb, CreateTransfer
from kardex.repos.v1.product_accounts import ProductAccountInDb

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    TransfersCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)

from kardex.core.counter_manager.counter_manager import CounterManager


async def process_outgoing_transfer(
    create_transfer: CreateTransfer,
) -> TransferInDb:
    mongo_client = MongoService().client

    # Colecciones
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()
    transfers_col = TransfersCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_transfer_id = UuidTool.generate_uuid()
            current_time = TimeTools.get_now_in_milliseconds()

            if not create_transfer.docNumber:
                create_transfer.docNumber = await CounterManager().next_tranfer_number(
                    session
                )

            # 1. PREPARAR DATOS (Mapeo a InventoryExitBatchItem)
            # Convertimos los items del traslado al formato genérico de salida
            batch_items = [
                InventoryExitBatchItem(
                    product_id=item.id,
                    quantity=item.quantity,
                    product_name=item.name,
                )
                for item in create_transfer.items
            ]

            # 2. OBTENER CUENTAS ACTUALES (Snapshot Read)
            # Obtenemos las cuentas para verificar stock y costo promedio
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=create_transfer.origin,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            # 3. EJECUTAR LÓGICA PURA REUTILIZABLE 🧠
            # Esta función valida stock (lanza InsufficientBalanceError si falla),
            # calcula saldos y prepara las transacciones.
            batch_result = InventoryBatchTransformer.prepare_exit(
                branch_id=create_transfer.origin,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                # Metadata
                document_id=new_transfer_id,
                doc_number=create_transfer.docNumber,
                tx_type="exit",
                tx_subtype="transfer",
            )

            # 4. ACTUALIZAR COSTOS EN EL OBJETO DE TRASLADO
            # La lógica nos devolvió 'assigned_costs' (los costos promedio al momento de la salida).
            # Debemos actualizar los items del traslado con este valor real antes de guardarlo.
            for i, item in enumerate(create_transfer.items):
                # batch_result.assigned_costs tiene el mismo orden que items
                item.cost = batch_result.assigned_costs[i]

            # 5. PERSISTENCIA MASIVA EN BD (Stock y Kardex) 💾
            await InventoryEngine.execute_exit(
                branch_id=create_transfer.origin,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                transaction_col=prd_transaction_col,
            )

            # 6. CREAR DOCUMENTO DE TRASLADO
            new_transfer_data = create_transfer.model_dump()
            new_transfer_data.update(
                {
                    "id": new_transfer_id,
                    "createdAt": current_time,
                    "status": "inTransit",
                    # Guardamos items con el costo actualizado en el paso 4
                    "items": [item.model_dump() for item in create_transfer.items],
                }
            )

            new_transfer_in_db = TransferInDb.model_validate(new_transfer_data)

            await transfers_col.create_transfer_with_session(
                new_transfer_in_db.model_dump(),
                session=session,
            )

            return new_transfer_in_db
