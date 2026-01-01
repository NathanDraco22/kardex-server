from pydantic import BaseModel, Field


class EntryItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int
    quantity: int = Field(..., gt=0)
    expirationDate: int | None = None
