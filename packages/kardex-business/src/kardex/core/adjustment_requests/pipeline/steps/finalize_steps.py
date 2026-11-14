from kardex.repos.v1.adjustment_requests import AdjustmentRequestInDb
from kardex.services.mongo_collections.v1 import AdjustmentRequestsCollection
from kardex.tools import InvalidOperation

from ..base import PipelineStep
from ..context import AdjustmentRequestContext, AdjustmentRequestPipelineResult


class ApproveRequestStep(PipelineStep[AdjustmentRequestContext]):
    """Marca la solicitud como aprobada y guarda las referencias a los documentos."""

    def __init__(self, adjustment_requests_col: AdjustmentRequestsCollection):
        self.adjustment_requests_col = adjustment_requests_col

    async def execute(self, context: AdjustmentRequestContext) -> None:
        request = context.request

        updated_data = {
            "status": "approved",
            "approvedBy": context.approved_by.model_dump(),
            "approvedAt": context.now,
            "updatedAt": context.now,
            "adjustEntryId": context.entry_doc.id if context.entry_doc else None,
            "adjustEntryDocNumber": (
                context.entry_doc.docNumber if context.entry_doc else None
            ),
            "adjustExitId": context.exit_doc.id if context.exit_doc else None,
            "adjustExitDocNumber": (
                context.exit_doc.docNumber if context.exit_doc else None
            ),
            "entryTotal": request.entryTotal,
            "exitTotal": request.exitTotal,
        }

        updated = await self.adjustment_requests_col.approve_with_session(
            request.id,
            updated_data,
            session=context.session,
            expected_updated_at=request.updatedAt,
        )

        if updated is None:
            current = await self.adjustment_requests_col.fetch_adjustment_request_by_id(
                request.id,
                session=context.session,
            )
            if current is not None and current.get("status") == "pending":
                raise InvalidOperation("REQUEST_CHANGED_RETRY")

            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_APPROVED")

        context.updated_request = AdjustmentRequestInDb.model_validate(updated)


class BuildResultStep(PipelineStep[AdjustmentRequestContext]):
    """Construye el resultado final del pipeline."""

    async def execute(self, context: AdjustmentRequestContext) -> None:
        request = context.updated_request
        if request is None:
            raise InvalidOperation("PIPELINE_RESULT_MISSING_REQUEST")

        context.result = AdjustmentRequestPipelineResult(
            request=request,
            adjust_entry=context.entry_doc,
            adjust_exit=context.exit_doc,
        )
