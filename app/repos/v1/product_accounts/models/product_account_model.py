from pydantic import BaseModel


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    promiseStock: int = 0
    averageCost: int
    lastCost: int
    maximumCost: int = 0


class UpdateProductAccount(BaseModel):
    currentStock: int | None = None
    averageCost: int | None = None


class AddToProductAccount(BaseModel):
    currentStock: int
    averageCost: int
    expirationDate: int | None = None


class SubstractToProductAccount(BaseModel):
    currentStock: int


class ProductAccountInDb(BaseProductAccount):
    createdAt: int
    updatedAt: int | None = None
