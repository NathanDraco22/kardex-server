from kardex.services.mongo_collections.v1 import ShiftsCollection
from kardex.tools import InvalidOperation, ShiftNotOpen, ShiftNotFound


async def validate_shift_link(
    shift_id: str | None, branch_id: str, *, require_open: bool = True
) -> None:
    """Valida que un documento comercial pueda vincularse al turno indicado.

    `None` se permite: la funcionalidad de turnos es opcional y el documento
    simplemente se guarda sin `shiftId`.

    `require_open=False` solo exige que el turno exista y sea de la misma
    sucursal; se usa al confirmar devoluciones creadas antes del cierre.
    """
    if shift_id is None:
        return

    collection = ShiftsCollection.get_instance()
    shift = await collection.fetch_shift_by_id(shift_id)

    if shift is None:
        raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)

    if require_open and shift.get("status") != "open":
        raise ShiftNotOpen(f"Shift {shift_id} is not open", shift_id=shift_id)

    if shift.get("branchId") != branch_id:
        raise InvalidOperation(
            f"Shift {shift_id} belongs to another branch.",
            detail=f"shiftBranchId={shift.get('branchId')} branchId={branch_id}",
        )
