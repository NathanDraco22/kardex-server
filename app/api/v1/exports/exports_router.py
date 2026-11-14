from fastapi import APIRouter, Depends, Header
from fastapi.responses import FileResponse

from app_middleware import auth_middleware

from .exports_controller import exports_controller

exports_router = APIRouter(
    tags=["exportsV1"],
    dependencies=[Depends(auth_middleware)],
)


@exports_router.get("/price-list", response_class=FileResponse)
async def export_price_list(
    branch_id: str = Header(...),
) -> FileResponse:
    return await exports_controller.export_price_list(branch_id)
