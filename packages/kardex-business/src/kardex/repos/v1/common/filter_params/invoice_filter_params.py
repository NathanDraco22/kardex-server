from .base_filter_params import BaseFilterParams
from kardex.repos.v1.invoices.models.invoice_model import InvoiceStatus
from kardex.repos.v1.common.models.sale_item import PaymentType

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
