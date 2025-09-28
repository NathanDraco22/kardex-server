from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class ProductTransactionsCollection:
    collection_name = "ProductTransactions"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_product_transaction(self, product_transaction: dict) -> None:
        collection = self.__collection
        await collection.insert_one(product_transaction)

    async def fetch_all_product_transactions(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_transaction_by_id(
        self, product_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": product_transaction_id})
        return result

    async def update_product_transaction_by_id(
        self,
        product_transaction_id: str,
        product_transaction: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": product_transaction_id},
            {"$set": product_transaction},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def create_index(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("productId", 1),
                        ("type", 1),
                        ("subtype", 1),
                    ]
                ),
                IndexModel(
                    [
                        ("createdAt", -1),
                    ],
                ),
            ]
        )

    async def create_product_transaction_with_session(
        self, product_transaction: dict, session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_one(product_transaction, session=session)

    async def create_many_product_transactions_with_session(
        self, product_transactions: list[dict], session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_many(product_transactions, session=session)
