from fastapi import APIRouter, Depends, Query

from app_middleware import auth_middleware
from kardex.repos.v1.shifts import ShiftArqueoResponse
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


@composite_router.get("/shift-arqueo/{shift_id}")
async def get_shift_arqueo(
    shift_id: str,
    include_documents: bool = Query(True, alias="includeDocuments"),
    documents_limit: int = Query(
        500, alias="documentsLimit", ge=1, le=1000
    ),
) -> ShiftArqueoResponse:
    return await composite_controller.get_shift_arqueo(
        shift_id=shift_id,
        include_documents=include_documents,
        documents_limit=documents_limit,
    )
