from kardex.repos.v1.expenses import ExpensesRepository
from kardex.repos.v1.shift_cash_movements import ShiftCashMovementInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ShiftCashMovementsCollection,
    ShiftsCollection,
)
from kardex.tools import CashMovementNotFound, ShiftNotOpen, ShiftNotFound, TimeTools


async def delete_cash_movement(movement_id: str) -> ShiftCashMovementInDb:
    """Borrado lógico del movimiento y del gasto vinculado.

    Solo se permite mientras el turno siga abierto: al arquear, el consolidado
    es inmutable.
    """
    movement_col = ShiftCashMovementsCollection.get_instance()
    shifts_col = ShiftsCollection.get_instance()
    expenses_repo = ExpensesRepository.get_instance()

    movement = await movement_col.fetch_shift_cash_movement_by_id(movement_id)
    if movement is None:
        raise CashMovementNotFound(
            f"Cash movement {movement_id} not found", movement_id=movement_id
        )

    shift = await shifts_col.fetch_shift_by_id(movement.get("shiftId") or "")
    if shift is None:
        raise ShiftNotFound(
            f"Shift {movement.get('shiftId')} not found",
            shift_id=movement.get("shiftId"),
        )

    if shift.get("status") != "open":
        raise ShiftNotOpen(
            f"Shift {shift.get('id')} is not open", shift_id=shift.get("id")
        )

    mongo_client = MongoService().client

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            now = TimeTools.get_now_in_milliseconds()

            deleted = await movement_col.soft_delete_shift_cash_movement_by_id(
                movement_id, now, session=session
            )

            expense_id = movement.get("expenseId")
            if expense_id:
                await expenses_repo.delete_expense_by_id(expense_id, session=session)

    if deleted is None:
        raise CashMovementNotFound(
            f"Cash movement {movement_id} not found", movement_id=movement_id
        )

    return ShiftCashMovementInDb.model_validate(deleted)
