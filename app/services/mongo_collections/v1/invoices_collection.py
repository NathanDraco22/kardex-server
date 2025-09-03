from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class InvoicesCollection:
    collection_name = "Invoices"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_invoice(self, invoice: dict) -> None:
        collection = self.__collection
        await collection.insert_one(invoice)

    async def fetch_all_invoices(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_invoice_by_id(self, invoice_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": invoice_id})
        return result

    async def fetch_invoice_by_doc_number(
        self, docNumber: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"docNumber": docNumber})
        return result

    async def update_invoice_by_id(
        self,
        invoice_id: str,
        invoice: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            {"$set": invoice},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_invoice_by_id(self, invoice_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": invoice_id})
        return result

    async def create_invoice_with_session(self, invoice: dict, session: Any) -> dict:
        collection = self.__collection
        await collection.insert_one(
            invoice,
            session=session,
        )

        return invoice

    async def add_to_amount_paid(self, invoice_id: str, amount_paid: int, session: Any):
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            {"$inc": {"amountPaid": amount_paid}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("id", 1)], unique=True),
                IndexModel([("createdAt", -1)]),
            ]
        )
