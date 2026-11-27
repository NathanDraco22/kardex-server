from typing import Literal

from pydantic import BaseModel, Field

from kardex.repos.v1.common.models import UserInfo

ShiftStatus = Literal["open", "closed"]


class BaseShift(BaseModel):
    branchId: str
    branchName: str = ""
    docNumber: str = ""
    status: ShiftStatus = "open"
    initialCash: int = Field(default=0, ge=0)
    openingNotes: str = ""
    openedBy: UserInfo
    openedAt: int

    # --- Consolidado de Facturas (al cerrar) ---
    invoiceCashTotal: int = 0
    invoiceTransferTotal: int = 0
    invoiceCardTotal: int = 0
    invoiceOtherTotal: int = 0
    invoiceCashSalesTotal: int = 0
    invoiceCreditTotal: int = 0
    invoiceTotal: int = 0
    invoiceCount: int = 0

    # --- Consolidado de Facturas Anuladas ---
    cancelledInvoiceCashTotal: int = 0
    cancelledInvoiceTransferTotal: int = 0
    cancelledInvoiceCardTotal: int = 0
    cancelledInvoiceOtherTotal: int = 0
    cancelledInvoiceCashSalesTotal: int = 0
    cancelledInvoiceCreditTotal: int = 0
    cancelledInvoiceTotal: int = 0
    cancelledInvoiceCount: int = 0

    # --- Consolidado de Recibos / Abonos (al cerrar) ---
    receiptCashTotal: int = 0
    receiptTransferTotal: int = 0
    receiptCardTotal: int = 0
    receiptOtherTotal: int = 0
    receiptTotal: int = 0
    receiptCount: int = 0
    cancelledReceiptTotal: int = 0
    cancelledReceiptCount: int = 0

    # --- Consolidado de Devoluciones y Notas de Crédito ---
    devolutionTotal: int = 0
    devolutionCount: int = 0
    creditNoteTotal: int = 0
    creditNoteCount: int = 0

    # --- Consolidado de Movimientos Manuales de Caja ---
    cashInTotal: int = 0
    cashOutTotal: int = 0

    # --- Totales Consolidados y Arqueo ---
    expectedCash: int = 0
    countedCash: int = Field(default=0, ge=0)
    cashDifference: int = 0
    totalTransfers: int = 0
    totalCardsAndOthers: int = 0
    grandTotal: int = 0

    # --- Auditoría de Cierre ---
    closingNotes: str = ""


class CreateShift(BaseModel):
    branchId: str
    branchName: str = ""
    initialCash: int = Field(default=0, ge=0)
    openingNotes: str = ""
    openedBy: UserInfo


class CloseShiftRequest(BaseModel):
    countedCash: int = Field(ge=0)
    closingNotes: str = ""
    closedBy: UserInfo


class UpdateShift(BaseModel):
    openingNotes: str | None = None
    closingNotes: str | None = None


class ShiftInDb(BaseShift):
    id: str
    createdAt: int
    updatedAt: int | None = None
    closedBy: UserInfo | None = None
    closedAt: int | None = None


class ShiftPreview(BaseShift):
    """Consolidado en vivo del turno.

    Hereda `countedCash`, `cashDifference` y `closingNotes` (quedan en cero /
    vacios mientras el turno esta abierto) y excluye `closedBy`/`closedAt` para
    no invitar a persistir el preview como si fuera un cierre.
    """

    id: str
