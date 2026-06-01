from fastapi import APIRouter
from kardex.repos.v1.expense_categories import CreateExpenseCategory, UpdateExpenseCategory, ExpenseCategoryInDb
from responses.v1 import ListResponse

from .expense_categories_controller import expense_categories_controller


expense_categories_router = APIRouter(tags=["expense_categoriesV1"])


@expense_categories_router.post("")
async def create_expense_category(body: CreateExpenseCategory) -> ExpenseCategoryInDb:
    return await expense_categories_controller.create_expense_category(body)


@expense_categories_router.get("")
async def get_all_expense_categories() -> ListResponse[ExpenseCategoryInDb]:
    return await expense_categories_controller.get_all_expense_categories()


@expense_categories_router.get("/{expense_category_id}")
async def get_expense_category_by_id(expense_category_id: str) -> ExpenseCategoryInDb:
    return await expense_categories_controller.get_expense_category_by_id(expense_category_id)


@expense_categories_router.patch("/{expense_category_id}")
async def update_expense_category_by_id(expense_category_id: str, body: UpdateExpenseCategory) -> ExpenseCategoryInDb: 
    return await expense_categories_controller.update_expense_category_by_id(expense_category_id, body)


@expense_categories_router.delete("/{expense_category_id}")
async def delete_expense_category_by_id(expense_category_id: str) -> ExpenseCategoryInDb:
    return await expense_categories_controller.delete_expense_category_by_id(expense_category_id)
