from .base_filter_params import BaseFilterParams


class ExecutiveSummaryFilterParams(BaseFilterParams):
    startDate: int | None = None
    endDate: int | None = None
