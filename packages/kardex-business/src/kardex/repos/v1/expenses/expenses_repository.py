from typing import Any
from kardex.tools import TimeTools, UuidTool
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.filter_params import ExpensesFilterParams

from .data.expenses_datasource import ExpensesDataSource
from .models.expense_model import CreateExpense, UpdateExpense, ExpenseInDb


class ExpensesRepository:
    
    _instance: "ExpensesRepository|None" = None
    
    def __init__(self, expenses_ds: ExpensesDataSource):
        self.expenses_ds = expenses_ds

    @classmethod
    def get_instance(cls) -> "ExpensesRepository":
        if cls._instance is None:
            cls._instance = cls(ExpensesDataSource())
        return cls._instance

    async def create_expense(self, create_expense: CreateExpense) -> ExpenseInDb:
        # Generar docNumber si viene vacío o no está especificado
        doc_number = create_expense.docNumber
        if not doc_number or doc_number.strip() == "":
            doc_number = await CounterManager().next_expense_number()

        new_expense = ExpenseInDb(
            **create_expense.model_dump(exclude={"docNumber"}),
            id=UuidTool.generate_uuid(),
            docNumber=doc_number,
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            isDeleted=False
        )

        await self.expenses_ds.create_expense(new_expense.model_dump())
        return new_expense

    async def get_all_expenses(self, params: ExpensesFilterParams) -> list[ExpenseInDb]:
        query_params = params.to_query_params()
        results = await self.expenses_ds.get_all_expenses(**query_params)
        models = [ExpenseInDb.model_validate(result) for result in results]
        return models

    async def get_expense_by_id(self, expense_id: str) -> ExpenseInDb | None:
        result = await self.expenses_ds.get_expense_by_id(expense_id)
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def get_expense_by_doc_number(self, doc_number: str) -> ExpenseInDb | None:
        result = await self.expenses_ds.get_expense_by_doc_number(doc_number)
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def update_expense_by_id(self, expense_id: str, expense: UpdateExpense) -> ExpenseInDb | None:
        updated_data = expense.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.expenses_ds.update_expense_by_id(expense_id, updated_data)
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def delete_expense_by_id(self, expense_id: str) -> ExpenseInDb | None:
        result = await self.expenses_ds.delete_expense_by_id(expense_id)
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def add_to_amount_paid(self, expense_id: str, amount_paid: int) -> ExpenseInDb | None:
        result = await self.expenses_ds.add_to_amount_paid(expense_id, amount_paid)
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def get_expenses_summary_in_range(self, start_date: int, end_date: int) -> dict[str, Any]:
        return await self.expenses_ds.get_expenses_summary_in_range(start_date, end_date)

