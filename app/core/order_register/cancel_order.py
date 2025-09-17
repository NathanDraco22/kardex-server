from services.mongo_collections.v1 import (
    OrdersCollection,
    ProductAccountsCollection,
)
from repos.v1.orders import OrderInDb

from services import MongoService


async def cancel_order(order: OrderInDb) -> OrderInDb:
    mongo_client = MongoService().client
    order_col = OrdersCollection()
    prd_account_col = ProductAccountsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            for item in order.saleItems:
                total_promise_qty = abs(item.quantity + item.bonQuantity)

                await prd_account_col.substract_from_promise_stock(
                    product_id=item.product.id,
                    branch_id=order.branchId,
                    quantity=total_promise_qty,
                    session=session,
                )

            cancelled_order_data = await order_col.update_order_status(
                order_id=order.id, status="cancelled", session=session
            )

            return OrderInDb.model_validate(cancelled_order_data)
