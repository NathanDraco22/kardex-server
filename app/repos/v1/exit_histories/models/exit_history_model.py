from datetime import datetime
from pydantic import BaseModel


class ExitItem(BaseModel):
    productId: str
    cost: int | None = None
    quantity: int


class Client(BaseModel):
    name: str


class BaseExitHistory(BaseModel):
    clientId: str
    client: Client
    docNumber: str
    docDate: datetime
    branchId: str
    description: str = ""
    items: list[ExitItem]


class ExitHistoryInDb(BaseExitHistory):
    id: str
    createdAt: datetime
