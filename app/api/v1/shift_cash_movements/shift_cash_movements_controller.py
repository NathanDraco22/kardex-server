from kardex.core.shift_cash_movement_register.delete_cash_movement import (
    delete_cash_movement,
)
from kardex.core.shift_cash_movement_register.process_cash_movement import (
    process_cash_movement,
)
from kardex.repos.v1.common.filter_params import ShiftCashMovementFilterParams
from kardex.repos.v1.shift_cash_movements import (
    CreateShiftCashMovement,
    ShiftCashMovementInDb,
    ShiftCashMovementsRepository,
)
from kardex.tools import CashMovementNotFound
from responses.v1 import ListResponse


class ShiftCashMovementsController:
    def __init__(self, movements_repo: ShiftCashMovementsRepository) -> None:
        self.movements_repo = movements_repo

    async def create_shift_cash_movement(
        self, body: CreateShiftCashMovement
    ) -> ShiftCashMovementInDb:
        return await process_cash_movement(body)

    async def get_all_shift_cash_movements(
        self, params: ShiftCashMovementFilterParams
    ) -> ListResponse[ShiftCashMovementInDb]:
        movements = await self.movements_repo.get_all_shift_cash_movements(params)
        return ListResponse(count=len(movements), data=movements)

    async def get_shift_cash_movement_by_id(
        self, movement_id: str
    ) -> ShiftCashMovementInDb:
        movement = await self.movements_repo.get_shift_cash_movement_by_id(
            movement_id
        )
        if movement is None:
            raise CashMovementNotFound(
                f"Cash movement {movement_id} not found", movement_id=movement_id
            )
        return movement

    async def delete_shift_cash_movement_by_id(
        self, movement_id: str
    ) -> ShiftCashMovementInDb:
        return await delete_cash_movement(movement_id)


shift_cash_movements_controller = ShiftCashMovementsController(
    movements_repo=ShiftCashMovementsRepository.get_instance(),
)
