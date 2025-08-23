from datetime import date
from params import PaginationParams


class EntryHistoryQueryParams(PaginationParams):
    branchId: str
    supplierId: str | None = None
    startDate: date | None = None
    endDate: date | None = None
