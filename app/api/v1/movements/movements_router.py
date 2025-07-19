from fastapi import APIRouter
from responses.v1 import ListResponse
from repos.v1.movements import CreateMovement, MovementInDb

from .movements_controller import movements_controller


movements_router = APIRouter(tags=["movementsV1"])


@movements_router.post("/entry")
async def create_entry_movement_endpoint(body: CreateMovement) -> MovementInDb:
    return await movements_controller.create_entry_movement(body)


@movements_router.post("/exit")
async def create_exit_movement_endpoint(body: CreateMovement) -> MovementInDb:
    return await movements_controller.create_exit_movement(body)


@movements_router.get("")
async def get_all_movements_endpoint() -> ListResponse[MovementInDb]:
    return await movements_controller.get_all_movements()


@movements_router.get("/{movement_id}")
async def get_movement_by_id_endpoint(movement_id: str) -> MovementInDb:
    return await movements_controller.get_movement_by_id(movement_id)
