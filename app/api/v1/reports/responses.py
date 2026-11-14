from pydantic import BaseModel
from kardex.repos.v1.invoices.models.invoice_totals_model import InvoiceTotals
from kardex.repos.v1.receipts.models.receipt_total import ReceiptTotal
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.receipts import ReceiptInDb
from kardex.repos.v1.expenses import ExpenseTotals


class TotalsResult(BaseModel):
    branchId: str
    receipts: list[ReceiptTotal]
    detailReceipts: list[ReceiptInDb]
    invoices: list[InvoiceTotals]
    detailInvoices: list[InvoiceInDb]
    expenses: ExpenseTotals | None = None


class DetailsResult(BaseModel):
    branchId: str
    receipts: list[ReceiptInDb]
    invoices: list[InvoiceInDb]
