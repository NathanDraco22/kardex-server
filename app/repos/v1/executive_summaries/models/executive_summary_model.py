from typing import Literal
from pydantic import BaseModel

from repos.v1.common.models import CommercialBranchDetail
from repos.v1.common.models import InventoryBranchDetail

SummaryType = Literal["weekly", "monthly", "yearly", "custom"]


class BaseExecutiveSummary(BaseModel):
    dateId: str
    type: SummaryType
    year: int
    month: int
    startDate: int
    endDate: int
    salesTotal: int
    salesTotalCost: int
    totalInvoices: int
    commercialBranches: list[CommercialBranchDetail]
    inventoryTotalCost: int
    inventoryBranches: list[InventoryBranchDetail]


class CreateExecutiveSummary(BaseExecutiveSummary):
    pass


class ExecutiveSummaryInDb(BaseExecutiveSummary):
    id: str
    createdAt: int
    updatedAt: int | None = None
