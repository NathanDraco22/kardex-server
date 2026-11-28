from typing import Any

import pytest

from kardex.core.default_values import SALE_CLIENT_ID
from kardex.core.devolution_register.devolution_policy import DevolutionPolicy
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.devolutions import DevolutionInDb
from kardex.repos.v1.invoices import InvoiceInDb


def _sale_item() -> SaleItem:
    return SaleItem(
        product=ProductItem(id="product-1", name="Producto", unitName="Unidad"),
        quantity=1,
        cost=500,
        price=1000,
        subTotal=1000,
        total=1000,
    )


def _invoice(**overrides: Any) -> InvoiceInDb:
    data: dict[str, Any] = {
        "id": "invoice-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "saleItems": [_sale_item()],
        "status": "open",
        "paymentType": "cash",
        "totalCost": 500,
        "total": 1000,
        "createdBy": UserInfo(id="user-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return InvoiceInDb(**data)


def _devolution(**overrides: Any) -> DevolutionInDb:
    data: dict[str, Any] = {
        "id": "dev-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "returnedItems": [_sale_item()],
        "description": "Devolución de prueba",
        "status": "open",
        "totalCost": 500,
        "total": 1000,
        "createdBy": UserInfo(id="user-1", name="Cajero"),
        "createdAt": 0,
    }
    data.update(overrides)
    return DevolutionInDb(**data)


@pytest.mark.parametrize(
    ("returned_items", "expected_reason"),
    [
        (
            [],
            "La devolución debe incluir al menos un producto.",
        ),
        ([_sale_item()], None),
    ],
)
def test_items_decision(
    returned_items: list[SaleItem], expected_reason: str | None
) -> None:
    decision = DevolutionPolicy().items_decision(returned_items)

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({}, None),
        (
            {"status": "cancelled"},
            "Cannot create a devolution for a cancelled invoice.",
        ),
        (
            {"invoiceDiscount": 100},
            "No se permiten devoluciones por producto en facturas con "
            "descuento global.",
        ),
        (
            {"paymentType": "credit", "amountPaid": 100},
            "No se permiten devoluciones sobre facturas a crédito con abonos "
            "o pagadas.",
        ),
        (
            {"paymentType": "credit", "status": "partiallyPaid"},
            "No se permiten devoluciones sobre facturas a crédito con abonos "
            "o pagadas.",
        ),
        (
            {"paymentType": "credit", "status": "paid"},
            "No se permiten devoluciones sobre facturas a crédito con abonos "
            "o pagadas.",
        ),
        ({"paymentType": "credit"}, None),
        ({"paymentType": "cash", "amountPaid": 1000}, None),
    ],
)
def test_invoice_decision(
    overrides: dict[str, Any], expected_reason: str | None
) -> None:
    decision = DevolutionPolicy().invoice_decision(_invoice(**overrides))

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


def test_invoice_decision_checks_global_discount_before_credit_payments():
    invoice = _invoice(
        invoiceDiscount=100,
        paymentType="credit",
        amountPaid=100,
    )

    decision = DevolutionPolicy().invoice_decision(invoice)

    assert decision.reason == (
        "No se permiten devoluciones por producto en facturas con descuento global."
    )


@pytest.mark.parametrize(
    ("client_id", "anonymous", "expected_reason"),
    [
        (
            SALE_CLIENT_ID,
            False,
            "Use the anonymous devolution endpoint for this client.",
        ),
        ("client-1", False, None),
        (
            "client-1",
            True,
            "Invalid client ID for anonymous devolution.",
        ),
        (SALE_CLIENT_ID, True, None),
    ],
)
def test_confirmation_client_decision(
    client_id: str, anonymous: bool, expected_reason: str | None
) -> None:
    decision = DevolutionPolicy().confirmation_client_decision(
        _devolution(clientId=client_id),
        anonymous=anonymous,
        sale_client_id=SALE_CLIENT_ID,
    )

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        ("open", None),
        ("confirmed", "Devolution is not open."),
        ("cancelled", "Devolution is not open."),
        ("applied", "Devolution is not open."),
    ],
)
def test_status_decision(status: str, expected_reason: str | None) -> None:
    decision = DevolutionPolicy().status_decision(_devolution(status=status))

    assert decision.allowed is (expected_reason is None)
    assert decision.reason == expected_reason
