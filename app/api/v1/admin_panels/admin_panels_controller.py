import asyncio
from kardex.repos.v1.invoices import InvoicesRepository, InvoicesDataSource

from tools import TimeTools

from .responses import AdminChartsResponses

# tao3c943of8bzpoukp9iu1ud7a


#
class AdminPanelsController:
    def __init__(self, invoices_repo: InvoicesRepository) -> None:
        self.invoices_repo = invoices_repo
        pass

    async def get_admin_charts(self, end_date: int) -> AdminChartsResponses:
        current_end_date = end_date
        coros = []
        for _ in range(0, 7):
            start_date = current_end_date - TimeTools.ms_day
            coro = self.invoices_repo.get_totals_from_invoices(
                startDate=start_date, endDate=current_end_date
            )

            current_end_date = start_date

            coros.append(coro)

        results = await asyncio.gather(*coros)

        results.reverse()
        return AdminChartsResponses(last7DaysTotals=results)

    async def get_last_7_days_by_branch(
        self, branch_id: str, end_date: int
    ) -> AdminChartsResponses:
        current_end_date = end_date
        coros = []
        for _ in range(0, 7):
            start_date = current_end_date - TimeTools.ms_day
            coro = self.invoices_repo.get_totals_from_invoices(
                startDate=start_date,
                endDate=current_end_date,
                branchId=branch_id,
            )

            current_end_date = start_date

            coros.append(coro)

        results = await asyncio.gather(*coros)

        results.reverse()
        return AdminChartsResponses(last7DaysTotals=results)


admin_panels_controller = AdminPanelsController(
    InvoicesRepository(InvoicesDataSource())
)
