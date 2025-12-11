from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import OrdersCollection


class OrdersDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_order(self, order: dict[str, Any]) -> dict[str, Any]:
        collection = OrdersCollection()
        await collection.create_order(order)
        return order

    async def get_paginated_orders(self, **kwargs) -> list[dict[str, Any]]:
        collection = OrdersCollection()
        return await collection.fetch_paginated_orders(**kwargs)

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
