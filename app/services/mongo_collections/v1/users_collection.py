from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class UsersCollection:
    collection_name = "Users"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_user(self, user: dict) -> None:
        collection = self.__collection
        await collection.insert_one(user)

    async def fetch_all_users(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": user_id})
        return result

    async def fetch_user_by_username(self, email: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"username": email})
        return result

    async def update_user_by_id(
        self,
        user_id: str,
        user: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": user_id},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": user_id})
        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("username", 1)], unique=True),
            ]
        )
