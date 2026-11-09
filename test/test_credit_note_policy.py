import pytest

from kardex.core.credit_note_register.process_credit_note import (
    calculate_returned_line_amounts,
    sum_previously_returned_quantities,
    validate_devolution_line,
)
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.credit_notes import CreateCreditNote
from kardex.tools import InvalidOperation


def _make_credit_note(idempotency_key: str | None = None) -> CreateCreditNote:
    return CreateCreditNote(
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente"),
        type="devolution",
        amount=100,
        createdBy=UserInfo(id="user-1", name="Usuario"),
        idempotencyKey=idempotency_key,
    )


def test_full_line_returns_exact_invoice_amounts():
    amounts = calculate_returned_line_amounts(
        invoice_quantity=5,
        invoice_sub_total=500,
        invoice_total=480,
        quantity=5,
    )

    assert amounts.quantity == 5
    assert amounts.subTotal == 500
    assert amounts.total == 480
    assert amounts.totalDiscount == 20


def test_partial_line_prorates_with_floor():
    amounts = calculate_returned_line_amounts(
        invoice_quantity=5,
        invoice_sub_total=100,
        invoice_total=90,
        quantity=1,
    )

    assert amounts.quantity == 1
    assert amounts.subTotal == 20
    assert amounts.total == 18
    assert amounts.totalDiscount == 2


def test_partial_line_floors_money():
    amounts = calculate_returned_line_amounts(
        invoice_quantity=3,
        invoice_sub_total=100,
        invoice_total=90,
        quantity=1,
    )

    assert amounts.subTotal == 33
    assert amounts.total == 30
    assert amounts.totalDiscount == 3


def test_discount_is_never_negative():
    amounts = calculate_returned_line_amounts(
        invoice_quantity=3,
        invoice_sub_total=100,
        invoice_total=110,
        quantity=1,
    )

    assert amounts.subTotal == 33
    assert amounts.total == 36
    assert amounts.totalDiscount == 0


def test_rejects_zero_quantity():
    with pytest.raises(InvalidOperation):
        calculate_returned_line_amounts(
            invoice_quantity=5,
            invoice_sub_total=500,
            invoice_total=500,
            quantity=0,
        )


def test_rejects_quantity_greater_than_invoice():
    with pytest.raises(InvalidOperation):
        calculate_returned_line_amounts(
            invoice_quantity=5,
            invoice_sub_total=500,
            invoice_total=500,
            quantity=6,
        )


def test_validate_accepts_partial_below_accumulated_limit():
    amounts = validate_devolution_line(
        invoice_item_index=0,
        invoice_quantity=5,
        invoice_sub_total=500,
        invoice_total=400,
        previously_returned=4,
        quantity=1,
    )

    assert amounts.quantity == 1
    assert amounts.subTotal == 100
    assert amounts.total == 80


def test_validate_rejects_accumulated_overflow():
    with pytest.raises(InvalidOperation):
        validate_devolution_line(
            invoice_item_index=0,
            invoice_quantity=5,
            invoice_sub_total=500,
            invoice_total=400,
            previously_returned=4,
            quantity=2,
        )


def test_validate_rejects_fully_returned_line():
    with pytest.raises(InvalidOperation):
        validate_devolution_line(
            invoice_item_index=0,
            invoice_quantity=5,
            invoice_sub_total=500,
            invoice_total=400,
            previously_returned=5,
            quantity=1,
        )


def test_sum_previously_returned_only_counts_matching_index_and_product():
    credit_notes = [
        {
            "status": "confirmed",
            "returnedItems": [
                {
                    "invoiceItemIndex": 0,
                    "product": {"id": "product-1"},
                    "quantity": 2,
                },
                {
                    "invoiceItemIndex": 1,
                    "product": {"id": "product-1"},
                    "quantity": 4,
                },
                {
                    "invoiceItemIndex": 0,
                    "product": {"id": "product-2"},
                    "quantity": 3,
                },
                {
                    "product": {"id": "product-1"},
                    "quantity": 5,
                },
            ],
        },
        {
            "status": "confirmed",
            "returnedItems": [
                {
                    "invoiceItemIndex": 0,
                    "product": {"id": "product-1"},
                    "quantity": 1,
                },
            ],
        },
    ]

    assert sum_previously_returned_quantities(credit_notes, 0, "product-1") == 3


def test_sum_previously_returned_skips_cancelled_notes():
    credit_notes = [
        {
            "status": "cancelled",
            "returnedItems": [
                {
                    "invoiceItemIndex": 0,
                    "product": {"id": "product-1"},
                    "quantity": 5,
                },
            ],
        },
    ]

    assert sum_previously_returned_quantities(credit_notes, 0, "product-1") == 0


def test_sale_item_accepts_invoice_item_index():
    item = SaleItem(
        product=ProductItem(
            id="product-1",
            name="Producto",
            unitName="Unidad",
            brandName="Marca",
        ),
        quantity=1,
        cost=10,
        price=20,
        subTotal=20,
        total=20,
        invoiceItemIndex=3,
    )

    assert item.model_dump()["invoiceItemIndex"] == 3


def test_credit_note_model_accepts_idempotency_key():
    credit_note = _make_credit_note(idempotency_key="key-123")

    assert credit_note.model_dump()["idempotencyKey"] == "key-123"


def test_credit_note_model_defaults_idempotency_key_to_none():
    credit_note = _make_credit_note()

    assert credit_note.model_dump()["idempotencyKey"] is None
