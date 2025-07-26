from datetime import datetime
from pydantic import BaseModel


class BaseAccount(BaseModel):
    name: str
    isActive: bool = True


class CreateAccount(BaseAccount):
    pass


class UpdateAccount(BaseModel):
    name: str | None = None
    isActive: bool | None = None


class AccountInDb(BaseAccount):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
