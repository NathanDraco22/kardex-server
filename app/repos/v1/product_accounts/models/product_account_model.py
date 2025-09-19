from pydantic import BaseModel


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    promiseStock: int = 0
    averageCost: int
    lastCost: int


class ProductAccountInDb(BaseProductAccount):
    createdAt: int
    updatedAt: int | None = None
