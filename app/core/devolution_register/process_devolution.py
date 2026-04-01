from typing import Tuple, List

from repos.v1.devolutions import DevolutionInDb, DevolutionStatus
from repos.v1.product_accounts import ProductAccountInDb
from services.mongo_collections.v1 import (
    DevolutionsCollection,
    ProductAccountsCollection,
)
from services import MongoService


async def process_devolution(
    devolution: DevolutionInDb,
) -> DevolutionInDb:
    """
    Procesa una devolución de forma atómica.
    1. Suma los productos de vuelta al inventario, recalculando el costo promedio.
    2. Resta (acredita) el monto del saldo de la cuenta del cliente.
    2. Resta (acredita) el monto del saldo de la cuenta del cliente.
    3. Guarda el documento de la devolución.
    """
    mongo_client = MongoService().client
    devolution_col = DevolutionsCollection()
    prd_account_col = ProductAccountsCollection()
    
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():

            for item in devolution.returnedItems:
                quantity_to_add = abs(item.quantity)

                await prd_account_col.update_product_account_balance_data(
                    product_id=item.product.id,
                    branch_id=devolution.branchId,
                    add_to_current_stock=quantity_to_add,
                    last_cost=item.cost,
                    session=session,
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
    1. Suma los productos de vuelta al inventario.
    2. Actualiza el estado de la devolución a "confirmed".
    """
    mongo_client = MongoService().client
    devolution_col = DevolutionsCollection()
    prd_account_col = ProductAccountsCollection()
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            updated_product_accounts: List[ProductAccountInDb] = []

            for item in devolution.returnedItems:
                quantity_to_add = abs(item.quantity)

                updated_account_data = await prd_account_col.update_product_account_balance_data(
                    product_id=item.product.id,
                    branch_id=devolution.branchId,
                    add_to_current_stock=quantity_to_add,
                    last_cost=item.cost,
                    session=session,
                )
                updated_product_account = ProductAccountInDb.model_validate(
                    updated_account_data
                )
                updated_product_accounts.append(updated_product_account)


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
