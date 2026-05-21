from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class ProductPricesCollection(BaseMongoCollection):
    collection_name = "ProductPrices"

    async def create_product_price(self, product_price: dict) -> None:
        collection = self._collection
        await collection.insert_one(product_price)

    async def fetch_all_product_prices(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_price_by_id(
        self, product_price_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": product_price_id})
        return result

    async def update_product_price_by_id(
        self,
        product_price_id: str,
        product_price: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": product_price_id},
            {"$set": product_price},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_product_price_by_id(
        self, product_price_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": product_price_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)], unique=True),
            ]
        )
