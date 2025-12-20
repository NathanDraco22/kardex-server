from fastapi import APIRouter


from .admin_panels_controller import admin_panels_controller
from .responses import AdminChartsResponses

admin_panels_router = APIRouter(tags=["admin_panelsV1"])


@admin_panels_router.get("/charts")
async def get_admin_panels_charts(endDate: int) -> AdminChartsResponses:
    return await admin_panels_controller.get_admin_charts(endDate)


@admin_panels_router.get("/charts/{branchId}")
async def get_admin_panels_charts_by_branch(
    branchId: str, endDate: int
) -> AdminChartsResponses:
    return await admin_panels_controller.get_last_7_days_by_branch(branchId, endDate)
