from fastapi import APIRouter, Depends

from .reports_controller import reports_controller
from kardex.repos.v1.common.filter_params import ReportFilterParams, TotalsFilterParams
from kardex.repos.v1.executive_summaries import ExecutiveSummaryInDb
from app_middleware import auth_middleware
from .responses import TotalsResult

reports_router = APIRouter(
    tags=["reportsV1"],
    dependencies=[Depends(auth_middleware)],
)


@reports_router.get("/general-report")
async def get_general_report(
    query_params: ReportFilterParams = Depends(),
) -> ExecutiveSummaryInDb:
    return await reports_controller.get_general_report(query_params)


@reports_router.get("/total-results-by-date-range")
async def get_total_results_by_date_range(
    query_params: TotalsFilterParams = Depends(),
) -> TotalsResult:
    return await reports_controller.get_total_results_by_date_range(query_params)
