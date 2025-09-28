from typing import List, Tuple
from services.mongo_collections.v1 import (
    SalesCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)
from repos.v1.sales import CreateSale, SaleInDb
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb
from tools import UuidTool, TimeTools
from services import MongoService


class InsufficientBalanceError(Exception):
    pass


async def process_sale(
    create_sale: CreateSale,
) -> Tuple[SaleInDb, List[ProductAccountInDb]]:
    mongo_client = MongoService().client
    prd_transaction_col = ProductTransactionsCollection()
    prd_account_col = ProductAccountsCollection()
    sale_col = SalesCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_sale_id = UuidTool.generate_uuid()

            updated_product_accounts: List[ProductAccountInDb] = []
            created_transactions: List[ProductTransactionInDb] = []

            for sale_item in create_sale.saleItems:
                total_to_substract = sale_item.quantity + sale_item.bonQuantity

                result = await prd_account_col.substract_product_account_data(
                    product_id=sale_item.product.id,
                    branch_id=create_sale.branchId,
                    substract_to_current_stock=total_to_substract,
                    session=session,
                )

                if result is None:
                    raise InsufficientBalanceError(
                        f"Stock insuficiente para el producto {sale_item.product.name}"
                    )

                updated_product_account = ProductAccountInDb.model_validate(result)
                updated_product_accounts.append(updated_product_account)

                sale_item.cost = updated_product_account.averageCost

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_sale_id,
                    type="exit",
                    subtype="invoice",
                    productId=sale_item.product.id,
                    branchId=create_sale.branchId,
                    quantity=total_to_substract,
                    averageCost=sale_item.cost,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                    resultStock=updated_product_account.currentStock,
                )
                created_transactions.append(new_transaction)

            new_sale_data = create_sale.model_dump()
            new_sale_data["id"] = new_sale_id
            new_sale_data["createdAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await sale_col.create_sale_with_session(
                new_sale_data,
                session=session,
            )
            new_sale_in_db = SaleInDb.model_validate(insert_result)

            created_transactions_data = [t.model_dump() for t in created_transactions]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            return new_sale_in_db, updated_product_accounts
