from .base_filter_params import BaseFilterParams

class EntryDocFilterParams(BaseFilterParams):
    branch_id: str
    supplierId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
