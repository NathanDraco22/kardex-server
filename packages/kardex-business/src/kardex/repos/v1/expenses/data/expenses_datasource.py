from typing import Any
from kardex.services.mongo_collections.v1 import ExpensesCollection


class ExpensesDataSource:

    async def create_expense(
        self, expense: dict[str, Any], session: Any = None
    ) -> dict[str, Any]:
        collection = ExpensesCollection.get_instance()
        await collection.create_expense(expense, session=session)
        return expense

    async def get_all_expenses(self, **kwargs) -> list[dict[str, Any]]:
        collection = ExpensesCollection.get_instance()
        return await collection.fetch_all_expenses(**kwargs)

    async def get_expense_by_id(self, expense_id: str) -> dict[str, Any] | None:
        collection = ExpensesCollection.get_instance()
        return await collection.fetch_expense_by_id(expense_id)

    async def get_expense_by_doc_number(self, doc_number: str) -> dict[str, Any] | None:
        collection = ExpensesCollection.get_instance()
        return await collection.fetch_expense_by_doc_number(doc_number)

    async def update_expense_by_id(
        self, expense_id: str, expense: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExpensesCollection.get_instance()
        return await collection.update_expense_by_id(expense_id, expense)

    async def delete_expense_by_id(
        self, expense_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = ExpensesCollection.get_instance()
        return await collection.delete_expense_by_id(expense_id, session=session)

    async def add_to_amount_paid(
        self,
        expense_id: str,
        amount_paid: int,
        payment_record: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        collection = ExpensesCollection.get_instance()
        return await collection.add_to_amount_paid(
            expense_id, amount_paid, payment_record=payment_record
        )

    async def get_accounts_payable_summary(
        self, branch_id: str | None = None, overdue_cutoff_ms: int | None = None
    ) -> dict[str, Any]:
        collection = ExpensesCollection.get_instance()
        return await collection.get_accounts_payable_summary(
            branch_id=branch_id,
            overdue_cutoff_ms=overdue_cutoff_ms,
        )

    async def get_expenses_summary_in_range(self, start_date: int, end_date: int) -> dict[str, Any]:
        collection = ExpensesCollection.get_instance()
        return await collection.get_expenses_summary_in_range(start_date, end_date)

    async def get_expenses_totals_in_range(
        self,
        start_date: int,
        end_date: int,
        branch_id: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        collection = ExpensesCollection.get_instance()
        return await collection.get_expenses_totals_in_range(
            start_date, end_date, branch_id, user_id
        )
