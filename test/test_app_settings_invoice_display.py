from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.orders.orders_controller import OrdersController
from kardex.repos.v1.app_settings.models.app_setting_model import (
    AppSettingInDb,
    CreateAppSetting,
    UpdateAppSetting,
)
from kardex.repos.v1.common.models import ClientInfo, PaymentDetail, UserInfo
from kardex.repos.v1.invoices.models.invoice_model import InvoiceInDb
from kardex.repos.v1.orders.models.order_model import OrderInDb


def test_create_app_setting_invoice_display_defaults_false():
    settings = CreateAppSetting()
    assert settings.showInvoiceItemsSummary is False
    assert settings.showInvoiceOrderCreator is False
    assert settings.chargeConvertedOrdersToShift is False


def test_legacy_app_setting_without_invoice_display_fields_defaults_false():
    legacy_doc = {
        "id": "Default",
        "createdAt": 1700000000000,
        "currency": "NIO",
    }
    settings = AppSettingInDb.model_validate(legacy_doc)
    assert settings.showInvoiceItemsSummary is False
    assert settings.showInvoiceOrderCreator is False
    assert settings.chargeConvertedOrdersToShift is False


def test_update_app_setting_partial_serialization():
    patch = UpdateAppSetting(showInvoiceItemsSummary=True)
    assert patch.model_dump(exclude_unset=True) == {
        "showInvoiceItemsSummary": True,
    }


def test_invoice_invoiced_by_is_optional_and_serializable():
    base_payload = {
        "id": "inv-1",
        "branchId": "branch-1",
        "clientId": "client-1",
        "clientInfo": {"name": "Cliente", "group": "General"},
        "docNumber": "F-0001",
        "saleItems": [],
        "status": "open",
        "paymentType": "cash",
        "totalCost": 0,
        "total": 1000,
        "createdBy": {"id": "seller-1", "name": "Carlos Vendedor"},
        "createdAt": 1700000000000,
    }

    legacy_invoice = InvoiceInDb.model_validate(base_payload)
    assert legacy_invoice.invoicedBy is None

    with_invoiced_by = InvoiceInDb.model_validate(
        {
            **base_payload,
            "invoicedBy": {"id": "cashier-1", "name": "María Cajera"},
        }
    )
    assert with_invoiced_by.invoicedBy == UserInfo(
        id="cashier-1", name="María Cajera"
    )


@pytest.mark.asyncio
async def test_convert_order_to_invoice_sets_invoiced_by_and_preserves_created_by():
    order = OrderInDb(
        id="ord-1",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="ORD-10",
        saleItems=[],
        status="open",
        paymentType="cash",
        totalCost=0,
        total=1000,
        createdBy=UserInfo(id="seller-1", name="Carlos Vendedor"),
        createdAt=1700000000000,
    )
    completed_order = order.model_copy(update={"status": "completed", "invoiceId": "inv-1"})
    created_invoice = InvoiceInDb(
        id="inv-1",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="F-0001",
        orderNumber="ORD-10",
        saleItems=[],
        status="open",
        paymentType="cash",
        totalCost=0,
        total=1000,
        createdBy=order.createdBy,
        invoicedBy=UserInfo(id="cashier-1", name="María Cajera"),
        createdAt=1700000001000,
    )

    orders_repo = SimpleNamespace(
        get_order_by_id=AsyncMock(side_effect=[order, completed_order]),
    )
    users_repo = SimpleNamespace(
        get_user_by_id=AsyncMock(
            return_value=SimpleNamespace(username="María Cajera")
        ),
    )
    controller = OrdersController(
        orders_repo=orders_repo,
        users_repo=users_repo,
        app_settings_tool=SimpleNamespace(
            get_current_app_settings=AsyncMock(return_value=CreateAppSetting())
        ),
    )
    regis_mock = AsyncMock(return_value=(created_invoice, None))
    controller.invoice_register = SimpleNamespace(regis_invoice=regis_mock)

    res_invoice, res_order = await controller.convert_order_to_invoice(
        "ord-1",
        invoiced_by_user_id="cashier-1",
        invoiced_by_username="maria",
        shift_id="shift-ignored",
    )

    assert res_order.status == "completed"
    assert res_invoice.invoicedBy == UserInfo(id="cashier-1", name="María Cajera")

    sent_payload = regis_mock.call_args.args[0]
    assert sent_payload.createdBy == UserInfo(id="seller-1", name="Carlos Vendedor")
    assert sent_payload.orderInfo is not None
    assert sent_payload.orderInfo.createdBy == UserInfo(
        id="seller-1", name="Carlos Vendedor"
    )
    assert sent_payload.invoicedBy == UserInfo(id="cashier-1", name="María Cajera")
    assert sent_payload.shiftId is None


@pytest.mark.asyncio
async def test_convert_order_to_invoice_links_shift_when_setting_enabled():
    order = OrderInDb(
        id="ord-2",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="ORD-20",
        saleItems=[],
        status="draft",
        paymentType="cash",
        totalCost=0,
        total=2000,
        createdBy=UserInfo(id="seller-1", name="Carlos Vendedor"),
        createdAt=1700000000000,
    )
    completed_order = order.model_copy(update={"status": "completed", "invoiceId": "inv-2"})
    created_invoice = InvoiceInDb(
        id="inv-2",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="F-0002",
        orderNumber="ORD-20",
        saleItems=[],
        status="open",
        paymentType="cash",
        totalCost=0,
        total=2000,
        createdBy=order.createdBy,
        shiftId="shift-1",
        createdAt=1700000001000,
    )

    orders_repo = SimpleNamespace(
        get_order_by_id=AsyncMock(side_effect=[order, completed_order]),
    )
    users_repo = SimpleNamespace(
        get_user_by_id=AsyncMock(return_value=SimpleNamespace(username="maria")),
    )
    controller = OrdersController(
        orders_repo=orders_repo,
        users_repo=users_repo,
        app_settings_tool=SimpleNamespace(
            get_current_app_settings=AsyncMock(
                return_value=CreateAppSetting(
                    useShifts=True,
                    chargeConvertedOrdersToShift=True,
                )
            )
        ),
    )
    regis_mock = AsyncMock(return_value=(created_invoice, None))
    controller.invoice_register = SimpleNamespace(regis_invoice=regis_mock)

    await controller.convert_order_to_invoice(
        "ord-2",
        invoiced_by_user_id="cashier-1",
        shift_id="shift-1",
    )

    sent_payload = regis_mock.call_args.args[0]
    assert sent_payload.shiftId == "shift-1"


@pytest.mark.asyncio
async def test_convert_order_to_invoice_allows_no_shift_when_user_has_no_active_shift():
    order = OrderInDb(
        id="ord-3",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="ORD-30",
        saleItems=[],
        status="open",
        paymentType="cash",
        totalCost=0,
        total=2000,
        createdBy=UserInfo(id="seller-1", name="Carlos Vendedor"),
        createdAt=1700000000000,
    )
    completed_order = order.model_copy(update={"status": "completed", "invoiceId": "inv-3"})
    created_invoice = InvoiceInDb(
        id="inv-3",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="F-0003",
        orderNumber="ORD-30",
        saleItems=[],
        status="open",
        paymentType="cash",
        totalCost=0,
        total=2000,
        createdBy=order.createdBy,
        shiftId=None,
        createdAt=1700000001000,
    )
    regis_mock = AsyncMock(return_value=(created_invoice, None))
    controller = OrdersController(
        orders_repo=SimpleNamespace(
            get_order_by_id=AsyncMock(side_effect=[order, completed_order])
        ),
        users_repo=SimpleNamespace(get_user_by_id=AsyncMock(return_value=None)),
        app_settings_tool=SimpleNamespace(
            get_current_app_settings=AsyncMock(
                return_value=CreateAppSetting(
                    useShifts=True,
                    chargeConvertedOrdersToShift=True,
                )
            )
        ),
    )
    controller.invoice_register = SimpleNamespace(regis_invoice=regis_mock)

    res_invoice, _ = await controller.convert_order_to_invoice("ord-3", shift_id=None)

    assert res_invoice.shiftId is None
    sent_payload = regis_mock.call_args.args[0]
    assert sent_payload.shiftId is None


@pytest.mark.asyncio
async def test_convert_order_to_invoice_applies_payment_type_reference_and_detail():
    order = OrderInDb(
        id="ord-4",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="ORD-40",
        saleItems=[],
        status="draft",
        paymentType="cash",
        totalCost=0,
        total=5000,
        createdBy=UserInfo(id="seller-1", name="Carlos Vendedor"),
        createdAt=1700000000000,
    )
    completed_order = order.model_copy(update={"status": "completed", "invoiceId": "inv-4"})
    detail = PaymentDetail(
        paidCurrency="NIO",
        tenderedAmount=5000,
        exchangeRate=1.0,
        changeAmount=0,
    )
    created_invoice = InvoiceInDb(
        id="inv-4",
        branchId="branch-1",
        clientId="client-1",
        clientInfo=ClientInfo(name="Cliente", group="General"),
        docNumber="F-0004",
        orderNumber="ORD-40",
        saleItems=[],
        status="paid",
        paymentType="transfer",
        bankReference="REF-999",
        paymentDetail=detail,
        totalCost=0,
        total=5000,
        createdBy=order.createdBy,
        createdAt=1700000001000,
    )

    regis_mock = AsyncMock(return_value=(created_invoice, None))
    controller = OrdersController(
        orders_repo=SimpleNamespace(
            get_order_by_id=AsyncMock(side_effect=[order, completed_order])
        ),
        users_repo=SimpleNamespace(get_user_by_id=AsyncMock(return_value=None)),
        app_settings_tool=SimpleNamespace(
            get_current_app_settings=AsyncMock(return_value=CreateAppSetting())
        ),
    )
    controller.invoice_register = SimpleNamespace(regis_invoice=regis_mock)

    await controller.convert_order_to_invoice(
        "ord-4",
        payment_type="transfer",
        bank_reference="  REF-999  ",
        payment_detail=detail,
    )
    sent_payload = regis_mock.call_args.args[0]
    assert sent_payload.paymentType == "transfer"
    assert sent_payload.bankReference == "REF-999"
    assert sent_payload.paymentDetail == detail

    # Cuando se convierte a crédito, limpia bankReference y paymentDetail
    regis_mock.reset_mock()
    controller.orders_repo = SimpleNamespace(
        get_order_by_id=AsyncMock(side_effect=[order, completed_order])
    )
    await controller.convert_order_to_invoice(
        "ord-4",
        payment_type="credit",
        bank_reference="REF-999",
        payment_detail=detail,
    )
    credit_payload = regis_mock.call_args.args[0]
    assert credit_payload.paymentType == "credit"
    assert credit_payload.bankReference == ""
    assert credit_payload.paymentDetail is None
