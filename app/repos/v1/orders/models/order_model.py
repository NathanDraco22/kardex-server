from typing import Literal
from repos.v1.common.models import (
    SaleItem,
    PaymentType,
    ClientInfo,
    UserInfo,
)
from pydantic import BaseModel

OrderStatus = Literal[
    "draft",
    "open",
    "completed",
    "cancelled",
]


class BaseOrder(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    docNumber: str = ""
    invoiceId: str = ""
    saleItems: list[SaleItem]
    description: str = ""
    amountPaid: int = 0
    status: OrderStatus
    paymentType: PaymentType
    totalCost: int
    total: int
    createdBy: UserInfo


class CreateOrder(BaseOrder):
    pass


class UpdateOrder(BaseModel):
    saleItems: list[SaleItem] | None = None
    description: str | None = None
    amountPaid: int | None = None
    status: OrderStatus | None = None
    paymentType: PaymentType | None = None
    totalCost: int | None = None
    total: int | None = None


class OrderInDb(BaseOrder):
    id: str
    createdAt: int
    updatedAt: int | None = None
