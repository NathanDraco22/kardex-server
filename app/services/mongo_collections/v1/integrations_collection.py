from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class IntegrationsCollection:
    collection_name = "Integrations"
    _instance: "IntegrationsCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_integration(self, integration: dict) -> None:
        collection = self.__collection
        await collection.insert_one(integration)

    async def create_integration_if_absent(self, integration: dict) -> None:
        collection = self.__collection
        await collection.find_one_and_update(
            {"id": integration["id"]},
            {"$setOnInsert": integration},
            upsert=True,
        )

    async def fetch_all_integrations(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_integration_by_id(
        self, integration_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": integration_id})
        return result

    async def update_integration_by_id(
        self,
        integration_id: str,
        integration: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": integration_id},
            {"$set": integration},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_integration_by_id(
        self, integration_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": integration_id})
        return result
