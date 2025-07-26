from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class AccountsCollection:
    collection_name = "Accounts"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_account(self, account: dict) -> None:
        collection = self.__collection
        await collection.insert_one(account)

    async def fetch_all_accounts(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_account_by_id(self, account_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": account_id})
        return result

    async def update_account_by_id(
        self,
        account_id: str,
        account: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": account_id},
            {"$set": account},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_account_by_id(self, account_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": account_id})
        return result

    async def count_accounts(self, account_ids: list[str]) -> int:
        collection = self.__collection
        result = await collection.count_documents(
            {
                "id": {"$in": account_ids},
            },
        )
        return result
