from datetime import date
from params import PaginationParams


class EntryHistoryQueryParams(PaginationParams):
    branch_id: str
    supplier_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
