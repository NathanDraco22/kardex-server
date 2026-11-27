from kardex.core.receipt_cancellation_register import (
    approve_receipt_cancellation_request,
    cancel_receipt_cancellation_request,
    create_receipt_cancellation_request,
    reject_receipt_cancellation_request,
)
from kardex.repos.v1.common.filter_params import (
    ReceiptCancellationRequestFilterParams,
)
from kardex.repos.v1.receipt_cancellation_requests import (
    ApproveReceiptCancellationRequest,
    CancelReceiptCancellationRequest,
    CreateReceiptCancellationRequest,
    ReceiptCancellationRequestInDb,
    ReceiptCancellationRequestsDataSource,
    ReceiptCancellationRequestsRepository,
    RejectReceiptCancellationRequest,
)
from responses.v1 import ListResponse


class ReceiptCancellationRequestsController:
    def __init__(
        self,
        repo: ReceiptCancellationRequestsRepository,
    ) -> None:
        self.repo = repo

    async def create_request(
        self, body: CreateReceiptCancellationRequest
    ) -> ReceiptCancellationRequestInDb:
        return await create_receipt_cancellation_request(body)

    async def get_all_requests(
        self, params: ReceiptCancellationRequestFilterParams
    ) -> ListResponse[ReceiptCancellationRequestInDb]:
        items = await self.repo.get_all_requests(params)
        return ListResponse(count=len(items), data=items)

    async def count_pending_requests(
        self, branch_id: str | None = None
    ) -> dict[str, int]:
        count = await self.repo.count_pending_requests(branch_id)
        return {"count": count}

    async def get_request_by_id(
        self, request_id: str
    ) -> ReceiptCancellationRequestInDb:
        return await self.repo.get_request_by_id(request_id)

    async def approve_request(
        self, request_id: str, body: ApproveReceiptCancellationRequest
    ) -> ReceiptCancellationRequestInDb:
        return await approve_receipt_cancellation_request(
            request_id=request_id,
            reviewed_by=body.reviewedBy,
            review_notes=body.reviewNotes,
        )

    async def reject_request(
        self, request_id: str, body: RejectReceiptCancellationRequest
    ) -> ReceiptCancellationRequestInDb:
        return await reject_receipt_cancellation_request(
            request_id=request_id,
            reviewed_by=body.reviewedBy,
            review_notes=body.reviewNotes,
        )

    async def cancel_request(
        self, request_id: str, body: CancelReceiptCancellationRequest
    ) -> ReceiptCancellationRequestInDb:
        return await cancel_receipt_cancellation_request(
            request_id=request_id,
            cancelled_by=body.cancelledBy,
        )


receipt_cancellation_requests_controller = ReceiptCancellationRequestsController(
    repo=ReceiptCancellationRequestsRepository(
        datasource=ReceiptCancellationRequestsDataSource()
    )
)
