from fastapi import HTTPException, status
from kardex.repos.v1.expense_categories import (
    CreateExpenseCategory, 
    UpdateExpenseCategory, 
    ExpenseCategoryInDb, 
    ExpenseCategoriesRepository,
)
from responses.v1 import ListResponse


class ExpenseCategoriesController:
    def __init__(self, expense_categories_repo: ExpenseCategoriesRepository) -> None:
        self.expense_categories_repo = expense_categories_repo

    async def create_expense_category(self, body: CreateExpenseCategory) -> ExpenseCategoryInDb:
        return await self.expense_categories_repo.create_expense_category(body)

    async def get_all_expense_categories(self) -> ListResponse[ExpenseCategoryInDb]:
        expense_categories = await self.expense_categories_repo.get_all_expense_categories()
        return ListResponse(
            count=len(expense_categories),
            data=expense_categories,
        )

    async def get_expense_category_by_id(self, expense_category_id: str) -> ExpenseCategoryInDb:
        expense_category = await self.expense_categories_repo.get_expense_category_by_id(expense_category_id)
        if expense_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExpenseCategory not found",
            )
        return expense_category

    async def update_expense_category_by_id(self, expense_category_id: str, body: UpdateExpenseCategory) -> ExpenseCategoryInDb:
        updated_expense_category = await self.expense_categories_repo.update_expense_category_by_id(expense_category_id, body)
        if updated_expense_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExpenseCategory not found",
            )
        return updated_expense_category

    async def delete_expense_category_by_id(self, expense_category_id: str) -> ExpenseCategoryInDb:
        deleted_expense_category = await self.expense_categories_repo.delete_expense_category_by_id(expense_category_id)
        if deleted_expense_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExpenseCategory not found",
            )
        return deleted_expense_category

expense_categories_controller = ExpenseCategoriesController(
    expense_categories_repo=ExpenseCategoriesRepository.get_instance(),
)
