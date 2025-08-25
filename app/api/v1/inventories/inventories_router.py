from fastapi import APIRouter

from repos.v1.inventories import InventoryInDb
from responses.v1 import ListResponse

from .inventories_controller import inventories_controller


inventories_router = APIRouter(tags=["inventoriesV1"])


@inventories_router.get("")
async def get_all_inventories(branchId: str) -> ListResponse[InventoryInDb]:
    return await inventories_controller.get_all_inventories_by_branch(branchId)
