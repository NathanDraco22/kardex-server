from typing import Literal
from pydantic import BaseModel
from repos.v1.common.models import ClientInfo, UserInfo

PaymentMethod = Literal[
    "cash",
    "transfer",
    "card",
    "check",
    "other",
]


class AppliedInvoice(BaseModel):
    invoiceId: str
    amountApplied: int


class BaseReceipt(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    docNumber: str = ""
    appliedInvoices: list[AppliedInvoice]
    paymentMethod: PaymentMethod
    bankReference: str = ""
    total: int
    createdBy: UserInfo


class CreateReceipt(BaseReceipt):
    pass


class UpdateReceipt(BaseModel):
    pass


class ReceiptInDb(BaseReceipt):
    id: str
    createdAt: int
    updatedAt: int | None = None
