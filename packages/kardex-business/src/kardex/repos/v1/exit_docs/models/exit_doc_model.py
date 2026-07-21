from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo, ExitItem


class Client(BaseModel):
    name: str


class BaseExitDoc(BaseModel):
    clientId: str
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[ExitItem]
    createdBy: UserInfo


class BaseExitHistory(BaseExitDoc):
    client: Client


class CreateExitDoc(BaseExitDoc):
    pass


class ExitDocInDb(BaseExitDoc):
    id: str
    createdAt: int


class ExitHistoryInDb(BaseExitHistory):
    id: str
    createdAt: int
