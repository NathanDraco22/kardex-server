from dataclasses import dataclass, fields
from typing import Any, Iterable, Literal, Mapping

CONFIRMED_DEVOLUTION_STATUSES = ("confirmed",)
COUNTABLE_CREDIT_NOTE_STATUSES = ("approved", "confirmed", "applied")
INVOICE_NON_COUNTED_STATUSES = ("cancelled",)

SHIFT_STATUS_OPEN = "open"
SHIFT_STATUS_CLOSED = "closed"

COLLECTION_INVOICES = "invoices"
COLLECTION_RECEIPTS = "receipts"
COLLECTION_DEVOLUTIONS = "devolutions"
COLLECTION_CREDIT_NOTES = "credit_notes"
COLLECTION_CASH_MOVEMENTS = "cash_movements"

TotalsSource = Literal["live", "stored"]


@dataclass(frozen=True)
class PaymentBreakdown:
    cash: int = 0
    transfer: int = 0
    card: int = 0
    other: int = 0
    credit: int = 0
    count: int = 0


@dataclass(frozen=True)
class ShiftTotals:
    invoiceCashTotal: int = 0
    invoiceTransferTotal: int = 0
    invoiceCardTotal: int = 0
    invoiceOtherTotal: int = 0
    invoiceCashSalesTotal: int = 0
    invoiceCreditTotal: int = 0
    invoiceTotal: int = 0
    invoiceCount: int = 0
    cancelledInvoiceCashTotal: int = 0
    cancelledInvoiceTransferTotal: int = 0
    cancelledInvoiceCardTotal: int = 0
    cancelledInvoiceOtherTotal: int = 0
    cancelledInvoiceCashSalesTotal: int = 0
    cancelledInvoiceCreditTotal: int = 0
    cancelledInvoiceTotal: int = 0
    cancelledInvoiceCount: int = 0
    receiptCashTotal: int = 0
    receiptTransferTotal: int = 0
    receiptCardTotal: int = 0
    receiptOtherTotal: int = 0
    receiptTotal: int = 0
    receiptCount: int = 0
    cancelledReceiptTotal: int = 0
    cancelledReceiptCount: int = 0
    devolutionTotal: int = 0
    devolutionCount: int = 0
    creditNoteTotal: int = 0
    creditNoteCount: int = 0
    cashInTotal: int = 0
    cashOutTotal: int = 0
    expectedCash: int = 0
    totalTransfers: int = 0
    totalCardsAndOthers: int = 0
    grandTotal: int = 0

    def to_dict(self) -> dict[str, int]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


def _as_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def resolve_totals_source(status: str | None) -> TotalsSource:
    """El arqueo de un turno cerrado usa el consolidado guardado, no uno nuevo."""
    if status == SHIFT_STATUS_CLOSED:
        return "stored"
    return "live"


def totals_from_shift_document(shift: Mapping[str, Any]) -> ShiftTotals:
    """Reconstruye `ShiftTotals` desde el documento persistido del turno.

    Los campos ausentes (documentos historicos) caen a 0.
    """
    return ShiftTotals(
        **{
            field.name: _as_int(shift.get(field.name))
            for field in fields(ShiftTotals)
        }
    )


def is_document_counted(
    collection: str, status: str | None, payment_type: str | None = None
) -> bool:
    """Indica si un documento entra en el consolidado del turno.

    Usa las mismas reglas que `aggregate_shift_totals` y las constantes de
    estados definidas arriba.
    """
    if collection == COLLECTION_RECEIPTS:
        return status != "cancelled"

    if collection == COLLECTION_CASH_MOVEMENTS:
        return True

    if collection == COLLECTION_INVOICES:
        return status not in INVOICE_NON_COUNTED_STATUSES

    if collection == COLLECTION_DEVOLUTIONS:
        return status in CONFIRMED_DEVOLUTION_STATUSES and payment_type != "credit"

    if collection == COLLECTION_CREDIT_NOTES:
        return status in COUNTABLE_CREDIT_NOTE_STATUSES

    return False


def payment_breakdown_from_aggregation(
    rows: Iterable[Mapping[str, Any]],
) -> PaymentBreakdown:
    """Convierte filas agregadas por Mongo (paymentType/paymentMethod) en un desglose."""
    totals = {"cash": 0, "transfer": 0, "card": 0, "other": 0, "credit": 0}
    count = 0

    for row in rows:
        key = str(row.get("_id") or "")
        amount = _as_int(row.get("total"))
        count += _as_int(row.get("count"))

        if key in totals:
            totals[key] += amount
        else:
            totals["other"] += amount

    return PaymentBreakdown(
        cash=totals["cash"],
        transfer=totals["transfer"],
        card=totals["card"],
        other=totals["other"],
        credit=totals["credit"],
        count=count,
    )


def status_totals_from_aggregation(
    rows: Iterable[Mapping[str, Any]], statuses: Iterable[str]
) -> tuple[int, int]:
    """Suma las filas cuyo estado esté dentro de `statuses`. Devuelve (total, count)."""
    allowed = set(statuses)
    total = 0
    count = 0

    for row in rows:
        if str(row.get("_id") or "") not in allowed:
            continue
        total += _as_int(row.get("total"))
        count += _as_int(row.get("count"))

    return total, count


def devolution_totals_from_aggregation(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[int, int]:
    return status_totals_from_aggregation(rows, CONFIRMED_DEVOLUTION_STATUSES)


def credit_note_totals_from_aggregation(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[int, int]:
    return status_totals_from_aggregation(rows, COUNTABLE_CREDIT_NOTE_STATUSES)


def cash_movement_totals_from_aggregation(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[int, int]:
    """Devuelve (cashInTotal, cashOutTotal) a partir de filas agrupadas por `type`."""
    cash_in = 0
    cash_out = 0

    for row in rows:
        amount = _as_int(row.get("total"))
        if row.get("_id") == "in":
            cash_in += amount
        elif row.get("_id") == "out":
            cash_out += amount

    return cash_in, cash_out


def compute_shift_totals(
    *,
    initial_cash: int = 0,
    invoices: PaymentBreakdown | None = None,
    cancelled_invoices: PaymentBreakdown | None = None,
    receipts: PaymentBreakdown | None = None,
    cancelled_receipt_total: int = 0,
    cancelled_receipt_count: int = 0,
    devolution_total: int = 0,
    devolution_count: int = 0,
    credit_note_total: int = 0,
    credit_note_count: int = 0,
    cash_in_total: int = 0,
    cash_out_total: int = 0,
) -> ShiftTotals:
    """Calcula el consolidado del turno a partir de importes ya agregados.

    Reglas:
    - `expectedCash` = fondo inicial + facturas en efectivo + recibos en efectivo
      + entradas manuales - devoluciones confirmadas - salidas manuales.
    - `grandTotal` = ventas de contado (facturas no-crédito) + recibos - devoluciones.
    - Una factura a crédito no entra en efectivo; su cobro posterior entra como recibo.
    - Las facturas anuladas se reportan en `cancelledInvoice*` solo de forma informativa
      (ya están excluidas de `invoices`, por lo que no se restan doble).
    """
    invoice_breakdown = invoices or PaymentBreakdown()
    cancelled_breakdown = cancelled_invoices or PaymentBreakdown()
    receipt_breakdown = receipts or PaymentBreakdown()

    invoice_cash_sales_total = (
        invoice_breakdown.cash
        + invoice_breakdown.transfer
        + invoice_breakdown.card
        + invoice_breakdown.other
    )
    invoice_total = invoice_cash_sales_total + invoice_breakdown.credit

    cancelled_invoice_cash_sales_total = (
        cancelled_breakdown.cash
        + cancelled_breakdown.transfer
        + cancelled_breakdown.card
        + cancelled_breakdown.other
    )
    cancelled_invoice_total = (
        cancelled_invoice_cash_sales_total + cancelled_breakdown.credit
    )

    receipt_total = (
        receipt_breakdown.cash
        + receipt_breakdown.transfer
        + receipt_breakdown.card
        + receipt_breakdown.other
    )

    expected_cash = (
        initial_cash
        + invoice_breakdown.cash
        + receipt_breakdown.cash
        + cash_in_total
        - devolution_total
        - cash_out_total
    )

    total_transfers = invoice_breakdown.transfer + receipt_breakdown.transfer
    total_cards_and_others = (
        invoice_breakdown.card
        + invoice_breakdown.other
        + receipt_breakdown.card
        + receipt_breakdown.other
    )
    grand_total = invoice_cash_sales_total + receipt_total - devolution_total

    return ShiftTotals(
        invoiceCashTotal=invoice_breakdown.cash,
        invoiceTransferTotal=invoice_breakdown.transfer,
        invoiceCardTotal=invoice_breakdown.card,
        invoiceOtherTotal=invoice_breakdown.other,
        invoiceCashSalesTotal=invoice_cash_sales_total,
        invoiceCreditTotal=invoice_breakdown.credit,
        invoiceTotal=invoice_total,
        invoiceCount=invoice_breakdown.count,
        cancelledInvoiceCashTotal=cancelled_breakdown.cash,
        cancelledInvoiceTransferTotal=cancelled_breakdown.transfer,
        cancelledInvoiceCardTotal=cancelled_breakdown.card,
        cancelledInvoiceOtherTotal=cancelled_breakdown.other,
        cancelledInvoiceCashSalesTotal=cancelled_invoice_cash_sales_total,
        cancelledInvoiceCreditTotal=cancelled_breakdown.credit,
        cancelledInvoiceTotal=cancelled_invoice_total,
        cancelledInvoiceCount=cancelled_breakdown.count,
        receiptCashTotal=receipt_breakdown.cash,
        receiptTransferTotal=receipt_breakdown.transfer,
        receiptCardTotal=receipt_breakdown.card,
        receiptOtherTotal=receipt_breakdown.other,
        receiptTotal=receipt_total,
        receiptCount=receipt_breakdown.count,
        cancelledReceiptTotal=cancelled_receipt_total,
        cancelledReceiptCount=cancelled_receipt_count,
        devolutionTotal=devolution_total,
        devolutionCount=devolution_count,
        creditNoteTotal=credit_note_total,
        creditNoteCount=credit_note_count,
        cashInTotal=cash_in_total,
        cashOutTotal=cash_out_total,
        expectedCash=expected_cash,
        totalTransfers=total_transfers,
        totalCardsAndOthers=total_cards_and_others,
        grandTotal=grand_total,
    )
