from pydantic import BaseModel, Field


class BaseProductAccount(BaseModel):
    productId: str
    branchId: str
    currentStock: int
    promiseStock: int = 0
    averageCost: int
    lastCost: int
    maximumCost: int = 0


class UpdateProductAccount(BaseModel):
    currentStock: int | None = Field(default=None, ge=0)
    averageCost: int | None = Field(default=None, ge=0)


class AddToProductAccount(BaseModel):
    currentStock: int = Field(ge=0)
    averageCost: int = Field(ge=0)
    expirationDate: int | None = None


class SubstractToProductAccount(BaseModel):
    currentStock: int = Field(ge=0)


class ProductAccountInDb(BaseProductAccount):
    createdAt: int
    updatedAt: int | None = None
