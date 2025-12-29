from tools import UuidTool, TimeTools
from repos.v1.transfers import TransferInDb, CreateTransfer
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb

from services import MongoService
from services.mongo_collections.v1 import (
    TransfersCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


class InsufficientBalanceError(Exception):
    pass


async def process_outgoing_transfer(
    create_transfer: CreateTransfer,
) -> tuple[TransferInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    # Colecciones
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()
    transfers_col = TransfersCollection()

    transfer_items = create_transfer.items

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_transfer_id = UuidTool.generate_uuid()
            current_time = TimeTools.get_now_in_milliseconds()

            updated_origin_accounts: list[ProductAccountInDb] = []
            created_transactions: list[ProductTransactionInDb] = []

            # 1. PROCESAR ITEMS (Descontar de Origen y crear transacciones)
            for item in transfer_items:
                # A. Restar Stock del Origen
                # Nota: Pasamos quantity positivo, la función se encarga de restar
                result = await product_account_col.substract_product_account_data(
                    product_id=item.id,
                    branch_id=create_transfer.origin,
                    substract_to_current_stock=item.quantity,
                    session=session,
                )

                if result is None:
                    raise InsufficientBalanceError(
                        f"Stock insuficiente para el producto: {item.name}"
                    )

                updated_account = ProductAccountInDb.model_validate(result)

                # B. Actualizar el costo del ítem en el documento de traslado
                # Regla: Se mantiene en int (centavos)
                item.cost = updated_account.averageCost

                updated_origin_accounts.append(updated_account)

                # C. Crear registro de Transacción (Kardex)
                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_transfer_id,
                    docNumber=create_transfer.docNumber,
                    type="exit",
                    subtype="transfer",  # Específico para salida de traslado
                    productId=item.id,
                    branchId=create_transfer.origin,
                    # REGLA: Salida de inventario = Cantidad Negativa
                    quantity=-abs(item.quantity),
                    averageCost=updated_account.averageCost,
                    createdAt=current_time,
                    resultStock=updated_account.currentStock,
                )
                created_transactions.append(new_transaction)

            # 2. PREPARAR DOCUMENTO DE TRASLADO
            new_transfer_data = create_transfer.model_dump()

            # Sobrescribimos/Agregamos campos de sistema
            new_transfer_data.update(
                {
                    "id": new_transfer_id,
                    "createdAt": current_time,
                    "status": "inTransit",  # Estado inicial obligatorio
                    # Guardamos los items con el costo actualizado
                    "items": [item.model_dump() for item in transfer_items],
                }
            )

            new_transfer_in_db = TransferInDb.model_validate(new_transfer_data)

            # 3. INSERTAR EL TRASLADO EN BD
            # Asumo que tienes este método en TransfersCollection similar a ExitDocsCollection
            await transfers_col.create_transfer_with_session(
                new_transfer_in_db.model_dump(),
                session=session,
            )

            # 4. INSERTAR LAS TRANSACCIONES EN LOTE
            created_transactions_data = [t.model_dump() for t in created_transactions]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            # 5. RETORNAR RESULTADOS

            return new_transfer_in_db, updated_origin_accounts
