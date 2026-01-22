from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_sale_profiles import ProductSaleProfileInDb

from pydantic import BaseModel


class BaseProduct(BaseModel):
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str]
    hasIva: bool = False
    isActive: bool = True


class CreateProduct(BaseProduct):
    pass


class UpdateProduct(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    categoryName: str | None = None
    tags: list[str] | None = None
    isActive: bool | None = None


class ProductInDb(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None


class ProductInDbWithAccounts(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None
    accounts: list[ProductAccountInDb]


class ProductInDbInBranch(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None
    account: ProductAccountInDb
    saleProfile: ProductSaleProfileInDb
