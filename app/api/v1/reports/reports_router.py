from fastapi import APIRouter
from typing import Any

from .reports_controller import reports_controller
from .query_params import ReportQueryParams

reports_router = APIRouter(tags=["reportsV1"])


@reports_router.get("/general-report")
async def get_general_report(query_params: ReportQueryParams) -> Any:
    return await reports_controller.get_general_report(**query_params.dict())