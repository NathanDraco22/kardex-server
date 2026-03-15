from pydantic import BaseModel
from repos.v1.invoices.models.invoice_model import InvoiceStatus
from repos.v1.common.models.sale_item import PaymentType


class InvoiceQueryParams(BaseModel):
    clientId: str | None = None
    branchId: str | None = None
    paymentType: PaymentType | None = None
    nePaymentType: PaymentType | None = None
    startDate: int | None = None
    endDate: int | None = None
    byPaidAt: bool = False
    status: InvoiceStatus | None = None
    createdBy: str | None = None
    offset: int = 0
    limit: int = 50


class AdjustQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
    branchId: str | None = None
    endDate: int | None = None
