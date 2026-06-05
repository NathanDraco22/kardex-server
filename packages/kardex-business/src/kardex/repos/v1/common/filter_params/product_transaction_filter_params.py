from .base_filter_params import BaseFilterParams


class ProductTransactionFilterParams(BaseFilterParams):
    branchId: str | None = None
    productId: str | None = None
    endDate: int | None = None
    type: str | None = None
    subtype: str | None = None
