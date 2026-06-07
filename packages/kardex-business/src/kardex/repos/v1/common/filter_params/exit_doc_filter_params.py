from .base_filter_params import BaseFilterParams

class ExitDocFilterParams(BaseFilterParams):
    branch_id: str
    clientId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
