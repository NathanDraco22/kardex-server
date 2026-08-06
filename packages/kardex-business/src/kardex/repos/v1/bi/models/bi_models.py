from datetime import datetime, timezone
from pydantic import BaseModel


def timestamp_to_iso(ts: int | float | None) -> str:
    if ts is None or ts == 0:
        return ""
    if ts > 10_000_000_000:
        ts = ts / 1000.0
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp_to_date_id(ts: int | float | None) -> str:
    if ts is None or ts == 0:
        return ""
    if ts > 10_000_000_000:
        ts = ts / 1000.0
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")


class BIVentaItem(BaseModel):
    invoiceId: str
    invoiceDocNumber: str
    fechaISO: str
    dateId: str
    branchId: str
    branchName: str
    clientId: str
    clientName: str
    paymentType: str
    subtotal: float
    tax: float
    discount: float
    total: float
    status: str


class BIDetalleVentaItem(BaseModel):
    invoiceId: str
    invoiceDocNumber: str
    fechaISO: str
    branchName: str
    productId: str
    productCode: str
    productName: str
    categoryName: str
    quantity: float
    unitPrice: float
    unitCost: float
    totalSales: float
    totalCost: float
    grossProfit: float


class BIFlujoCajaItem(BaseModel):
    movementId: str
    type: str
    receiptDocNumber: str = ""
    expenseDocNumber: str = ""
    fechaISO: str
    dateId: str
    branchName: str
    clientName: str
    category: str
    income: float
    expense: float
    paymentMethod: str


class BIInventarioItem(BaseModel):
    productId: str
    productCode: str
    productName: str
    categoryName: str
    branchId: str
    branchName: str
    currentStock: float
    averageCost: float
    totalInventoryValue: float


class BIClienteItem(BaseModel):
    clientId: str
    clientName: str
    phone: str
    currentDebt: float
    totalPurchasesCount: int
    hasOverdueBalance: bool
