from typing import Any

from pymongo import IndexModel, ReturnDocument

from kardex.services import BaseMongoCollection
from kardex.tools import build_query


class ReceiptCancellationRequestsCollection(BaseMongoCollection):
    collection_name = "ReceiptCancellationRequests"

    async def create_request(self, request_data: dict[str, Any]) -> None:
        await self._collection.insert_one(request_data)

    async def fetch_all_requests(self, **kwargs: Any) -> list[dict[str, Any]]:
        result = build_query("createdAt", **kwargs)
        if result.query.get("requestedById"):
            result.query["requestedBy.id"] = result.query.pop("requestedById")

        cursor = (
            self._collection.find(result.query)
            .skip(result.offset)
            .limit(result.limit)
            .sort("createdAt", -1)
        )
        items = await cursor.to_list(length=None)
        await cursor.close()
        return items

    async def count_pending_requests(self, branch_id: str | None = None) -> int:
        query: dict[str, Any] = {"status": "pending"}
        if branch_id:
            query["branchId"] = branch_id
        return await self._collection.count_documents(query)

    async def fetch_request_by_id(self, request_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"id": request_id})

    async def fetch_request_by_id_with_session(
        self, request_id: str, session: Any
    ) -> dict[str, Any] | None:
        return await self._collection.find_one({"id": request_id}, session=session)

    async def fetch_pending_by_receipt_id(
        self, receipt_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        return await self._collection.find_one(
            {"receiptId": receipt_id, "status": "pending"},
            session=session,
        )

    async def transition_request_status(
        self,
        request_id: str,
        update_data: dict[str, Any],
        session: Any = None,
    ) -> dict[str, Any] | None:
        return await self._collection.find_one_and_update(
            {"id": request_id, "status": "pending"},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

    async def create_indexes(self) -> None:
        await self._collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("receiptId", 1)]),
                IndexModel([("branchId", 1), ("status", 1), ("createdAt", -1)]),
                IndexModel(
                    [("receiptId", 1)],
                    unique=True,
                    partialFilterExpression={"status": "pending"},
                    name="ux_pending_cancellation_per_receipt",
                ),
            ]
        )
