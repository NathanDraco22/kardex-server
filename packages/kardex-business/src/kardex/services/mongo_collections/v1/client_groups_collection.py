from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


class ClientGroupsCollection(BaseMongoCollection):
    collection_name = "ClientGroups"

    async def create_client_group(self, client_group: dict) -> None:
        collection = self._collection
        await collection.insert_one(client_group)

    async def fetch_all_client_groups(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_group_by_id(self, client_group_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": client_group_id})
        return result

    async def update_client_group_by_id(
        self,
        client_group_id: str,
        client_group: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": client_group_id},
            {"$set": client_group},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_client_group_by_id(self, client_group_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": client_group_id})
        return result
