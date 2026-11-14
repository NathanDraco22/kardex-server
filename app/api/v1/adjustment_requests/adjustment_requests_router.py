from fastapi import APIRouter, BackgroundTasks, Depends

from app_middleware import auth_middleware
from responses.v1 import ListResponse
from kardex.repos.v1.adjustment_requests import (
    AdjustmentRequestInDb,
    ApproveAdjustmentRequest,
    CancelAdjustmentRequest,
    CreateAdjustmentRequest,
    UpdateAdjustmentRequest,
)
from kardex.repos.v1.common.filter_params import AdjustmentRequestFilterParams

from .adjustment_requests_controller import adjustment_requests_controller


adjustment_requests_router = APIRouter(
    tags=["adjustment_requestsV1"], dependencies=[Depends(auth_middleware)]
)


@adjustment_requests_router.post("")
async def create_adjustment_request(
    body: CreateAdjustmentRequest,
) -> AdjustmentRequestInDb:
    return await adjustment_requests_controller.create_adjustment_request(body)


@adjustment_requests_router.get("")
async def get_all_adjustment_requests(
    query: AdjustmentRequestFilterParams = Depends(),
) -> ListResponse[AdjustmentRequestInDb]:
    return await adjustment_requests_controller.get_all_adjustment_requests(query)


@adjustment_requests_router.get("/{adjustment_request_id}")
async def get_adjustment_request_by_id(
    adjustment_request_id: str,
) -> AdjustmentRequestInDb:
    return await adjustment_requests_controller.get_adjustment_request_by_id(
        adjustment_request_id
    )


@adjustment_requests_router.patch("/{adjustment_request_id}")
async def update_adjustment_request_by_id(
    adjustment_request_id: str, body: UpdateAdjustmentRequest
) -> AdjustmentRequestInDb:
    return await adjustment_requests_controller.update_adjustment_request_by_id(
        adjustment_request_id, body
    )


@adjustment_requests_router.delete("/{adjustment_request_id}")
async def delete_adjustment_request_by_id(
    adjustment_request_id: str,
) -> AdjustmentRequestInDb:
    return await adjustment_requests_controller.delete_adjustment_request_by_id(
        adjustment_request_id
    )


@adjustment_requests_router.post("/{adjustment_request_id}/approve")
async def approve_adjustment_request(
    adjustment_request_id: str,
    body: ApproveAdjustmentRequest,
    bg_tasks: BackgroundTasks,
) -> AdjustmentRequestInDb:
    return await adjustment_requests_controller.approve_adjustment_request(
        adjustment_request_id, body, bg_tasks
    )


@adjustment_requests_router.post("/{adjustment_request_id}/cancel")
async def cancel_adjustment_request(
    adjustment_request_id: str,
    body: CancelAdjustmentRequest,
) -> AdjustmentRequestInDb:
    return await adjustment_requests_controller.cancel_adjustment_request(
        adjustment_request_id, body
    )
