from fastapi import APIRouter, Depends

from app_middleware import auth_middleware
from kardex.repos.v1.common.filter_params import (
    InvoiceCancellationRequestFilterParams,
)
from kardex.repos.v1.invoice_cancellation_requests import (
    ApproveInvoiceCancellationRequest,
    CancelInvoiceCancellationRequest,
    CreateInvoiceCancellationRequest,
    InvoiceCancellationRequestInDb,
    RejectInvoiceCancellationRequest,
)
from responses.v1 import ListResponse

from .invoice_cancellation_requests_controller import (
    invoice_cancellation_requests_controller,
)

invoice_cancellation_requests_router = APIRouter(
    tags=["invoiceCancellationRequestsV1"],
    dependencies=[Depends(auth_middleware)],
)


@invoice_cancellation_requests_router.post("")
async def create_invoice_cancellation_request(
    body: CreateInvoiceCancellationRequest,
) -> InvoiceCancellationRequestInDb:
    return await invoice_cancellation_requests_controller.create_request(body)


@invoice_cancellation_requests_router.get("")
async def get_all_invoice_cancellation_requests(
    params: InvoiceCancellationRequestFilterParams = Depends(),
) -> ListResponse[InvoiceCancellationRequestInDb]:
    return await invoice_cancellation_requests_controller.get_all_requests(params)


@invoice_cancellation_requests_router.get("/pending/count")
async def count_pending_invoice_cancellation_requests(
    branchId: str | None = None,
) -> dict[str, int]:
    return await invoice_cancellation_requests_controller.count_pending_requests(
        branchId
    )


@invoice_cancellation_requests_router.get("/{request_id}")
async def get_invoice_cancellation_request_by_id(
    request_id: str,
) -> InvoiceCancellationRequestInDb:
    return await invoice_cancellation_requests_controller.get_request_by_id(
        request_id
    )


@invoice_cancellation_requests_router.post("/{request_id}/approve")
async def approve_invoice_cancellation_request(
    request_id: str,
    body: ApproveInvoiceCancellationRequest,
) -> InvoiceCancellationRequestInDb:
    return await invoice_cancellation_requests_controller.approve_request(
        request_id, body
    )


@invoice_cancellation_requests_router.post("/{request_id}/reject")
async def reject_invoice_cancellation_request(
    request_id: str,
    body: RejectInvoiceCancellationRequest,
) -> InvoiceCancellationRequestInDb:
    return await invoice_cancellation_requests_controller.reject_request(
        request_id, body
    )


@invoice_cancellation_requests_router.post("/{request_id}/cancel")
async def cancel_invoice_cancellation_request(
    request_id: str,
    body: CancelInvoiceCancellationRequest,
) -> InvoiceCancellationRequestInDb:
    return await invoice_cancellation_requests_controller.cancel_request(
        request_id, body
    )
