from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class SalesCollection:
    collection_name = "Sales"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_sale(self, sale: dict) -> None:
        collection = self.__collection
        await collection.insert_one(sale)

    async def fetch_all_sales(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_sale_by_id(self, sale_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": sale_id})
        return result

    async def update_sale_by_id(
        self,
        sale_id: str,
        sale: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": sale_id},
            {"$set": sale},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_sale_by_id(self, sale_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": sale_id})
        return result

    async def create_sale_with_session(self, sale: dict, session: Any) -> dict:
        collection = self.__collection
        await collection.insert_one(sale, session=session)

        return sale
