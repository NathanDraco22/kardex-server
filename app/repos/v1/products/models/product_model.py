from datetime import datetime
from pydantic import BaseModel


class BaseProduct(BaseModel):
    name: str


class CreateProduct(BaseProduct):
    pass


class UpdateProduct(BaseModel):
    name: str | None = None


class ProductInDb(BaseProduct):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
