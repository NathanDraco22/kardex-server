from datetime import datetime
from pydantic import BaseModel


class Supplier(BaseModel):
    name: str


class BaseEntryHistory(BaseModel):
    supplierId: str
    supplier: Supplier
    docNumber: str
    docDate: datetime
    branchId: str
    description: str = ""


class EntryHistoryInDb(BaseEntryHistory):
    id: str
    createdAt: datetime
