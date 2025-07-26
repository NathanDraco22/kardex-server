from datetime import datetime
from pydantic import BaseModel


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    averageCost: int
    lastCost: int


class ProductAccountInDb(BaseProductAccount):
    id: str
    created_at: datetime
    updated_at: datetime | None = None
