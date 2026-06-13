from typing import Tuple, List

from kardex.repos.v1.devolutions import DevolutionInDb, DevolutionStatus
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import ProductTransactionInDb
from kardex.services.mongo_collections.v1 import (
    DevolutionsCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.tools import UuidTool, TimeTools
from kardex.services import MongoService


async def process_devolution(
    devolution: DevolutionInDb,
) -> DevolutionInDb:
    """
    Procesa una devolución de forma atómica.
    1. Suma los productos de vuelta al inventario, recalculando el costo promedio.
    2. Resta (acredita) el monto del saldo de la cuenta del cliente.
    3. Guarda el documento de la devolución.
    4. Crea las transacciones de producto y de cliente para el Kardex.
    """
    mongo_client = MongoService().client
    devolution_col = DevolutionsCollection.get_instance()
    prd_account_col = ProductAccountsCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            created_product_transactions: List[ProductTransactionInDb] = []

            for item in devolution.returnedItems:
                quantity_to_add = abs(item.quantity)

                updated_account_data = (
                    await prd_account_col.update_product_account_balance_data(
                        product_id=item.product.id,
                        branch_id=devolution.branchId,
                        add_to_current_stock=quantity_to_add,
                        last_cost=item.cost,
                        session=session,
                    )
                )
                updated_product_account = ProductAccountInDb.model_validate(
                    updated_account_data
                )

                new_prod_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=devolution.id,
                    docNumber=devolution.docNumber,
                    type="entry",
                    subtype="devolution",
                    productId=item.product.id,
                    branchId=devolution.branchId,
                    quantity=quantity_to_add,
                    averageCost=updated_product_account.averageCost,
                    resultStock=updated_product_account.currentStock,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                )
                created_product_transactions.append(new_prod_transaction)

            product_transactions_data = [
                t.model_dump() for t in created_product_transactions
            ]
            await prd_transaction_col.create_many_product_transactions_with_session(
                product_transactions_data, session=session
            )

            new_status: DevolutionStatus = "confirmed"
            confirmed_devolution_data = (
                await devolution_col.update_devolution_status_by_id(
                    devolution_id=devolution.id,
                    status=new_status,
                    session=session,
                )
            )

            confirmed_devolution = DevolutionInDb.model_validate(
                confirmed_devolution_data
            )

            return confirmed_devolution


async def process_anon_devolution(
    devolution: DevolutionInDb,
) -> Tuple[DevolutionInDb, List[ProductAccountInDb]]:
    """
    Confirma una devolución anónima (sin cliente) de forma atómica.
    1. Suma los productos de vuelta al inventario.
    2. Guarda las transacciones de producto para el Kardex.
    3. Actualiza el estado de la devolución a "confirmed".
    """
    mongo_client = MongoService().client
    devolution_col = DevolutionsCollection.get_instance()
    prd_account_col = ProductAccountsCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            created_product_transactions: List[ProductTransactionInDb] = []
            updated_product_accounts: List[ProductAccountInDb] = []

            for item in devolution.returnedItems:
                quantity_to_add = abs(item.quantity)

                updated_account_data = (
                    await prd_account_col.update_product_account_balance_data(
                        product_id=item.product.id,
                        branch_id=devolution.branchId,
                        add_to_current_stock=quantity_to_add,
                        last_cost=item.cost,
                        session=session,
                    )
                )
                updated_product_account = ProductAccountInDb.model_validate(
                    updated_account_data
                )
                updated_product_accounts.append(updated_product_account)

                new_prod_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=devolution.id,
                    docNumber=devolution.docNumber,
                    type="entry",
                    subtype="devolution",
                    productId=item.product.id,
                    branchId=devolution.branchId,
                    quantity=quantity_to_add,
                    averageCost=updated_product_account.averageCost,
                    resultStock=updated_product_account.currentStock,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                )
                created_product_transactions.append(new_prod_transaction)

            product_transactions_data = [
                t.model_dump() for t in created_product_transactions
            ]
            await prd_transaction_col.create_many_product_transactions_with_session(
                product_transactions_data, session=session
            )

            confirmed_devolution_data = (
                await devolution_col.update_devolution_status_by_id(
                    devolution_id=devolution.id,
                    status="confirmed",
                    session=session,
                )
            )
            confirmed_devolution = DevolutionInDb.model_validate(
                confirmed_devolution_data
            )

            return confirmed_devolution, updated_product_accounts
