from kardex.repos.v1.common.filter_params import (
    ReceiptCancellationRequestFilterParams,
)
from kardex.tools import ReceiptCancellationRequestNotFound

from .data import ReceiptCancellationRequestsDataSource
from .models import ReceiptCancellationRequestInDb


class ReceiptCancellationRequestsRepository:
    _instance: "ReceiptCancellationRequestsRepository | None" = None

    def __init__(
        self, datasource: ReceiptCancellationRequestsDataSource
    ) -> None:
        self._datasource = datasource

    @classmethod
    def get_instance(cls) -> "ReceiptCancellationRequestsRepository":
        if cls._instance is None:
            cls._instance = cls(ReceiptCancellationRequestsDataSource())
        return cls._instance

    async def get_all_requests(
        self, params: ReceiptCancellationRequestFilterParams
    ) -> list[ReceiptCancellationRequestInDb]:
        raw_list = await self._datasource.get_all_requests(params)
        return [
            ReceiptCancellationRequestInDb.model_validate(item) for item in raw_list
        ]

    async def count_pending_requests(self, branch_id: str | None = None) -> int:
        return await self._datasource.count_pending_requests(branch_id)

    async def get_request_by_id(
        self, request_id: str
    ) -> ReceiptCancellationRequestInDb:
        raw = await self._datasource.get_request_by_id(request_id)
        if raw is None:
            raise ReceiptCancellationRequestNotFound(
                f"ReceiptCancellationRequest {request_id} not found",
                request_id=request_id,
            )
        return ReceiptCancellationRequestInDb.model_validate(raw)
