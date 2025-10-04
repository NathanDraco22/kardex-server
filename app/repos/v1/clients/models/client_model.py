from pydantic import BaseModel


class BaseClient(BaseModel):
    name: str
    cardId: str | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    email: str | None = None
    balance: int = 0
    creditLimit: int = 0
    isCreditActive: bool = False
    isActive: bool = True


class CreateClient(BaseClient):
    pass


class UpdateClient(BaseModel):
    name: str | None = None
    cardId: str | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    email: str | None = None
    isActive: bool | None = None
    isCreditActive: bool | None = None
    creditLimit: int | None = None


class ClientInDb(BaseClient):
    id: str
    isDeleted: bool = False
    isInternal: bool = False
    createdAt: int
    updatedAt: int | None = None
