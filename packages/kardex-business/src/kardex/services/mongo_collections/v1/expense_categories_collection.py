from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class ExpenseCategoriesCollection(BaseMongoCollection):
    collection_name = "ExpenseCategories"

    async def create_expense_category(self, expense_category: dict) -> None:
        collection = self._collection
        await collection.insert_one(expense_category)

    async def fetch_all_expense_categories(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_expense_category_by_id(self, expense_category_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": expense_category_id})
        return result

    async def update_expense_category_by_id(
        self,
        expense_category_id: str,
        expense_category: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": expense_category_id},
            {"$set": expense_category},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_expense_category_by_id(self, expense_category_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": expense_category_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)], unique=True),
            ]
        )
