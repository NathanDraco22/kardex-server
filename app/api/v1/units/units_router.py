from fastapi import APIRouter

from repos.v1.units import CreateUnit, UpdateUnit, UnitInDb

from responses.v1 import ListResponse

from .units_controller import units_controller


units_router = APIRouter(tags=["unitsV1"])


@units_router.post("")
async def create_unit(body: CreateUnit) -> UnitInDb:
    return await units_controller.create_unit(body)


@units_router.get("")
async def get_all_units() -> ListResponse[UnitInDb]:
    return await units_controller.get_all_units()


@units_router.get("/{unit_id}")
async def get_unit_by_id(unit_id: str) -> UnitInDb:
    return await units_controller.get_unit_by_id(unit_id)


@units_router.patch("/{unit_id}")
async def update_unit_by_id(unit_id: str, body: UpdateUnit) -> UnitInDb:
    return await units_controller.update_unit_by_id(unit_id, body)


@units_router.delete("/{unit_id}")
async def delete_unit_by_id(unit_id: str) -> UnitInDb:
    return await units_controller.delete_unit_by_id(unit_id)
