from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class AdjustExitsCollection(BaseMongoCollection):
    collection_name = "AdjustExits"

    async def create_adjust_exit(self, adjust_exit: dict) -> None:
        collection = self._collection
        await collection.insert_one(adjust_exit)

    async def create_adjust_exit_with_session(
        self, adjust_exit: dict, session: Any
    ) -> None:
        collection = self._collection
        await collection.insert_one(adjust_exit, session=session)

    async def fetch_all_adjust_exits(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        offset = kwargs.pop("offset", 0)
        limit = kwargs.pop("limit", 50)

        end_date = kwargs.pop("endDate", None)

        query = kwargs

        if end_date:
            query["createdAt"] = {"$lte": end_date}

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_adjust_exit_by_id(
        self, adjust_exit_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": adjust_exit_id})
        return result

    async def fetch_adjust_exit_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"docNumber": doc_number, "branchId": branch_id}
        )
        return result

    async def update_adjust_exit_by_id(
        self,
        adjust_exit_id: str,
        adjust_exit: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": adjust_exit_id},
            {"$set": adjust_exit},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_adjust_exit_by_id(
        self, adjust_exit_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": adjust_exit_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel(
                    [("docNumber", 1), ("branchId", 1)],
                    unique=True,
                ),
                IndexModel([("branchId", 1), ("type", 1), ("createdAt", -1)]),
                IndexModel([("type", 1)]),
                IndexModel([("createdBy.id", 1)]),
                IndexModel([("createdAt", -1)]),
            ]
        )
