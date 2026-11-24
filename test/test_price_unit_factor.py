import pytest

from kardex.core.default_values.create_default_unit_scales import (
    OLD_DEFAULT_SCALES,
    default_unit_scales,
)
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryEntryBatchItem,
    calculate_line_amount,
)
from kardex.core.invoice_register.process_invoice import normalize_invoice_discounts
from kardex.core.order_register.process_order import normalize_order_totals
from kardex.core.product_register.product_type_lifecycle import (
    update_product_with_type_transition,
)
from kardex.repos.v1.adjustment_requests.models.adjustment_request_model import (
    CreateAdjustmentRequestItem,
)
from kardex.repos.v1.common.models import ClientInfo, UserInfo
from kardex.repos.v1.common.models.entry_item import EntryItem
from kardex.repos.v1.common.models.exit_item import ExitItem
from kardex.repos.v1.common.models.sale_item import ProductItem, SaleItem
from kardex.repos.v1.common.models.transfer_item import TransferItem
from kardex.repos.v1.invoices.models.invoice_model import CreateInvoice
from kardex.repos.v1.orders.models.order_model import CreateOrder
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.products.models.product_model import BaseProduct, UpdateProduct
from kardex.repos.v1.unit_scales.models.unit_scale_model import BaseUnitScale
from kardex.services.mongo_collections.v1 import (
    ProductAccountsCollection,
    ProductTransactionsCollection,
    ProductsCollection,
)
from kardex.tools import InvalidOperation


def test_models_default_price_unit_factor_is_one() -> None:
    scale = BaseUnitScale(name="Unidad", baseUnit="Unidad")
    assert scale.priceUnitFactor == 1

    product = BaseProduct(name="Arroz", unitName="Libra", tags=[])
    assert product.priceUnitFactor == 1

    sale_item = SaleItem(
        product=ProductItem(id="p1", name="Arroz", unitName="Libra"),
        quantity=10,
        cost=100,
        price=200,
        subTotal=2000,
        total=2000,
    )
    assert sale_item.priceUnitFactor == 1

    entry_item = EntryItem(productId="p1", productName="Arroz", cost=100, quantity=10)
    assert entry_item.priceUnitFactor == 1

    exit_item = ExitItem(productId="p1", productName="Arroz", cost=100, quantity=-10)
    assert exit_item.priceUnitFactor == 1

    transfer_item = TransferItem(
        id="p1",
        name="Arroz",
        unitName="Libra",
        brandName="",
        quantity=10,
        cost=100,
    )
    assert transfer_item.priceUnitFactor == 1

    adj_item = CreateAdjustmentRequestItem(
        productId="p1",
        productName="Arroz",
        countedQuantity=5,
        cost=100,
    )
    assert adj_item.priceUnitFactor == 1


def test_default_continuous_scales_keep_quarters_and_add_decimal_variants() -> None:
    by_name = {scale.name: scale for scale in default_unit_scales}

    for unit_name in ("Libra", "Kilo", "Litro", "Metro"):
        quarter_scale = by_name[unit_name]
        assert quarter_scale.baseUnit == f"1/4 {unit_name}"
        assert quarter_scale.priceUnitFactor == 1
        assert quarter_scale.defaultUnitIndex == 1
        assert quarter_scale.units[0].name == unit_name
        assert quarter_scale.units[0].conversionFactor == 4

        decimal_scale = by_name[f"{unit_name} (Decimal)"]
        assert decimal_scale.baseUnit == f"0.01 {unit_name}"
        assert decimal_scale.priceUnitFactor == 100
        assert decimal_scale.defaultUnitIndex == 1
        assert decimal_scale.units[0].name == unit_name
        assert decimal_scale.units[0].conversionFactor == 100

    assert ("Libra", "1/4 Libra") not in OLD_DEFAULT_SCALES
    assert ("Litro", "1/4 Litro") not in OLD_DEFAULT_SCALES
    assert ("Metro", "1/4 Metro") not in OLD_DEFAULT_SCALES


def test_calculate_line_amount_with_price_unit_factor() -> None:
    # Retrocompatible (factor = 1)
    assert calculate_line_amount(1450, 10, 1) == 14500

    # 1.35 lb (135 centésimas) a 14.50/lb (1450¢) -> 19.575 -> 1958¢ (19.58)
    assert calculate_line_amount(1450, 135, 100) == 1958

    # Caso exacto .5 con parte entera par: 18.50/lb × 0.25 lb = 462.5¢ -> 463¢ (half-up)
    assert calculate_line_amount(1850, 25, 100) == 463

    # Caso negativo half-away-from-zero: -462.5¢ -> -463¢
    assert calculate_line_amount(1850, -25, 100) == -463

    # 0.10 lb (10 centésimas) a 14.50/lb -> 145¢ (1.45 exacto)
    assert calculate_line_amount(1450, 10, 100) == 145

    # 2 Arrobas = 50 lb (5000 centésimas) a 14.50/lb -> 72500¢ (725.00 exacto)
    assert calculate_line_amount(1450, 5000, 100) == 72500


def test_weighted_average_cost_is_invariant_to_price_unit_factor() -> None:
    # Tenías 5.00 lb (500 centésimas) a 16.00/lb (1600¢)
    existing = {
        "p1": ProductAccountInDb(
            branchId="b1",
            productId="p1",
            currentStock=500,
            promiseStock=0,
            averageCost=1600,
            lastCost=1600,
            maximumCost=1600,
            createdAt=1000,
            updatedAt=None,
        )
    }
    # Compras 10.00 lb (1000 centésimas) a 18.50/lb (1850¢)
    batch = InventoryBatchTransformer.prepare_entry(
        branch_id="b1",
        is_commerce_branch=True,
        items=[InventoryEntryBatchItem(product_id="p1", quantity=1000, unit_cost=1850)],
        existing_accounts_dict=existing,
        document_id="doc1",
        doc_number="ENT-1",
        tx_type="entry",
        tx_subtype="entry",
    )
    # Promedio esperado: (5*1600 + 10*1850) / 15 = 26500 / 15 = 1766.67 -> 1767¢/lb
    assert batch.accounts_update[0]["avg_cost"] == 1767


@pytest.mark.asyncio
async def test_update_product_blocks_price_unit_factor_change_with_stock_or_tx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_doc = {
        "id": "p1",
        "name": "Arroz",
        "unitName": "1/4 Libra",
        "tags": [],
        "productType": "item",
        "priceUnitFactor": 1,
        "createdAt": 1000,
        "updatedAt": None,
        "isDeleted": False,
    }

    class FakeProductsCol:
        async def fetch_product_by_id(self, product_id: str) -> dict | None:
            return existing_doc if product_id == "p1" else None

        async def update_product_by_id(
            self, product_id: str, data: dict, session=None
        ) -> dict:
            return {**existing_doc, **data}

    class FakeAccountsColWithStock:
        async def get_product_accounts_by_product(self, product_id: str) -> list[dict]:
            return [{"productId": product_id, "currentStock": 40, "promiseStock": 0}]

    class FakeAccountsColEmpty:
        async def get_product_accounts_by_product(self, product_id: str) -> list[dict]:
            return [{"productId": product_id, "currentStock": 0, "promiseStock": 0}]

    class FakeTxColWithTx:
        async def has_transactions_for_product(self, product_id: str) -> bool:
            return True

    class FakeTxColEmpty:
        async def has_transactions_for_product(self, product_id: str) -> bool:
            return False

    monkeypatch.setattr(
        ProductsCollection, "get_instance", classmethod(lambda cls: FakeProductsCol())
    )

    # Caso 1: Con stock -> debe fallar
    monkeypatch.setattr(
        ProductAccountsCollection,
        "get_instance",
        classmethod(lambda cls: FakeAccountsColWithStock()),
    )
    monkeypatch.setattr(
        ProductTransactionsCollection,
        "get_instance",
        classmethod(lambda cls: FakeTxColEmpty()),
    )
    with pytest.raises(InvalidOperation):
        await update_product_with_type_transition(
            "p1", UpdateProduct(priceUnitFactor=100)
        )

    # Caso 2: Sin stock pero con transacciones históricas -> debe fallar
    monkeypatch.setattr(
        ProductAccountsCollection,
        "get_instance",
        classmethod(lambda cls: FakeAccountsColEmpty()),
    )
    monkeypatch.setattr(
        ProductTransactionsCollection,
        "get_instance",
        classmethod(lambda cls: FakeTxColWithTx()),
    )
    with pytest.raises(InvalidOperation):
        await update_product_with_type_transition(
            "p1", UpdateProduct(priceUnitFactor=100)
        )

    # Caso 3: Sin stock ni transacciones -> debe permitirlo
    monkeypatch.setattr(
        ProductTransactionsCollection,
        "get_instance",
        classmethod(lambda cls: FakeTxColEmpty()),
    )
    updated = await update_product_with_type_transition(
        "p1", UpdateProduct(priceUnitFactor=100)
    )
    assert updated is not None
    assert updated.priceUnitFactor == 100


def test_normalize_invoice_discounts_recalculates_inflated_subtotal_with_price_unit_factor() -> (
    None
):
    # Simula un cliente con caché desactualizada que envía 1800 * 5000 = 9_000_000 (90,000.00)
    # mientras el servidor ya resolvió priceUnitFactor = 100 (50.00 lb a 18.00 = 900.00).
    item = SaleItem(
        product=ProductItem(
            id="azucar-1",
            name="Azúcar",
            unitName="Libra",
            priceUnitFactor=100,
        ),
        selectedPrice=1,
        quantity=5000,
        cost=1000,
        price=1800,
        subTotal=9_000_000,
        total=9_000_000,
        conversionFactor=100,
        priceUnitFactor=100,
    )
    invoice = CreateInvoice(
        branchId="b1",
        clientId="c1",
        clientInfo=ClientInfo(name="Cliente"),
        saleItems=[item],
        status="paid",
        paymentType="cash",
        totalCost=50_000,
        total=9_000_000,
        createdBy=UserInfo(id="u1", name="User"),
    )

    normalize_invoice_discounts(invoice)

    assert invoice.saleItems[0].subTotal == 90_000
    assert invoice.saleItems[0].total == 90_000
    assert invoice.total == 90_000


def test_normalize_order_totals_recalculates_inflated_subtotal_with_price_unit_factor() -> (
    None
):
    item = SaleItem(
        product=ProductItem(
            id="azucar-1",
            name="Azúcar",
            unitName="Libra",
            priceUnitFactor=100,
        ),
        selectedPrice=1,
        quantity=5000,
        cost=1000,
        price=1800,
        subTotal=9_000_000,
        discountPercentage=10,
        totalDiscount=900_000,
        total=8_100_000,
        conversionFactor=100,
        priceUnitFactor=100,
    )
    order = CreateOrder(
        branchId="b1",
        clientId="c1",
        clientInfo=ClientInfo(name="Cliente"),
        saleItems=[item],
        status="open",
        paymentType="cash",
        totalCost=50_000,
        total=8_100_000,
        createdBy=UserInfo(id="u1", name="User"),
    )

    normalize_order_totals(order)

    assert order.saleItems[0].subTotal == 90_000
    assert order.saleItems[0].totalDiscount == 9_000
    assert order.saleItems[0].total == 81_000
    assert order.total == 81_000
