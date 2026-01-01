from pydantic import BaseModel
from repos.v1.common.models import UserInfo, EntryItem


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
