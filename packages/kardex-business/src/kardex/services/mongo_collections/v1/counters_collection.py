from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection
from kardex.tools import MongoMigrationException


class CountersCollection(BaseMongoCollection):
    collection_name = "Counters"

    async def increment_counter(
        self, counter_name: str, session: Any
    ) -> dict[str, Any]:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"name": counter_name},
            {"$inc": {"value": 1}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        if result is None:
            raise MongoMigrationException("Failed to increment counter: result is None")

        return result

    async def set_counter(
        self, counter_name: str, value: int, session: Any
    ) -> dict[str, Any]:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"name": counter_name},
            {"$set": {"value": value}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        if result is None:
            raise MongoMigrationException("Failed to set counter: result is None")

        return result

    async def get_counter(self, counter_name: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"name": counter_name})

        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_index([("name", 1)])
