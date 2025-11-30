from pydantic import BaseModel
from typing import Literal

from repos.v1.common.models import (
    SaleItem,
    ClientInfo,
    UserInfo,
)

DevolutionStatus = Literal["open", "confirmed", "cancelled", "applied"]


class BaseDevolution(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    docNumber: str = ""
    originalInvoiceId: str = ""
    originalInvoiceDocNumber: str = ""
    returnedItems: list[SaleItem]
    description: str
    status: DevolutionStatus = "open"
    totalCost: int
    total: int
    createdBy: UserInfo


class CreateDevolution(BaseDevolution):
    pass


class UpdateDevolution(BaseModel):
    status: DevolutionStatus | None = None
    pass


class DevolutionInDb(BaseDevolution):
    id: str
    createdAt: int
    updatedAt: int | None = None
