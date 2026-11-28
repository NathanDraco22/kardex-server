import pytest

from kardex.core.invoice_register.invoice_rounding_policy import InvoiceRoundingPolicy


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-101, 0),
        (-1, 0),
        (0, 0),
        (1, 100),
        (99, 100),
        (100, 100),
        (101, 200),
        (1012, 1100),
    ],
)
def test_line_subtotal_rounds_up_when_enabled(value: int, expected: int) -> None:
    assert InvoiceRoundingPolicy(True).line_subtotal(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-101, -101),
        (-1, -1),
        (0, 0),
        (1, 1),
        (99, 99),
        (100, 100),
        (101, 101),
        (1012, 1012),
    ],
)
def test_line_subtotal_is_unchanged_when_disabled(value: int, expected: int) -> None:
    assert InvoiceRoundingPolicy(False).line_subtotal(value) == expected


@pytest.mark.parametrize("method_name", ["line_discount", "invoice_discount"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-101, 0),
        (-1, 0),
        (0, 0),
        (1, 0),
        (99, 0),
        (100, 100),
        (199, 100),
        (1012, 1000),
    ],
)
def test_discounts_round_down_when_enabled(
    method_name: str, value: int, expected: int
) -> None:
    method = getattr(InvoiceRoundingPolicy(True), method_name)

    assert method(value) == expected


@pytest.mark.parametrize("method_name", ["line_discount", "invoice_discount"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-101, -101),
        (-1, -1),
        (0, 0),
        (1, 1),
        (99, 99),
        (100, 100),
        (199, 199),
        (1012, 1012),
    ],
)
def test_discounts_are_unchanged_when_disabled(
    method_name: str, value: int, expected: int
) -> None:
    method = getattr(InvoiceRoundingPolicy(False), method_name)

    assert method(value) == expected
