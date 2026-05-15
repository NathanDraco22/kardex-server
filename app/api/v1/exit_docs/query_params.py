from params import PaginationParams


class ExitDocQueryParams(PaginationParams):
    branch_id: str
    clientId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
