from pydantic import BaseModel
from repos.v1.invoices.models.invoice_totals_model import InvoiceTotals
from repos.v1.receipts.models.receipt_total import ReceiptTotal

from repos.v1.invoices import InvoiceInDb
from repos.v1.receipts import ReceiptInDb


class TotalsResult(BaseModel):
    branchId: str
    receipts: list[ReceiptTotal]
    detailReceipts: list[ReceiptInDb]
    invoices: list[InvoiceTotals]
    detailInvoices: list[InvoiceInDb]


class DetailsResult(BaseModel):
    branchId: str
    receipts: list[ReceiptInDb]
    invoices: list[InvoiceInDb]
