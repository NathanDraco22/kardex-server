from typing import Literal

from pydantic import BaseModel, Field

from kardex.repos.v1.common.models import ClientInfo, PaymentType, UserInfo
from kardex.repos.v1.invoices.models.invoice_model import InvoiceStatus

InvoiceCancellationRequestStatus = Literal[
    "pending", "approved", "rejected", "cancelled"
]


class BaseInvoiceCancellationRequest(BaseModel):
    docNumber: str = ""
    branchId: str
    invoiceId: str
    invoiceDocNumber: str
    invoiceTotal: int
    invoicePaymentType: PaymentType
    invoiceStatus: InvoiceStatus
    invoiceShiftId: str | None = None
    clientId: str
    clientInfo: ClientInfo
    reason: str = Field(min_length=3)
    requestedBy: UserInfo


class CreateInvoiceCancellationRequest(BaseModel):
    invoiceId: str
    reason: str = Field(min_length=3)
    requestedBy: UserInfo


class ApproveInvoiceCancellationRequest(BaseModel):
    reviewedBy: UserInfo
    reviewNotes: str = ""


class RejectInvoiceCancellationRequest(BaseModel):
    reviewedBy: UserInfo
    reviewNotes: str = Field(min_length=3)


class CancelInvoiceCancellationRequest(BaseModel):
    cancelledBy: UserInfo


class InvoiceCancellationRequestInDb(BaseInvoiceCancellationRequest):
    id: str
    status: InvoiceCancellationRequestStatus = "pending"
    createdAt: int
    updatedAt: int | None = None
    reviewedBy: UserInfo | None = None
    reviewedAt: int | None = None
    reviewNotes: str | None = None
