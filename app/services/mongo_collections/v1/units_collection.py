from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class UnitsCollection:
    collection_name = "Units"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_unit(self, unit: dict) -> None:
        collection = self.__collection
        await collection.insert_one(unit)

    async def fetch_all_units(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_unit_by_id(self, unit_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": unit_id})
        return result

    async def update_unit_by_id(
        self,
        unit_id: str,
        unit: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": unit_id},
            {"$set": unit},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_unit_by_id(self, unit_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": unit_id})
        return result
