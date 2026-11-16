import pytest
from pydantic import ValidationError

from kardex.repos.v1.common.models import ClientInfo, PaymentDetail, UserInfo
from kardex.repos.v1.invoices import CreateInvoice, InvoiceInDb
from kardex.repos.v1.receipts import CreateReceipt, ReceiptInDb


def _client_info() -> ClientInfo:
    return ClientInfo(name="Cliente Test", phone="88888888", address="")


def _user_info() -> UserInfo:
    return UserInfo(id="u1", name="Cajero")


def test_invoice_without_payment_detail_is_retrocompatible():
    inv = InvoiceInDb(
        id="inv1",
        branchId="b1",
        clientId="c1",
        clientInfo=_client_info(),
        saleItems=[],
        amountPaid=30000,
        status="paid",
        paymentType="cash",
        totalCost=20000,
        total=30000,
        createdBy=_user_info(),
        createdAt=1700000000,
    )
    assert inv.paymentDetail is None


def test_invoice_with_secondary_currency_payment_detail():
    detail = PaymentDetail(
        paidCurrency="USD",
        tenderedAmount=1000,
        exchangeRate=36.0,
        changeAmount=6000,
    )
    inv = CreateInvoice(
        branchId="b1",
        clientId="c1",
        clientInfo=_client_info(),
        saleItems=[],
        amountPaid=30000,
        status="paid",
        paymentType="cash",
        paymentDetail=detail,
        totalCost=20000,
        total=30000,
        createdBy=_user_info(),
    )
    assert inv.paymentDetail is not None
    assert inv.paymentDetail.paidCurrency == "USD"
    assert inv.paymentDetail.tenderedAmount == 1000
    assert inv.paymentDetail.exchangeRate == 36.0
    assert inv.paymentDetail.changeAmount == 6000


def test_receipt_with_and_without_payment_detail():
    legacy = ReceiptInDb(
        id="r1",
        branchId="b1",
        clientId="c1",
        clientInfo=_client_info(),
        paymentMethod="cash",
        total=30000,
        createdBy=_user_info(),
        createdAt=1700000000,
    )
    assert legacy.paymentDetail is None

    receipt = CreateReceipt(
        branchId="b1",
        clientId="c1",
        clientInfo=_client_info(),
        paymentMethod="cash",
        paymentDetail=PaymentDetail(
            paidCurrency="USD",
            tenderedAmount=1000,
            exchangeRate=36.0,
            changeAmount=6000,
        ),
        total=30000,
        createdBy=_user_info(),
    )
    assert receipt.paymentDetail is not None
    assert receipt.paymentDetail.paidCurrency == "USD"


def test_payment_detail_rejects_invalid_rate_or_negative_amounts():
    with pytest.raises(ValidationError):
        PaymentDetail(
            paidCurrency="USD",
            tenderedAmount=1000,
            exchangeRate=0,
            changeAmount=0,
        )

    with pytest.raises(ValidationError):
        PaymentDetail(
            paidCurrency="USD",
            tenderedAmount=-100,
            exchangeRate=36.0,
            changeAmount=0,
        )
