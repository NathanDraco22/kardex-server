from dataclasses import dataclass
from typing import Any, Iterable, List

from kardex.repos.v1.credit_notes import CreateCreditNote, CreditNoteInDb
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import ProductTransactionInDb
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    InvoicesCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.tools import InvalidOperation, UuidTool, TimeTools
from kardex.services import MongoService


@dataclass(frozen=True)
class ReturnedLineAmounts:
    quantity: int
    subTotal: int
    totalDiscount: int
    total: int


def calculate_returned_line_amounts(
    *,
    invoice_quantity: int,
    invoice_sub_total: int,
    invoice_total: int,
    quantity: int,
) -> ReturnedLineAmounts:
    """Prorratea los importes de una linea facturada usando division entera (floor)."""
    if invoice_quantity <= 0:
        raise InvalidOperation("Invoice line quantity must be greater than 0.")
    if quantity <= 0:
        raise InvalidOperation("Returned quantity must be greater than 0.")
    if quantity > invoice_quantity:
        raise InvalidOperation(
            "Returned quantity cannot be greater than the invoiced quantity."
        )

    returned_sub_total = (invoice_sub_total * quantity) // invoice_quantity
    returned_total = (invoice_total * quantity) // invoice_quantity

    return ReturnedLineAmounts(
        quantity=quantity,
        subTotal=returned_sub_total,
        totalDiscount=max(0, returned_sub_total - returned_total),
        total=returned_total,
    )


def validate_devolution_line(
    *,
    invoice_item_index: int,
    invoice_quantity: int,
    invoice_sub_total: int,
    invoice_total: int,
    previously_returned: int,
    quantity: int,
) -> ReturnedLineAmounts:
    """Valida el acumulado de devoluciones de una linea y prorratea sus importes."""
    if previously_returned < 0:
        raise InvalidOperation("Previously returned quantity cannot be negative.")

    remaining = invoice_quantity - previously_returned
    if remaining <= 0:
        raise InvalidOperation(
            f"Invoice line {invoice_item_index} was already fully returned."
        )
    if quantity <= 0:
        raise InvalidOperation(
            f"Returned quantity for invoice line {invoice_item_index} must be greater than 0."
        )
    if quantity > remaining:
        raise InvalidOperation(
            f"Returned quantity for invoice line {invoice_item_index} exceeds the "
            f"remaining quantity ({remaining})."
        )

    return calculate_returned_line_amounts(
        invoice_quantity=invoice_quantity,
        invoice_sub_total=invoice_sub_total,
        invoice_total=invoice_total,
        quantity=quantity,
    )


def sum_previously_returned_quantities(
    credit_notes: Iterable[dict[str, Any]],
    invoice_item_index: int,
    product_id: str,
) -> int:
    """Suma lo ya devuelto por linea de factura en notas de credito no canceladas ni rechazadas.

    Las notas antiguas sin `invoiceItemIndex` no se pueden atribuir con certeza a
    una linea concreta, por lo que se ignoran aqui. El frontend aplica un fallback
    conservador para mostrarlas, y el riesgo residual queda documentado.
    """
    total = 0
    for credit_note in credit_notes:
        if credit_note.get("status") in ("cancelled", "rejected"):
            continue
        for item in credit_note.get("returnedItems") or []:
            if item.get("invoiceItemIndex") != invoice_item_index:
                continue
            product = item.get("product") or {}
            if product.get("id") != product_id:
                continue
            total += abs(int(item.get("quantity") or 0))
    return total


async def _recalculate_devolution_items(
    create_credit_note: CreateCreditNote,
    session: Any,
) -> None:
    """Valida y recalcula los items devueltos dentro de la transaccion del insert."""
    invoices_col = InvoicesCollection.get_instance()
    credit_notes_col = CreditNotesCollection.get_instance()

    invoice_id = create_credit_note.originalInvoiceId
    if not invoice_id:
        raise InvalidOperation("Devolution credit notes require an original invoice.")

    invoice_data = await invoices_col.fetch_invoice_by_id_with_session(
        invoice_id, session
    )
    if invoice_data is None:
        raise InvalidOperation(f"Original invoice {invoice_id} not found.")
    invoice = InvoiceInDb.model_validate(invoice_data)

    if invoice.branchId != create_credit_note.branchId:
        raise InvalidOperation("The original invoice belongs to a different branch.")
    if invoice.clientId != create_credit_note.clientId:
        raise InvalidOperation("The original invoice belongs to a different client.")

    previous_credit_notes = await credit_notes_col.fetch_credit_notes_by_invoice_id(
        invoice_id, session=session
    )

    seen_indices: set[int] = set()
    total_amount = 0

    for item in create_credit_note.returnedItems:
        index = item.invoiceItemIndex
        if index is None:
            raise InvalidOperation(
                "Every returned item must include its invoiceItemIndex."
            )
        if index in seen_indices:
            raise InvalidOperation(
                f"Duplicate invoiceItemIndex {index} in returned items."
            )
        seen_indices.add(index)

        if index < 0 or index >= len(invoice.saleItems):
            raise InvalidOperation(
                f"invoiceItemIndex {index} is out of range for invoice {invoice_id}."
            )

        invoice_item = invoice.saleItems[index]

        if item.product.id != invoice_item.product.id:
            raise InvalidOperation(
                f"Product {item.product.id} does not match invoice line {index}."
            )

        returned_factor = max(item.conversionFactor, 1)
        invoice_factor = max(invoice_item.conversionFactor, 1)
        if returned_factor != invoice_factor:
            raise InvalidOperation(
                f"conversionFactor {returned_factor} does not match invoice line "
                f"{index} (expected {invoice_factor})."
            )

        previously_returned = sum_previously_returned_quantities(
            previous_credit_notes, index, invoice_item.product.id
        )

        amounts = validate_devolution_line(
            invoice_item_index=index,
            invoice_quantity=invoice_item.quantity,
            invoice_sub_total=invoice_item.subTotal,
            invoice_total=invoice_item.total,
            previously_returned=previously_returned,
            quantity=item.quantity,
        )

        # El backend es la fuente de verdad: se ignoran cantidades e importes del cliente.
        item.quantity = amounts.quantity
        item.subTotal = amounts.subTotal
        item.totalDiscount = amounts.totalDiscount
        item.total = amounts.total
        item.cost = invoice_item.cost
        item.price = invoice_item.price
        item.selectedPrice = invoice_item.selectedPrice
        item.discountPercentage = invoice_item.discountPercentage
        item.iva = invoice_item.iva
        item.conversionFactor = invoice_factor

        total_amount += amounts.total

    if total_amount <= 0:
        raise InvalidOperation("Credit note total must be greater than 0.")

    create_credit_note.amount = total_amount


async def process_credit_note(
    create_credit_note: CreateCreditNote,
) -> CreditNoteInDb:
    """
    Procesa la emisión inicial de una nota de crédito de forma atómica:
    1. Si llega idempotencyKey y ya existe una nota para la sucursal, la devuelve.
    2. Si type == 'devolution':
       - Valida y recalcula los items contra la factura original y notas previas.
       - NO toca inventario físico ni kárdex (el reingreso ocurre formalmente al APROBAR).
    3. Si type == 'amount':
       - Solo valida y registra el documento por el monto establecido.
    4. Asigna número de documento correlativo si no viene especificado.
    5. Guarda la nota de crédito en MongoDB con status='emitted'.
    """
    mongo_client = MongoService().client
    credit_note_col = CreditNotesCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            if create_credit_note.idempotencyKey:
                existing = await credit_note_col.fetch_credit_note_by_idempotency_key(
                    create_credit_note.branchId,
                    create_credit_note.idempotencyKey,
                    session=session,
                )
                if existing is not None:
                    return CreditNoteInDb.model_validate(existing)

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()
            credit_note_id = UuidTool.generate_uuid()

            # 1. Si es de tipo devolución, validamos contra la factura original
            if create_credit_note.type == "devolution":
                if not create_credit_note.returnedItems:
                    raise InvalidOperation(
                        "Devolution credit notes must include returned items."
                    )
                await _recalculate_devolution_items(create_credit_note, session)

            if not create_credit_note.docNumber:
                create_credit_note.docNumber = (
                    await CounterManager().next_credit_note_number(session=session)
                )

            # 2. Crear el documento de la nota de crédito en estado "emitted"
            new_credit_note_data = create_credit_note.model_dump()
            new_credit_note_data["id"] = credit_note_id
            new_credit_note_data["status"] = "emitted"
            new_credit_note_data["createdAt"] = now_in_milliseconds
            new_credit_note_data["updatedAt"] = None

            await credit_note_col.create_credit_note_with_session(
                new_credit_note_data, session=session
            )

            return CreditNoteInDb.model_validate(new_credit_note_data)
