from typing import Literal

from .base_filter_params import BaseFilterParams


AdjustmentRequestStatus = Literal["pending", "approved", "cancelled"]


class AdjustmentRequestFilterParams(BaseFilterParams):
    branchId: str | None = None
    status: AdjustmentRequestStatus | None = None
    createdBy: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    docNumber: str | None = None
