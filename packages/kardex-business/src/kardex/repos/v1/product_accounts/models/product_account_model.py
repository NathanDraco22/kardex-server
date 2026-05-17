from pydantic import BaseModel


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    promiseStock: int = 0
    averageCost: int
    lastCost: int
    maximumCost: int = 0


class ProductAccountInDb(BaseProductAccount):
    createdAt: int
    updatedAt: int | None = None
