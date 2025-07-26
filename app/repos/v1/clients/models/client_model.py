from datetime import datetime
from pydantic import BaseModel


class BaseClient(BaseModel):
    name: str


class CreateClient(BaseClient):
    pass


class UpdateClient(BaseModel):
    name: str | None = None


class ClientInDb(BaseClient):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
