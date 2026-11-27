from typing import Literal

from pydantic import BaseModel, Field

from kardex.repos.v1.common.models import ClientInfo, UserInfo
from kardex.repos.v1.receipts.models.receipt_model import PaymentMethod

ReceiptCancellationRequestStatus = Literal[
    "pending", "approved", "rejected", "cancelled"
]


class BaseReceiptCancellationRequest(BaseModel):
    docNumber: str = ""
    branchId: str
    receiptId: str
    receiptDocNumber: str
    receiptTotal: int
    receiptPaymentMethod: PaymentMethod
    receiptShiftId: str | None = None
    clientId: str
    clientInfo: ClientInfo
    reason: str = Field(min_length=3)
    requestedBy: UserInfo


class CreateReceiptCancellationRequest(BaseModel):
    receiptId: str
    reason: str = Field(min_length=3)
    requestedBy: UserInfo


class ApproveReceiptCancellationRequest(BaseModel):
    reviewedBy: UserInfo
    reviewNotes: str = ""


class RejectReceiptCancellationRequest(BaseModel):
    reviewedBy: UserInfo
    reviewNotes: str = Field(min_length=3)


class CancelReceiptCancellationRequest(BaseModel):
    cancelledBy: UserInfo


class ReceiptCancellationRequestInDb(BaseReceiptCancellationRequest):
    id: str
    status: ReceiptCancellationRequestStatus = "pending"
    createdAt: int
    updatedAt: int | None = None
    reviewedBy: UserInfo | None = None
    reviewedAt: int | None = None
    reviewNotes: str | None = None
