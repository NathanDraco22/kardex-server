from datetime import datetime
from pydantic import BaseModel


class PriceObject(BaseModel):
    name: str
    price: int


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    averageCost: int
    lastCost: int


class ProductAccountInDb(BaseProductAccount):
    createdAt: datetime
    updatedAt: datetime | None = None
