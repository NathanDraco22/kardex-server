from typing import Literal

from .base_filter_params import BaseFilterParams


ReceiptCancellationRequestStatus = Literal[
    "pending", "approved", "rejected", "cancelled"
]


class ReceiptCancellationRequestFilterParams(BaseFilterParams):
    branchId: str | None = None
    status: ReceiptCancellationRequestStatus | None = None
    receiptId: str | None = None
    requestedById: str | None = None
    startDate: int | None = None
    endDate: int | None = None
