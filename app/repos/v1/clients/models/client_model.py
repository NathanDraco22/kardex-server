from datetime import datetime
from pydantic import BaseModel


class BaseClient(BaseModel):
    name: str
    cardId: str | None = None
    phone: str | None = None
    isActive: bool = True


class CreateClient(BaseClient):
    pass


class UpdateClient(BaseModel):
    name: str | None = None
    cardId: str | None = None
    phone: str | None = None
    isActive: bool | None = None


class ClientInDb(BaseClient):
    id: str
    isDeleted: bool = False
    createdAt: datetime
    updatedAt: datetime | None = None
