from .base_filter_params import BaseFilterParams


class HoldSaleFilterParams(BaseFilterParams):
    branchId: str | None = None
    createdBy: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    search: str | None = None
