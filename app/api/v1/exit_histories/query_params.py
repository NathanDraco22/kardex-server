from params import PaginationParams


class ExitHistoryQueryParams(PaginationParams):
    branch_id: str
    client_id: str | None = None
    pass
