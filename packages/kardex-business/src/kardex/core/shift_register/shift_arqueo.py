import asyncio
from typing import Any, Mapping, Sequence

from kardex.core.shift_register.close_shift import aggregate_shift_totals
from kardex.core.shift_register.shift_totals import (
    COLLECTION_CREDIT_NOTES,
    COLLECTION_DEVOLUTIONS,
    COLLECTION_INVOICES,
    COLLECTION_RECEIPTS,
    ShiftTotals,
    is_document_counted,
    resolve_totals_source,
    totals_from_shift_document,
)
from kardex.repos.v1.common.filter_params import ShiftCashMovementFilterParams
from kardex.repos.v1.shift_cash_movements import ShiftCashMovementsRepository
from kardex.repos.v1.shifts import (
    ShiftArqueoDocument,
    ShiftArqueoMeta,
    ShiftArqueoResponse,
    ShiftArqueoTotals,
    ShiftInDb,
)
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    DevolutionsCollection,
    InvoicesCollection,
    ReceiptsCollection,
    ShiftsCollection,
)
from kardex.tools import ShiftNotFound


def _as_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def _payment_method(
    collection: str, row: Mapping[str, Any]
) -> str | None:
    if collection == COLLECTION_INVOICES:
        return row.get("paymentType")
    if collection == COLLECTION_RECEIPTS:
        return row.get("paymentMethod")
    return None


def _to_arqueo_document(
    collection: str, row: Mapping[str, Any]
) -> ShiftArqueoDocument:
    amount_key = "amount" if collection == COLLECTION_CREDIT_NOTES else "total"
    client_info = row.get("clientInfo") or {}

    reference_doc_number = None
    if collection in (COLLECTION_DEVOLUTIONS, COLLECTION_CREDIT_NOTES):
        reference_doc_number = row.get("originalInvoiceDocNumber")

    bank_reference = (
        row.get("bankReference")
        if collection in (COLLECTION_INVOICES, COLLECTION_RECEIPTS)
        else None
    )

    return ShiftArqueoDocument(
        id=str(row.get("id") or ""),
        docNumber=str(row.get("docNumber") or ""),
        amount=_as_int(row.get(amount_key)),
        paymentMethod=_payment_method(collection, row),
        bankReference=bank_reference,
        status=row.get("status"),
        type=row.get("type") if collection == COLLECTION_CREDIT_NOTES else None,
        clientName=client_info.get("name"),
        createdAt=_as_int(row.get("createdAt")),
        referenceDocNumber=reference_doc_number,
        counted=is_document_counted(collection, row.get("status")),
    )


def _limit_rows(
    rows: Sequence[Any], limit: int
) -> tuple[list[Any], bool]:
    if len(rows) > limit:
        return list(rows[:limit]), True
    return list(rows), False


async def build_shift_arqueo(
    shift_id: str,
    include_documents: bool = True,
    limit: int = 500,
) -> ShiftArqueoResponse:
    """Arma el arqueo completo de un turno en una sola respuesta.

    Para turnos `closed` no se recalcula el consolidado: se devuelve el que
    quedo persistido al cerrar, para que el arqueo coincida con el ticket.
    """
    shifts_col = ShiftsCollection.get_instance()
    shift_data = await shifts_col.fetch_shift_by_id(shift_id)

    if shift_data is None:
        raise ShiftNotFound(f"Shift {shift_id} not found", shift_id=shift_id)

    totals_source = resolve_totals_source(shift_data.get("status"))
    initial_cash = _as_int(shift_data.get("initialCash"))

    async def _resolve_totals() -> ShiftTotals:
        if totals_source == "stored":
            return totals_from_shift_document(shift_data)
        return await aggregate_shift_totals(shift_id, initial_cash)

    shift = ShiftInDb.model_validate(shift_data)

    if not include_documents:
        totals = await _resolve_totals()
        return ShiftArqueoResponse(
            shift=shift,
            totals=ShiftArqueoTotals.model_validate(totals.to_dict()),
            cashMovements=[],
            invoices=[],
            receipts=[],
            devolutions=[],
            creditNotes=[],
            meta=ShiftArqueoMeta(
                totalsSource=totals_source,
                documentsLimit=limit,
                truncated=None,
            ),
        )

    movements_repo = ShiftCashMovementsRepository.get_instance()
    movements_params = ShiftCashMovementFilterParams(
        shiftId=shift_id, offset=0, limit=limit + 1
    )

    (
        totals,
        invoice_rows,
        receipt_rows,
        devolution_rows,
        credit_note_rows,
        movements,
    ) = await asyncio.gather(
        _resolve_totals(),
        InvoicesCollection.get_instance().fetch_documents_by_shift(shift_id, limit),
        ReceiptsCollection.get_instance().fetch_documents_by_shift(shift_id, limit),
        DevolutionsCollection.get_instance().fetch_documents_by_shift(shift_id, limit),
        CreditNotesCollection.get_instance().fetch_documents_by_shift(shift_id, limit),
        movements_repo.get_all_shift_cash_movements(movements_params),
    )

    invoices, invoices_truncated = _limit_rows(invoice_rows, limit)
    receipts, receipts_truncated = _limit_rows(receipt_rows, limit)
    devolutions, devolutions_truncated = _limit_rows(devolution_rows, limit)
    credit_notes, credit_notes_truncated = _limit_rows(credit_note_rows, limit)

    movements_truncated = len(movements) > limit
    movements = movements[:limit]
    movements.reverse()

    truncated = any(
        (
            invoices_truncated,
            receipts_truncated,
            devolutions_truncated,
            credit_notes_truncated,
            movements_truncated,
        )
    )

    return ShiftArqueoResponse(
        shift=shift,
        totals=ShiftArqueoTotals.model_validate(totals.to_dict()),
        cashMovements=movements,
        invoices=[_to_arqueo_document(COLLECTION_INVOICES, row) for row in invoices],
        receipts=[_to_arqueo_document(COLLECTION_RECEIPTS, row) for row in receipts],
        devolutions=[
            _to_arqueo_document(COLLECTION_DEVOLUTIONS, row) for row in devolutions
        ],
        creditNotes=[
            _to_arqueo_document(COLLECTION_CREDIT_NOTES, row) for row in credit_notes
        ],
        meta=ShiftArqueoMeta(
            totalsSource=totals_source,
            documentsLimit=limit,
            truncated=truncated,
        ),
    )
