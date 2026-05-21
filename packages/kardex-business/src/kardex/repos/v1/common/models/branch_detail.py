from pydantic import BaseModel


class CommercialBranchDetail(BaseModel):
    branchId: str
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

    def __add__(self, other: "CommercialBranchDetail") -> "CommercialBranchDetail":
        if self.branchId != other.branchId:
            raise ValueError("No se pueden sumar sucursales diferentes")

        return CommercialBranchDetail(
            branchId=self.branchId,
            total=self.total + other.total,
            totalCost=self.totalCost + other.totalCost,
            totalInvoices=self.totalInvoices + other.totalInvoices,
            totalPaid=self.totalPaid + other.totalPaid,
            totalOwed=self.totalOwed + other.totalOwed,
            creditSales=self.creditSales + other.creditSales,
            cashSales=self.cashSales + other.cashSales,
            totalReceiptCash=self.totalReceiptCash + other.totalReceiptCash,
            totalReceiptDevolutions=self.totalReceiptDevolutions
            + other.totalReceiptDevolutions,
            totalReceipts=self.totalReceipts + other.totalReceipts,
            receiptCount=self.receiptCount + other.receiptCount,
        )


class InventoryBranchDetail(BaseModel):
    branchId: str
    inventoryTotalCost: int
