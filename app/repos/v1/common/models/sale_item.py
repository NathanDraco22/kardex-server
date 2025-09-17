from typing import Literal
from pydantic import BaseModel

PaymentType = Literal["cash", "credit"]


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
    subTotal: int
    discount: int = 0
    iva: int = 0
    total: int
