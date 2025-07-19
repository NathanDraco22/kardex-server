from pydantic import BaseModel


class BaseProduct(BaseModel):
    sku: str
    name: str
    description: str | None = None


class CreateProduct(BaseProduct):
    pass


class UpdateProduct(BaseModel):
    sku: str | None = None
    name: str | None = None
    description: str | None = None


class ProductInDb(BaseProduct):
    id: str
    created_at: int
    updated_at: int | None = None

    class Config:
        populate_by_name = True
