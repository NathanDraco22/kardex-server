from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class SuppliersCollection:
    collection_name = "Suppliers"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_supplier(self, supplier: dict) -> None:
        collection = self.__collection
        await collection.insert_one(supplier)

    async def fetch_all_suppliers(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": supplier_id})
        return result

    async def update_supplier_by_id(
        self,
        supplier_id: str,
        supplier: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": supplier_id},
            {"$set": supplier},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": supplier_id})
        return result
