from pydantic import BaseModel, Field


class ExitItem(BaseModel):
    productId: str
    cost: int | None = None
    quantity: int = Field(..., lt=0)


class BaseExitDoc(BaseModel):
    clientId: str
    docNumber: str
    docDate: int
    branchId: str
    description: str = ""
    items: list[ExitItem]


class CreateExitDoc(BaseExitDoc):
    pass


class ExitDocInDb(BaseExitDoc):
    id: str
    createdAt: int
