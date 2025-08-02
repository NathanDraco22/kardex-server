from datetime import datetime
from pydantic import BaseModel


class BaseProductCategory(BaseModel):
    name: str
    pass


class CreateProductCategory(BaseProductCategory):
    pass


class UpdateProductCategory(BaseModel):
    name: str | None = None


class ProductCategoryInDb(BaseProductCategory):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
