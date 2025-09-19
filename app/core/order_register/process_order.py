from typing import List, Tuple
from services.mongo_collections.v1 import (
    OrdersCollection,
    ProductAccountsCollection,
)
from repos.v1.orders import CreateOrder, OrderInDb
from repos.v1.product_accounts import ProductAccountInDb
from tools import UuidTool, TimeTools
from services import MongoService


class InsufficientBalanceError(Exception):
    pass


async def process_order(
    create_order: CreateOrder,
) -> Tuple[OrderInDb, List[ProductAccountInDb]]:
    mongo_client = MongoService().client
    prd_account_col = ProductAccountsCollection()
    order_col = OrdersCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            updated_product_accounts: List[ProductAccountInDb] = []

            for sale_item in create_order.saleItems:
                quantity_to_promise = abs(sale_item.quantity + sale_item.bonQuantity)

                result = await prd_account_col.add_to_promise_stock(
                    product_id=sale_item.product.id,
                    branch_id=create_order.branchId,
                    quantity=quantity_to_promise,
                    session=session,
                )

                if result is None:
                    raise InsufficientBalanceError(
                        f"Stock insuficiente para {sale_item.product.name}"
                    )

                updated_product_account = ProductAccountInDb.model_validate(result)
                sale_item.cost = updated_product_account.averageCost
                updated_product_accounts.append(updated_product_account)

            new_order_data = create_order.model_dump()
            new_order_data["id"] = UuidTool.generate_uuid()
            new_order_data["createdAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await order_col.create_order_with_session(
                new_order_data,
                session=session,
            )
            new_order_in_db = OrderInDb.model_validate(insert_result)

            return new_order_in_db, updated_product_accounts
