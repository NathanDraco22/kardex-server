from fastapi import APIRouter, Depends

from app_middleware import auth_middleware
from kardex.repos.v1.unit_scales import CreateUnitScale, UpdateUnitScale, UnitScaleInDb
from responses.v1 import ListResponse

from .unit_scales_controller import unit_scales_controller

unit_scales_router = APIRouter(
    tags=["unit_scalesV1"],
    dependencies=[Depends(auth_middleware)],
)


@unit_scales_router.post("")
async def create_unit_scale(body: CreateUnitScale) -> UnitScaleInDb:
    return await unit_scales_controller.create_unit_scale(body)


@unit_scales_router.get("")
async def get_all_unit_scales() -> ListResponse[UnitScaleInDb]:
    return await unit_scales_controller.get_all_unit_scales()


@unit_scales_router.get("/{unit_scale_id}")
async def get_unit_scale_by_id(unit_scale_id: str) -> UnitScaleInDb:
    return await unit_scales_controller.get_unit_scale_by_id(unit_scale_id)


@unit_scales_router.patch("/{unit_scale_id}")
async def update_unit_scale_by_id(
    unit_scale_id: str, body: UpdateUnitScale
) -> UnitScaleInDb:
    return await unit_scales_controller.update_unit_scale_by_id(unit_scale_id, body)


@unit_scales_router.delete("/{unit_scale_id}")
async def delete_unit_scale_by_id(unit_scale_id: str) -> UnitScaleInDb:
    return await unit_scales_controller.delete_unit_scale_by_id(unit_scale_id)
