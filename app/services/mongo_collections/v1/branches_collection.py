from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class BranchesCollection:
    collection_name = "Branches"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_branch(self, branch: dict) -> None:
        collection = self.__collection
        await collection.insert_one(branch)

    async def fetch_all_branches(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": branch_id})
        return result

    async def update_branch_by_id(
        self,
        branch_id: str,
        branch: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": branch_id},
            {"$set": branch},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": branch_id})
        return result
