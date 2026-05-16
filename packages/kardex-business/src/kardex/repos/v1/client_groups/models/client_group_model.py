from pydantic import BaseModel


class BaseClientGroup(BaseModel):
    name: str
    description: str = ""


class CreateClientGroup(BaseClientGroup):
    pass


class UpdateClientGroup(BaseModel):
    name: str | None = None
    description: str | None = None
    pass


class ClientGroupInDb(BaseClientGroup):
    id: str
    createdAt: int
    updatedAt: int | None = None
