from params import PaginationParams


class ProductQueryParams(PaginationParams):
    branchId: str | None = None
