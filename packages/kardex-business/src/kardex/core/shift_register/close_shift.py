import asyncio
from typing import Any

from kardex.repos.v1.shifts import CloseShiftRequest, ShiftInDb, ShiftPreview
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    DevolutionsCollection,
    InvoicesCollection,
    ReceiptsCollection,
    ShiftCashMovementsCollection,
    ShiftsCollection,
)
from kardex.tools import ShiftNotOpen, ShiftNotFound, TimeTools

from .shift_totals import (
    ShiftTotals,
    cash_movement_totals_from_aggregation,
    compute_shift_totals,
    credit_note_totals_from_aggregation,
    devolution_totals_from_aggregation,
    payment_breakdown_from_aggregation,
)


async def aggregate_shift_totals(shift_id: str, initial_cash: int) -> ShiftTotals:
    """Recolecta los totales del turno mediante agregaciones de MongoDB."""
    invoices_col = InvoicesCollection.get_instance()
    receipts_col = ReceiptsCollection.get_instance()
    devolutions_col = DevolutionsCollection.get_instance()
    credit_notes_col = CreditNotesCollection.get_instance()
    movements_col = ShiftCashMovementsCollection.get_instance()

    (
        invoice_rows,
        cancelled_invoice_rows,
        receipt_rows,
        devolution_rows,
        credit_note_rows,
        movement_rows,
    ) = await asyncio.gather(
        invoices_col.get_payment_type_totals_by_shift(shift_id),
        invoices_col.get_cancelled_payment_type_totals_by_shift(shift_id),
        receipts_col.get_payment_method_totals_by_shift(shift_id),
        devolutions_col.get_totals_by_status_by_shift(shift_id),
        credit_notes_col.get_totals_by_status_by_shift(shift_id),
        movements_col.get_type_totals_by_shift(shift_id),
    )
    cancelled_receipt_totals = await receipts_col.get_cancelled_totals_by_shift(shift_id)

    devolution_total, devolution_count = devolution_totals_from_aggregation(
        devolution_rows
    )
    credit_note_total, credit_note_count = credit_note_totals_from_aggregation(
        credit_note_rows
    )
    cash_in_total, cash_out_total = cash_movement_totals_from_aggregation(
        movement_rows
    )

    return compute_shift_totals(
        initial_cash=initial_cash,
        invoices=payment_breakdown_from_aggregation(invoice_rows),
        cancelled_invoices=payment_breakdown_from_aggregation(cancelled_invoice_rows),
        receipts=payment_breakdown_from_aggregation(receipt_rows),
        cancelled_receipt_total=cancelled_receipt_totals.get("total", 0),
        cancelled_receipt_count=cancelled_receipt_totals.get("count", 0),
        devolution_total=devolution_total,
        devolution_count=devolution_count,
        credit_note_total=credit_note_total,
        credit_note_count=credit_note_count,
        cash_in_total=cash_in_total,
        cash_out_total=cash_out_total,
    )


async def _get_shift_or_raise(shift_id: str) -> dict[str, Any]:
    collection = ShiftsCollection.get_instance()
    shift = await collection.fetch_shift_by_id(shift_id)

    if shift is None:
        raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)

    return shift


async def calculate_shift_preview(shift_id: str) -> ShiftPreview:
    """Devuelve el consolidado en vivo del turno sin persistirlo."""
    shift = await _get_shift_or_raise(shift_id)
    totals = await aggregate_shift_totals(
        shift_id, int(shift.get("initialCash") or 0)
    )

    payload = {
        key: value
        for key, value in shift.items()
        if key in ShiftPreview.model_fields
    }
    payload.update(totals.to_dict())

    return ShiftPreview(**payload)


async def close_shift(
    shift_id: str, close_request: CloseShiftRequest
) -> ShiftInDb:
    """Cierra y arquea el turno guardando el consolidado inmutable.

    Orden intencional:
    1. Marca el turno como `closed` de forma atomica (filtro `status == "open"`
       en el update). A partir de ese momento `validate_shift_link` rechaza
       documentos nuevos con ese `shiftId`, cerrando la ventana en la que un
       documento podia quedar fuera del consolidado.
    2. Agrega los totales con el turno ya cerrado.
    3. Persiste el consolidado y `cashDifference` en un unico `$set`.

    Si la agregacion fallara entre (1) y (3), el turno quedaria cerrado con
    totales en cero. Es una consecuencia aceptada de eliminar la ventana entre
    agregacion y escritura; no se usa un estado intermedio ni transacciones.
    """
    collection = ShiftsCollection.get_instance()
    now = TimeTools.get_now_in_milliseconds()

    closing_data: dict[str, Any] = {
        "status": "closed",
        "countedCash": close_request.countedCash,
        "closingNotes": close_request.closingNotes,
        "closedBy": close_request.closedBy.model_dump(),
        "closedAt": now,
        "updatedAt": now,
    }

    closing_shift = await collection.close_shift_by_id(shift_id, closing_data)

    if closing_shift is None:
        existing = await collection.fetch_shift_by_id(shift_id)
        if existing is None:
            raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)
        raise ShiftNotOpen(
            f"Shift {shift_id} is not open", shift_id=shift_id
        )

    totals = await aggregate_shift_totals(
        shift_id, int(closing_shift.get("initialCash") or 0)
    )

    consolidated_data: dict[str, Any] = {
        **totals.to_dict(),
        "cashDifference": close_request.countedCash - totals.expectedCash,
    }

    updated = await collection.update_shift_by_id(shift_id, consolidated_data)

    if updated is None:
        raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)

    return ShiftInDb.model_validate(updated)
