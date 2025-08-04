from datetime import datetime
from pydantic import BaseModel


class BaseUnit(BaseModel):
    name: str
    pass


class CreateUnit(BaseUnit):
    pass


class UpdateUnit(BaseModel):
    name: str | None = None
    pass


class UnitInDb(BaseUnit):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
