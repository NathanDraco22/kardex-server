from pydantic import BaseModel


class BranchPortfolioSummary(BaseModel):
    branchId: str
    totalSales: int
    totalCost: int
    totalPaid: int
    totalOwed: int
    creditSales: int
    cashSales: int
    totalInvoices: int
