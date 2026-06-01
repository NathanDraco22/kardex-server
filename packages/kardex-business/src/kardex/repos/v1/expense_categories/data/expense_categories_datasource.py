from typing import Any
from kardex.services.mongo_collections.v1 import ExpenseCategoriesCollection


class ExpenseCategoriesDataSource:

    async def create_expense_category(self, expense_category: dict[str, Any]) -> dict[str, Any]:
        collection = ExpenseCategoriesCollection.get_instance()
        await collection.create_expense_category(expense_category)
        return expense_category

    async def get_all_expense_categories(self) -> list[dict[str, Any]]:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.fetch_all_expense_categories()

    async def get_expense_category_by_id(self, expense_category_id: str) -> dict[str, Any] | None:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.fetch_expense_category_by_id(expense_category_id)

    async def update_expense_category_by_id(
        self, expense_category_id: str, expense_category: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.update_expense_category_by_id(expense_category_id, expense_category)

    async def delete_expense_category_by_id(self, expense_category_id: str) -> dict[str, Any] | None:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.delete_expense_category_by_id(expense_category_id)
