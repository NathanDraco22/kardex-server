from datetime import datetime, timedelta
from functools import reduce

from core.report_manager.report_manager import ReportManager
from repos.v1.daily_summaries import (
    DailySummariesRepository,
    DailySummariesDataSource,
    CommercialBranchDetail,
    CreateDailySummary,
    DailySummaryInDb,
)
from repos.v1.executive_summaries import (
    ExecutiveSummariesRepository,
    ExecutiveSummariesDataSource,
    CreateExecutiveSummary,
    ExecutiveSummaryInDb,
)
from repos.v1.common.models import InventoryBranchDetail


class DailyReportMaker:
    def __init__(self) -> None:
        self.report_maker = ReportManager()
        self.daily_summaries_repo = DailySummariesRepository(DailySummariesDataSource())

    async def ensure_daily_report(
        self, current_time: datetime
    ) -> DailySummaryInDb | None:
        selected_time = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            tzinfo=current_time.tzinfo,
        )
        yesterday = selected_time - timedelta(days=1)
        date_id = yesterday.strftime("%Y-%m-%d")

        print(f"🔍 Checking existence for Daily Report: {date_id}")
        existing_report = await self.daily_summaries_repo.get_daily_summary_by_date_id(
            date_id
        )
        if existing_report:
            print(f"⚠️ Daily Report {date_id} already exists. Skipping creation.")
            return existing_report

        print(f"✨ Creating NEW Daily Report for {date_id}")

        current_timestamp = int(selected_time.timestamp() * 1000)
        yesterday_timestamp = int(yesterday.timestamp() * 1000)

        res = await self.report_maker.get_invoice_summary(
            startDate=yesterday_timestamp, endDate=current_timestamp
        )

        if not res:
            return

        branch_details: list[CommercialBranchDetail] = []

        for branch_id, summary in res.results:
            current_receipt_summary = None

            for _, receipt_summary in res.receiptResults:
                if receipt_summary.branchId == branch_id:
                    current_receipt_summary = receipt_summary
                    break

            total_receipt_cash = 0
            total_receipt_devolutions = 0
            total_receipts = 0
            receipt_count = 0

            if current_receipt_summary:
                total_receipt_cash = current_receipt_summary.totalAppliedInvoices
                total_receipt_devolutions = (
                    current_receipt_summary.totalAppliedDevolutions
                )
                total_receipts = current_receipt_summary.totalReceipts
                receipt_count = current_receipt_summary.receiptCount

            branch_details.append(
                CommercialBranchDetail(
                    branchId=branch_id,
                    total=summary.totalSales,
                    totalCost=summary.totalCost,
                    totalInvoices=summary.totalInvoices,
                    totalPaid=summary.totalPaid,
                    totalOwed=summary.totalOwed,
                    creditSales=summary.creditSales,
                    cashSales=summary.cashSales,
                    totalReceiptCash=total_receipt_cash,
                    totalReceiptDevolutions=total_receipt_devolutions,
                    totalReceipts=total_receipts,
                    receiptCount=receipt_count,
                )
            )

        create_daily = CreateDailySummary(
            dateId=date_id,
            startDate=yesterday_timestamp,
            endDate=current_timestamp,
            total=res.totalSales,
            totalCost=res.totalCost,
            totalPaid=res.totalPaid,
            totalOwed=res.totalOwed,
            creditSales=res.creditSales,
            cashSales=res.cashSales,
            totalInvoices=res.totalInvoices,
            totalReceiptCash=res.totalReceiptCash,
            totalReceiptDevolutions=res.totalReceiptDevolutions,
            totalReceipts=res.totalReceipts,
            receiptCount=res.receiptCount,
            branches=branch_details,
        )

        res = await self.daily_summaries_repo.create_daily_summary(create_daily)
        return res


class WeeklyReportMaker:
    def __init__(self) -> None:
        self.report_maker = ReportManager()
        self.daily_summaries_repo = DailySummariesRepository(DailySummariesDataSource())
        self.executive_summaries_repo = ExecutiveSummariesRepository(
            ExecutiveSummariesDataSource()
        )

    async def ensure_weekly_report(
        self, current_time: datetime
    ) -> ExecutiveSummaryInDb | None:
        print(
            f"🔍 Checking existence for Weekly Report: {current_time.strftime('%Y-%m-%d')}"
        )
        selected_time = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            tzinfo=current_time.tzinfo,
        )
        if current_time.weekday() != 0:
            selected_time = current_time - timedelta(days=current_time.weekday())

        result = await self.executive_summaries_repo.get_executive_summary_by_date_id_and_type(
            selected_time.strftime("%Y-%m-%d"), "weekly"
        )

        if result:
            print(
                f"⚠️ Weekly Report {selected_time.strftime('%Y-%m-%d')} already exists. Skipping creation."
            )
            return result

        print(f"✨ Creating NEW Weekly Report for {selected_time.strftime('%Y-%m-%d')}")

        res = await self._create_report(selected_time)

        return res

    async def _create_report(
        self, current_time: datetime
    ) -> ExecutiveSummaryInDb | None:
        current_timestamp = int(current_time.timestamp() * 1000)
        previous_week = current_time - timedelta(weeks=1)
        previous_week_timestamp = int(previous_week.timestamp() * 1000)

        # We want reports from Monday (inclusive) to Sunday (inclusive).
        # Daily Report for Sunday starts at Sunday 00:00.
        # Next Monday report starts at Monday 00:00 (current_timestamp).
        # So we want startDate < current_timestamp.
        # Since we use $lte in repo, we subtract 1ms to exclude Next Monday.
        end_date_limit = current_timestamp - 1

        sumaries = (
            await self.daily_summaries_repo.get_daily_summary_by_start_date_range(
                startDate=previous_week_timestamp,
                endDate=end_date_limit,
            )
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
            dateId=current_time.strftime("%Y-%m-%d"),
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

        res = await self.executive_summaries_repo.create_executive_summary(
            create_weekly_summary
        )

        return res


class MonthlyReportMaker:
    def __init__(self) -> None:
        self.report_maker = ReportManager()
        self.daily_summaries_repo = DailySummariesRepository(DailySummariesDataSource())
        self.executive_summaries_repo = ExecutiveSummariesRepository(
            ExecutiveSummariesDataSource()
        )

    async def ensure_monthly_report(
        self, current_time: datetime
    ) -> ExecutiveSummaryInDb | None:
        """
        Generates a report for the PREVIOUS month based on current_time.
        e.g. if current_time is March 1st, generates report for February.
        Idempotent: checks if exists first.
        """
        # Normalize to start of current day
        date_current = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            tzinfo=current_time.tzinfo,
        )

        # Go back to the last day of previous month
        last_day_prev_month = date_current.replace(day=1) - timedelta(days=1)
        # First day of previous month
        first_day_prev_month = last_day_prev_month.replace(day=1)

        date_id = first_day_prev_month.strftime("%Y-%m")  # e.g., 2024-02

        print(f"🔍 Checking existence for Monthly Report: {date_id}")

        result = await self.executive_summaries_repo.get_executive_summary_by_date_id_and_type(
            date_id, "monthly"
        )

        if result:
            print(f"⚠️ Monthly Report {date_id} already exists. Skipping creation.")
            return result

        print(f"✨ Creating NEW Monthly Report for {date_id}")

        res = await self._create_report(
            first_day_prev_month, last_day_prev_month, date_id
        )

        return res

    async def _create_report(
        self, start_date: datetime, end_date: datetime, date_id: str
    ) -> ExecutiveSummaryInDb | None:
        # Using startDate for filtering is much cleaner.
        # We want all daily summaries where startDate is within the month range.
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)

        sumaries = (
            await self.daily_summaries_repo.get_daily_summary_by_start_date_range(
                startDate=start_timestamp,
                endDate=end_timestamp,
            )
        )

        if not sumaries:
            return

        monthly_summary = reduce(lambda a, b: a + b, sumaries)

        inventory_result = await self.report_maker.get_total_inventory_all_branches()

        inventory_branches = [
            InventoryBranchDetail(
                branchId=branch.id,
                inventoryTotalCost=total,
            )
            for branch, total in inventory_result.results
        ]

        create_monthly_summary = CreateExecutiveSummary(
            dateId=date_id,
            type="monthly",
            year=start_date.year,
            month=start_date.month,
            startDate=start_timestamp,
            endDate=end_timestamp,
            salesTotal=monthly_summary.total,
            salesTotalCost=monthly_summary.totalCost,
            totalInvoices=monthly_summary.totalInvoices,
            commercialBranches=monthly_summary.branches,
            inventoryTotalCost=inventory_result.total,
            inventoryBranches=inventory_branches,
        )

        res = await self.executive_summaries_repo.create_executive_summary(
            create_monthly_summary
        )

        return res


class YearlyReportMaker:
    def __init__(self) -> None:
        self.report_maker = ReportManager()
        self.daily_summaries_repo = DailySummariesRepository(DailySummariesDataSource())
        self.executive_summaries_repo = ExecutiveSummariesRepository(
            ExecutiveSummariesDataSource()
        )

    async def ensure_yearly_report(
        self, current_time: datetime
    ) -> ExecutiveSummaryInDb | None:
        """
        Generates a report for the PREVIOUS year based on current_time.
        e.g. if current_time is Jan 1st 2025, generates report for 2024.
        """
        # Normalize
        date_current = datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            tzinfo=current_time.tzinfo,
        )

        prev_year = date_current.year - 1
        date_id = str(prev_year)

        print(f"🔍 Checking existence for Yearly Report: {date_id}")

        result = await self.executive_summaries_repo.get_executive_summary_by_date_id_and_type(
            date_id, "yearly"
        )

        if result:
            print(f"⚠️ Yearly Report {date_id} already exists. Skipping creation.")
            return

        print(f"✨ Creating NEW Yearly Report for {date_id}")

        start_date = datetime(prev_year, 1, 1, tzinfo=current_time.tzinfo)
        end_date = datetime(prev_year, 12, 31, tzinfo=current_time.tzinfo)

        await self._create_report(start_date, end_date, date_id)

    async def _create_report(
        self, start_date: datetime, end_date: datetime, date_id: str
    ) -> None:
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)

        sumaries = (
            await self.daily_summaries_repo.get_daily_summary_by_start_date_range(
                startDate=start_timestamp,
                endDate=end_timestamp,
            )
        )

        if not sumaries:
            return

        yearly_summary = reduce(lambda a, b: a + b, sumaries)

        inventory_result = await self.report_maker.get_total_inventory_all_branches()

        inventory_branches = [
            InventoryBranchDetail(
                branchId=branch.id,
                inventoryTotalCost=total,
            )
            for branch, total in inventory_result.results
        ]

        create_yearly_summary = CreateExecutiveSummary(
            dateId=date_id,
            type="yearly",
            year=start_date.year,
            month=0,  # 0 indicates full year in this context
            startDate=start_timestamp,
            endDate=end_timestamp,
            salesTotal=yearly_summary.total,
            salesTotalCost=yearly_summary.totalCost,
            totalInvoices=yearly_summary.totalInvoices,
            commercialBranches=yearly_summary.branches,
            inventoryTotalCost=inventory_result.total,
            inventoryBranches=inventory_branches,
        )

        await self.executive_summaries_repo.create_executive_summary(
            create_yearly_summary
        )
