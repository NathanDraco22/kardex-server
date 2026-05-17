from pydantic import BaseModel


class ProductInfo(BaseModel):
    id: str
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    categoryName: str | None = None


class BaseExpirationLog(BaseModel):
    product: ProductInfo
    branchId: str
    lotNumber: str | None = None
    expirationDate: int


class CreateExpirationLog(BaseExpirationLog):
    pass


class UpdateExpirationLog(BaseModel):
    pass


class ExpirationLogInDb(BaseExpirationLog):
    id: str
    createdAt: int
    updatedAt: int | None = None
