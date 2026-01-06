from repos.v1.adjust_entries import AdjustEntryInDb, CreateAdjustEntry
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb

from tools import UuidTool, TimeTools, BranchesTool

from services import MongoService
from services.mongo_collections.v1 import (
    AdjustEntriesCollection,  # <--- Nueva Colección
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


async def process_adjust_entry(
    adjust_entry: CreateAdjustEntry,
) -> tuple[AdjustEntryInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    # Colecciones
    adjust_col = AdjustEntriesCollection()  # Asumo que esta clase existe
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()

    adjust_items = adjust_entry.items

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # 1. Validar Branch
            # Es vital saber si es comercio para crear stats
            current_branch_in_db = BranchesTool().get_branch_by_id(
                adjust_entry.branchId
            )

            if current_branch_in_db is None:
                raise Exception(
                    f"Branch {adjust_entry.branchId} not found processing Adjust Entry"
                )

            # 2. Crear Documento de Ajuste
            new_adjust_data = adjust_entry.model_dump()
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            new_adjust_data["id"] = UuidTool.generate_uuid()
            new_adjust_data["createdAt"] = now_in_milliseconds

            # Insertar en BD
            await adjust_col.create_adjust_entry_with_session(
                new_adjust_data,
                session=session,
            )

            new_adjust_in_db = AdjustEntryInDb.model_validate(new_adjust_data)

            # 3. Listas para Bulk Operations
            updated_product_accounts: list[ProductAccountInDb] = []
            created_transactions: list[ProductTransactionInDb] = []

            for item in adjust_items:
                # A. Actualizar Stock
                # NOTA: Usamos 'update_product_account_balance_data' (con WAC).
                # Un ajuste de entrada positivo (encontré mercancía) AUMENTA el valor del inventario.
                # Si el usuario puso costo 0, el promedio bajará. Si puso costo real, se ajustará.
                result = await product_account_col.update_product_account_balance_data(
                    product_id=item.productId,
                    branch_id=adjust_entry.branchId,
                    add_to_current_stock=item.quantity,  # Cantidad positiva
                    last_cost=item.cost,
                    session=session,
                )

                updated_account = ProductAccountInDb.model_validate(result)
                updated_product_accounts.append(updated_account)

                # D. Crear Transacción (Kardex)
                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_adjust_in_db.id,
                    docNumber=new_adjust_in_db.docNumber,
                    type="entry",  # Sigue siendo una Entrada de inventario
                    subtype="adjustment",  # <--- DIFERENCIADOR CLAVE
                    productId=item.productId,
                    branchId=adjust_entry.branchId,
                    quantity=item.quantity,
                    averageCost=updated_account.averageCost,
                    createdAt=now_in_milliseconds,
                    resultStock=updated_account.currentStock,
                )
                created_transactions.append(new_transaction)

            # 4. EJECUTAR BULK INSERTS

            # Transacciones
            if created_transactions:
                created_transactions_data = [
                    t.model_dump() for t in created_transactions
                ]
                await prd_transaction_col.create_many_product_transactions_with_session(
                    created_transactions_data,
                    session=session,
                )

            return new_adjust_in_db, updated_product_accounts
