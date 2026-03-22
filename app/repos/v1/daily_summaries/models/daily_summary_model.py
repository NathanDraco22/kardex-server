from pydantic import BaseModel

from repos.v1.common.models import CommercialBranchDetail


class BaseDailySummary(BaseModel):
    dateId: str
    startDate: int
    endDate: int
    total: int
    totalCost: int
    totalPaid: int = 0
    totalOwed: int = 0
    creditSales: int = 0
    cashSales: int = 0
    totalInvoices: int = 0
    totalReceiptCash: int = 0
    totalReceiptDevolutions: int = 0
    totalReceipts: int = 0
    receiptCount: int = 0
    branches: list[CommercialBranchDetail]

    def __add__(self, other: "BaseDailySummary") -> "BaseDailySummary":
        if self.dateId == other.dateId:
            raise ValueError("No se pueden sumar diarios iguales")

        branches_map = {b.branchId: b for b in self.branches}

        for other_branch in other.branches:
            if other_branch.branchId in branches_map:
                branches_map[other_branch.branchId] += other_branch
            else:
                branches_map[other_branch.branchId] = other_branch

        startDate = min(self.startDate, other.startDate)
        endDate = max(self.endDate, other.endDate)

        return BaseDailySummary(
            dateId=f"SUM({self.dateId}, {other.dateId})",
            startDate=startDate,
            endDate=endDate,
            total=self.total + other.total,
            totalCost=self.totalCost + other.totalCost,
            totalInvoices=self.totalInvoices + other.totalInvoices,
            branches=list(branches_map.values()),
            creditSales=self.creditSales + other.creditSales,
            cashSales=self.cashSales + other.cashSales,
            totalReceiptCash=self.totalReceiptCash + other.totalReceiptCash,
            totalReceiptDevolutions=self.totalReceiptDevolutions
            + other.totalReceiptDevolutions,
            totalReceipts=self.totalReceipts + other.totalReceipts,
            receiptCount=self.receiptCount + other.receiptCount,
        )


class CreateDailySummary(BaseDailySummary):
    pass


class DailySummaryInDb(BaseDailySummary):
    id: str
    createdAt: int
