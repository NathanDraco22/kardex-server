from typing import Literal
from datetime import datetime
from pydantic import BaseModel

from repos.v1.common.models.sale_item import SaleItem, PaymentType

InvoiceStatus = Literal["open", "paid", "partially_paid", "cancelled"]


class BaseInvoice(BaseModel):
    branchId: str
    clientId: str
    docNumber: str = ""
    orderNumber: str = ""
    saleItems: list[SaleItem]
    description: str = ""
    amountPaid: int = 0
    status: InvoiceStatus
    paymentType: PaymentType
    totalCost: int
    total: int


class CreateInvoice(BaseInvoice):
    pass


class UpdateInvoice(BaseModel):
    amountPaid: int | None = None
    status: InvoiceStatus | None = None
    pass


class InvoiceInDb(BaseInvoice):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
