from pydantic import BaseModel, Field


class SupplierPayableSummary(BaseModel):
    supplierId: str
    supplierName: str
    totalAmount: int
    totalPaid: int
    pendingAmount: int
    overdueAmount: int
    pendingCount: int
    overdueCount: int
    oldestDueDate: int | None = None


class AccountsPayableSummary(BaseModel):
    totalPending: int = 0
    totalOverdue: int = 0
    suppliersCount: int = 0
    documentsCount: int = 0
    suppliers: list[SupplierPayableSummary] = Field(default_factory=list)
