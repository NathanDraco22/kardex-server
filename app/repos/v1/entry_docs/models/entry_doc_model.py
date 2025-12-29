from pydantic import BaseModel, Field
from repos.v1.common.models import UserInfo


class EntryItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int
    quantity: int = Field(..., gt=0)
    expirationDate: int | None = None


class BaseEntryDoc(BaseModel):
    supplierId: str
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[EntryItem]
    createdBy: UserInfo


class CreateEntryDoc(BaseEntryDoc):
    pass


class EntryDocInDb(BaseEntryDoc):
    id: str
    createdAt: int
