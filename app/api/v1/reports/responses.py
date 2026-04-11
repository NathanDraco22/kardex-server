from pydantic import BaseModel
from repos.v1.invoices.models.invoice_totals_model import InvoiceTotals
from repos.v1.receipts.models.receipt_total import ReceiptTotal


class TotalsResult(BaseModel):
    branchId: str
    receipts: list[ReceiptTotal]
    invoices: list[InvoiceTotals]
