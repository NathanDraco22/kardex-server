from datetime import datetime
from pydantic import BaseModel


class ProductItem(BaseModel):
    id: str
    name: str
    unitName: str
    brandName: str
    code: str | None = None
    categoryName: str | None = None
    tags: list[str] = []


class SaleItem(BaseModel):
    product: ProductItem
    quantity: int
    bonQuantity: int = 0
    cost: int
    price: int
    priceName: str
    discount: int = 0


class BaseSale(BaseModel):
    branchId: str
    saleItems: list[SaleItem]
    description: str = ""
    totalCost: int
    total: int


class CreateSale(BaseSale):
    pass


class UpdateSale(BaseModel):
    pass


class SaleInDb(BaseSale):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
