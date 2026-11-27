from typing import Literal

from .base_filter_params import BaseFilterParams


InvoiceCancellationRequestStatus = Literal[
    "pending", "approved", "rejected", "cancelled"
]


class InvoiceCancellationRequestFilterParams(BaseFilterParams):
    branchId: str | None = None
    status: InvoiceCancellationRequestStatus | None = None
    invoiceId: str | None = None
    requestedById: str | None = None
    startDate: int | None = None
    endDate: int | None = None
