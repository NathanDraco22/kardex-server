from kardex.services.mongo_collections.v1 import (
    OrdersCollection,
    ProductAccountsCollection,
)
from kardex.repos.v1.orders import OrderInDb
from kardex.services import MongoService


async def cancel_order(order: OrderInDb) -> OrderInDb:
    """
    Cancela un pedido y libera el stock prometido (si estaba en estado 'open').
    """
    mongo_client = MongoService().client
    order_col = OrdersCollection()
    prd_account_col = ProductAccountsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            if order.status == "open":
                bulk_release_data: list[tuple[str, int]] = []

                for item in order.saleItems:
                    total_promise_qty = abs(item.quantity + item.bonQuantity)
                    bulk_release_data.append((item.product.id, total_promise_qty))

                if bulk_release_data:
                    await prd_account_col.bulk_substract_from_promise_stock(
                        branch_id=order.branchId,
                        bulk_data=bulk_release_data,
                        session=session,
                    )

            cancelled_order_data = await order_col.update_order_status(
                order_id=order.id, status="cancelled", session=session
            )

            return OrderInDb.model_validate(cancelled_order_data)
