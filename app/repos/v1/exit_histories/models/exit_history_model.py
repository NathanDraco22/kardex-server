from datetime import datetime
from pydantic import BaseModel


class Client(BaseModel):
    name: str


class BaseExitHistory(BaseModel):
    clientId: str
    client: Client
    docNumber: str
    docDate: datetime
    branchId: str
    description: str = ""


class ExitHistoryInDb(BaseExitHistory):
    id: str
    createdAt: datetime
