from typing import AsyncGenerator
from .data.inventories_datasource import InventoriesDataSource
from .models.inventory_model import InventoryInDb

class InventoriesRepository:
    _instance: "InventoriesRepository | None" = None

    def __init__(self, inventories_ds: InventoriesDataSource):
        self.inventories_ds = inventories_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = InventoriesRepository(
                inventories_ds=InventoriesDataSource()
            )
        return cls._instance

    async def get_all_inventories_by_branch(
        self, branch_id: str
    ) -> AsyncGenerator[InventoryInDb, None]:
        async for result in self.inventories_ds.get_all_inventories_by_branch(
            branch_id
        ):
            yield InventoryInDb.model_validate(result)

    async def get_total_current_stock(self, branch_id: str) -> int:
        return await self.inventories_ds.get_total_current_stock(branch_id)
