from typing import Any

from kardex.services.mongo_collections.v1 import AdjustmentRequestsCollection


class AdjustmentRequestsDataSource:
    async def create_adjustment_request(
        self, adjustment_request: dict[str, Any]
    ) -> dict[str, Any]:
        collection = AdjustmentRequestsCollection.get_instance()
        await collection.create_adjustment_request_with_session(
            adjustment_request, session=None
        )
        return adjustment_request

    async def get_all_adjustment_requests(
        self, **filters
    ) -> list[dict[str, Any]]:
        collection = AdjustmentRequestsCollection.get_instance()
        return await collection.fetch_all_adjustment_requests(**filters)

    async def get_adjustment_request_by_id(
        self, adjustment_request_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustmentRequestsCollection.get_instance()
        return await collection.fetch_adjustment_request_by_id(adjustment_request_id)

    async def update_adjustment_request_by_id(
        self, adjustment_request_id: str, adjustment_request: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = AdjustmentRequestsCollection.get_instance()
        return await collection.update_adjustment_request_by_id(
            adjustment_request_id, adjustment_request
        )

    async def delete_adjustment_request_by_id(
        self, adjustment_request_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustmentRequestsCollection.get_instance()
        return await collection.soft_delete_adjustment_request_by_id(
            adjustment_request_id
        )

    async def cancel_adjustment_request(
        self, adjustment_request_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = AdjustmentRequestsCollection.get_instance()
        return await collection.cancel_with_session(adjustment_request_id, data)
