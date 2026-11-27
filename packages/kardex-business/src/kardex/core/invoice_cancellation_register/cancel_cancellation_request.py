from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.invoice_cancellation_requests import (
    InvoiceCancellationRequestInDb,
)
from kardex.services.mongo_collections.v1 import InvoiceCancellationRequestsCollection
from kardex.tools import (
    InvalidOperation,
    InvoiceCancellationRequestNotFound,
    TimeTools,
)


async def cancel_cancellation_request(
    request_id: str,
    cancelled_by: UserInfo,
) -> InvoiceCancellationRequestInDb:
    requests_col = InvoiceCancellationRequestsCollection.get_instance()
    now = TimeTools.get_now_in_milliseconds()

    updated = await requests_col.transition_request_status(
        request_id=request_id,
        update_data={
            "status": "cancelled",
            "reviewedBy": cancelled_by.model_dump(),
            "reviewedAt": now,
            "updatedAt": now,
        },
    )

    if updated is None:
        existing = await requests_col.fetch_request_by_id(request_id)
        if existing is None:
            raise InvoiceCancellationRequestNotFound(
                f"InvoiceCancellationRequest {request_id} not found",
                request_id=request_id,
            )
        raise InvalidOperation(
            f"La solicitud ya fue procesada (estado: {existing.get('status')})."
        )

    return InvoiceCancellationRequestInDb.model_validate(updated)
