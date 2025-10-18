from pydantic import BaseModel


class Supplier(BaseModel):
    name: str


class EntryItem(BaseModel):
    productId: str
    productName: str
    cost: int
    quantity: int


class BaseEntryHistory(BaseModel):
    supplierId: str
    supplier: Supplier
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[EntryItem]


class EntryHistoryInDb(BaseEntryHistory):
    id: str
    createdAt: int
