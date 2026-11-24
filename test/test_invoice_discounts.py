from kardex.core.invoice_register.process_invoice import normalize_invoice_discounts
from kardex.repos.v1.app_settings.models.app_setting_model import BaseAppSetting
from kardex.repos.v1.common.models import (
    ClientInfo,
    DiscountType,
    ProductItem,
    SaleItem,
    UserInfo,
)
from kardex.repos.v1.invoices.models.invoice_model import CreateInvoice, InvoiceInDb


def _make_sale_item(
    *,
    sub_total: int,
    discount_type: DiscountType | None = None,
    discount_percentage: int = 0,
    total_discount: int = 0,
    total: int | None = None,
) -> SaleItem:
    return SaleItem(
        product=ProductItem(id="p1", name="Producto 1", unitName="UND"),
        selectedPrice=1,
        quantity=1,
        cost=500,
        price=sub_total,
        subTotal=sub_total,
        discountType=discount_type,
        discountPercentage=discount_percentage,
        totalDiscount=total_discount,
        total=sub_total if total is None else total,
    )


def _make_invoice(
    items: list[SaleItem],
    *,
    discount_type: DiscountType | None = None,
    discount_value: int = 0,
) -> CreateInvoice:
    return CreateInvoice(
        branchId="b1",
        clientId="c1",
        clientInfo=ClientInfo(name="Cliente"),
        saleItems=items,
        status="paid",
        paymentType="cash",
        discountType=discount_type,
        discountValue=discount_value,
        totalCost=500,
        total=0,
        createdBy=UserInfo(id="u1", name="User"),
    )


def test_app_setting_use_discounts_defaults_false() -> None:
    setting = BaseAppSetting()
    assert setting.useDiscounts is False


def test_normalize_item_percentage_and_amount_discounts() -> None:
    item_pct = _make_sale_item(
        sub_total=10000,
        discount_type="percentage",
        discount_percentage=15,
    )
    item_amt = _make_sale_item(
        sub_total=10000,
        discount_type="amount",
        total_discount=2500,
    )
    inv = _make_invoice([item_pct, item_amt])
    normalize_invoice_discounts(inv)

    assert inv.saleItems[0].totalDiscount == 1500
    assert inv.saleItems[0].total == 8500
    assert inv.saleItems[1].discountPercentage == 0
    assert inv.saleItems[1].totalDiscount == 2500
    assert inv.saleItems[1].total == 7500
    assert inv.itemDiscounts == 4000
    assert inv.invoiceDiscount == 0
    assert inv.total == 16000
    assert inv.totalDiscount == 4000


def test_normalize_invoice_percentage_discount_after_item_discounts() -> None:
    item = _make_sale_item(
        sub_total=10000,
        discount_type="percentage",
        discount_percentage=10,
    )
    inv = _make_invoice([item], discount_type="percentage", discount_value=20)
    normalize_invoice_discounts(inv)

    # Item net = 9000; 20% of 9000 = 1800 -> total = 7200
    assert inv.itemDiscounts == 1000
    assert inv.invoiceDiscount == 1800
    assert inv.total == 7200
    assert inv.totalDiscount == 2800


def test_normalize_invoice_amount_discount_clamped_to_net_total() -> None:
    item = _make_sale_item(sub_total=5000)
    inv = _make_invoice([item], discount_type="amount", discount_value=8000)
    normalize_invoice_discounts(inv)

    assert inv.invoiceDiscount == 5000
    assert inv.discountValue == 5000
    assert inv.total == 0


def test_legacy_invoice_deserialization_without_discount_fields() -> None:
    legacy_payload = {
        "id": "inv-legacy",
        "branchId": "b1",
        "clientId": "c1",
        "clientInfo": {"id": "c1", "name": "Cliente"},
        "saleItems": [
            {
                "product": {"id": "p1", "name": "P1", "unitName": "UND"},
                "selectedPrice": 1,
                "quantity": 1,
                "cost": 500,
                "price": 10000,
                "subTotal": 10000,
                "discountPercentage": 10,
                "totalDiscount": 1000,
                "total": 9000,
            }
        ],
        "status": "paid",
        "paymentType": "cash",
        "totalCost": 500,
        "total": 9000,
        "createdBy": {"id": "u1", "name": "User", "username": "user"},
        "createdAt": 1700000000000,
    }
    inv = InvoiceInDb.model_validate(legacy_payload)
    assert inv.discountType is None
    assert inv.discountValue == 0
    assert inv.invoiceDiscount == 0
    assert inv.effectiveItemDiscounts == 1000
    assert inv.totalDiscount == 1000
