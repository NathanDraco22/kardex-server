from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo


class ExitItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int | None = None
    quantity: int


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
