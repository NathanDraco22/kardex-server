from datetime import datetime
from pydantic import BaseModel


class BaseClientAccount(BaseModel):
    clientId: str
    balance: int = 0


class CreateClientAccount(BaseClientAccount):
    pass


class UpdateClientAccount(BaseModel):
    pass


class ClientAccountInDb(BaseClientAccount):
    createdAt: datetime
    updatedAt: datetime | None = None
