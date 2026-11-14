from typing import Literal

from .base_filter_params import BaseFilterParams

ShiftStatus = Literal["open", "closed"]


class ShiftFilterParams(BaseFilterParams):
    branchId: str | None = None
    userId: str | None = None
    status: ShiftStatus | None = None
    startDate: int | None = None
    endDate: int | None = None
