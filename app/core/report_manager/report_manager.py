import asyncio
from pydantic import BaseModel

from repos.v1.invoices import InvoicesRepository, InvoicesDataSource, InvoiceTotals
from repos.v1.branches import BranchesRepository, BranchesDataSource, BranchInDb
from repos.v1.inventories import InventoriesRepository, InventoriesDataSource


class DailyInvoiceReportResult(BaseModel):
    results: list[tuple[BranchInDb, InvoiceTotals]]
    total: int
    totalCost: int


class CurrentInventoryReportResult(BaseModel):
    results: list[tuple[BranchInDb, int]]
    total: int


class ReportManager:
    def __init__(self) -> None:
        self.invoices_repo = InvoicesRepository(InvoicesDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.inventories_repo = InventoriesRepository(InventoriesDataSource())

    async def get_total_invoices_by_date_range(
        self, start_date: int, end_date: int
    ) -> DailyInvoiceReportResult:
        all_branches = await self.branches_repo.get_all_branches()

        coros = []

        for branch in all_branches:
            coro = self.invoices_repo.get_totals_from_invoices(
                startDate=start_date, endDate=end_date, branchId=branch.id
            )
            coros.append(coro)

        results: list[InvoiceTotals] = await asyncio.gather(*coros)

        paired_results = list(zip(all_branches, results))

        total = 0
        total_cost = 0

        for result in results:
            total += result.total
            total_cost += result.totalCost

        return DailyInvoiceReportResult(
            results=paired_results, total=total, totalCost=total_cost
        )

    async def get_total_inventory_all_branches(self) -> CurrentInventoryReportResult:
        all_branches = await self.branches_repo.get_all_branches()

        coros = []

        for branch in all_branches:
            coro = self.inventories_repo.get_total_current_stock(branch.id)
            coros.append(coro)

        results: list[int] = await asyncio.gather(*coros)

        paired_results = list(zip(all_branches, results))

        total = sum(results)

        return CurrentInventoryReportResult(
            results=paired_results,
            total=total,
        )
