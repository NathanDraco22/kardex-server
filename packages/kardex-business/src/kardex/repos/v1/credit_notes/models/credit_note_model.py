from typing import Literal
from pydantic import BaseModel

from kardex.repos.v1.common.models import (
    SaleItem,
    ClientInfo,
    UserInfo,
)

CreditNoteType = Literal["devolution", "amount"]
CreditNoteStatus = Literal["open", "confirmed", "cancelled", "applied"]


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
    status: CreditNoteStatus = "confirmed"
    createdBy: UserInfo
    appliedReceiptId: str | None = None
    appliedReceiptDocNumber: str | None = None
    appliedAt: int | None = None
    idempotencyKey: str | None = None


class CreateCreditNote(BaseCreditNote):
    pass


class UpdateCreditNote(BaseModel):
    status: CreditNoteStatus | None = None
    appliedReceiptId: str | None = None
    appliedReceiptDocNumber: str | None = None
    appliedAt: int | None = None


class CreditNoteInDb(BaseCreditNote):
    id: str
    createdAt: int
    updatedAt: int | None = None
