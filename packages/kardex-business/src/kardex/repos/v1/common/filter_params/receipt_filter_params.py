from .base_filter_params import BaseFilterParams
from kardex.repos.v1.receipts.models.receipt_model import PaymentMethod


class ReceiptFilterParams(BaseFilterParams):
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    paymentMethod: PaymentMethod | None = None
    nePaymentMethod: PaymentMethod | None = None
    endDate: int | None = None
