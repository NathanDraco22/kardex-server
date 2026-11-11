import asyncio

from pymongo.errors import OperationFailure

from kardex.core.adjust_ledger.adjust_ledger import adjust_mutex
from kardex.repos.v1.adjustment_requests import (
    AdjustmentRequestInDb,
    AdjustmentRequestsDataSource,
    AdjustmentRequestsRepository,
)
from kardex.repos.v1.common.models import UserInfo
from kardex.tools import (
    InsufficientBalanceError,
    InvalidOperation,
    KardexException,
)

from .process_adjustment_request import process_adjustment_request


class AdjustmentRequestManager:
    def __init__(self) -> None:
        self.adjustment_requests_repo = AdjustmentRequestsRepository(
            adjustment_requests_ds=AdjustmentRequestsDataSource()
        )

    async def approve(
        self,
        request_id: str,
        approved_by: UserInfo,
    ) -> AdjustmentRequestInDb:
        adjustment_request = (
            await self.adjustment_requests_repo.get_adjustment_request_by_id(
                request_id
            )
        )

        if adjustment_request is None or adjustment_request.isDeleted:
            raise InvalidOperation("ADJUSTMENT_REQUEST_NOT_FOUND")

        if adjustment_request.status != "pending":
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_APPROVED")

        if approved_by.id == adjustment_request.createdBy.id:
            raise InvalidOperation("SELF_APPROVAL_NOT_ALLOWED")

        if not any(item.difference != 0 for item in adjustment_request.items):
            raise InvalidOperation("ADJUSTMENT_REQUEST_WITHOUT_DIFFERENCES")

        locked = False
        await asyncio.wait_for(adjust_mutex.acquire(), timeout=7)
        locked = True

        try:
            max_retries = 3

            for _ in range(max_retries):
                try:
                    return await process_adjustment_request(
                        adjustment_request,
                        approved_by,
                    )

                except InsufficientBalanceError as error:
                    raise InsufficientBalanceError(
                        "INSUFFICIENT_STOCK_FOR_ADJUSTMENT",
                        product_id=error.product_id,
                        product_name=error.product_name,
                    )

                except OperationFailure as error:
                    if error.code == 112:
                        await asyncio.sleep(0.3)
                        continue

                    raise InvalidOperation(
                        "Error processing adjustment request \n" + str(error)
                    )

                except KardexException:
                    raise

                except Exception as error:
                    raise InvalidOperation(
                        "Error processing adjustment request \n" + str(error)
                    )

            raise InvalidOperation("Server is too busy, try again later")

        finally:
            if locked:
                adjust_mutex.release()

    async def cancel(
        self,
        request_id: str,
        cancelled_by: UserInfo,
        reason: str | None = None,
    ) -> AdjustmentRequestInDb:
        return await self.adjustment_requests_repo.cancel_adjustment_request(
            request_id,
            cancelled_by,
            reason,
        )
