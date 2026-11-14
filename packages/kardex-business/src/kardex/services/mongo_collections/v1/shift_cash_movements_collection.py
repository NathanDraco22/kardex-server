from typing import Any

from pymongo import IndexModel, ReturnDocument

from kardex.services import BaseMongoCollection


class ShiftCashMovementsCollection(BaseMongoCollection):
    collection_name = "ShiftCashMovements"

    async def create_shift_cash_movement(
        self, shift_cash_movement: dict, session: Any = None
    ) -> None:
        collection = self._collection
        await collection.insert_one(shift_cash_movement, session=session)

    async def fetch_all_shift_cash_movements(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query: dict[str, Any] = {"isDeleted": {"$ne": True}}

        shift_id = kwargs.get("shiftId")
        if shift_id:
            query["shiftId"] = shift_id

        branch_id = kwargs.get("branchId")
        if branch_id:
            query["branchId"] = branch_id

        movement_type = kwargs.get("type")
        if movement_type:
            query["type"] = movement_type

        start_date = kwargs.get("startDate")
        end_date = kwargs.get("endDate")
        if start_date is not None or end_date is not None:
            date_filter: dict[str, Any] = {}
            if start_date is not None:
                date_filter["$gte"] = start_date
            if end_date is not None:
                date_filter["$lte"] = end_date
            query["createdAt"] = date_filter

        offset = int(kwargs.get("offset") or 0)
        limit = int(kwargs.get("limit") or 50)

        cursor = (
            collection.find(query)
            .sort("createdAt", -1)
            .skip(offset)
            .limit(limit)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_shift_cash_movement_by_id(
        self, movement_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": movement_id, "isDeleted": {"$ne": True}}, session=session
        )
        return result

    async def update_shift_cash_movement_by_id(
        self,
        movement_id: str,
        shift_cash_movement: dict,
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": movement_id, "isDeleted": {"$ne": True}},
            {"$set": shift_cash_movement},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def soft_delete_shift_cash_movement_by_id(
        self, movement_id: str, deleted_at: int, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": movement_id, "isDeleted": {"$ne": True}},
            {"$set": {"isDeleted": True, "deletedAt": deleted_at}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def get_type_totals_by_shift(self, shift_id: str) -> list[dict[str, Any]]:
        collection = self._collection

        pipeline = [
            {"$match": {"shiftId": shift_id, "isDeleted": {"$ne": True}}},
            {
                "$group": {
                    "_id": "$type",
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1},
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        await cursor.close()

        return results

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("shiftId", 1)]),
                IndexModel([("branchId", 1), ("createdAt", -1)]),
            ]
        )
