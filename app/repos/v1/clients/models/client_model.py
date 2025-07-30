from datetime import datetime
from pydantic import BaseModel


class BaseClient(BaseModel):
    name: str
    cardId: str
    phone: str
    isActive: bool


class CreateClient(BaseClient):
    pass


class UpdateClient(BaseModel):
    name: str | None = None
    cardId: str | None = None
    phone: str | None = None
    isActive: bool | None = None


class ClientInDb(BaseClient):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
