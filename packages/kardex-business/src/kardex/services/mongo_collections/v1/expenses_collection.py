from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


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

    async def create_indexes(self):
        collection = self._collection
        await collection.create_index([("docNumber", 1)], unique=True)
        await collection.create_index([("branchId", 1)])
        await collection.create_index([("dateId", 1)])
        await collection.create_index([("createdAt", 1)])
