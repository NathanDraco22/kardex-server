from pydantic import BaseModel


class ClientImport(BaseModel):
    name: str
    cardId: str | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    email: str | None = None
    group: str | None = None
    creditLimit: int = 0
    initialBalance: int = 0
