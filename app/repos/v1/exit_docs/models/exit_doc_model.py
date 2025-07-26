from datetime import datetime
from pydantic import BaseModel, Field


class ExitItem(BaseModel):
    productId: str
    quantity: int = Field(..., lt=0)


class BaseExitDoc(BaseModel):
    providerId: str
    docNumber: str
    docDate: datetime
    branchId: str
    description: str = ""
    items: list[ExitItem]


class CreateExitDoc(BaseExitDoc):
    pass


class UpdateExitDoc(BaseModel):
    pass


class ExitDocInDb(BaseExitDoc):
    id: str
    createdAt: datetime
