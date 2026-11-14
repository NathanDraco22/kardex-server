from fastapi import APIRouter, Depends

from kardex.repos.v1.common.filter_params import ShiftCashMovementFilterParams
from kardex.repos.v1.shift_cash_movements import (
    CreateShiftCashMovement,
    ShiftCashMovementInDb,
)
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .shift_cash_movements_controller import shift_cash_movements_controller

shift_cash_movements_router = APIRouter(
    tags=["shiftCashMovementsV1"], dependencies=[Depends(auth_middleware)]
)


@shift_cash_movements_router.post("")
async def create_shift_cash_movement(
    body: CreateShiftCashMovement,
) -> ShiftCashMovementInDb:
    return await shift_cash_movements_controller.create_shift_cash_movement(body)


@shift_cash_movements_router.get("")
async def get_all_shift_cash_movements(
    params: ShiftCashMovementFilterParams = Depends(),
) -> ListResponse[ShiftCashMovementInDb]:
    return await shift_cash_movements_controller.get_all_shift_cash_movements(params)


@shift_cash_movements_router.get("/{movement_id}")
async def get_shift_cash_movement_by_id(
    movement_id: str,
) -> ShiftCashMovementInDb:
    return await shift_cash_movements_controller.get_shift_cash_movement_by_id(
        movement_id
    )


@shift_cash_movements_router.delete("/{movement_id}")
async def delete_shift_cash_movement_by_id(
    movement_id: str,
) -> ShiftCashMovementInDb:
    return await shift_cash_movements_controller.delete_shift_cash_movement_by_id(
        movement_id
    )
