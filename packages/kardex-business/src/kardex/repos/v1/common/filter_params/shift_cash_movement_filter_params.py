from typing import Literal

from .base_filter_params import BaseFilterParams

CashMovementType = Literal["in", "out"]


class ShiftCashMovementFilterParams(BaseFilterParams):
    shiftId: str | None = None
    branchId: str | None = None
    type: CashMovementType | None = None
    startDate: int | None = None
    endDate: int | None = None
