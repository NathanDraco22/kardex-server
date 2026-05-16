from typing import Any
from kardex.services.mongo_collections.v1 import OrdersCollection


class OrdersDataSource:
    async def create_order(self, order: dict[str, Any]) -> dict[str, Any]:
        collection = OrdersCollection()
        await collection.create_order(order)
        return order

    async def get_paginated_orders(self, **kwargs) -> list[dict[str, Any]]:
        collection = OrdersCollection()
        return await collection.fetch_paginated_orders(**kwargs)

    async def get_products_in_orders(self, **kwargs) -> list[dict[str, Any]]:
        collection = OrdersCollection()
        return await collection.fetch_products_in_orders(**kwargs)

    async def get_demand_vs_stock(self, **kwargs) -> list[dict[str, Any]]:
        collection = OrdersCollection()
        return await collection.fetch_demand_vs_stock(**kwargs)

    async def get_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = OrdersCollection()
        return await collection.fetch_order_by_id(order_id)

    async def get_order_by_doc_number(self, doc_number: str) -> dict[str, Any] | None:
        collection = OrdersCollection()
        return await collection.fetch_order_by_doc_number(doc_number)

    async def update_order_draft_by_id(
        self, order_id: str, order: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = OrdersCollection()
        return await collection.update_order_draft_by_id(order_id, order)

    async def delete_order_draft_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = OrdersCollection()
        return await collection.delete_order_draft_by_id(order_id)
