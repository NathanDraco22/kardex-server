from typing import Literal
from pydantic import BaseModel, Field

PaymentType = Literal["cash", "credit", "transfer", "card", "check", "other"]
ProductType = Literal["item", "nonInventory", "service"]
DiscountType = Literal["percentage", "amount"]


class ProductItem(BaseModel):
    id: str
    name: str
    unitName: str
    brandName: str = ""
    code: str | None = None
    categoryName: str | None = None
    tags: list[str] = []
    productType: ProductType = "item"
    priceUnitFactor: int = Field(default=1, ge=1)


class SaleItem(BaseModel):
    product: ProductItem
    selectedPrice: int = 1
    quantity: int
    bonQuantity: int = 0
    cost: int
    price: int
    subTotal: int
    discountType: DiscountType | None = None
    discountPercentage: int = 0
    totalDiscount: int = 0
    iva: int = 0
    total: int
    conversionFactor: int = 1
    priceUnitFactor: int = Field(default=1, ge=1)
    invoiceItemIndex: int | None = None
    selectedUnitName: str | None = None
    standardUnitName: str | None = None
    standardUnitFactor: int | None = None
