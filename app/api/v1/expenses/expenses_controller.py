from fastapi import HTTPException, status

from kardex.repos.v1.common.filter_params import ExpensesFilterParams
from kardex.repos.v1.expenses import (
    CreateExpense, 
    UpdateExpense, 
    ExpenseInDb, 
    ExpensesRepository,
    AddToAmountRequest,
)
from responses.v1 import ListResponse


class ExpensesController:
    def __init__(self, expenses_repo: ExpensesRepository) -> None:
        self.expenses_repo = expenses_repo

    async def create_expense(self, body: CreateExpense) -> ExpenseInDb:
        if body.docNumber and body.docNumber.strip() != "":
            existing = await self.expenses_repo.get_expense_by_doc_number(body.docNumber)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document number '{body.docNumber}' already exists",
                )
        try:
            return await self.expenses_repo.create_expense(body)
        except Exception as e:
            if "duplicate key error" in str(e) or "E11000" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document number already exists",
                )
            raise e

    async def get_all_expenses(self, params: ExpensesFilterParams) -> ListResponse[ExpenseInDb]:
        expenses = await self.expenses_repo.get_all_expenses(params)
        return ListResponse(count=len(expenses), data=expenses)

    async def get_expense_by_id(self, expense_id: str) -> ExpenseInDb:
        expense = await self.expenses_repo.get_expense_by_id(expense_id)
        if expense is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )
        return expense

    async def update_expense_by_id(self, expense_id: str, body: UpdateExpense) -> ExpenseInDb:
        updated_expense = await self.expenses_repo.update_expense_by_id(expense_id, body)
        if updated_expense is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )
        return updated_expense

    async def delete_expense_by_id(self, expense_id: str) -> ExpenseInDb:
        deleted_expense = await self.expenses_repo.delete_expense_by_id(expense_id)
        if deleted_expense is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )
        return deleted_expense

    async def add_to_amount_paid(self, body: AddToAmountRequest) -> ExpenseInDb:
        updated_expense = await self.expenses_repo.add_to_amount_paid(body.expenseId, body.amountPaid)
        if updated_expense is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )
        return updated_expense



expenses_controller = ExpensesController(
    expenses_repo=ExpensesRepository.get_instance(),
)
