from pydantic import BaseModel


class ClientInfo(BaseModel):
    name: str
    cardId: str | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    email: str | None = None
