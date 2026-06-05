from kardex.tools import TimeTools, UuidTool
from .data.orders_datasource import OrdersDataSource
from .models.order_model import CreateOrder, UpdateOrder, OrderInDb
from kardex.repos.v1.common.filter_params import OrderFilterParams

from kardex.repos.v1.common.models.invoice_product_sale import ProductSalesTotal
from kardex.repos.v1.common.models import ProductStockDemand

class OrdersRepository:
    _instance: "OrdersRepository | None" = None

    def __init__(self, orders_ds: OrdersDataSource):
        self.orders_ds = orders_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = OrdersRepository(
                orders_ds=OrdersDataSource()
            )
        return cls._instance

    async def create_draft_order(self, order: CreateOrder) -> OrderInDb:
        newDraftOrder = OrderInDb(
            **order.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        result = await self.orders_ds.create_order(newDraftOrder.model_dump())
        return OrderInDb.model_validate(result)

    async def get_paginated_orders(self, params: OrderFilterParams) -> list[OrderInDb]:
        result = await self.orders_ds.get_paginated_orders(
            **params.model_dump(exclude_unset=True)
        )
        return [OrderInDb.model_validate(order) for order in result]

    async def get_products_in_orders(
        self, params: OrderFilterParams
    ) -> list[ProductSalesTotal]:
        result = await self.orders_ds.get_products_in_orders(
            **params.model_dump(exclude_none=True)
        )
        return [ProductSalesTotal.model_validate(order) for order in result]

    async def get_demand_vs_stock(
        self, params: OrderFilterParams
    ) -> list[ProductStockDemand]:
        result = await self.orders_ds.get_demand_vs_stock(
            **params.model_dump(exclude_none=True)
        )
        return [ProductStockDemand.model_validate(order) for order in result]

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

    async def delete_order_draft_by_id(self, order_id: str) -> OrderInDb | None:
        result = await self.orders_ds.delete_order_draft_by_id(order_id)

        if result is None:
            return None

        return OrderInDb.model_validate(result)
