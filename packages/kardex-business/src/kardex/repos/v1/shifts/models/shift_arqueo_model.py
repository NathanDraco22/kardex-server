from typing import Literal

from pydantic import BaseModel

from kardex.repos.v1.shift_cash_movements import ShiftCashMovementInDb

from .shift_model import ShiftInDb


class ShiftArqueoDocument(BaseModel):
    id: str
    docNumber: str
    amount: int
    paymentMethod: str | None = None
    bankReference: str | None = None
    status: str | None = None
    type: str | None = None
    clientName: str | None = None
    createdAt: int
    referenceDocNumber: str | None = None
    cancellationReason: str | None = None
    counted: bool


class ShiftArqueoTotals(BaseModel):
    invoiceCashTotal: int = 0
    invoiceTransferTotal: int = 0
    invoiceCardTotal: int = 0
    invoiceOtherTotal: int = 0
    invoiceCashSalesTotal: int = 0
    invoiceCreditTotal: int = 0
    invoiceTotal: int = 0
    invoiceCount: int = 0
    cancelledInvoiceCashTotal: int = 0
    cancelledInvoiceTransferTotal: int = 0
    cancelledInvoiceCardTotal: int = 0
    cancelledInvoiceOtherTotal: int = 0
    cancelledInvoiceCashSalesTotal: int = 0
    cancelledInvoiceCreditTotal: int = 0
    cancelledInvoiceTotal: int = 0
    cancelledInvoiceCount: int = 0
    receiptCashTotal: int = 0
    receiptTransferTotal: int = 0
    receiptCardTotal: int = 0
    receiptOtherTotal: int = 0
    receiptTotal: int = 0
    receiptCount: int = 0
    cancelledReceiptTotal: int = 0
    cancelledReceiptCount: int = 0
    devolutionTotal: int = 0
    devolutionCount: int = 0
    creditNoteTotal: int = 0
    creditNoteCount: int = 0
    cashInTotal: int = 0
    cashOutTotal: int = 0
    expectedCash: int = 0
    totalTransfers: int = 0
    totalCardsAndOthers: int = 0
    grandTotal: int = 0


class ShiftArqueoMeta(BaseModel):
    totalsSource: Literal["live", "stored"]
    documentsLimit: int
    # `None` = no se solicitaron documentos; `false` = se devolvieron completos.
    truncated: bool | None = None


class ShiftArqueoResponse(BaseModel):
    shift: ShiftInDb
    totals: ShiftArqueoTotals
    cashMovements: list[ShiftCashMovementInDb]
    invoices: list[ShiftArqueoDocument]
    receipts: list[ShiftArqueoDocument]
    devolutions: list[ShiftArqueoDocument]
    creditNotes: list[ShiftArqueoDocument]
    meta: ShiftArqueoMeta
