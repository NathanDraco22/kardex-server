from datetime import date
from params import PaginationParams


class ExitHistoryQueryParams(PaginationParams):
    branchId: str
    clientId: str | None = None
    startDate: date | None = None
    endDate: date | None = None
