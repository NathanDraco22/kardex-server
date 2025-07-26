from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class ClientsCollection:
    collection_name = "Clients"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_client(self, client: dict) -> None:
        collection = self.__collection
        await collection.insert_one(client)

    async def fetch_all_clients(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": client_id})
        return result

    async def update_client_by_id(
        self,
        client_id: str,
        client: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": client_id},
            {"$set": client},
            return_document=ReturnDocument.AFTER,
        )

        return result
