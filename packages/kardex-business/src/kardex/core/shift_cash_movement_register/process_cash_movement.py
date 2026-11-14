from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.core.shift_register.validate_shift_link import validate_shift_link
from kardex.repos.v1.expenses import CreateExpense, ExpensesRepository
from kardex.repos.v1.shift_cash_movements import (
    CreateShiftCashMovement,
    ShiftCashMovementInDb,
)
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import ShiftCashMovementsCollection
from kardex.tools import InvalidOperation, TimeTools, UuidTool


async def process_cash_movement(
    create_movement: CreateShiftCashMovement,
) -> ShiftCashMovementInDb:
    """Registra una entrada/salida de caja de forma atómica.

    Si es una salida (`out`) con `registerAsExpense`, crea también un gasto
    operativo pagado y lo vincula mediante `expenseId`.
    """
    if create_movement.registerAsExpense and create_movement.type != "out":
        raise InvalidOperation("Only cash-out movements can be registered as an expense.")

    await validate_shift_link(create_movement.shiftId, create_movement.branchId)

    mongo_client = MongoService().client
    movement_col = ShiftCashMovementsCollection.get_instance()
    expenses_repo = ExpensesRepository.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            now = TimeTools.get_now_in_milliseconds()

            expense_id: str | None = None
            if create_movement.type == "out" and create_movement.registerAsExpense:
                new_expense = await expenses_repo.create_expense(
                    CreateExpense(
                        type="operative",
                        branchId=create_movement.branchId,
                        amount=create_movement.amount,
                        amountPaid=create_movement.amount,
                        category=create_movement.expenseCategory or "General",
                        description=create_movement.reason,
                        date=now,
                        dateId=TimeTools.timestamp_to_date_id(now),
                        status="paid",
                        paidAt=now,
                        shiftId=create_movement.shiftId,
                        createdBy=create_movement.createdBy,
                    ),
                    session=session,
                )
                expense_id = new_expense.id

            doc_number = await CounterManager().next_cash_movement_number(session)

            new_movement = ShiftCashMovementInDb(
                **create_movement.model_dump(),
                id=UuidTool.generate_uuid(),
                docNumber=doc_number,
                expenseId=expense_id,
                createdAt=now,
                updatedAt=None,
            )

            await movement_col.create_shift_cash_movement(
                new_movement.model_dump(), session=session
            )

            return new_movement
