from fastapi import HTTPException, status
from responses.v1.list_response import ListResponse
from kardex.repos.v1.inventories import (
    InventoryInDb,
    InventoriesRepository,
    InventoriesDataSource,
    ResetBranchInventoryRequest,
    ResetBranchInventoryResponse,
)
from kardex.core.inventory import process_reset_inventory
from kardex.tools import BranchNotFound, InvalidOperation


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

    async def reset_branch_inventory(
        self, body: ResetBranchInventoryRequest
    ) -> ResetBranchInventoryResponse:
        try:
            return await process_reset_inventory(body)
        except BranchNotFound as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except InvalidOperation as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al reiniciar inventario: {str(e)}",
            )


inventories_controller = InventoriesController(
    inventories_repo=InventoriesRepository(
        inventories_ds=InventoriesDataSource(),
    ),
)
