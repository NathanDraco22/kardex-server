from kardex.tools import TimeTools, UuidTool

from .data.expense_categories_datasource import ExpenseCategoriesDataSource
from .models.expense_category_model import CreateExpenseCategory, UpdateExpenseCategory, ExpenseCategoryInDb


class ExpenseCategoriesRepository:

    _instance: "ExpenseCategoriesRepository|None" = None

    def __init__(self, expense_categories_ds: ExpenseCategoriesDataSource):
        self.expense_categories_ds = expense_categories_ds

    @classmethod
    def get_instance(cls) -> "ExpenseCategoriesRepository":
        if cls._instance is None:
            cls._instance = cls(ExpenseCategoriesDataSource())
        return cls._instance

    async def create_expense_category(self, create_expense_category: CreateExpenseCategory) -> ExpenseCategoryInDb:
        new_expense_category = ExpenseCategoryInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_expense_category.model_dump(),
        )

        result = await self.expense_categories_ds.create_expense_category(
            new_expense_category.model_dump()
        )

        return ExpenseCategoryInDb.model_validate(result)

    async def get_all_expense_categories(self) -> list[ExpenseCategoryInDb]:
        results = await self.expense_categories_ds.get_all_expense_categories()
        models = [ExpenseCategoryInDb.model_validate(result) for result in results]
        return models

    async def get_expense_category_by_id(self, expense_category_id: str) -> ExpenseCategoryInDb | None :
        result = await self.expense_categories_ds.get_expense_category_by_id(expense_category_id)

        if result is None:
            return None

        return ExpenseCategoryInDb.model_validate(result)

    async def update_expense_category_by_id(self, expense_category_id: str, expense_category: UpdateExpenseCategory) -> ExpenseCategoryInDb | None:
        updated_expense_category_data = expense_category.model_dump(exclude_unset=True)

        result = await self.expense_categories_ds.update_expense_category_by_id(
            expense_category_id, updated_expense_category_data
        )

        if result is None:
            return None

        return ExpenseCategoryInDb.model_validate(result)

    async def delete_expense_category_by_id(self, expense_category_id: str) -> ExpenseCategoryInDb | None:
        result = await self.expense_categories_ds.delete_expense_category_by_id(expense_category_id)

        if result is None:
            return None

        return ExpenseCategoryInDb.model_validate(result)
