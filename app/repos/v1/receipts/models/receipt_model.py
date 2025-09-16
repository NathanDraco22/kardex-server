from typing import Literal
from pydantic import BaseModel
from datetime import datetime

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
    docNumber: str = ""
    appliedInvoices: list[AppliedInvoice]
    paymentMethod: PaymentMethod
    bankReference: str = ""
    total: int


class CreateReceipt(BaseReceipt):
    pass


class UpdateReceipt(BaseModel):
    pass


class ReceiptInDb(BaseReceipt):
    id: str
    createdAt: datetime
    updatedAt: datetime | None = None
