from params import PaginationParams


class ExitHistoryQueryParams(PaginationParams):
    branchId: str
    clientId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
