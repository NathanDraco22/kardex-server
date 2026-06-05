from typing import Literal
from .base_filter_params import BaseFilterParams

InvoiceStatus = Literal["draft", "open", "paid", "partiallyPaid", "cancelled"]
PaymentType = Literal["cash", "credit", "transfer", "card", "check", "other"]

class InvoiceFilterParams(BaseFilterParams):
    clientId: str | None = None
    branchId: str | None = None
    paymentType: PaymentType | None = None
    nePaymentType: PaymentType | None = None
    startDate: int | None = None
    endDate: int | None = None
    byPaidAt: bool = False
    status: InvoiceStatus | None = None
    createdBy: str | None = None

class AdjustFilterParams(BaseFilterParams):
    branchId: str | None = None
    endDate: int | None = None
