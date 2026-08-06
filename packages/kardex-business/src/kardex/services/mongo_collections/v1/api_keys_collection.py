from typing import Any

from pymongo import IndexModel, ReturnDocument

from kardex.services import BaseMongoCollection


class ApiKeysCollection(BaseMongoCollection):
    collection_name = "ApiKeys"

    async def create_api_key(self, api_key: dict[str, Any]) -> None:
        collection = self._collection
        await collection.insert_one(api_key)

    async def fetch_all_api_keys(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find().sort("createdAt", -1)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_api_key_by_id(self, key_id: str) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one({"id": key_id})

    async def fetch_api_key_by_value(self, key_value: str) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one({"key": key_value})

    async def toggle_api_key_status(self, key_id: str, is_active: bool) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one_and_update(
            {"id": key_id},
            {"$set": {"isActive": is_active}},
            return_document=ReturnDocument.AFTER,
        )

    async def update_last_used_at(self, key_id: str, timestamp: int) -> None:
        collection = self._collection
        await collection.update_one(
            {"id": key_id},
            {"$set": {"lastUsedAt": timestamp}},
        )

    async def delete_api_key_by_id(self, key_id: str) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one_and_delete({"id": key_id})

    async def create_indexes(self) -> None:
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("key", 1)], unique=True),
                IndexModel([("isActive", 1)]),
                IndexModel([("createdAt", -1)]),
            ]
        )

