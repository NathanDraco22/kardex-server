from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection
from kardex.tools import TimeTools


class ExpensesCollection(BaseMongoCollection):
    collection_name = "Expenses"

    async def create_expense(self, expense: dict) -> None:
        collection = self._collection
        await collection.insert_one(expense)

    async def fetch_all_expenses(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {"isDeleted": False}

        params = kwargs.copy()
        offset = params.pop("offset", 0)
        limit = params.pop("limit", 50)

        query.update(params)

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_expense_by_id(self, expense_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": expense_id, "isDeleted": False})
        return result

    async def fetch_expense_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"docNumber": doc_number, "isDeleted": False}
        )
        return result

    async def update_expense_by_id(
        self,
        expense_id: str,
        expense: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": expense_id, "isDeleted": False},
            {"$set": expense},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_expense_by_id(self, expense_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": expense_id, "isDeleted": False},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def add_to_amount_paid(
        self, expense_id: str, amount_paid: int, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection

        pipeline = [
            {
                "$set": {
                    "amountPaid": {
                        "$add": [{"$ifNull": ["$amountPaid", 0]}, amount_paid],
                    },
                },
            },
            {
                "$set": {
                    "status": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$amount"]},
                            "then": "paid",
                            "else": "partiallyPaid",
                        }
                    },
                    "paidAt": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$amount"]},
                            "then": TimeTools.get_now_in_milliseconds(),
                            "else": None,
                        }
                    },
                }
            },
        ]

        result = await collection.find_one_and_update(
            {"id": expense_id, "isDeleted": False},
            pipeline,
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def create_indexes(self):

        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("branchId", 1)]),
                IndexModel([("dateId", 1)]),
                IndexModel([("createdAt", -1)]),
                IndexModel([("type", 1), ("createdAt", -1)]),
            ]
        )
