from datetime import datetime, timedelta
from functools import reduce

from core.report_manager.report_manager import ReportManager
from repos.v1.daily_summaries import (
    DailySummariesRepository,
    DailySummariesDataSource,
    CommercialBranchDetail,
    CreateDailySummary,
)
from repos.v1.executive_summaries import (
    ExecutiveSummariesRepository,
    ExecutiveSummariesDataSource,
    CreateExecutiveSummary,
)
from repos.v1.common.models import InventoryBranchDetail


class DailyReportMaker:
    def __init__(self) -> None:
        self.report_maker = ReportManager()
        self.daily_summaries_repo = DailySummariesRepository(DailySummariesDataSource())

    async def create_report(self, current_time: datetime) -> None:
        yesterday = current_time - timedelta(days=1)

        current_timestamp = int(current_time.timestamp() * 1000)
        yesterday_timestamp = int(yesterday.timestamp() * 1000)

        res = await self.report_maker.get_total_invoices_by_date_range(
            yesterday_timestamp, current_timestamp
        )

        branch_details = [
            CommercialBranchDetail(
                branchId=branch.id,
                total=totals.total,
                totalCost=totals.totalCost,
                totalInvoices=totals.count,
            )
            for branch, totals in res.results
        ]

        create_daily = CreateDailySummary(
            dateId=yesterday.strftime("%Y-%m-%d"),
            startDate=yesterday_timestamp,
            endDate=current_timestamp,
            total=res.total,
            totalCost=res.totalCost,
            totalInvoices=res.totalInvoices,
            branches=branch_details,
        )

        await self.daily_summaries_repo.create_daily_summary(create_daily)


class WeeklyReportMaker:
    def __init__(self) -> None:
        self.report_maker = ReportManager()
        self.daily_summaries_repo = DailySummariesRepository(DailySummariesDataSource())
        self.executive_summaries_repo = ExecutiveSummariesRepository(
            ExecutiveSummariesDataSource()
        )

    async def create_report(self, current_time: datetime) -> None:
        current_timestamp = int(current_time.timestamp() * 1000)
        previous_week = current_time - timedelta(weeks=1)
        previous_week_timestamp = int(previous_week.timestamp() * 1000)

        sumaries = await self.daily_summaries_repo.get_all_daily_summaries(
            startDate=previous_week_timestamp,
            endDate=current_timestamp + 5000,  # add 5 seconds
        )

        if not sumaries:
            return

        weekly_summary = reduce(lambda a, b: a + b, sumaries)

        inventory_result = await self.report_maker.get_total_inventory_all_branches()

        inventory_branches = [
            InventoryBranchDetail(
                branchId=branch.id,
                inventoryTotalCost=total,
            )
            for branch, total in inventory_result.results
        ]

        create_weekly_summary = CreateExecutiveSummary(
            type="weekly",
            year=current_time.year,
            month=current_time.month,
            startDate=previous_week_timestamp,
            endDate=current_timestamp,
            salesTotal=weekly_summary.total,
            salesTotalCost=weekly_summary.totalCost,
            totalInvoices=weekly_summary.totalInvoices,
            commercialBranches=weekly_summary.branches,
            inventoryTotalCost=inventory_result.total,
            inventoryBranches=inventory_branches,
        )

        await self.executive_summaries_repo.create_executive_summary(
            create_weekly_summary
        )
