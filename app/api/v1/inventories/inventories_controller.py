from responses.v1.list_response import ListResponse
from kardex.repos.v1.inventories import (
    InventoryInDb,
    InventoriesRepository,
    InventoriesDataSource,
)


class InventoriesController:
    def __init__(self, inventories_repo: InventoriesRepository) -> None:
        self.inventories_repo = inventories_repo

    async def get_all_inventories_by_branch(
        self, branch_id: str
    ) -> ListResponse[InventoryInDb]:
        models = [
            inventory
            async for inventory in self.inventories_repo.get_all_inventories_by_branch(
                branch_id
            )
        ]

        return ListResponse(count=len(models), data=models)


inventories_controller = InventoriesController(
    inventories_repo=InventoriesRepository(
        inventories_ds=InventoriesDataSource(),
    ),
)
