from datetime import datetime
from pydantic import BaseModel


class BaseSupplier(BaseModel):
    name: str


class CreateSupplier(BaseSupplier):
    pass


class UpdateSupplier(BaseModel):
    name: str | None = None


class SupplierInDb(BaseSupplier):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
