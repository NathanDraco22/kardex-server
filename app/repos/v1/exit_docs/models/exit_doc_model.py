from pydantic import BaseModel, Field
from repos.v1.common.models import UserInfo


class ExitItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int | None = None
    quantity: int = Field(..., lt=0)


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
