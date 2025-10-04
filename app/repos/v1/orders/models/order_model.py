from typing import Literal
from repos.v1.common.models import SaleItem, PaymentType, ClientInfo
from pydantic import BaseModel

OrderStatus = Literal["open", "completed", "cancelled"]


class BaseOrder(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    docNumber: str = ""
    saleItems: list[SaleItem]
    description: str = ""
    amountPaid: int = 0
    status: OrderStatus
    paymentType: PaymentType
    totalCost: int
    total: int


class CreateOrder(BaseOrder):
    pass


class UpdateOrder(BaseModel):
    status: OrderStatus | None = None
    pass


class OrderInDb(BaseOrder):
    id: str
    createdAt: int
    updatedAt: int | None = None
