from functools import reduce
from datetime import datetime
from tools import TimeTools

from repos.v1.daily_summaries import DailySummariesRepository, DailySummariesDataSource
from repos.v1.executive_summaries import (
    ExecutiveSummariesRepository,
    ExecutiveSummariesDataSource,
    ExecutiveSummaryInDb,
)
from repos.v1.common.models import InventoryBranchDetail
from core.report_manager.report_manager import ReportManager

from .query_params import ReportQueryParams


class ReportsController:
    def __init__(
        self,
        daily_summaries_repo: DailySummariesRepository,
        executive_summaries_repo: ExecutiveSummariesRepository,
    ):
        self.daily_summaries_repo = daily_summaries_repo
        self.executive_summaries_repo = executive_summaries_repo
        self.report_manager = ReportManager()
        pass

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


reports_controller = ReportsController(
    daily_summaries_repo=DailySummariesRepository(
        daily_summaries_ds=DailySummariesDataSource(),
    ),
    executive_summaries_repo=ExecutiveSummariesRepository(
        executive_summaries_ds=ExecutiveSummariesDataSource(),
    ),
)
