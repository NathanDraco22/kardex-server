from typing import Any

from pymongo import IndexModel, ReturnDocument

from kardex.services import BaseMongoCollection


class ShiftsCollection(BaseMongoCollection):
    collection_name = "Shifts"

    async def create_shift(self, shift: dict, session: Any = None) -> None:
        collection = self._collection
        await collection.insert_one(shift, session=session)

    async def fetch_all_shifts(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query: dict[str, Any] = {}

        user_id = kwargs.get("userId")
        if user_id:
            query["openedBy.id"] = user_id

        branch_id = kwargs.get("branchId")
        if branch_id:
            query["branchId"] = branch_id

        status = kwargs.get("status")
        if status:
            query["status"] = status

        start_date = kwargs.get("startDate")
        end_date = kwargs.get("endDate")
        if start_date is not None or end_date is not None:
            date_filter: dict[str, Any] = {}
            if start_date is not None:
                date_filter["$gte"] = start_date
            if end_date is not None:
                date_filter["$lte"] = end_date
            query["openedAt"] = date_filter

        offset = int(kwargs.get("offset") or 0)
        limit = int(kwargs.get("limit") or 50)

        cursor = (
            collection.find(query)
            .sort("openedAt", -1)
            .skip(offset)
            .limit(limit)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_shift_by_id(
        self, shift_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": shift_id}, session=session
        )
        return result

    async def fetch_active_shift_by_user(
        self, user_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"openedBy.id": user_id, "status": "open"},
            session=session,
        )
        return result

    async def update_shift_by_id(
        self,
        shift_id: str,
        shift: dict,
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": shift_id},
            {"$set": shift},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def close_shift_by_id(
        self,
        shift_id: str,
        shift: dict,
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": shift_id, "status": "open"},
            {"$set": shift},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel(
                    [("openedBy.id", 1), ("status", 1)],
                    unique=True,
                    name="ux_open_shift_per_user",
                    partialFilterExpression={"status": "open"},
                ),
                IndexModel([("branchId", 1), ("status", 1), ("openedAt", -1)]),
            ]
        )

