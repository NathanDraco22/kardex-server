from fastapi import APIRouter, Depends

from kardex.repos.v1.common.filter_params import ShiftFilterParams
from kardex.repos.v1.shifts import (
    CloseShiftRequest,
    CreateShift,
    ShiftInDb,
    ShiftPreview,
    UpdateShift,
)
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .shifts_controller import shifts_controller

shifts_router = APIRouter(tags=["shiftsV1"], dependencies=[Depends(auth_middleware)])


@shifts_router.post("")
async def create_shift(body: CreateShift) -> ShiftInDb:
    return await shifts_controller.create_shift(body)


@shifts_router.get("")
async def get_all_shifts(
    params: ShiftFilterParams = Depends(),
) -> ListResponse[ShiftInDb]:
    return await shifts_controller.get_all_shifts(params)


@shifts_router.get("/active/{user_id}")
async def get_active_shift_by_user(user_id: str) -> ShiftInDb | None:
    return await shifts_controller.get_active_shift_by_user(user_id)


@shifts_router.get("/{shift_id}/preview")
async def get_shift_preview(shift_id: str) -> ShiftPreview:
    return await shifts_controller.get_shift_preview(shift_id)


@shifts_router.post("/{shift_id}/close")
async def close_shift_by_id(shift_id: str, body: CloseShiftRequest) -> ShiftInDb:
    return await shifts_controller.close_shift(shift_id, body)


@shifts_router.get("/{shift_id}")
async def get_shift_by_id(shift_id: str) -> ShiftInDb:
    return await shifts_controller.get_shift_by_id(shift_id)


@shifts_router.patch("/{shift_id}")
async def update_shift_by_id(shift_id: str, body: UpdateShift) -> ShiftInDb:
    return await shifts_controller.update_shift_by_id(shift_id, body)
