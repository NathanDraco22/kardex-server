from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class ExpirationLogsCollection(BaseMongoCollection):
    collection_name = "ExpirationLog"

    async def create_expiration_log(self, expiration_log: dict) -> None:
        collection = self._collection
        await collection.insert_one(expiration_log)

    async def create_many_expiration_logs(self, expiration_logs: list[dict]) -> None:
        collection = self._collection
        await collection.insert_many(expiration_logs)

    async def fetch_all_expiration_logs(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        cursor = collection.find(query).sort("expirationDate", 1)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": expiration_log_id})
        return result

    async def update_expiration_log_by_id(
        self,
        expiration_log_id: str,
        expiration_log: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": expiration_log_id},
            {"$set": expiration_log},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": expiration_log_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("branchId", 1)]),
                IndexModel([("expirationDate", 1)]),
            ]
        )

    async def has_near_expiration_date(self, target_date: int, branch_id: str) -> bool:
        collection = self._collection
        result = await collection.find_one(
            {
                "expirationDate": {"$lte": target_date},
                "branchId": branch_id,
            },
        )

        return result is not None
