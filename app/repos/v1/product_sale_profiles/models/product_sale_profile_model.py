from pydantic import BaseModel, Field


class InventoryProduct(BaseModel):
    id: str
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str]
    isActive: bool = True


class ProductAccount(BaseModel):
    currentStock: int
    averageCost: int
    lastCost: int


class Discount(BaseModel):
    name: str
    percentValue: int = Field(..., ge=0, le=100)
    autoApply: bool = False
    isActive: bool


class BaseProductSaleProfile(BaseModel):
    branchId: str
    productId: str
    salePrice: int
    discounts: list[Discount] = []


class CreateProductSaleProfile(BaseProductSaleProfile):
    pass


class UpdateProductSaleProfile(BaseModel):
    salePrice: int | None = None
    discounts: list[Discount] | None = None


class ProductSaleProfileInDb(BaseProductSaleProfile):
    updatedAt: int | None = None


class ProductSaleProfileInDbWithProduct(BaseProductSaleProfile):
    updated_at: int | None = None
    product: InventoryProduct
    account: ProductAccount
