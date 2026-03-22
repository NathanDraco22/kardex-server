from fastapi import APIRouter, Depends

from repos.v1.inventories import InventoryInDb
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .inventories_controller import inventories_controller


inventories_router = APIRouter(
    tags=["inventoriesV1"], dependencies=[Depends(auth_middleware)]
)


@inventories_router.get("")
async def get_all_inventories(branchId: str) -> ListResponse[InventoryInDb]:
    return await inventories_controller.get_all_inventories_by_branch(branchId)
