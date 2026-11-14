from pymongo.errors import DuplicateKeyError

from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.shifts import CreateShift, ShiftInDb
from kardex.services.mongo_collections.v1 import ShiftsCollection
from kardex.tools import ActiveShiftAlreadyExistsError, TimeTools, UuidTool


async def open_shift(create_shift: CreateShift) -> ShiftInDb:
    """Abre un turno para un cajero.

    La unicidad de "un turno abierto por usuario" la garantiza el índice único
    parcial de MongoDB (`ux_open_shift_per_user`), no un check-then-insert.
    """
    collection = ShiftsCollection.get_instance()

    existing = await collection.fetch_active_shift_by_user(create_shift.openedBy.id)
    if existing is not None:
        raise ActiveShiftAlreadyExistsError(
            f"User {create_shift.openedBy.id} already has an open shift",
            user_id=create_shift.openedBy.id,
        )

    now = TimeTools.get_now_in_milliseconds()
    doc_number = await CounterManager().next_shift_number()

    new_shift = ShiftInDb(
        **create_shift.model_dump(),
        id=UuidTool.generate_uuid(),
        docNumber=doc_number,
        status="open",
        openedAt=now,
        createdAt=now,
        updatedAt=None,
    )

    try:
        await collection.create_shift(new_shift.model_dump())
    except DuplicateKeyError as error:
        if error.code == 11000:
            raise ActiveShiftAlreadyExistsError(
                f"User {create_shift.openedBy.id} already has an open shift",
                user_id=create_shift.openedBy.id,
            ) from error
        raise

    return new_shift
