from fastapi import APIRouter, Depends

from app_middleware import auth_middleware
from kardex.repos.v1.common.filter_params import (
    ReceiptCancellationRequestFilterParams,
)
from kardex.repos.v1.receipt_cancellation_requests import (
    ApproveReceiptCancellationRequest,
    CancelReceiptCancellationRequest,
    CreateReceiptCancellationRequest,
    ReceiptCancellationRequestInDb,
    RejectReceiptCancellationRequest,
)
from responses.v1 import ListResponse

from .receipt_cancellation_requests_controller import (
    receipt_cancellation_requests_controller,
)

receipt_cancellation_requests_router = APIRouter(
    tags=["receiptCancellationRequestsV1"],
    dependencies=[Depends(auth_middleware)],
)


@receipt_cancellation_requests_router.post("")
async def create_receipt_cancellation_request(
    body: CreateReceiptCancellationRequest,
) -> ReceiptCancellationRequestInDb:
    return await receipt_cancellation_requests_controller.create_request(body)


@receipt_cancellation_requests_router.get("")
async def get_all_receipt_cancellation_requests(
    params: ReceiptCancellationRequestFilterParams = Depends(),
) -> ListResponse[ReceiptCancellationRequestInDb]:
    return await receipt_cancellation_requests_controller.get_all_requests(params)


@receipt_cancellation_requests_router.get("/pending/count")
async def count_pending_receipt_cancellation_requests(
    branchId: str | None = None,
) -> dict[str, int]:
    return await receipt_cancellation_requests_controller.count_pending_requests(
        branchId
    )


@receipt_cancellation_requests_router.get("/{request_id}")
async def get_receipt_cancellation_request_by_id(
    request_id: str,
) -> ReceiptCancellationRequestInDb:
    return await receipt_cancellation_requests_controller.get_request_by_id(
        request_id
    )


@receipt_cancellation_requests_router.post("/{request_id}/approve")
async def approve_receipt_cancellation_request(
    request_id: str,
    body: ApproveReceiptCancellationRequest,
) -> ReceiptCancellationRequestInDb:
    return await receipt_cancellation_requests_controller.approve_request(
        request_id, body
    )


@receipt_cancellation_requests_router.post("/{request_id}/reject")
async def reject_receipt_cancellation_request(
    request_id: str,
    body: RejectReceiptCancellationRequest,
) -> ReceiptCancellationRequestInDb:
    return await receipt_cancellation_requests_controller.reject_request(
        request_id, body
    )


@receipt_cancellation_requests_router.post("/{request_id}/cancel")
async def cancel_receipt_cancellation_request(
    request_id: str,
    body: CancelReceiptCancellationRequest,
) -> ReceiptCancellationRequestInDb:
    return await receipt_cancellation_requests_controller.cancel_request(
        request_id, body
    )
