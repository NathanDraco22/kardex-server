import pytest

from kardex.core.shift_register import shift_arqueo
from kardex.core.shift_register.shift_totals import (
    COLLECTION_CASH_MOVEMENTS,
    COLLECTION_CREDIT_NOTES,
    COLLECTION_DEVOLUTIONS,
    COLLECTION_INVOICES,
    COLLECTION_RECEIPTS,
    PaymentBreakdown,
    ShiftTotals,
    cash_movement_totals_from_aggregation,
    compute_shift_totals,
    devolution_totals_from_aggregation,
    is_document_counted,
    payment_breakdown_from_aggregation,
    resolve_totals_source,
    totals_from_shift_document,
)
from kardex.repos.v1.shifts import ShiftArqueoTotals


def test_exact_reconciliation() -> None:
    totals = compute_shift_totals(
        initial_cash=100_000,
        invoices=PaymentBreakdown(
            cash=50_000, transfer=20_000, card=10_000, other=5_000, credit=80_000, count=6
        ),
        receipts=PaymentBreakdown(
            cash=30_000, transfer=15_000, card=5_000, other=2_000, count=3
        ),
        devolution_total=10_000,
        devolution_count=1,
        credit_note_total=25_000,
        credit_note_count=2,
        cash_in_total=5_000,
        cash_out_total=2_000,
    )

    # 100000 + 50000 + 30000 + 5000 - 10000 - 2000
    assert totals.expectedCash == 173_000
    assert totals.invoiceCashSalesTotal == 85_000
    assert totals.invoiceTotal == 165_000
    assert totals.receiptTotal == 52_000
    assert totals.totalTransfers == 35_000
    assert totals.totalCardsAndOthers == 22_000
    assert totals.grandTotal == 85_000 + 52_000 - 10_000
    assert totals.creditNoteTotal == 25_000
    assert totals.creditNoteCount == 2
    assert totals.invoiceCount == 6
    assert totals.receiptCount == 3


def test_surplus() -> None:
    totals = compute_shift_totals(
        initial_cash=10_000,
        invoices=PaymentBreakdown(cash=20_000, count=1),
    )

    assert totals.expectedCash == 30_000

    counted_cash = 35_000
    assert counted_cash - totals.expectedCash == 5_000


def test_shortage() -> None:
    totals = compute_shift_totals(
        initial_cash=10_000,
        invoices=PaymentBreakdown(cash=20_000, count=1),
        receipts=PaymentBreakdown(cash=15_000, count=1),
    )

    assert totals.expectedCash == 45_000

    counted_cash = 40_000
    assert counted_cash - totals.expectedCash == -5_000


def test_empty_shift() -> None:
    totals = compute_shift_totals(initial_cash=25_000)

    assert totals.expectedCash == 25_000
    assert totals.invoiceTotal == 0
    assert totals.receiptTotal == 0
    assert totals.devolutionTotal == 0
    assert totals.grandTotal == 0
    assert totals.invoiceCount == 0


def test_credit_invoice_does_not_enter_cash() -> None:
    totals = compute_shift_totals(
        initial_cash=0,
        invoices=PaymentBreakdown(credit=120_000, cash=5_000, count=2),
    )

    assert totals.invoiceCashTotal == 5_000
    assert totals.invoiceCreditTotal == 120_000
    assert totals.invoiceTotal == 125_000
    assert totals.expectedCash == 5_000

    # Al cobrarse despues, el ingreso entra como recibo del turno de cobro.
    totals_with_receipt = compute_shift_totals(
        initial_cash=0,
        invoices=PaymentBreakdown(credit=120_000, count=1),
        receipts=PaymentBreakdown(cash=120_000, count=1),
    )
    assert totals_with_receipt.expectedCash == 120_000
    assert totals_with_receipt.grandTotal == 120_000


def test_devolution_applied_is_not_counted() -> None:
    rows = [
        {"_id": "applied", "total": 7_000, "count": 1},
        {"_id": "confirmed", "total": 3_000, "count": 1},
        {"_id": "cancelled", "total": 9_000, "count": 1},
    ]

    total, count = devolution_totals_from_aggregation(rows)

    assert total == 3_000
    assert count == 1


def test_payment_breakdown_maps_check_and_other() -> None:
    rows = [
        {"_id": "cash", "total": 1_000, "count": 1},
        {"_id": "check", "total": 2_000, "count": 1},
        {"_id": "other", "total": 3_000, "count": 1},
        {"_id": "card", "total": 4_000, "count": 1},
    ]

    breakdown = payment_breakdown_from_aggregation(rows)

    assert breakdown.cash == 1_000
    assert breakdown.other == 5_000
    assert breakdown.card == 4_000
    assert breakdown.count == 4


def test_cash_movement_totals() -> None:
    rows = [
        {"_id": "in", "total": 8_000, "count": 2},
        {"_id": "out", "total": 3_500, "count": 1},
    ]

    cash_in, cash_out = cash_movement_totals_from_aggregation(rows)

    assert cash_in == 8_000
    assert cash_out == 3_500


def test_totals_from_shift_document_roundtrip() -> None:
    totals = compute_shift_totals(
        initial_cash=50_000,
        invoices=PaymentBreakdown(
            cash=10_000, transfer=5_000, card=2_000, other=1_000, credit=30_000, count=5
        ),
        receipts=PaymentBreakdown(cash=7_000, count=1),
        devolution_total=500,
        devolution_count=1,
        credit_note_total=2_000,
        credit_note_count=1,
        cash_in_total=1_000,
        cash_out_total=300,
    )

    restored = totals_from_shift_document({"id": "shift-1", **totals.to_dict()})

    assert restored == totals


def test_totals_from_shift_document_defaults_to_zero() -> None:
    restored = totals_from_shift_document({"id": "shift-1", "expectedCash": 5_000})

    assert restored == ShiftTotals(expectedCash=5_000)
    assert restored.invoiceTotal == 0
    assert restored.receiptCount == 0
    assert restored.grandTotal == 0


def test_is_document_counted_rules() -> None:
    assert is_document_counted(COLLECTION_INVOICES, "paid")
    assert is_document_counted(COLLECTION_INVOICES, "partiallyPaid")
    assert not is_document_counted(COLLECTION_INVOICES, "cancelled")

    assert is_document_counted(COLLECTION_RECEIPTS, None)

    assert is_document_counted(COLLECTION_DEVOLUTIONS, "confirmed")
    assert not is_document_counted(COLLECTION_DEVOLUTIONS, "open")
    assert not is_document_counted(COLLECTION_DEVOLUTIONS, "applied")

    for status in ("approved", "confirmed", "applied"):
        assert is_document_counted(COLLECTION_CREDIT_NOTES, status)
    assert not is_document_counted(COLLECTION_CREDIT_NOTES, "emitted")
    assert not is_document_counted(COLLECTION_CREDIT_NOTES, "rejected")

    assert is_document_counted(COLLECTION_CASH_MOVEMENTS, None)


def test_resolve_totals_source() -> None:
    assert resolve_totals_source("open") == "live"
    assert resolve_totals_source("closed") == "stored"


def test_arqueo_totals_mirror_shift_totals_fields() -> None:
    """Si `ShiftTotals` crece, el arqueo no debe perder el campo en silencio."""

    assert list(ShiftArqueoTotals.model_fields) == list(ShiftTotals().to_dict())


@pytest.mark.asyncio
async def test_arqueo_without_documents_skips_every_listing(monkeypatch) -> None:
    """`includeDocuments=false` no debe tocar ninguna colección de documentos."""

    closed_shift = {
        "id": "shift-1",
        "branchId": "branch-1",
        "docNumber": "0001",
        "status": "closed",
        "initialCash": 10_000,
        "openedBy": {"id": "user-1", "name": "Cajero"},
        "openedAt": 1_760_000_000_000,
        "createdAt": 1_760_000_000_000,
        "expectedCash": 25_000,
        "grandTotal": 30_000,
    }

    class _FakeShifts:
        @classmethod
        def get_instance(cls):
            return cls()

        async def fetch_shift_by_id(self, shift_id: str):
            return closed_shift

    class _Forbidden:
        @classmethod
        def get_instance(cls):
            raise AssertionError(
                "no debe consultar listados con includeDocuments=false"
            )

    monkeypatch.setattr(shift_arqueo, "ShiftsCollection", _FakeShifts)
    for name in (
        "InvoicesCollection",
        "ReceiptsCollection",
        "DevolutionsCollection",
        "CreditNotesCollection",
        "ShiftCashMovementsRepository",
    ):
        monkeypatch.setattr(shift_arqueo, name, _Forbidden)

    result = await shift_arqueo.build_shift_arqueo(
        "shift-1", include_documents=False
    )

    assert result.meta.totalsSource == "stored"
    assert result.meta.truncated is None
    assert result.totals.expectedCash == 25_000
    assert result.totals.grandTotal == 30_000
    assert result.cashMovements == []
    assert result.invoices == []
    assert result.receipts == []
    assert result.devolutions == []
    assert result.creditNotes == []
