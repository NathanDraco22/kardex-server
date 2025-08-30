import re
from typing import Any
from datetime import datetime

from pymongo import ReturnDocument
from services import MongoService

from pymongo import IndexModel


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
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": client_id, "isDeleted": False})
        return result

    async def search_client_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self.__collection

        safe_query = re.escape(text_query)

        query = {
            "name": {
                "$regex": safe_query,
                "$options": "i",  # 'i' para case-insensitive
            },
            "isDeleted": False,
        }

        cursor = collection.find(query).limit(7)

        result = await cursor.to_list(length=None)
        await cursor.close()

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

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                        ("isDeleted", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("name", "text"),
                    ],
                ),
            ]
        )

    async def add_to_client_balance(
        self, client_id: str, amount: int, session: Any
    ) -> dict[str, Any]:
        collection = self.__collection
        updated_at = datetime.now()

        result = await collection.find_one_and_update(
            {"id": client_id},
            {"$inc": {"balance": amount}, "$set": {"updatedAt": updated_at}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def substract_from_client_balance(
        self, client_id: str, amount: int, session: Any
    ) -> dict[str, Any]:
        collection = self.__collection
        updated_at = datetime.now()

        result = await collection.find_one_and_update(
            {"id": client_id},
            {"$inc": {"balance": -amount}, "$set": {"updatedAt": updated_at}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result
