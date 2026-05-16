from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import MongoService


class ProductPricesCollection:
    collection_name = "ProductPrices"
    _instance: "ProductPricesCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_product_price(self, product_price: dict) -> None:
        collection = self.__collection
        await collection.insert_one(product_price)

    async def fetch_all_product_prices(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_price_by_id(
        self, product_price_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": product_price_id})
        return result

    async def update_product_price_by_id(
        self,
        product_price_id: str,
        product_price: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": product_price_id},
            {"$set": product_price},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_product_price_by_id(
        self, product_price_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": product_price_id})
        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)], unique=True),
            ]
        )
