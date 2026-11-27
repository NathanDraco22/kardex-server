from kardex.repos.v1.common.filter_params import (
    InvoiceCancellationRequestFilterParams,
)
from kardex.tools import InvoiceCancellationRequestNotFound

from .data import InvoiceCancellationRequestsDataSource
from .models import InvoiceCancellationRequestInDb


class InvoiceCancellationRequestsRepository:
    _instance: "InvoiceCancellationRequestsRepository | None" = None

    def __init__(
        self, datasource: InvoiceCancellationRequestsDataSource
    ) -> None:
        self._datasource = datasource

    @classmethod
    def get_instance(cls) -> "InvoiceCancellationRequestsRepository":
        if cls._instance is None:
            cls._instance = cls(InvoiceCancellationRequestsDataSource())
        return cls._instance

    async def get_all_requests(
        self, params: InvoiceCancellationRequestFilterParams
    ) -> list[InvoiceCancellationRequestInDb]:
        raw_list = await self._datasource.get_all_requests(params)
        return [
            InvoiceCancellationRequestInDb.model_validate(item) for item in raw_list
        ]

    async def count_pending_requests(self, branch_id: str | None = None) -> int:
        return await self._datasource.count_pending_requests(branch_id)

    async def get_request_by_id(
        self, request_id: str
    ) -> InvoiceCancellationRequestInDb:
        raw = await self._datasource.get_request_by_id(request_id)
        if raw is None:
            raise InvoiceCancellationRequestNotFound(
                f"InvoiceCancellationRequest {request_id} not found",
                request_id=request_id,
            )
        return InvoiceCancellationRequestInDb.model_validate(raw)
