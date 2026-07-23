from pydantic import BaseModel, Field


class ExitItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int | None = None
    quantity: int = Field(..., lt=0)
    conversionFactor: int = 1
