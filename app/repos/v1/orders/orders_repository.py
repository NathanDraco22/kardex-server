from tools import TimeTools, UuidTool
from .data.orders_datasource import OrdersDataSource
from .models.order_model import CreateOrder, UpdateOrder, OrderInDb


class OrdersRepository:
    def __init__(self, orders_ds: OrdersDataSource):
        self.orders_ds = orders_ds

    async def create_draft_order(self, order: CreateOrder) -> OrderInDb:
        newDraftOrder = OrderInDb(
            **order.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        result = await self.orders_ds.create_order(newDraftOrder.model_dump())
        return OrderInDb.model_validate(result)

    async def get_paginated_orders(self, **kwargs) -> list[OrderInDb]:
        result = await self.orders_ds.get_paginated_orders(**kwargs)
        return [OrderInDb.model_validate(order) for order in result]

    async def get_order_by_id(self, order_id: str) -> OrderInDb | None:
        result = await self.orders_ds.get_order_by_id(order_id)

        if result is None:
            return None

        return OrderInDb.model_validate(result)

    async def get_order_by_doc_number(self, doc_number: str) -> OrderInDb | None:
        result = await self.orders_ds.get_order_by_doc_number(doc_number)

        if result is None:
            return None

        return OrderInDb.model_validate(result)

    async def update_order_draft_by_id(
        self, order_id: str, order: UpdateOrder
    ) -> OrderInDb | None:
        update_order_data = order.model_dump(exclude_unset=True)

        update_order_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.orders_ds.update_order_draft_by_id(
            order_id,
            update_order_data,
        )

        if result is None:
            return None

        return OrderInDb.model_validate(result)

    async def delete_order_by_id(self, order_id: str) -> OrderInDb | None:
        result = await self.orders_ds.delete_order_by_id(order_id)

        if result is None:
            return None

        return OrderInDb.model_validate(result)
