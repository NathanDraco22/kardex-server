from kardex.core.shift_register.close_shift import (
    calculate_shift_preview,
    close_shift,
)
from kardex.core.shift_register.open_shift import open_shift
from kardex.repos.v1.common.filter_params import ShiftFilterParams
from kardex.repos.v1.shifts import (
    CloseShiftRequest,
    CreateShift,
    ShiftInDb,
    ShiftPreview,
    UpdateShift,
    ShiftsRepository,
)
from kardex.tools import ShiftNotFound
from responses.v1 import ListResponse


class ShiftsController:
    def __init__(self, shifts_repo: ShiftsRepository) -> None:
        self.shifts_repo = shifts_repo

    async def create_shift(self, body: CreateShift) -> ShiftInDb:
        return await open_shift(body)

    async def get_all_shifts(
        self, params: ShiftFilterParams
    ) -> ListResponse[ShiftInDb]:
        shifts = await self.shifts_repo.get_all_shifts(params)
        return ListResponse(count=len(shifts), data=shifts)

    async def get_active_shift_by_user(self, user_id: str) -> ShiftInDb | None:
        return await self.shifts_repo.get_active_shift_by_user(user_id)

    async def get_shift_by_id(self, shift_id: str) -> ShiftInDb:
        shift = await self.shifts_repo.get_shift_by_id(shift_id)
        if shift is None:
            raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)
        return shift

    async def get_shift_preview(self, shift_id: str) -> ShiftPreview:
        return await calculate_shift_preview(shift_id)

    async def close_shift(
        self, shift_id: str, body: CloseShiftRequest
    ) -> ShiftInDb:
        return await close_shift(shift_id, body)

    async def update_shift_by_id(
        self, shift_id: str, body: UpdateShift
    ) -> ShiftInDb:
        shift = await self.shifts_repo.update_shift_by_id(shift_id, body)
        if shift is None:
            raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)
        return shift


shifts_controller = ShiftsController(
    shifts_repo=ShiftsRepository.get_instance(),
)
