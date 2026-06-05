from .base_filter_params import BaseFilterParams

class DailySummaryFilterParams(BaseFilterParams):
    dateId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
