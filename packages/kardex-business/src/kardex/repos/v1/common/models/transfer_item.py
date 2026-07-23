from pydantic import BaseModel


class TransferItem(BaseModel):
    id: str
    name: str
    unitName: str
    brandName: str
    code: str | None = None
    categoryName: str | None = None
    quantity: int
    cost: int
    conversionFactor: int = 1
    expirationDate: int | None = None
    salePrice: int = 0
    salePrice2: int = 0
    salePrice3: int = 0
    salePrice4: int = 0
