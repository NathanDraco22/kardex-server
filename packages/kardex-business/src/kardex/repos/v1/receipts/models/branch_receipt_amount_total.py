from pydantic import BaseModel


class BranchAppliedReceiptsAmountsSummary(BaseModel):
    branchId: str
    totalAppliedInvoices: int
    totalAppliedDevolutions: int
    totalReceipts: int
    receiptCount: int
