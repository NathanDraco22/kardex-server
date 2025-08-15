from datetime import datetime
from pydantic import BaseModel, Field


class EntryItem(BaseModel):
    productId: str
    cost: int
    quantity: int = Field(..., gt=0)


class BaseEntryDoc(BaseModel):
    supplierId: str
    docNumber: str
    docDate: datetime
    branchId: str
    description: str = ""
    items: list[EntryItem]


class CreateEntryDoc(BaseEntryDoc):
    pass


class EntryDocInDb(BaseEntryDoc):
    id: str
    createdAt: datetime
