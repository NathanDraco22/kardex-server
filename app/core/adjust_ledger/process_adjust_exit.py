from repos.v1.adjust_exits import AdjustExitInDb, CreateAdjustExit
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb, TransactionSubType

from tools import UuidTool, TimeTools, BranchesTool

from services import MongoService
from services.mongo_collections.v1 import (
    AdjustExitsCollection,  # <--- Asumo que crearás esta colección
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


# Reutilizamos tu excepción personalizada
class InsufficientBalanceError(Exception):
    pass


async def process_adjust_exit(
    adjust_exit: CreateAdjustExit,
) -> tuple[AdjustExitInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    # Colecciones
    adjust_col = AdjustExitsCollection()
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()

    exit_items = adjust_exit.items

    transaction_sub_type: TransactionSubType = "adjustment"

    if adjust_exit.type == "devolution":
        transaction_sub_type = "devolution"
    if adjust_exit.type == "loss":
        transaction_sub_type = "loss"

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # 1. Validar Branch
            current_branch_in_db = BranchesTool().get_branch_by_id(adjust_exit.branchId)

            if current_branch_in_db is None:
                raise Exception(
                    f"Branch {adjust_exit.branchId} not found processing Adjust Exit"
                )

            new_adjust_id = UuidTool.generate_uuid()
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            updated_product_accounts: list[ProductAccountInDb] = []
            created_transactions: list[ProductTransactionInDb] = []

            # 2. Procesar Ítems (Restar Stock)
            for item in exit_items:
                # A. Restar del Stock
                # Nota: substract_product_account_data maneja la lógica de restar
                result = await product_account_col.substract_product_account_data(
                    product_id=item.productId,
                    branch_id=adjust_exit.branchId,
                    substract_to_current_stock=item.quantity,  # Se pasa positivo, el método resta
                    session=session,
                )

                if result is None:
                    # Si devuelve None es porque no alcanzó el stock
                    raise InsufficientBalanceError("Stock insuficiente para ajuste")

                updated_account = ProductAccountInDb.model_validate(result)

                # B. Snapshot del Costo
                # Es vital guardar cuánto costaba el producto cuando lo ajustamos (perdimos)
                item.cost = updated_account.averageCost

                updated_product_accounts.append(updated_account)

                # C. Crear Transacción (Kardex)
                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_adjust_id,
                    docNumber=adjust_exit.docNumber,
                    type="exit",  # Salida de inventario
                    subtype=transaction_sub_type,  # <--- Subtipo Ajuste
                    productId=item.productId,
                    branchId=adjust_exit.branchId,
                    # REGLA: Salida = Negativo
                    quantity=-abs(item.quantity),
                    averageCost=updated_account.averageCost,
                    createdAt=now_in_milliseconds,
                    resultStock=updated_account.currentStock,
                )
                created_transactions.append(new_transaction)

            # 3. Crear Documento de Ajuste
            new_adjust_data = adjust_exit.model_dump()

            new_adjust_data["id"] = new_adjust_id
            new_adjust_data["createdAt"] = now_in_milliseconds
            # Actualizamos items con el costo capturado
            new_adjust_data["items"] = [item.model_dump() for item in exit_items]

            # Insertar en BD
            await adjust_col.create_adjust_exit_with_session(
                new_adjust_data,
                session=session,
            )

            new_adjust_in_db = AdjustExitInDb.model_validate(new_adjust_data)

            # 4. Insertar Transacciones (Bulk)
            if created_transactions:
                created_transactions_data = [
                    t.model_dump() for t in created_transactions
                ]
                await prd_transaction_col.create_many_product_transactions_with_session(
                    created_transactions_data,
                    session=session,
                )

            return new_adjust_in_db, updated_product_accounts
