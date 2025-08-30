from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import SalesCollection


class SalesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_sale(self, sale: dict[str, Any]) -> dict[str, Any]:
        collection = SalesCollection()
        await collection.create_sale(sale)
        return sale

    async def get_all_sales(self) -> list[dict[str, Any]]:
        collection = SalesCollection()
        return await collection.fetch_all_sales()

    async def get_sale_by_id(self, sale_id: str) -> dict[str, Any] | None:
        collection = SalesCollection()
        return await collection.fetch_sale_by_id(sale_id)

    async def update_sale_by_id(
        self, sale_id: str, sale: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = SalesCollection()
        return await collection.update_sale_by_id(sale_id, sale)

    async def delete_sale_by_id(self, sale_id: str) -> dict[str, Any] | None:
        collection = SalesCollection()
        return await collection.delete_sale_by_id(sale_id)
