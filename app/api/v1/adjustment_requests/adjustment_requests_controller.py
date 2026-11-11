from fastapi import BackgroundTasks, HTTPException, status

from core.app_notifier.app_notifier import AppNotifier
from responses.v1.list_response import ListResponse
from kardex.core.adjustment_requests import AdjustmentRequestManager
from kardex.repos.v1.adjustment_requests import (
    AdjustmentRequestInDb,
    AdjustmentRequestsDataSource,
    AdjustmentRequestsRepository,
    ApproveAdjustmentRequest,
    CancelAdjustmentRequest,
    CreateAdjustmentRequest,
    UpdateAdjustmentRequest,
)
from kardex.repos.v1.common.filter_params import AdjustmentRequestFilterParams
from kardex.tools import BranchesTool


class AdjustmentRequestsController:
    def __init__(
        self,
        adjustment_requests_repo: AdjustmentRequestsRepository,
        adjustment_request_manager: AdjustmentRequestManager,
    ) -> None:
        self.adjustment_requests_repo = adjustment_requests_repo
        self.adjustment_request_manager = adjustment_request_manager

    async def create_adjustment_request(
        self, body: CreateAdjustmentRequest
    ) -> AdjustmentRequestInDb:
        return await self.adjustment_requests_repo.create_adjustment_request(body)

    async def get_all_adjustment_requests(
        self, query: AdjustmentRequestFilterParams
    ) -> ListResponse[AdjustmentRequestInDb]:
        adjustment_requests = (
            await self.adjustment_requests_repo.get_all_adjustment_requests(query)
        )
        return ListResponse(
            count=len(adjustment_requests),
            data=adjustment_requests,
        )

    async def get_adjustment_request_by_id(
        self, adjustment_request_id: str
    ) -> AdjustmentRequestInDb:
        adjustment_request = (
            await self.adjustment_requests_repo.get_adjustment_request_by_id(
                adjustment_request_id
            )
        )
        if adjustment_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustmentRequest not found",
            )
        return adjustment_request

    async def update_adjustment_request_by_id(
        self, adjustment_request_id: str, body: UpdateAdjustmentRequest
    ) -> AdjustmentRequestInDb:
        updated = await self.adjustment_requests_repo.update_adjustment_request_by_id(
            adjustment_request_id, body
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustmentRequest not found",
            )
        return updated

    async def delete_adjustment_request_by_id(
        self, adjustment_request_id: str
    ) -> AdjustmentRequestInDb:
        deleted = await self.adjustment_requests_repo.delete_adjustment_request_by_id(
            adjustment_request_id
        )
        if deleted is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustmentRequest not found",
            )
        return deleted

    async def approve_adjustment_request(
        self,
        adjustment_request_id: str,
        body: ApproveAdjustmentRequest,
        bg_tasks: BackgroundTasks,
    ) -> AdjustmentRequestInDb:
        existing = (
            await self.adjustment_requests_repo.get_adjustment_request_by_id(
                adjustment_request_id
            )
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustmentRequest not found",
            )

        result = await self.adjustment_request_manager.approve(
            adjustment_request_id,
            body.approvedBy,
        )

        doc_branch = BranchesTool().get_branch_by_id(result.branchId)

        if doc_branch is not None:
            if result.adjustEntryDocNumber:
                bg_tasks.add_task(
                    AppNotifier().notify_adjustments,
                    doc_branch.name,
                    result.adjustEntryDocNumber,
                    "in",
                    result.createdBy.name,
                )

            if result.adjustExitDocNumber:
                bg_tasks.add_task(
                    AppNotifier().notify_adjustments,
                    doc_branch.name,
                    result.adjustExitDocNumber,
                    "out",
                    result.createdBy.name,
                )

        return result

    async def cancel_adjustment_request(
        self,
        adjustment_request_id: str,
        body: CancelAdjustmentRequest,
    ) -> AdjustmentRequestInDb:
        existing = (
            await self.adjustment_requests_repo.get_adjustment_request_by_id(
                adjustment_request_id
            )
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustmentRequest not found",
            )

        return await self.adjustment_request_manager.cancel(
            adjustment_request_id,
            body.cancelledBy,
            body.reason,
        )


adjustment_requests_controller = AdjustmentRequestsController(
    adjustment_requests_repo=AdjustmentRequestsRepository(
        adjustment_requests_ds=AdjustmentRequestsDataSource(),
    ),
    adjustment_request_manager=AdjustmentRequestManager(),
)
