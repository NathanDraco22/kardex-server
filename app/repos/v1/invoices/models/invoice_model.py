from typing import Literal
from datetime import datetime
from pydantic import BaseModel

InvoiceStatus = Literal["open", "paid", "partially_paid", "cancelled"]
PaymentType = Literal["cash", "credit"]


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
    subTotal: int
    discount: int = 0
    iva: int = 0
    total: int


class BaseInvoice(BaseModel):
    branchId: str
    clientId: str
    docNumber: str = ""
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
    ammountPaid: int | None = None
    status: InvoiceStatus | None = None
    pass


class InvoiceInDb(BaseInvoice):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
