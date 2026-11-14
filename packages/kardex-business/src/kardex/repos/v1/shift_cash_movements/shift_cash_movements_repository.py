from kardex.tools import TimeTools
from kardex.repos.v1.common.filter_params import ShiftCashMovementFilterParams

from .data.shift_cash_movements_datasource import ShiftCashMovementsDataSource
from .models.shift_cash_movement_model import (
    ShiftCashMovementInDb,
    UpdateShiftCashMovement,
)


class ShiftCashMovementsRepository:

    _instance: "ShiftCashMovementsRepository|None" = None

    def __init__(self, movements_ds: ShiftCashMovementsDataSource):
        self.movements_ds = movements_ds

    @classmethod
    def get_instance(cls) -> "ShiftCashMovementsRepository":
        if cls._instance is None:
            cls._instance = cls(ShiftCashMovementsDataSource())
        return cls._instance

    async def get_all_shift_cash_movements(
        self, params: ShiftCashMovementFilterParams
    ) -> list[ShiftCashMovementInDb]:
        results = await self.movements_ds.get_all_shift_cash_movements(
            **params.model_dump()
        )
        models = [ShiftCashMovementInDb.model_validate(result) for result in results]
        return models

    async def get_shift_cash_movement_by_id(
        self, movement_id: str
    ) -> ShiftCashMovementInDb | None:
        result = await self.movements_ds.get_shift_cash_movement_by_id(movement_id)

        if result is None:
            return None

        return ShiftCashMovementInDb.model_validate(result)

    async def update_shift_cash_movement_by_id(
        self, movement_id: str, movement: UpdateShiftCashMovement
    ) -> ShiftCashMovementInDb | None:
        updated_data = movement.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.movements_ds.update_shift_cash_movement_by_id(
            movement_id, updated_data
        )

        if result is None:
            return None

        return ShiftCashMovementInDb.model_validate(result)
