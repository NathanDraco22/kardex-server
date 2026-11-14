import re
from typing import Any

from pymongo import IndexModel, ReturnDocument

from kardex.services import BaseMongoCollection


class AdjustmentRequestsCollection(BaseMongoCollection):
    collection_name = "AdjustmentRequests"

    async def create_adjustment_request_with_session(
        self, doc: dict, session: Any
    ) -> None:
        collection = self._collection
        await collection.insert_one(doc, session=session)

    async def fetch_all_adjustment_requests(
        self, **filters
    ) -> list[dict[str, Any]]:
        collection = self._collection

        offset = filters.pop("offset", 0)
        limit = filters.pop("limit", 50)

        query: dict[str, Any] = {"isDeleted": {"$ne": True}}

        branch_id = filters.pop("branchId", None)
        if branch_id:
            query["branchId"] = branch_id

        status = filters.pop("status", None)
        if status:
            query["status"] = status

        created_by = filters.pop("createdBy", None)
        if created_by:
            query["createdBy.id"] = created_by

        start_date = filters.pop("startDate", None)
        end_date = filters.pop("endDate", None)

        date_filter: dict[str, Any] = {}
        if start_date is not None:
            date_filter["$gte"] = start_date
        if end_date is not None:
            date_filter["$lte"] = end_date
        if date_filter:
            query["createdAt"] = date_filter

        doc_number = filters.pop("docNumber", None)
        if doc_number:
            query["docNumber"] = {
                "$regex": re.escape(doc_number),
                "$options": "i",
            }

        cursor = (
            collection.find(query)
            .sort("createdAt", -1)
            .skip(offset or 0)
            .limit(limit or 50)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_adjustment_request_by_id(
        self, adjustment_request_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {
                "id": adjustment_request_id,
                "isDeleted": {"$ne": True},
            },
            session=session,
        )

    async def update_adjustment_request_by_id(
        self,
        adjustment_request_id: str,
        data: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        return await collection.find_one_and_update(
            {
                "id": adjustment_request_id,
                "status": "pending",
                "isDeleted": {"$ne": True},
            },
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )

    async def soft_delete_adjustment_request_by_id(
        self, adjustment_request_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        from kardex.tools import TimeTools

        collection = self._collection

        return await collection.find_one_and_update(
            {
                "id": adjustment_request_id,
                "status": "pending",
                "isDeleted": {"$ne": True},
            },
            {
                "$set": {
                    "isDeleted": True,
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                }
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

    async def approve_with_session(
        self,
        request_id: str,
        data: dict,
        session: Any,
        expected_updated_at: int | None = None,
    ) -> dict[str, Any] | None:
        collection = self._collection

        query: dict[str, Any] = {
            "id": request_id,
            "status": "pending",
            "isDeleted": {"$ne": True},
            "updatedAt": expected_updated_at,
        }

        return await collection.find_one_and_update(
            query,
            {"$set": data},
            session=session,
            return_document=ReturnDocument.AFTER,
        )

    async def cancel_with_session(
        self, request_id: str, data: dict, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection

        return await collection.find_one_and_update(
            {
                "id": request_id,
                "status": "pending",
                "isDeleted": {"$ne": True},
            },
            {"$set": data},
            session=session,
            return_document=ReturnDocument.AFTER,
        )

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel(
                    [("docNumber", 1), ("branchId", 1)],
                    unique=True,
                ),
                IndexModel([("branchId", 1), ("status", 1), ("createdAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
                IndexModel([("createdAt", -1)]),
            ]
        )
