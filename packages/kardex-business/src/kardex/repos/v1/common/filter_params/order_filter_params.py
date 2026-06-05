from typing import Literal
from pydantic import BaseModel

OrderStatus = Literal["draft", "open", "completed", "cancelled"]

class OrderFilterParams(BaseModel):
    skip: int = 0
    limit: int = 50
    status: OrderStatus | None = None
    neStatus: OrderStatus | None = None
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    createdBy: str | None = None
