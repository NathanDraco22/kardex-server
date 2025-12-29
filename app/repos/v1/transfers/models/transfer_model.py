from typing import Literal
from pydantic import BaseModel
from repos.v1.common.models import TransferItem, UserInfo

TransferStatus = Literal["inTransit", "received", "cancelled"]


class BaseTransfer(BaseModel):
    origin: str
    destination: str
    docNumber: str = ""
    description: str = ""
    status: TransferStatus
    items: list[TransferItem]
    createdBy: UserInfo
    receivedBy: UserInfo | None = None
    receivedAt: int | None = None
    cancelledBy: UserInfo | None = None
    cancelledAt: int | None = None


class CreateTransfer(BaseTransfer):
    pass


class UpdateTransfer(BaseModel):
    pass


class ReceiveTransferIntent(BaseModel):
    receivedAt: int
    receivedBy: UserInfo
    status: TransferStatus = "received"


class CancelTransferIntent(BaseModel):
    cancelledAt: int
    cancelledBy: UserInfo
    status: TransferStatus = "cancelled"


class TransferInDb(BaseTransfer):
    id: str
    createdAt: int
    updatedAt: int | None = None
