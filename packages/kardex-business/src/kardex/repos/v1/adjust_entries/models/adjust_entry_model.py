from pydantic import BaseModel

from kardex.repos.v1.common.models import UserInfo, EntryItem


class BaseAdjustEntry(BaseModel):
    docNumber: str = ""
    branchId: str
    description: str = ""
    items: list[EntryItem]
    createdBy: UserInfo


class CreateAdjustEntry(BaseAdjustEntry):
    pass


class UpdateAdjustEntry(BaseModel):
    pass


class AdjustEntryInDb(BaseAdjustEntry):
    id: str
    createdAt: int
    updatedAt: int | None = None
