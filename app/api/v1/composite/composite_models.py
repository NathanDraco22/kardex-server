from pydantic import BaseModel

from kardex.repos.v1.credit_notes import CreditNoteInDb
from kardex.repos.v1.devolutions import DevolutionInDb
from kardex.repos.v1.invoices import InvoiceInDb


class PendingCheckoutSummary(BaseModel):
    totalInvoices: int
    totalDevolutions: int
    totalCreditNotes: int
    netTotalPayable: int


class ClientPendingInvoicesCompositeResponse(BaseModel):
    invoices: list[InvoiceInDb]
    devolutions: list[DevolutionInDb]
    creditNotes: list[CreditNoteInDb]
    summary: PendingCheckoutSummary
