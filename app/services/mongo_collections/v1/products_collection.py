from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class ProductsCollection:
    collection_name = "Products"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_product(self, product: dict) -> None:
        collection = self.__collection
        await collection.insert_one(product)

    async def fetch_all_products(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": product_id, "isDeleted": False})
        return result

    async def fetch_product_by_ids(
        self, product_ids: list[str]
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find({"id": {"$in": product_ids}})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def search_product_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {
            "$text": {
                "$search": text_query,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            },
            "isDeleted": False,
        }

        projection = {"score": {"$meta": "textScore"}}

        cursor = (
            collection.find(query, projection)
            .sort([("score", {"$meta": "textScore"})])
            .limit(7)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_all_products_with_accounts(
        self, branch_id: str, page: int, limit: int
    ):
        collection = self.__collection

        cursor = collection.aggregate(
            [
                {
                    "$match": {"isDeleted": False},
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                    }
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$match": {"account.branchId": branch_id},
                },
                {
                    "$sort": {"name": 1},
                },
                {
                    "$skip": (page - 1) * limit,
                },
                {
                    "$limit": limit,
                },
            ]
        )

        result = await cursor.to_list(length=None)

        return result

    async def update_product_by_id(
        self,
        product_id: str,
        product: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": product_id},
            {"$set": product},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": product_id})
        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)]),
                IndexModel(
                    [
                        ("name", "text"),
                        ("code", "text"),
                        ("brandName", "text"),
                        ("unitName", "text"),
                        ("categoryName", "text"),
                        ("tags", "text"),
                        ("searchPrefixes", "text"),
                    ],
                    weights={
                        "name": 10,
                        "code": 3,
                        "brandName": 5,
                        "unitName": 5,
                        "categoryName": 3,
                        "tags": 10,
                    },
                ),
            ]
        )
