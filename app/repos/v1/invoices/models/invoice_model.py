from typing import Literal
from datetime import datetime
from pydantic import BaseModel

InvoiceStatus = Literal["OPEN", "PAID"]
PaymentType = Literal["CASH", "CREDIT"]


class ProductItem(BaseModel):
    id: str
    name: str
    unitName: str
    brandName: str
    code: str | None = None
    categoryName: str | None = None
    tags: list[str] = []


class SaleItem(BaseModel):
    product: ProductItem
    quantity: int
    bonQuantity: int = 0
    cost: int
    price: int
    priceName: str
    discount: int = 0


class BaseInvoice(BaseModel):
    branchId: str
    clientId: str
    docNumber: str
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
    pass


class InvoiceInDb(BaseInvoice):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
