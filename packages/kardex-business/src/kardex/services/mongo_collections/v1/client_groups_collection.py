from typing import Any

from pymongo import ReturnDocument
from kardex.services import MongoService


class ClientGroupsCollection:
    collection_name = "ClientGroups"
    _instance: "ClientGroupsCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_client_group(self, client_group: dict) -> None:
        collection = self.__collection
        await collection.insert_one(client_group)

    async def fetch_all_client_groups(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_group_by_id(self, client_group_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": client_group_id})
        return result

    async def update_client_group_by_id(
        self,
        client_group_id: str,
        client_group: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": client_group_id},
            {"$set": client_group},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_client_group_by_id(self, client_group_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": client_group_id})
        return result
