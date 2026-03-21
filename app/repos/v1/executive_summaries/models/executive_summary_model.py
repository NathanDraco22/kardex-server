from typing import Literal
from pydantic import BaseModel

from repos.v1.common.models import CommercialBranchDetail
from repos.v1.common.models import InventoryBranchDetail
from repos.v1.invoices import PendingInvoiceTotalsByBranch

SummaryType = Literal["weekly", "monthly", "yearly", "custom"]


class BaseExecutiveSummary(BaseModel):
    dateId: str
    type: SummaryType
    year: int
    month: int
    startDate: int
    endDate: int
    salesTotal: int
    creditSales: int = 0
    cashSales: int = 0
    salesTotalCost: int
    totalInvoices: int
    totalPendingInvoices: int
    totalPendingBranches: list[PendingInvoiceTotalsByBranch]
    totalReceiptCash: int = 0
    totalReceiptDevolutions: int = 0
    totalReceipts: int = 0
    receiptCount: int = 0
    commercialBranches: list[CommercialBranchDetail]
    inventoryTotalCost: int
    inventoryBranches: list[InventoryBranchDetail]


class CreateExecutiveSummary(BaseExecutiveSummary):
    pass


class ExecutiveSummaryInDb(BaseExecutiveSummary):
    id: str
    createdAt: int
    updatedAt: int | None = None
