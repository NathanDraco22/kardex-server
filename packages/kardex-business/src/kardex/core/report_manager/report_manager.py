import asyncio
from typing import Any
from pydantic import BaseModel

from kardex.repos.v1.invoices import (
    InvoicesRepository,
    InvoicesDataSource,
    InvoiceTotals,
    BranchPortfolioSummary,
    PendingInvoiceTotalsByBranch,
)
from kardex.repos.v1.common.filter_params import InvoiceFilterParams
from kardex.repos.v1.receipts import ReceiptsRepository, ReceiptsDataSource
from kardex.repos.v1.receipts.models.branch_receipt_amount_total import (
    BranchAppliedReceiptsAmountsSummary,
)
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource, BranchInDb
from kardex.repos.v1.inventories import InventoriesRepository, InventoriesDataSource
from kardex.repos.v1.expenses import ExpensesRepository, ExpensesDataSource


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
        self.expenses_repo = ExpensesRepository(ExpensesDataSource())

    async def get_total_invoices_by_date_range(
        self, start_date: int, end_date: int
    ) -> DailyInvoiceReportResult:
        all_branches = await self.branches_repo.get_all_commerce_branches()

        coros = []

        for branch in all_branches:
            coro = self.invoices_repo.get_totals_from_invoices(
                InvoiceFilterParams(startDate=start_date, endDate=end_date, branchId=branch.id)
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

        all_branches = await self.branches_repo.get_all_commerce_branches()

        result = await self.invoices_repo.get_invoice_summary(
            startDate=start_date, endDate=end_date
        )

        total_receipt = await self.receipts_repo.get_branch_receipt_amounts_summary(
            startDate=start_date, endDate=end_date
        )

        invoices_by_branch = {model.branchId: model for model in result}
        receipts_by_branch = {model.branchId: model for model in total_receipt}

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

        for branch in all_branches:
            branch_id = branch.id

            invoice_model = invoices_by_branch.get(branch_id)
            if invoice_model:
                current_result.totalSales += invoice_model.totalSales
                current_result.totalCost += invoice_model.totalCost
                current_result.totalPaid += invoice_model.totalPaid
                current_result.totalOwed += invoice_model.totalOwed
                current_result.creditSales += invoice_model.creditSales
                current_result.cashSales += invoice_model.cashSales
                current_result.totalInvoices += invoice_model.totalInvoices
                current_result.results.append((branch_id, invoice_model))
            else:
                empty_invoice = BranchPortfolioSummary(
                    branchId=branch_id,
                    totalSales=0,
                    totalCost=0,
                    totalPaid=0,
                    totalOwed=0,
                    creditSales=0,
                    cashSales=0,
                    totalInvoices=0,
                )
                current_result.results.append((branch_id, empty_invoice))

            receipt_model = receipts_by_branch.get(branch_id)
            if receipt_model:
                current_result.totalReceiptDevolutions += (
                    receipt_model.totalAppliedDevolutions
                )
                current_result.totalReceiptCash += receipt_model.totalAppliedInvoices
                current_result.totalReceipts += receipt_model.totalReceipts
                current_result.receiptCount += receipt_model.receiptCount
                current_result.receiptResults.append((branch_id, receipt_model))
            else:
                empty_receipt = BranchAppliedReceiptsAmountsSummary(
                    branchId=branch_id,
                    totalAppliedInvoices=0,
                    totalAppliedDevolutions=0,
                    totalReceipts=0,
                    receiptCount=0,
                )
                current_result.receiptResults.append((branch_id, empty_receipt))

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

    async def get_pending_invoice_totals_by_branch(
        self, **kwargs
    ) -> list[PendingInvoiceTotalsByBranch]:
        all_branches = await self.branches_repo.get_all_commerce_branches()

        pending_invoice_total = (
            await self.invoices_repo.get_pending_invoice_totals_by_branch(**kwargs)
        )

        total_by_branch = {total.branchId: total for total in pending_invoice_total}

        paired_results: list[PendingInvoiceTotalsByBranch] = []

        for branch in all_branches:
            current_branch = total_by_branch.get(branch.id)
            if current_branch:
                paired_results.append(current_branch)
            else:
                paired_results.append(
                    PendingInvoiceTotalsByBranch(
                        branchId=branch.id,
                        total=0,
                        totalCost=0,
                        amountPaid=0,
                        totalOwed=0,
                        count=0,
                    )
                )
        return paired_results

    async def get_expenses_summary_in_range(
        self, start_date: int, end_date: int
    ) -> dict[str, Any]:
        return await self.expenses_repo.get_expenses_summary_in_range(start_date, end_date)
