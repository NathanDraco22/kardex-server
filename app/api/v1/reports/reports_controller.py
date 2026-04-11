from functools import reduce
from datetime import datetime
from tools import TimeTools

from repos.v1.daily_summaries import DailySummariesRepository, DailySummariesDataSource
from repos.v1.executive_summaries import (
    ExecutiveSummariesRepository,
    ExecutiveSummariesDataSource,
    ExecutiveSummaryInDb,
)
from repos.v1.receipts import ReceiptsRepository
from repos.v1.invoices import InvoicesRepository

from repos.v1.common.models import InventoryBranchDetail
from core.report_manager.report_manager import ReportManager

from .query_params import ReportQueryParams, TotalsQueryParams
from .responses import TotalsResult


class ReportsController:
    def __init__(
        self,
        daily_summaries_repo: DailySummariesRepository,
        executive_summaries_repo: ExecutiveSummariesRepository,
    ):
        self.daily_summaries_repo = daily_summaries_repo
        self.executive_summaries_repo = executive_summaries_repo
        self.report_manager = ReportManager()
        self.receipts_repo = ReceiptsRepository.get_instance()
        self.invoices_repo = InvoicesRepository.get_instance()

    async def get_general_report(
        self, params: ReportQueryParams
    ) -> ExecutiveSummaryInDb:
        query = params.model_dump(exclude_none=True)
        daily_reports = await self.daily_summaries_repo.get_all_daily_summaries(**query)

        all_summary = reduce(lambda a, b: a + b, daily_reports)

        inventory_result = await self.report_manager.get_total_inventory_all_branches()

        inventory_branches = [
            InventoryBranchDetail(
                branchId=branch.id,
                inventoryTotalCost=total,
            )
            for branch, total in inventory_result.results
        ]

        year = datetime.now().year
        month = datetime.now().month

        executive_summary = ExecutiveSummaryInDb(
            id="None",
            dateId="None",
            year=year,
            month=month,
            startDate=params.startDate,
            endDate=params.endDate,
            salesTotal=all_summary.total,
            salesTotalCost=all_summary.totalCost,
            totalInvoices=all_summary.totalInvoices,
            commercialBranches=all_summary.branches,
            inventoryTotalCost=inventory_result.total,
            inventoryBranches=inventory_branches,
            type="custom",
            createdAt=TimeTools.get_now_in_milliseconds(),
        )
        return executive_summary

    async def get_total_results_by_date_range(
        self, params: TotalsQueryParams
    ) -> TotalsResult:
        query = params.model_dump(exclude_none=True)
        invoices_totals = await self.invoices_repo.get_totals_invoices_by_payment_type(
            **query
        )
        receipts = await self.receipts_repo.get_totals_from_receipts_by_payment_method(
            **query
        )

        return TotalsResult(
            branchId=params.branchId,
            invoices=invoices_totals,
            receipts=receipts,
        )


reports_controller = ReportsController(
    daily_summaries_repo=DailySummariesRepository(
        daily_summaries_ds=DailySummariesDataSource(),
    ),
    executive_summaries_repo=ExecutiveSummariesRepository(
        executive_summaries_ds=ExecutiveSummariesDataSource(),
    ),
)
