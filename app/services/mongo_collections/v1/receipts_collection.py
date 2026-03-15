from typing import Any

from pymongo import ReturnDocument, IndexModel
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

    async def fetch_all_receipts(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)

        if kwargs.get("startDate") and kwargs.get("endDate"):
            query["createdAt"] = {
                "$gte": kwargs.get("startDate"),
                "$lte": kwargs.get("endDate"),
            }

            del query["startDate"]
            del query["endDate"]

        if kwargs.get("startDate") and not kwargs.get("endDate"):
            query["createdAt"] = {"$gte": kwargs.get("startDate")}

            del query["startDate"]

        cursor = collection.find(query).skip(offset).limit(limit).sort("createdAt", -1)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_receipts_by_invoice_id(
        self, invoice_id: str
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find({"appliedInvoices.invoiceId": invoice_id})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def get_totals_from_receipts(self, **kwargs) -> dict[str, Any]:
        collection = self.__collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        if kwargs.get("startDate") and kwargs.get("endDate"):
            query["createdAt"] = {
                "$gte": kwargs.get("startDate"),
                "$lte": kwargs.get("endDate"),
            }

            del query["startDate"]
            del query["endDate"]

        cursor = collection.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$total"},
                        "count": {"$sum": 1},
                    }
                },
            ]
        )

        result = await cursor.to_list(length=None)

        await cursor.close()

        if result:
            data = result[0]
            return data

        return {"total": 0}

    async def get_totals_from_receipts_by_payment_method(
        self, **kwargs
    ) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        if kwargs.get("paymentMethod"):
            query["paymentMethod"] = kwargs.get("paymentMethod")

        if kwargs.get("nePaymentMethod"):
            query["paymentMethod"] = {"$ne": kwargs.get("nePaymentMethod")}

        if kwargs.get("startDate") and kwargs.get("endDate"):
            query["createdAt"] = {
                "$gte": kwargs.get("startDate"),
                "$lte": kwargs.get("endDate"),
            }

            del query["startDate"]
            del query["endDate"]

        cursor = collection.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$paymentMethod",
                        "total": {"$sum": "$total"},
                        "count": {"$sum": 1},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "paymentMethod": "$_id",
                        "total": 1,
                        "count": 1,
                    }
                },
            ]
        )

        result = await cursor.to_list(length=None)

        await cursor.close()

        if result:
            return result

        return []

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

    async def fetch_receipt_history(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("clientId", 1), ("createdAt", -1)]),
                IndexModel([("branchId", 1), ("createdAt", -1)]),
                IndexModel([("appliedInvoices.invoiceId", 1)]),
                IndexModel([("createdBy.id", 1)]),
                IndexModel([("paymentMethod", 1)]),
            ]
        )
