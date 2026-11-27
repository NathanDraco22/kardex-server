from kardex.core.invoice_cancellation_register import (
    approve_cancellation_request,
    cancel_cancellation_request,
    create_cancellation_request,
    reject_cancellation_request,
)
from kardex.repos.v1.common.filter_params import (
    InvoiceCancellationRequestFilterParams,
)
from kardex.repos.v1.invoice_cancellation_requests import (
    ApproveInvoiceCancellationRequest,
    CancelInvoiceCancellationRequest,
    CreateInvoiceCancellationRequest,
    InvoiceCancellationRequestInDb,
    InvoiceCancellationRequestsDataSource,
    InvoiceCancellationRequestsRepository,
    RejectInvoiceCancellationRequest,
)
from responses.v1 import ListResponse


class InvoiceCancellationRequestsController:
    def __init__(
        self,
        repo: InvoiceCancellationRequestsRepository,
    ) -> None:
        self.repo = repo

    async def create_request(
        self, body: CreateInvoiceCancellationRequest
    ) -> InvoiceCancellationRequestInDb:
        return await create_cancellation_request(body)

    async def get_all_requests(
        self, params: InvoiceCancellationRequestFilterParams
    ) -> ListResponse[InvoiceCancellationRequestInDb]:
        items = await self.repo.get_all_requests(params)
        return ListResponse(count=len(items), data=items)

    async def count_pending_requests(
        self, branch_id: str | None = None
    ) -> dict[str, int]:
        count = await self.repo.count_pending_requests(branch_id)
        return {"count": count}

    async def get_request_by_id(
        self, request_id: str
    ) -> InvoiceCancellationRequestInDb:
        return await self.repo.get_request_by_id(request_id)

    async def approve_request(
        self, request_id: str, body: ApproveInvoiceCancellationRequest
    ) -> InvoiceCancellationRequestInDb:
        return await approve_cancellation_request(
            request_id=request_id,
            reviewed_by=body.reviewedBy,
            review_notes=body.reviewNotes,
        )

    async def reject_request(
        self, request_id: str, body: RejectInvoiceCancellationRequest
    ) -> InvoiceCancellationRequestInDb:
        return await reject_cancellation_request(
            request_id=request_id,
            reviewed_by=body.reviewedBy,
            review_notes=body.reviewNotes,
        )

    async def cancel_request(
        self, request_id: str, body: CancelInvoiceCancellationRequest
    ) -> InvoiceCancellationRequestInDb:
        return await cancel_cancellation_request(
            request_id=request_id,
            cancelled_by=body.cancelledBy,
        )


invoice_cancellation_requests_controller = InvoiceCancellationRequestsController(
    repo=InvoiceCancellationRequestsRepository(
        datasource=InvoiceCancellationRequestsDataSource()
    )
)
