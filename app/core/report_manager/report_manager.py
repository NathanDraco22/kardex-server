import asyncio
from pydantic import BaseModel

from repos.v1.invoices import (
    InvoicesRepository,
    InvoicesDataSource,
    InvoiceTotals,
    BranchPortfolioSummary,
)
from repos.v1.receipts import ReceiptsRepository, ReceiptsDataSource
from repos.v1.receipts.models.branch_receipt_amount_total import (
    BranchAppliedReceiptsAmountsSummary,
)
from repos.v1.branches import BranchesRepository, BranchesDataSource, BranchInDb
from repos.v1.inventories import InventoriesRepository, InventoriesDataSource


class DailyInvoiceReportResult(BaseModel):
    results: list[tuple[BranchInDb, InvoiceTotals]]
    total: int
    totalCost: int
    totalInvoices: int


class DailySummaryReportResult(BaseModel):
    results: list[tuple[str, BranchPortfolioSummary]]
    totalSales: int
    totalCost: int
    totalPaid: int
    totalOwed: int
    creditSales: int
    cashSales: int
    totalInvoices: int
    receiptResults: list[tuple[str, BranchAppliedReceiptsAmountsSummary]]
    totalReceiptDevolutions: int = 0
    totalReceiptCash: int = 0
    totalReceipts: int = 0
    receiptCount: int = 0


class CurrentInventoryReportResult(BaseModel):
    results: list[tuple[BranchInDb, int]]
    total: int


class ReportManager:
    def __init__(self) -> None:
        self.invoices_repo = InvoicesRepository(InvoicesDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.inventories_repo = InventoriesRepository(InventoriesDataSource())
        self.receipts_repo = ReceiptsRepository(ReceiptsDataSource())

    async def get_total_invoices_by_date_range(
        self, start_date: int, end_date: int
    ) -> DailyInvoiceReportResult:
        all_branches = await self.branches_repo.get_all_commerce_branches()

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
        total_invoices = 0

        for result in results:
            total += result.total
            total_cost += result.totalCost
            total_invoices += result.count

        return DailyInvoiceReportResult(
            results=paired_results,
            total=total,
            totalCost=total_cost,
            totalInvoices=total_invoices,
        )

    async def get_invoice_summary(self, **kwargs) -> DailySummaryReportResult | None:
        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)

        if not start_date or not end_date:
            return None

        result = await self.invoices_repo.get_invoice_summary(
            startDate=start_date, endDate=end_date
        )

        total_receipt = await self.receipts_repo.get_branch_receipt_amounts_summary(
            startDate=start_date, endDate=end_date
        )

        current_result = DailySummaryReportResult(
            results=[],
            totalSales=0,
            totalCost=0,
            totalPaid=0,
            totalOwed=0,
            creditSales=0,
            cashSales=0,
            totalInvoices=0,
            receiptResults=[],
            totalReceiptDevolutions=0,
            totalReceiptCash=0,
            totalReceipts=0,
            receiptCount=0,
        )

        for model in result:
            current_result.totalSales += model.totalSales
            current_result.totalCost += model.totalCost
            current_result.totalPaid += model.totalPaid
            current_result.totalOwed += model.totalOwed
            current_result.creditSales += model.creditSales
            current_result.cashSales += model.cashSales
            current_result.totalInvoices += model.totalInvoices

            current_result.results.append((model.branchId, model))

        for receiptSummary in total_receipt:
            current_result.totalReceiptDevolutions += (
                receiptSummary.totalAppliedDevolutions
            )
            current_result.totalReceiptCash += receiptSummary.totalAppliedInvoices
            current_result.totalReceipts += receiptSummary.totalReceipts
            current_result.receiptCount += receiptSummary.receiptCount

            current_result.receiptResults.append(
                (receiptSummary.branchId, receiptSummary)
            )

        return current_result

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
