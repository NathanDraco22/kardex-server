from typing import Literal
from pydantic import BaseModel

from kardex.repos.v1.common.models import (
    SaleItem,
    ClientInfo,
    UserInfo,
)

CreditNoteType = Literal["devolution", "amount"]
CreditNoteStatus = Literal[
    "emitted",
    "open",
    "approved",
    "confirmed",
    "rejected",
    "cancelled",
    "applied",
]


class BaseCreditNote(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    type: CreditNoteType
    docNumber: str = ""
    originalInvoiceId: str = ""
    originalInvoiceDocNumber: str = ""
    returnedItems: list[SaleItem] = []
    amount: int
    description: str = ""
    status: CreditNoteStatus = "emitted"
    createdBy: UserInfo
    approvedBy: UserInfo | None = None
    approvedAt: int | None = None
    rejectedBy: UserInfo | None = None
    rejectedAt: int | None = None
    rejectionReason: str | None = None
    appliedReceiptId: str | None = None
    appliedReceiptDocNumber: str | None = None
    appliedAt: int | None = None
    idempotencyKey: str | None = None


class CreateCreditNote(BaseCreditNote):
    pass


class ApproveCreditNote(BaseModel):
    approvedBy: UserInfo


class RejectCreditNote(BaseModel):
    rejectedBy: UserInfo
    reason: str = ""


class UpdateCreditNote(BaseModel):
    status: CreditNoteStatus | None = None
    approvedBy: UserInfo | None = None
    approvedAt: int | None = None
    rejectedBy: UserInfo | None = None
    rejectedAt: int | None = None
    rejectionReason: str | None = None
    appliedReceiptId: str | None = None
    appliedReceiptDocNumber: str | None = None
    appliedAt: int | None = None


class CreditNoteInDb(BaseCreditNote):
    id: str
    createdAt: int
    updatedAt: int | None = None
