from datetime import datetime
from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class ClientAccountsCollection:
    collection_name = "ClientAccounts"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_client_account(self, client_account: dict) -> None:
        collection = self.__collection
        await collection.insert_one(client_account)

    async def fetch_all_client_accounts(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_account_by_id(
        self, client_account_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": client_account_id})
        return result

    async def update_client_account_by_id(
        self,
        client_account_id: str,
        client_account: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": client_account_id},
            {"$set": client_account},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_client_account_by_id(
        self, client_account_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": client_account_id})
        return result

    async def add_to_client_account(
        self, client_id: str, amount: int, session: Any
    ) -> dict[str, Any]:
        collection = self.__collection
        updated_at = datetime.now()

        result = await collection.find_one_and_update(
            {"clientId": client_id},
            {"$inc": {"balance": amount}, "$set": {"updatedAt": updated_at}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def substract_from_client_account(
        self, client_id: str, amount: int, session: Any
    ) -> dict[str, Any]:
        collection = self.__collection
        updated_at = datetime.now()

        result = await collection.find_one_and_update(
            {"clientId": client_id},
            {"$inc": {"balance": -amount}, "$set": {"updatedAt": updated_at}},
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result
