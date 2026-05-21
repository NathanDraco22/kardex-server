from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


class IntegrationsCollection(BaseMongoCollection):
    collection_name = "Integrations"

    async def create_integration(self, integration: dict) -> None:
        collection = self._collection
        await collection.insert_one(integration)

    async def create_integration_if_absent(self, integration: dict) -> None:
        collection = self._collection
        await collection.find_one_and_update(
            {"id": integration["id"]},
            {"$setOnInsert": integration},
            upsert=True,
        )

    async def fetch_all_integrations(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_integration_by_id(
        self, integration_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": integration_id})
        return result

    async def update_integration_by_id(
        self,
        integration_id: str,
        integration: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": integration_id},
            {"$set": integration},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_integration_by_id(
        self, integration_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": integration_id})
        return result
