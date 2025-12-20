from pydantic import BaseModel
from repos.v1.invoices.models.invoice_model import InvoiceStatus


class InvoiceQueryParams(BaseModel):
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    byPaidAt: bool = False
    status: InvoiceStatus | None = None
    createdBy: str | None = None
    offset: int = 0
    limit: int = 50
