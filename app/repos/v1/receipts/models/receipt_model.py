from typing import Literal
from pydantic import BaseModel


PaymentMethod = Literal[
    "CASH",
    "TRANSFER",
    "CREDIT_CARD",
    "DEBIT_CARD",
    "CHECK",
    "OTHER",
]


class AppliedInvoice(BaseModel):
    invoiceId: str
    amountApplied: int


class BaseReceipt(BaseModel):
    branchId: str
    clientId: str
    docNumber: str
    appliedInvoices: list[AppliedInvoice]
    paymentMethod: PaymentMethod
    total: int


class CreateReceipt(BaseReceipt):
    pass


class UpdateReceipt(BaseModel):
    pass


class ReceiptInDb(BaseReceipt):
    id: str
    created_at: str
    updated_at: str
