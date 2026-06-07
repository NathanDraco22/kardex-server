from typing import Any
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ExpenseCategoriesCollection,
    ExpensesCollection,
)


class ExpenseCategoriesDataSource:
    async def create_expense_category(
        self, expense_category: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ExpenseCategoriesCollection.get_instance()
        await collection.create_expense_category(expense_category)
        return expense_category

    async def get_all_expense_categories(self) -> list[dict[str, Any]]:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.fetch_all_expense_categories()

    async def get_expense_category_by_id(
        self, expense_category_id: str
    ) -> dict[str, Any] | None:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.fetch_expense_category_by_id(expense_category_id)

    async def update_expense_category_by_id(
        self, expense_category_id: str, expense_category: dict[str, Any]
    ) -> dict[str, Any] | None:
        mongo_client = MongoService().client

        collection = ExpenseCategoriesCollection.get_instance()
        expenses_collection = ExpensesCollection.get_instance()

        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                old_category_doc = await collection.fetch_expense_category_by_id(
                    expense_category_id, session=session
                )

                if old_category_doc is None:
                    return None

                updated_expense_category = (
                    await collection.update_expense_category_by_id(
                        expense_category_id, expense_category, session=session
                    )
                )

                if updated_expense_category is not None:
                    if "name" in updated_expense_category:
                        old_name = old_category_doc["name"]
                        new_name = updated_expense_category["name"]

                        if old_name != new_name:
                            await expenses_collection.update_expenses_category(
                                old_name,
                                new_name,
                                session=session,
                            )

                return updated_expense_category

    async def delete_expense_category_by_id(
        self, expense_category_id: str
    ) -> dict[str, Any] | None:
        collection = ExpenseCategoriesCollection.get_instance()
        return await collection.delete_expense_category_by_id(expense_category_id)
