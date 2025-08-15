from datetime import datetime
from pydantic import BaseModel, Field


class ExitItem(BaseModel):
    productId: str
    cost: int | None = None
    quantity: int = Field(..., lt=0)


class BaseExitDoc(BaseModel):
    supplierId: str
    docNumber: str
    docDate: datetime
    branchId: str
    description: str = ""
    items: list[ExitItem]


class CreateExitDoc(BaseExitDoc):
    pass


class ExitDocInDb(BaseExitDoc):
    id: str
    createdAt: datetime
