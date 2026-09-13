from typing import Any
from kardex.services.mongo_collections.v1 import HoldSalesCollection


class HoldSalesDataSource:

    async def create_hold_sale(self, hold_sale: dict[str, Any]) -> dict[str, Any]:
        collection = HoldSalesCollection.get_instance()
        await collection.create_hold_sale(hold_sale)
        return hold_sale

    async def get_all_hold_sales(self, **kwargs) -> list[dict[str, Any]]:
        collection = HoldSalesCollection.get_instance()
        return await collection.fetch_all_hold_sales(**kwargs)

    async def get_hold_sale_by_id(self, hold_sale_id: str) -> dict[str, Any] | None:
        collection = HoldSalesCollection.get_instance()
        return await collection.fetch_hold_sale_by_id(hold_sale_id)

    async def update_hold_sale_by_id(
        self, hold_sale_id: str, hold_sale: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = HoldSalesCollection.get_instance()
        return await collection.update_hold_sale_by_id(hold_sale_id, hold_sale)

    async def delete_hold_sale_by_id(self, hold_sale_id: str) -> dict[str, Any] | None:
        collection = HoldSalesCollection.get_instance()
        return await collection.delete_hold_sale_by_id(hold_sale_id)

    async def delete_all_hold_sales_by_branch(self, branch_id: str) -> int:
        collection = HoldSalesCollection.get_instance()
        return await collection.delete_all_hold_sales_by_branch(branch_id)

