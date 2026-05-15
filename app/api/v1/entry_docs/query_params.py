from params import PaginationParams


class EntryDocQueryParams(PaginationParams):
    branch_id: str
    supplierId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    limit: int = 50
    offset: int = 0
