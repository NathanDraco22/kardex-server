from typing import Any

from pymongo import ReturnDocument
from services import MongoService

from pymongo import IndexModel


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
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": supplier_id, "isDeleted": False})
        return result

    async def search_supplier_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {
            "$text": {
                "$search": text_query,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            },
            "isDeleted": False,
        }
        cursor = collection.find(query).limit(10)

        result = await cursor.to_list(length=None)
        await cursor.close()

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

    async def create_indexes(self):
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
                        ("name", "text"),
                    ],
                ),
            ]
        )
