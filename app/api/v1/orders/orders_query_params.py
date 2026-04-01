from pydantic import BaseModel
from repos.v1.orders.models.order_model import OrderStatus

class OrderQueryParams(BaseModel):
    skip: int = 0
    limit: int = 50
    status: OrderStatus | None = None
    neStatus: OrderStatus | None = None
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
