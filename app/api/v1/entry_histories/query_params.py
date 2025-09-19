from params import PaginationParams


class EntryHistoryQueryParams(PaginationParams):
    branchId: str
    supplierId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
