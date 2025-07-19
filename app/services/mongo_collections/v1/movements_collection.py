from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class MovementsCollection:
    collection_name = "Movements"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_movement(self, movement: dict) -> None:
        collection = self.__collection
        await collection.insert_one(movement)

    async def fetch_all_movements(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_movement_by_id(self, movement_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": movement_id})
        return result

    async def update_movement_by_id(
        self,
        movement_id: str,
        movement: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": movement_id},
            {"$set": movement},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_movement_by_id(self, movement_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": movement_id})
        return result
