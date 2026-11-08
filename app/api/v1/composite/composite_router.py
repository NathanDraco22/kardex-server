from fastapi import APIRouter, Depends, Query

from app_middleware import auth_middleware
from .composite_controller import composite_controller
from .composite_models import ClientPendingInvoicesCompositeResponse

composite_router = APIRouter(
    tags=["compositeV1"], dependencies=[Depends(auth_middleware)]
)


@composite_router.get("/client-pending-invoices")
async def get_client_pending_invoices(
    client_id: str = Query(..., alias="clientId"),
    branch_id: str = Query(..., alias="branchId"),
) -> ClientPendingInvoicesCompositeResponse:
    return await composite_controller.get_client_pending_invoices(
        client_id=client_id,
        branch_id=branch_id,
    )
