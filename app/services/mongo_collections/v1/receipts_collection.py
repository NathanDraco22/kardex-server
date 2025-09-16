from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class ReceiptsCollection:
    collection_name = "Receipts"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_receipt(self, receipt: dict) -> None:
        collection = self.__collection
        await collection.insert_one(receipt)

    async def fetch_all_receipts(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": receipt_id})
        return result

    async def fetch_receipt_by_doc_number(
        self, docNumber: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"docNumber": docNumber})
        return result

    async def update_receipt_by_id(
        self,
        receipt_id: str,
        receipt: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": receipt_id},
            {"$set": receipt},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": receipt_id})
        return result

    async def create_receipt_with_session(
        self,
        receipt: dict,
        session: Any,
    ) -> dict[str, Any]:
        collection = self.__collection
        await collection.insert_one(receipt, session=session)
        return receipt
