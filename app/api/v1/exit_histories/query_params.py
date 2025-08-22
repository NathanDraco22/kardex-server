from datetime import date
from params import PaginationParams


class ExitHistoryQueryParams(PaginationParams):
    branch_id: str
    client_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
