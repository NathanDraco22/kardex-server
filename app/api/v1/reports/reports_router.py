from fastapi import APIRouter, Depends
from typing import Any

from .reports_controller import reports_controller
from .query_params import ReportQueryParams, TotalsQueryParams
from .responses import TotalsResult

reports_router = APIRouter(tags=["reportsV1"])


@reports_router.get("/general-report")
async def get_general_report(query_params: ReportQueryParams = Depends()) -> Any:
    return await reports_controller.get_general_report(**query_params.model_dump())


@reports_router.get("/total-results-by-date-range")
async def get_total_results_by_date_range(
    query_params: TotalsQueryParams = Depends(),
) -> TotalsResult:
    return await reports_controller.get_total_results_by_date_range(query_params)
