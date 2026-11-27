from typing import Any

import pytest

from kardex.core.receipt_register.validate_receipt_payment import (
    validate_receipt_payment,
)
from kardex.repos.v1.app_settings import AppSettingInDb
from kardex.repos.v1.app_settings.models.app_setting_model import CurrencyCode
from kardex.repos.v1.common.models import ClientInfo, PaymentDetail, UserInfo
from kardex.repos.v1.receipts import AppliedInvoice, CreateReceipt
from kardex.tools import InvalidOperation


def _settings(
    currency: CurrencyCode = "NIO",
    secondary_currency: CurrencyCode = "USD",
    exchange_rate: float = 36.0,
    allow_secondary_currency_payment: bool = False,
) -> AppSettingInDb:
    return AppSettingInDb(
        id="Default",
        createdAt=0,
        currency=currency,
        secondaryCurrency=secondary_currency,
        exchangeRate=exchange_rate,
        allowSecondaryCurrencyPayment=allow_secondary_currency_payment,
    )


def _receipt(**overrides: Any) -> CreateReceipt:
    data: dict[str, Any] = {
        "branchId": "b1",
        "clientId": "c1",
        "clientInfo": ClientInfo(name="Cliente Test"),
        "paymentMethod": "cash",
        "total": 1000,
        "createdBy": UserInfo(id="u1", name="Cajero"),
        "appliedInvoices": [
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=1000)
        ],
    }
    data.update(overrides)
    return CreateReceipt(**data)


def test_primary_cash_with_change_is_valid():
    receipt = _receipt(
        paymentDetail=PaymentDetail(
            paidCurrency="NIO",
            tenderedAmount=1500,
            exchangeRate=1.0,
            changeAmount=500,
        )
    )

    validate_receipt_payment(receipt, _settings())


def test_secondary_cash_converts_and_validates_change():
    receipt = _receipt(
        total=60000,
        appliedInvoices=[
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=60000)
        ],
        paymentDetail=PaymentDetail(
            paidCurrency="USD",
            tenderedAmount=2000,
            exchangeRate=36.0,
            changeAmount=12000,
        ),
    )

    validate_receipt_payment(
        receipt,
        _settings(allow_secondary_currency_payment=True),
    )


def test_secondary_payment_requires_flag_enabled():
    receipt = _receipt(
        total=60000,
        appliedInvoices=[
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=60000)
        ],
        paymentDetail=PaymentDetail(
            paidCurrency="USD",
            tenderedAmount=2000,
            exchangeRate=36.0,
            changeAmount=12000,
        ),
    )

    with pytest.raises(InvalidOperation, match="moneda secundaria no está habilitado"):
        validate_receipt_payment(
            receipt,
            _settings(allow_secondary_currency_payment=False),
        )


def test_secondary_payment_requires_valid_exchange_rate():
    receipt = _receipt(
        total=60000,
        appliedInvoices=[
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=60000)
        ],
        paymentDetail=PaymentDetail(
            paidCurrency="USD",
            tenderedAmount=2000,
            exchangeRate=36.0,
            changeAmount=12000,
        ),
    )

    with pytest.raises(InvalidOperation, match="tasa de cambio válida"):
        validate_receipt_payment(
            receipt,
            _settings(
                exchange_rate=0.0,
                allow_secondary_currency_payment=True,
            ),
        )


def test_cash_without_payment_detail_is_legacy_compatible():
    validate_receipt_payment(_receipt(), _settings())


def test_card_with_reference_is_valid_without_payment_detail():
    receipt = _receipt(
        paymentMethod="card",
        bankReference="BAC - 12345",
        paymentDetail=None,
    )

    validate_receipt_payment(receipt, _settings())


def test_card_requires_bank_reference():
    receipt = _receipt(paymentMethod="card", bankReference="", paymentDetail=None)

    with pytest.raises(InvalidOperation, match="referencia bancaria"):
        validate_receipt_payment(receipt, _settings())


def test_transfer_requires_bank_reference():
    receipt = _receipt(paymentMethod="transfer", bankReference="", paymentDetail=None)

    with pytest.raises(InvalidOperation, match="referencia bancaria"):
        validate_receipt_payment(receipt, _settings())


def test_transfer_with_reference_is_valid():
    receipt = _receipt(
        paymentMethod="transfer",
        bankReference="BAC - 12345",
        paymentDetail=None,
    )

    validate_receipt_payment(receipt, _settings())


def test_zero_cash_without_payment_detail_is_valid():
    receipt = _receipt(
        total=0,
        appliedInvoices=[],
        paymentDetail=None,
    )

    validate_receipt_payment(receipt, _settings())


def test_payment_detail_only_applies_to_cash():
    receipt = _receipt(
        paymentMethod="transfer",
        bankReference="BAC - 12345",
        paymentDetail=PaymentDetail(
            paidCurrency="NIO",
            tenderedAmount=1500,
            exchangeRate=1.0,
            changeAmount=500,
        ),
    )

    with pytest.raises(InvalidOperation, match="solo aplica a pagos en efectivo"):
        validate_receipt_payment(receipt, _settings())


def test_tendered_amount_must_cover_total():
    receipt = _receipt(
        paymentDetail=PaymentDetail(
            paidCurrency="NIO",
            tenderedAmount=900,
            exchangeRate=1.0,
            changeAmount=0,
        )
    )

    with pytest.raises(InvalidOperation, match="no cubre el total"):
        validate_receipt_payment(receipt, _settings())


def test_change_must_match_received_amount():
    receipt = _receipt(
        paymentDetail=PaymentDetail(
            paidCurrency="NIO",
            tenderedAmount=1500,
            exchangeRate=1.0,
            changeAmount=400,
        )
    )

    with pytest.raises(InvalidOperation, match="cambio registrado"):
        validate_receipt_payment(receipt, _settings())


def test_payment_currency_must_match_settings():
    receipt = _receipt(
        paymentDetail=PaymentDetail(
            paidCurrency="EUR",
            tenderedAmount=1500,
            exchangeRate=1.0,
            changeAmount=500,
        )
    )

    with pytest.raises(InvalidOperation, match="moneda del pago"):
        validate_receipt_payment(receipt, _settings())


def test_zero_cash_receipt_rejects_payment_detail():
    receipt = _receipt(
        total=0,
        appliedInvoices=[],
        paymentDetail=PaymentDetail(
            paidCurrency="NIO",
            tenderedAmount=0,
            exchangeRate=1.0,
            changeAmount=0,
        ),
    )

    with pytest.raises(InvalidOperation, match="sin cobro en efectivo"):
        validate_receipt_payment(receipt, _settings())


def test_negative_amounts_are_rejected():
    receipt = _receipt(
        appliedInvoices=[
            AppliedInvoice(invoiceId="inv1", docNumber="F-1", amountApplied=-1)
        ]
    )

    with pytest.raises(InvalidOperation, match="no puede ser negativo"):
        validate_receipt_payment(receipt, _settings())

    with pytest.raises(InvalidOperation, match="total del recibo"):
        validate_receipt_payment(_receipt(total=-1), _settings())


def test_payment_detail_without_settings_is_rejected():
    receipt = _receipt(
        paymentDetail=PaymentDetail(
            paidCurrency="NIO",
            tenderedAmount=1000,
            exchangeRate=1.0,
            changeAmount=0,
        )
    )

    with pytest.raises(InvalidOperation, match="configuración de moneda"):
        validate_receipt_payment(receipt, None)
