from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class UserRolesCollection(BaseMongoCollection):
    collection_name = "UserRoles"

    async def create_user_role(self, user_role: dict) -> None:
        collection = self._collection
        await collection.insert_one(user_role)

    async def create_role_if_absent(self, user_role_id, user_role: dict) -> None:
        collection = self._collection
        await collection.find_one_and_update(
            {"id": user_role_id},
            {"$setOnInsert": user_role},
            upsert=True,
        )

    async def fetch_all_user_roles(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_user_role_by_id(self, user_role_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": user_role_id})
        return result

    async def update_user_role_by_id(
        self,
        user_role_id: str,
        user_role: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": user_role_id},
            {"$set": user_role},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_user_role_by_id(self, user_role_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": user_role_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
            ],
        )
