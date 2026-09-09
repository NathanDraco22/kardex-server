from typing import Literal
from .base_filter_params import BaseFilterParams

PaymentMethod = Literal["cash", "transfer", "card", "check", "other"]


class ReceiptFilterParams(BaseFilterParams):
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    paymentMethod: PaymentMethod | None = None
    nePaymentMethod: PaymentMethod | None = None
    endDate: int | None = None
    createdBy: str | None = None
