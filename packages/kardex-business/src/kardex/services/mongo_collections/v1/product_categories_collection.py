from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection
from pymongo import IndexModel


class ProductCategoriesCollection(BaseMongoCollection):
    collection_name = "ProductCategories"

    async def create_product_category(self, product_category: dict) -> None:
        collection = self._collection
        await collection.insert_one(product_category)

    async def fetch_all_product_categories(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_category_by_id(
        self, product_category_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": product_category_id})
        return result

    async def update_product_category_by_id(
        self,
        product_category_id: str,
        product_category: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": product_category_id},
            {"$set": product_category},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_product_category_by_id(
        self, product_category_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": product_category_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)], unique=True),
            ]
        )
