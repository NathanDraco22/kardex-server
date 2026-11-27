from typing import Any

from kardex.repos.v1.common.filter_params import (
    ReceiptCancellationRequestFilterParams,
)
from kardex.services.mongo_collections.v1 import ReceiptCancellationRequestsCollection


class ReceiptCancellationRequestsDataSource:
    def __init__(
        self,
        collection: ReceiptCancellationRequestsCollection | None = None,
    ) -> None:
        self._collection = (
            collection or ReceiptCancellationRequestsCollection.get_instance()
        )

    async def get_all_requests(
        self, params: ReceiptCancellationRequestFilterParams
    ) -> list[dict[str, Any]]:
        return await self._collection.fetch_all_requests(
            **params.model_dump(exclude_none=True)
        )

    async def count_pending_requests(self, branch_id: str | None = None) -> int:
        return await self._collection.count_pending_requests(branch_id)

    async def get_request_by_id(self, request_id: str) -> dict[str, Any] | None:
        return await self._collection.fetch_request_by_id(request_id)
