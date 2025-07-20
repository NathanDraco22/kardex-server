from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class BranchStocksCollection:
    collection_name = "BranchStocks"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_branch_stock(self, branch_stock: dict) -> None:
        collection = self.__collection
        await collection.insert_one(branch_stock)

    async def fetch_all_branch_stocks(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_branch_stock_by_id(
        self, branch_stock_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": branch_stock_id})
        return result

    async def fetch_branch_stock_by_branch_and_product_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {
                "branch_id": branch_id,
                "product_id": product_id,
            }
        )
        return result

    async def update_branch_stock_with_pipeline(
        self, filter_doc: dict, pipeline: list
    ) -> None:
        collection = self.__collection
        await collection.find_one_and_update(
            filter_doc,
            pipeline,
            upsert=True,
        )

    async def update_branch_stock_with_params(
        self, filter_doc: dict, params: dict
    ) -> dict:
        collection = self.__collection
        return await collection.find_one_and_update(
            filter_doc,
            params,
        )

    async def update_branch_stock_by_id(
        self,
        branch_stock_id: str,
        branch_stock: dict,
    ) -> dict[str, Any]:
        collection = self.__collection

        update_doc_operation = {
            "$inc": {
                "current_stock": branch_stock["current_stock"],
            },
            "$setOnInsert": {
                "product_id": branch_stock["product_id"],
                "branch_id": branch_stock["branch_id"],
            },
            "$set": {
                "average_cost": branch_stock["average_cost"],
                "last_cost": branch_stock["last_cost"],
                "updated_at": branch_stock["updated_at"],
            },
        }

        result = await collection.find_one_and_update(
            {"id": branch_stock_id},
            update_doc_operation,
            return_document=ReturnDocument.AFTER,
            upsert=True,
        )

        return result

    async def update_branch_stock_by_branch_and_product_id(
        self,
        product_id: str,
        branch_id: str,
        branch_stock: dict,
    ) -> dict[str, Any]:
        collection = self.__collection

        update_doc_operation = {
            "$inc": {
                "current_stock": branch_stock["current_stock"],
            },
            "$set": {
                "average_cost": branch_stock["average_cost"],
                "last_cost": branch_stock["last_cost"],
                "updated_at": branch_stock["updated_at"],
            },
        }

        result = await collection.find_one_and_update(
            {
                "product_id": product_id,
                "branch_id": branch_id,
            },
            update_doc_operation,
            return_document=ReturnDocument.AFTER,
            upsert=True,
        )

        return result
