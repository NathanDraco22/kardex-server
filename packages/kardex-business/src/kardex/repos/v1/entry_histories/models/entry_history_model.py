from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo, EntryItem


class Supplier(BaseModel):
    name: str


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
