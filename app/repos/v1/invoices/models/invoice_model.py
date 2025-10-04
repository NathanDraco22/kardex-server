from typing import Literal

from pydantic import BaseModel

from repos.v1.common.models import SaleItem, PaymentType, ClientInfo

InvoiceStatus = Literal["open", "paid", "partially_paid", "cancelled"]


class BaseInvoice(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    docNumber: str = ""
    orderNumber: str = ""
    saleItems: list[SaleItem]
    description: str = ""
    amountPaid: int = 0
    status: InvoiceStatus
    paymentType: PaymentType
    totalCost: int
    total: int
    paidAt: int | None = None


class CreateInvoice(BaseInvoice):
    pass


class UpdateInvoice(BaseModel):
    amountPaid: int | None = None
    status: InvoiceStatus | None = None
    pass


class InvoiceInDb(BaseInvoice):
    id: str
    createdAt: int
    updatedAt: int | None = None
