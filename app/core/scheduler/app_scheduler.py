import asyncio
from typing_extensions import Self
from functools import reduce
from datetime import datetime, timedelta
from tools import TimeTools

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

from repos.v1.inventories import InventoriesRepository, InventoriesDataSource

from repos.v1.common.models import InventoryBranchDetail


class AppScheduler:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    _started = False

    def __init__(self) -> None:
        if hasattr(self, "initialized"):
            return
        self.initialized = True

        self.daily_summaries_repo = DailySummariesRepository(
            DailySummariesDataSource(),
        )
        self.executive_summaries_repo = ExecutiveSummariesRepository(
            ExecutiveSummariesDataSource(),
        )

        self.inventories_repo = InventoriesRepository(
            InventoriesDataSource(),
        )

    async def start_task(self):
        if self._started:
            return
        asyncio.create_task(self.run_every_midnight())
        self._started = True
        print("🕒 Scheduler Init")

    async def run_every_midnight(self):
        nic_tz = TimeTools.default_timezone
        while True:
            try:
                next_day = datetime.now(nic_tz) + timedelta(days=1)
                next_midnight = next_day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                diff_seconds = (next_midnight - datetime.now(nic_tz)).total_seconds()
                await asyncio.sleep(diff_seconds)
                await self._set_daily_tasks(next_midnight)
            except asyncio.CancelledError:
                print("Scheduler Stopped")
                break
            except Exception as e:
                print("Error in run_every_midnight")
                print(e)
                await asyncio.sleep(60)

    async def _set_daily_tasks(self, current_time: datetime):
        print(f"🚀 Daily Task: {current_time}")
        await asyncio.sleep(1)
        # here the daily tasks will be set
        report_maker = ReportManager()

        yesterday = current_time - timedelta(days=1)

        current_timestamp = int(current_time.timestamp() * 1000)
        yesterday_timestamp = int(yesterday.timestamp() * 1000)

        res = await report_maker.get_total_invoices_by_date_range(
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

        # detect is new week
        if current_time.weekday() == 0:
            previous_week = current_time - timedelta(weeks=1)
            previous_week_timestamp = int(previous_week.timestamp() * 1000)
            sumaries = await self.daily_summaries_repo.get_all_daily_summaries(
                startDate=previous_week_timestamp,
                endDate=current_timestamp + 5000,  # add 5 seconds
            )

            weekly_summary = reduce(lambda a, b: a + b, sumaries)

            inventory_result = await report_maker.get_total_inventory_all_branches()

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

        pass
