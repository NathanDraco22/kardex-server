from pydantic import BaseModel


class CommercialBranchDetail(BaseModel):
    branchId: str
    total: int
    totalCost: int
    totalInvoices: int

    def __add__(self, other: "CommercialBranchDetail") -> "CommercialBranchDetail":
        if self.branchId != other.branchId:
            raise ValueError("No se pueden sumar sucursales diferentes")

        return CommercialBranchDetail(
            branchId=self.branchId,
            total=self.total + other.total,
            totalCost=self.totalCost + other.totalCost,
            totalInvoices=self.totalInvoices + other.totalInvoices,
        )


class InventoryBranchDetail(BaseModel):
    branchId: str
    inventoryTotalCost: int
