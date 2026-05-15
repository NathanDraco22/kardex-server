from fastapi import APIRouter, Header
from fastapi.responses import FileResponse

from .exports_controller import exports_controller

exports_router = APIRouter(tags=["exportsV1"])

@exports_router.get("/price-list", response_class=FileResponse)
async def export_price_list(
    branch_id: str = Header(...),
) -> FileResponse:
    return await exports_controller.export_price_list(branch_id)
