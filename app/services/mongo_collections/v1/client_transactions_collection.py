from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class ClientTransactionsCollection:
    collection_name = "ClientTransactions"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_client_transaction(self, client_transaction: dict) -> None:
        collection = self.__collection
        await collection.insert_one(client_transaction)

    async def fetch_all_client_transactions(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_transaction_by_id(
        self, client_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": client_transaction_id})
        return result

    async def update_client_transaction_by_id(
        self,
        client_transaction_id: str,
        client_transaction: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": client_transaction_id},
            {"$set": client_transaction},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_client_transaction_by_id(
        self, client_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": client_transaction_id})
        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("documentId", 1)]),
                IndexModel([("clientId", 1), ("createdAt", -1)]),
                IndexModel([("type", 1), ("subtype", 1), ("createdAt", -1)]),
                IndexModel([("createdAt", -1)]),
            ],
        )

    async def create_client_transaction_with_session(
        self, client_transaction: dict, session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_one(client_transaction, session=session)
