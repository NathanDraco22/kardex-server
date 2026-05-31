from pydantic import BaseModel


class BaseSupplier(BaseModel):
    name: str
    creditDays: int = 0
    cardId: str | None = None
    email: str | None = None
    phone: str | None = None
    isActive: bool = True


class CreateSupplier(BaseSupplier):
    pass


class UpdateSupplier(BaseModel):
    name: str | None = None
    cardId: str | None = None
    email: str | None = None
    phone: str | None = None
    isActive: bool | None = None


class SupplierInDb(BaseSupplier):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None
