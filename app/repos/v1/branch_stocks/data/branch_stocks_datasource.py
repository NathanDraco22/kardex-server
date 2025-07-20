from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import BranchStocksCollection


class BranchStocksDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_branch_stock(self, branch_stock: dict[str, Any]):
        collection = BranchStocksCollection()
        await collection.create_branch_stock(branch_stock)

    async def get_branch_stock_by_id(
        self, branch_stock_id: str
    ) -> dict[str, Any] | None:
        collection = BranchStocksCollection()
        return await collection.fetch_branch_stock_by_id(branch_stock_id)

    async def get_branch_stock_by_branch_and_product_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = BranchStocksCollection()
        return await collection.fetch_branch_stock_by_branch_and_product_id(
            product_id, branch_id
        )

    async def update_branch_stock_by_id(
        self, branch_stock_id: str, branch_stock: dict[str, Any]
    ) -> dict[str, Any]:
        collection = BranchStocksCollection()
        return await collection.update_branch_stock_by_id(branch_stock_id, branch_stock)

    async def update_branch_stock_by_branch_and_product_id(
        self, product_id: str, branch_id: str, branch_stock: dict[str, Any]
    ) -> dict[str, Any]:
        collection = BranchStocksCollection()
        return await collection.update_branch_stock_by_branch_and_product_id(
            product_id, branch_id, branch_stock
        )
