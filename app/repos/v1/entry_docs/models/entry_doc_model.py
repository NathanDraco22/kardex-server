from pydantic import BaseModel
from repos.v1.common.models import UserInfo, EntryItem


class Supplier(BaseModel):
    name: str


class BaseEntryDoc(BaseModel):
    supplierId: str
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[EntryItem]
    createdBy: UserInfo


class BaseEntryHistory(BaseEntryDoc):
    supplier: Supplier


class CreateEntryDoc(BaseEntryDoc):
    pass


class EntryDocInDb(BaseEntryDoc):
    id: str
    createdAt: int


class EntryHistoryInDb(BaseEntryHistory):
    id: str
    createdAt: int
