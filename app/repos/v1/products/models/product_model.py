from repos.v1.product_accounts import ProductAccountInDb
from datetime import datetime
from pydantic import BaseModel


class BaseProduct(BaseModel):
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str]
    isActive: bool = True


class CreateProduct(BaseProduct):
    pass


class UpdateProduct(BaseModel):
    name: str | None = None
    description: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    categoryName: str | None = None
    tags: list[str] | None = None
    isActive: bool | None = None


class ProductInDb(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: datetime
    updatedAt: datetime | None = None


class ProductInDbWithAccounts(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: datetime
    updatedAt: datetime | None = None
    accounts: list[ProductAccountInDb]
