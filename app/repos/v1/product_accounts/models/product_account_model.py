from datetime import datetime
from pydantic import BaseModel


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    averageCost: int
    lastCost: int


class ProductAccountInDb(BaseProductAccount):
    createdAt: datetime
    updatedAt: datetime | None = None
