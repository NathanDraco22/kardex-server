from typing import Any
from pymongo import ReturnDocument, IndexModel
from services import MongoService

from tools import TimeTools, build_query


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

    async def fetch_all_invoices(self, **kargs) -> list[dict[str, Any]]:
        collection = self.__collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)

        cursor = (
            collection.find(result.query)
            .skip(result.offset)
            .limit(result.limit)
            .sort(date_field, -1)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_all_invoices_by(
        self,
        client_id: str,
        offset: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find({"clientId": client_id})

        cursor = cursor.sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_pending_to_paid_invoices(
        self, client_id: str
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find(
            {
                "clientId": client_id,
                "status": {"$ne": "paid"},
            }
        )

        result = await cursor.sort("createdAt", -1).to_list(length=None)
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

        pipeline = [
            {
                "$set": {
                    "amountPaid": {
                        "$add": ["$amountPaid", amount_paid],
                    },
                },
            },
            {
                "$set": {
                    "status": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$total"]},
                            "then": "paid",
                            "else": "partially_paid",
                        }
                    },
                    "paidAt": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$total"]},
                            "then": TimeTools.get_now_in_milliseconds(),
                            "else": None,
                        }
                    },
                }
            },
        ]

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            pipeline,
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def update_invoice_by_id_with_session(
        self,
        invoice_id: str,
        invoice: dict,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            {"$set": invoice},
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def get_totals_from_invoices(self, **kargs) -> dict[str, Any]:
        collection = self.__collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)

        cursor = collection.aggregate(
            [
                {"$match": result.query},
                {
                    "$group": {
                        "_id": None,
                        "totalCost": {"$sum": "$totalCost"},
                        "total": {"$sum": "$total"},
                    }
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        if result:
            data = result[0]
            return data

        return {
            "totalCost": 0,
            "total": 0,
        }

    async def fetch_invoice_history(self, **kwargs) -> list[dict[str, Any]]:
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
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("id", 1)], unique=True),
                IndexModel([("clientId", 1), ("status", 1), ("docDate", -1)]),
                IndexModel([("saleItems.product.id", 1)]),
                IndexModel([("branchId", 1), ("saleItems.product.id", 1)]),
                IndexModel([("createdAt", -1)]),
                IndexModel([("paidAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
            ]
        )
