from pydantic import BaseModel, Field


class EntryItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int
    quantity: int
    conversionFactor: int = 1
    priceUnitFactor: int = Field(default=1, ge=1)
    standardUnitName: str | None = None
    standardUnitFactor: int | None = None
    expirationDate: int | None = None
