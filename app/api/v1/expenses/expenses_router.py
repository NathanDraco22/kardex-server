from fastapi import APIRouter, Depends

from kardex.repos.v1.common.filter_params import ExpensesFilterParams
from kardex.repos.v1.expenses import (
    AccountsPayableSummary,
    AddToAmountRequest,
    CreateExpense,
    ExpenseInDb,
    UpdateExpense,
)
from responses.v1 import ListResponse

from .expenses_controller import expenses_controller


expenses_router = APIRouter(tags=["expensesV1"])


@expenses_router.post("")
async def create_expense(body: CreateExpense) -> ExpenseInDb:
    return await expenses_controller.create_expense(body)


@expenses_router.get("")
async def get_all_expenses(
    params: ExpensesFilterParams = Depends(),
) -> ListResponse[ExpenseInDb]:
    return await expenses_controller.get_all_expenses(params)


@expenses_router.get("/accounts-payable/summary")
async def get_accounts_payable_summary(
    branchId: str | None = None,
    overdueCutoffMs: int | None = None,
) -> AccountsPayableSummary:
    return await expenses_controller.get_accounts_payable_summary(
        branchId, overdueCutoffMs
    )


@expenses_router.get("/{expense_id}")
async def get_expense_by_id(expense_id: str) -> ExpenseInDb:
    return await expenses_controller.get_expense_by_id(expense_id)


@expenses_router.patch("/{expense_id}")
async def update_expense_by_id(expense_id: str, body: UpdateExpense) -> ExpenseInDb: 
    return await expenses_controller.update_expense_by_id(expense_id, body)


@expenses_router.delete("/{expense_id}")
async def delete_expense_by_id(expense_id: str) -> ExpenseInDb:
    return await expenses_controller.delete_expense_by_id(expense_id)


@expenses_router.post("/add-to-amount-paid")
async def add_to_amount_paid(body: AddToAmountRequest) -> ExpenseInDb:
    return await expenses_controller.add_to_amount_paid(body)

