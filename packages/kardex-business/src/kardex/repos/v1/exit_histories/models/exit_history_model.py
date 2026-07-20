from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo, ExitItem


class Client(BaseModel):
    name: str


class BaseExitHistory(BaseModel):
    clientId: str
    client: Client
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[ExitItem]
    createdBy: UserInfo


class ExitHistoryInDb(BaseExitHistory):
    id: str
    createdAt: int
