from pydantic import BaseModel, Field
from repos.v1.common.models import UserInfo


class ExitItem(BaseModel):
    productId: str
    productName: str
    cost: int | None = None
    quantity: int = Field(..., lt=0)


class BaseExitDoc(BaseModel):
    clientId: str
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[ExitItem]
    createdBy: UserInfo


class CreateExitDoc(BaseExitDoc):
    pass


class ExitDocInDb(BaseExitDoc):
    id: str
    createdAt: int
