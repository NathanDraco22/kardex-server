from kardex.repos.v1.adjustment_requests import AdjustmentRequestInDb
from kardex.repos.v1.common.models import UserInfo
from kardex.services import MongoService
from kardex.tools import InvalidOperation

from .pipeline import AdjustmentRequestContext, build_adjustment_request_pipeline


async def process_adjustment_request(
    adjustment_request: AdjustmentRequestInDb,
    approved_by: UserInfo,
    approver_role: str,
) -> AdjustmentRequestInDb:
    """Orquesta la aprobación de una solicitud dentro de una sola transacción.

    Los pasos concretos viven en `pipeline/steps/` y no abren transacciones por
    su cuenta. Si un paso falla, la transacción aborta y no se persiste ningún
    documento ni movimiento de inventario.
    """

    async with MongoService().client.start_session() as session:
        async with await session.start_transaction():
            context = AdjustmentRequestContext(
                request=adjustment_request,
                approved_by=approved_by,
                approver_role=approver_role,
                session=session,
            )

            pipeline_result = await build_adjustment_request_pipeline().run(context)
            result = pipeline_result.context.result

            if result is None:
                raise InvalidOperation("PIPELINE_RESULT_MISSING")

            return result.request
