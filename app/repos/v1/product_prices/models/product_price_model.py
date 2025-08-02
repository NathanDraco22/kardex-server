from datetime import datetime
from pydantic import BaseModel


class BaseProductPrice(BaseModel):
    name: str
    pass


class CreateProductPrice(BaseProductPrice):
    pass


class UpdateProductPrice(BaseModel):
    name: str | None = None


class ProductPriceInDb(BaseProductPrice):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
