from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class CountersCollection:
    collection_name = "Counters"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def increment_counter(
        self, counter_name: str, session: Any
    ) -> dict[str, Any]:
        collection = self.__collection
        result = await collection.find_one_and_update(
            {"name": counter_name},
            {"$inc": {"value": 1}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def get_counter(self, counter_name: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"name": counter_name})

        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_index([("name", 1)])
