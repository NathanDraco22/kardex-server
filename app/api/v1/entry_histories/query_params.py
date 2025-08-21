from params import PaginationParams


class EntryHistoryQueryParams(PaginationParams):
    branch_id: str
    supplier_id: str | None = None
    pass
