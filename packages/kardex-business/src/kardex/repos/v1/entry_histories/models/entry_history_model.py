from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo


class Supplier(BaseModel):
    name: str


class EntryItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    cost: int
    quantity: int
    expirationDate: int | None = None


class BaseEntryHistory(BaseModel):
    supplierId: str
    supplier: Supplier
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[EntryItem]
    createdBy: UserInfo


class EntryHistoryInDb(BaseEntryHistory):
    id: str
    createdAt: int
