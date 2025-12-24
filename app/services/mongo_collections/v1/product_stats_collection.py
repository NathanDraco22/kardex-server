from ast import Index
from typing import Any

from pymongo import ReturnDocument, IndexModel, UpdateOne
from services import MongoService


class ProductStatsCollection:
    collection_name = "ProductStats"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_product_stat(self, product_stat: dict) -> None:
        collection = self.__collection
        await collection.insert_one(product_stat)

    async def fetch_all_product_stats(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = kwargs

        cursor = collection.find(query)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_all_product_stats_with_info(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = kwargs

        cursor = collection.aggregate(
            [
                {"$match": {**query}},
                {"$sort": {"estimationLevel": -1}},
                {
                    "$lookup": {
                        "from": "Products",
                        "localField": "productId",
                        "foreignField": "id",
                        "as": "product",
                    }
                },
                {"$unwind": "$product"},
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_all_product_stats_with_transaction(self) -> list[dict[str, Any]]:
        collection = self.__collection

        cursor = collection.find(
            {
                "totalUnits": {"$gt": 0},
                "totalTransactions": {"$gt": 0},
            }
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_stat_by_id(
        self, product_stat_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": product_stat_id})
        return result

    async def update_product_stat_by_id(
        self,
        product_stat_id: str,
        product_stat: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": product_stat_id},
            {"$set": product_stat},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_product_batch(self, product_stats: list[dict]):
        operations = []

        for product in product_stats:
            operations.append(
                UpdateOne(
                    {
                        "productId": product["productId"],
                        "branchId": product["branchId"],
                    },
                    {
                        "$set": {
                            "estimationLevel": product["estimationLevel"],
                        }
                    },
                ),
            )

        await self.__collection.bulk_write(operations)

    async def delete_product_stat_by_id(
        self, product_stat_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": product_stat_id})
        return result

    async def set_no_transtaction_product_stats(self, last_estimation: int):
        collection = self.__collection
        await collection.update_many(
            {"lastEstimation": {"$lt": last_estimation}},
            {
                "$set": {
                    "totalUnits": 0,
                    "totalTransactions": 0,
                    "lastEstimation": last_estimation,
                    "estimationLevel": 1,
                }
            },
        )

    async def create_product_stats_if_not_exist_with_session(
        self,
        branch_id: str,
        product_id: str,
        product_stats: dict,
        session: Any,
    ):
        collection = self.__collection

        await collection.find_one_and_update(
            {
                "branchId": branch_id,
                "productId": product_id,
            },
            {"$setOnInsert": product_stats},
            return_document=ReturnDocument.AFTER,
            session=session,
            upsert=True,
        )

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("productId", 1),
                        ("branchId", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("lastEstimation", -1),
                    ],
                ),
                IndexModel(
                    [
                        ("estimationLevel", -1),
                    ],
                ),
            ]
        )
