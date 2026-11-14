from kardex.tools import TimeTools
from kardex.repos.v1.common.filter_params import ShiftFilterParams

from .data.shifts_datasource import ShiftsDataSource
from .models.shift_model import UpdateShift, ShiftInDb


class ShiftsRepository:

    _instance: "ShiftsRepository|None" = None

    def __init__(self, shifts_ds: ShiftsDataSource):
        self.shifts_ds = shifts_ds

    @classmethod
    def get_instance(cls) -> "ShiftsRepository":
        if cls._instance is None:
            cls._instance = cls(ShiftsDataSource())
        return cls._instance

    async def get_all_shifts(self, params: ShiftFilterParams) -> list[ShiftInDb]:
        results = await self.shifts_ds.get_all_shifts(**params.model_dump())
        models = [ShiftInDb.model_validate(result) for result in results]
        return models

    async def get_shift_by_id(self, shift_id: str) -> ShiftInDb | None:
        result = await self.shifts_ds.get_shift_by_id(shift_id)

        if result is None:
            return None

        return ShiftInDb.model_validate(result)

    async def get_active_shift_by_user(self, user_id: str) -> ShiftInDb | None:
        result = await self.shifts_ds.get_active_shift_by_user(user_id)

        if result is None:
            return None

        return ShiftInDb.model_validate(result)

    async def update_shift_by_id(
        self, shift_id: str, shift: UpdateShift
    ) -> ShiftInDb | None:
        updated_data = shift.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.shifts_ds.update_shift_by_id(shift_id, updated_data)

        if result is None:
            return None

        return ShiftInDb.model_validate(result)
