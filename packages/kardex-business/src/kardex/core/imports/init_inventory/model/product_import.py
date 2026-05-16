from pydantic import BaseModel


class ProductImport(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str] = []
    hasIva: bool = False
    isActive: bool = True
    quantity: int
    cost: int
    price: int
    price2: int = 0
    price3: int = 0
