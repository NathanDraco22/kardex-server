from pydantic import BaseModel


class PendingInvoiceTotalsByBranch(BaseModel):
    branchId: str
    total: int
    totalCost: int
    amountPaid: int
    totalOwed: int
    count: int
