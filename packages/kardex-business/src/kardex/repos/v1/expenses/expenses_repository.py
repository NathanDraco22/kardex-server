from typing import Any
from kardex.tools import TimeTools, UuidTool
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.filter_params import ExpensesFilterParams

from .data.expenses_datasource import ExpensesDataSource
from .models.accounts_payable_model import AccountsPayableSummary
from .models.expense_model import (
    AddToAmountRequest,
    CreateExpense,
    ExpenseInDb,
    ExpensePayment,
    UpdateExpense,
)
from .models.expense_totals_model import ExpenseTotals


class ExpensesRepository:
    
    _instance: "ExpensesRepository|None" = None
    
    def __init__(self, expenses_ds: ExpensesDataSource):
        self.expenses_ds = expenses_ds

    @classmethod
    def get_instance(cls) -> "ExpensesRepository":
        if cls._instance is None:
            cls._instance = cls(ExpensesDataSource())
        return cls._instance

    async def create_expense(
        self, create_expense: CreateExpense, session: Any = None
    ) -> ExpenseInDb:
        # Generar docNumber si viene vacío o no está especificado
        doc_number = create_expense.docNumber
        if not doc_number or doc_number.strip() == "":
            doc_number = await CounterManager().next_expense_number(session)

        now_ms = TimeTools.get_now_in_milliseconds()
        expense_data = create_expense.model_dump(exclude={"docNumber"})
        if expense_data.get("status") == "paid":
            if expense_data.get("amountPaid", 0) == 0:
                expense_data["amountPaid"] = expense_data["amount"]
            if expense_data.get("paidAt") is None:
                expense_data["paidAt"] = now_ms

        new_expense = ExpenseInDb(
            **expense_data,
            id=UuidTool.generate_uuid(),
            docNumber=doc_number,
            createdAt=now_ms,
            updatedAt=None,
            isDeleted=False,
        )

        await self.expenses_ds.create_expense(new_expense.model_dump(), session=session)
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
        current = await self.get_expense_by_id(expense_id)
        if current is None:
            return None

        now_ms = TimeTools.get_now_in_milliseconds()
        updated_data = expense.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = now_ms

        if "amount" in updated_data:
            new_amount = updated_data["amount"]
            if new_amount is None or new_amount <= 0:
                raise ValueError("El monto del gasto debe ser mayor a cero")
            if new_amount < max(0, current.amountPaid):
                raise ValueError(
                    "El monto no puede ser menor al total ya abonado"
                )

        if updated_data.get("status") == "open" and (
            current.amountPaid > 0 or len(current.payments) > 0
        ):
            raise ValueError(
                "No se puede cambiar a abierto un gasto con abonos registrados"
            )

        if updated_data.get("status") == "paid" and "amountPaid" not in updated_data:
            target_amount = updated_data.get("amount", current.amount)
            updated_data["amountPaid"] = target_amount
            updated_data.setdefault("paidAt", now_ms)

        result = await self.expenses_ds.update_expense_by_id(expense_id, updated_data)
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def delete_expense_by_id(
        self, expense_id: str, session: Any = None
    ) -> ExpenseInDb | None:
        current = await self.get_expense_by_id(expense_id)
        if current is None:
            return None
        if len(current.payments) > 0 or current.status == "partiallyPaid":
            raise ValueError(
                "No se puede eliminar un gasto que ya tiene abonos registrados"
            )

        result = await self.expenses_ds.delete_expense_by_id(
            expense_id, session=session
        )
        if result is None:
            return None
        return ExpenseInDb.model_validate(result)

    async def add_to_amount_paid(self, request: AddToAmountRequest) -> ExpenseInDb | None:
        if request.amountPaid <= 0:
            raise ValueError("El monto del abono debe ser mayor a cero")

        existing = await self.get_expense_by_id(request.expenseId)
        if existing is None:
            return None

        if existing.status in {"paid", "cancelled"}:
            raise ValueError("El gasto ya está pagado o cancelado")

        remaining = max(0, existing.amount - max(0, existing.amountPaid))
        if request.amountPaid > remaining:
            raise ValueError("El monto del abono excede el saldo pendiente")

        now_ms = TimeTools.get_now_in_milliseconds()
        payment = ExpensePayment(
            id=UuidTool.generate_uuid(),
            amount=request.amountPaid,
            paymentMethod=request.paymentMethod,
            reference=request.reference,
            note=request.note,
            paidAt=request.paidAt or now_ms,
            createdBy=request.createdBy,
            createdAt=now_ms,
        )

        result = await self.expenses_ds.add_to_amount_paid(
            request.expenseId,
            request.amountPaid,
            payment_record=payment.model_dump(),
        )
        if result is None:
            raise ValueError("No se pudo registrar el abono porque el saldo cambió")
        return ExpenseInDb.model_validate(result)

    async def get_accounts_payable_summary(
        self, branch_id: str | None = None, overdue_cutoff_ms: int | None = None
    ) -> AccountsPayableSummary:
        result = await self.expenses_ds.get_accounts_payable_summary(
            branch_id=branch_id,
            overdue_cutoff_ms=overdue_cutoff_ms,
        )
        return AccountsPayableSummary.model_validate(result)

    async def get_expenses_summary_in_range(self, start_date: int, end_date: int) -> dict[str, Any]:
        return await self.expenses_ds.get_expenses_summary_in_range(start_date, end_date)

    async def get_expenses_totals_in_range(
        self,
        start_date: int,
        end_date: int,
        branch_id: str,
        user_id: str | None = None,
    ) -> ExpenseTotals:
        result = await self.expenses_ds.get_expenses_totals_in_range(
            start_date, end_date, branch_id, user_id
        )
        return ExpenseTotals.model_validate(result)
