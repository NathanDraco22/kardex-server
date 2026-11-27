from typing import Any

from kardex.repos.v1.common.filter_params import (
    InvoiceCancellationRequestFilterParams,
)
from kardex.services.mongo_collections.v1 import InvoiceCancellationRequestsCollection


class InvoiceCancellationRequestsDataSource:
    def __init__(
        self,
        collection: InvoiceCancellationRequestsCollection | None = None,
    ) -> None:
        self._collection = collection

    @property
    def collection(self) -> InvoiceCancellationRequestsCollection:
        return self._collection or InvoiceCancellationRequestsCollection.get_instance()

    async def get_all_requests(
        self, params: InvoiceCancellationRequestFilterParams
    ) -> list[dict[str, Any]]:
        return await self.collection.fetch_all_requests(
            **params.model_dump(exclude_none=True)
        )

    async def count_pending_requests(self, branch_id: str | None = None) -> int:
        return await self.collection.count_pending_requests(branch_id)

    async def get_request_by_id(self, request_id: str) -> dict[str, Any] | None:
        return await self.collection.fetch_request_by_id(request_id)
