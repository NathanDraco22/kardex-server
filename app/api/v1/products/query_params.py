from kardex.repos.v1.receipts.models.receipt_model import PaymentMethod
from params import PaginationParams


class ProductQueryParams(PaginationParams):
    branchId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    paymentMethod: PaymentMethod | None = None
    nePaymentMethod: PaymentMethod | None = None
