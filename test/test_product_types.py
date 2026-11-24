from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from kardex.core.credit_note_register.approve_credit_note import approve_credit_note
from kardex.core.credit_note_register.reverse_credit_note import reverse_credit_note
from kardex.core.inventory import ensure_inventory_products, fetch_product_types_map
from kardex.core.invoice_register.process_invoice import (
    _prepare_and_execute_invoice_inventory,
)
from kardex.core.order_register.cancel_order import cancel_order
from kardex.core.product_register.product_type_lifecycle import (
    create_branch_scoped_product,
    update_product_with_type_transition,
)
from kardex.core.product_register.process_create_product_with_data import (
    process_create_product_with_data,
)
from kardex.core.transfer_manager.process_incoming_transfer import (
    process_incoming_transfer,
)
from kardex.kardex_config import KardexConfig, KardexContext, kardexCtx
from kardex.repos.v1.branches.models.branch_model import BranchInDb
from kardex.repos.v1.common.models import (
    ClientInfo,
    ProductItem,
    SaleItem,
    TransferItem,
    UserInfo,
)
from kardex.repos.v1.credit_notes import CreditNoteInDb
from kardex.repos.v1.inventories.models.inventory_model import InventoryProduct
from kardex.repos.v1.invoices import CreateInvoice
from kardex.repos.v1.orders import OrderInDb
from kardex.repos.v1.product_accounts.data.product_accounts_datasource import (
    ProductAccountsDataSource,
)
from kardex.repos.v1.product_accounts.models.product_account_model import (
    UpdateProductAccount,
)
from kardex.repos.v1.product_accounts.product_accounts_repository import (
    ProductAccountsRepository,
)
from kardex.repos.v1.products import (
    CreateProduct,
    CreateProductWithData,
    InventoryInfo,
    ProductInDb,
    UpdateProduct,
)
from kardex.repos.v1.transfers import ReceiveTransferIntent, TransferInDb
from kardex.services.mongo_collections.v1.products_collection import ProductsCollection
from kardex.tools import BranchNotFound, DirectStockAdjustmentBlocked, InvalidOperation


def _fake_mongo_client():
    class _FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        @asynccontextmanager
        async def _tx(self):
            yield

        async def start_transaction(self):
            return self._tx()

    class _FakeClient:
        def start_session(self):
            return _FakeSession()

    return _FakeClient()


def _user() -> UserInfo:
    return UserInfo(id="u1", name="Admin")


@pytest.fixture
def branch_context():
    token = kardexCtx.set(KardexContext(branchId="b1"))
    yield
    kardexCtx.reset(token)


def _client() -> ClientInfo:
    return ClientInfo(name="Cliente Test", phone="88888888", address="")


def test_models_default_to_item_for_retrocompatibility():
    prod = ProductInDb(
        id="p1",
        name="Arroz",
        unitName="Libra",
        tags=[],
        createdAt=1700000000,
    )
    assert prod.productType == "item"
    assert prod.brandName == ""
    assert prod.tracks_inventory is True
    assert prod.is_service is False
    assert prod.branchId is None

    item = ProductItem(id="p1", name="Consulta", unitName="Servicio")
    assert item.productType == "item"
    assert item.brandName == ""

    inv_prod = InventoryProduct(
        id="p1",
        name="Consulta",
        unitName="Servicio",
        tags=[],
    )
    assert inv_prod.productType == "item"


def test_products_collection_filter_builder_branch_and_inventory():
    f_branch = ProductsCollection._build_product_filters(branch_id="b1")
    assert "$and" in f_branch

    f_inv = ProductsCollection._build_product_filters(
        branch_id="b1", only_inventory=True
    )
    clauses = f_inv["$and"]
    assert {"isDeleted": False} in clauses
    assert {
        "$or": [{"productType": "item"}, {"productType": {"$exists": False}}]
    } in clauses

    f_srv = ProductsCollection._build_product_filters(
        branch_id="b1", product_type="service"
    )
    assert {"productType": "service"} in f_srv["$and"]


@pytest.mark.asyncio
async def test_create_branch_scoped_product_creates_only_requested_branch():
    branch = BranchInDb(
        id="b1",
        name="Sucursal A",
        address="",
        phone="",
        idCard="",
        isCommerce=True,
        createdAt=1700000000,
    )
    products_col = MagicMock()
    products_col.create_product_with_session = AsyncMock()
    accounts_col = MagicMock()
    accounts_col.create_new_product_account_with_session = AsyncMock()
    profiles_col = MagicMock()
    profiles_col.create_product_sale_profile_with_session = AsyncMock()

    with (
        patch(
            "kardex.core.product_register.product_type_lifecycle.BranchesTool"
        ) as mock_branches,
        patch(
            "kardex.core.product_register.product_type_lifecycle.MongoService"
        ) as mock_mongo,
        patch(
            "kardex.core.product_register.product_type_lifecycle.CounterManager"
        ) as mock_counter,
        patch.object(ProductsCollection, "get_instance", return_value=products_col),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductAccountsCollection.get_instance",
            return_value=accounts_col,
        ),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductSaleProfilesCollection.get_instance",
            return_value=profiles_col,
        ),
    ):
        mock_branches.return_value.get_branch_by_id.return_value = branch
        mock_mongo.return_value.client = _fake_mongo_client()
        mock_counter.return_value.next_product_number = AsyncMock(return_value="SRV-1")

        created = await create_branch_scoped_product(
            CreateProduct(
                name="Consulta Médica",
                unitName="Consulta",
                tags=["salud"],
                productType="service",
                branchId="b1",
            )
        )

    assert created.productType == "service"
    assert created.branchId == "b1"
    accounts_col.create_new_product_account_with_session.assert_awaited_once()
    profiles_col.create_product_sale_profile_with_session.assert_awaited_once()
    saved_acc = accounts_col.create_new_product_account_with_session.call_args.kwargs[
        "product_account"
    ]
    saved_prof = profiles_col.create_product_sale_profile_with_session.call_args.kwargs[
        "product_sale_profile"
    ]
    assert saved_acc["branchId"] == "b1"
    assert saved_acc["currentStock"] == 0
    assert saved_prof["branchId"] == "b1"


@pytest.mark.asyncio
async def test_create_branch_scoped_product_requires_branch_id():
    with pytest.raises(InvalidOperation):
        await create_branch_scoped_product(
            CreateProduct(
                name="Caramelo",
                unitName="Unidad",
                tags=[],
                productType="nonInventory",
                branchId=None,
            )
        )


@pytest.mark.asyncio
async def test_transition_item_to_service_blocks_with_promise_stock(branch_context):
    branch = BranchInDb(
        id="b1",
        name="Sucursal A",
        address="",
        phone="",
        idCard="",
        isCommerce=True,
        createdAt=1700000000,
    )
    products_col = MagicMock()
    products_col.fetch_product_by_id = AsyncMock(
        return_value={
            "id": "p1",
            "name": "Producto X",
            "unitName": "Unidad",
            "brandName": "Marca",
            "tags": [],
            "productType": "item",
            "createdAt": 1700000000,
        }
    )
    accounts_col = MagicMock()
    accounts_col.get_product_accounts_by_product = AsyncMock(
        return_value=[{"productId": "p1", "branchId": "b1", "currentStock": 10, "promiseStock": 2}]
    )

    with (
        patch(
            "kardex.core.product_register.product_type_lifecycle.BranchesTool"
        ) as mock_branches,
        patch(
            "kardex.core.product_register.product_type_lifecycle.MongoService"
        ) as mock_mongo,
        patch.object(ProductsCollection, "get_instance", return_value=products_col),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductAccountsCollection.get_instance",
            return_value=accounts_col,
        ),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductSaleProfilesCollection.get_instance",
            return_value=MagicMock(),
        ),
    ):
        mock_branches.return_value.get_branch_by_id.return_value = branch
        mock_mongo.return_value.client = _fake_mongo_client()

        with pytest.raises(InvalidOperation):
            await update_product_with_type_transition(
                "p1", UpdateProduct(productType="service")
            )


@pytest.mark.asyncio
async def test_transition_item_to_service_blocks_with_current_stock(branch_context):
    KardexConfig().followTransaction = True
    branch = BranchInDb(
        id="b1",
        name="Sucursal A",
        address="",
        phone="",
        idCard="",
        isCommerce=True,
        createdAt=1700000000,
    )
    existing = {
        "id": "p1",
        "name": "Consulta",
        "unitName": "Unidad",
        "brandName": "",
        "tags": [],
        "productType": "item",
        "createdAt": 1700000000,
    }
    products_col = MagicMock()
    products_col.fetch_product_by_id = AsyncMock(return_value=existing)
    products_col.update_product_by_id = AsyncMock(return_value=existing)
    accounts_col = MagicMock()
    accounts_col.get_product_accounts_by_product = AsyncMock(
        return_value=[
            {
                "productId": "p1",
                "branchId": "b1",
                "currentStock": 50,
                "promiseStock": 0,
                "averageCost": 200,
            }
        ]
    )
    accounts_col.reset_product_accounts_stock_and_cost_with_session = AsyncMock()
    accounts_col.create_product_account_if_not_exist_with_session = AsyncMock()
    profiles_col = MagicMock()
    profiles_col.create_product_sale_profile_if_not_exist_with_session = AsyncMock()

    with (
        patch(
            "kardex.core.product_register.product_type_lifecycle.BranchesTool"
        ) as mock_branches,
        patch(
            "kardex.core.product_register.product_type_lifecycle.MongoService"
        ) as mock_mongo,
        patch.object(ProductsCollection, "get_instance", return_value=products_col),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductAccountsCollection.get_instance",
            return_value=accounts_col,
        ),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductSaleProfilesCollection.get_instance",
            return_value=profiles_col,
        ),
    ):
        mock_branches.return_value.get_branch_by_id.return_value = branch
        mock_mongo.return_value.client = _fake_mongo_client()

        with pytest.raises(InvalidOperation, match="existencias"):
            await update_product_with_type_transition(
                "p1", UpdateProduct(productType="service")
            )

    accounts_col.reset_product_accounts_stock_and_cost_with_session.assert_not_awaited()
    accounts_col.create_product_account_if_not_exist_with_session.assert_not_awaited()
    products_col.update_product_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_transition_item_to_service_allowed_with_zero_stock(branch_context):
    branch = BranchInDb(
        id="b1",
        name="Sucursal A",
        address="",
        phone="",
        idCard="",
        isCommerce=True,
        createdAt=1700000000,
    )
    existing = {
        "id": "p1",
        "name": "Consulta",
        "unitName": "Unidad",
        "brandName": "",
        "tags": [],
        "productType": "item",
        "createdAt": 1700000000,
    }
    products_col = MagicMock()
    products_col.fetch_product_by_id = AsyncMock(return_value=existing)
    products_col.update_product_by_id = AsyncMock(
        return_value={**existing, "productType": "service", "branchId": "b1"}
    )
    accounts_col = MagicMock()
    accounts_col.get_product_accounts_by_product = AsyncMock(
        return_value=[
            {
                "productId": "p1",
                "branchId": "b1",
                "currentStock": 0,
                "promiseStock": 0,
                "averageCost": 0,
            }
        ]
    )
    accounts_col.reset_product_accounts_stock_and_cost_with_session = AsyncMock()
    accounts_col.create_product_account_if_not_exist_with_session = AsyncMock()
    profiles_col = MagicMock()
    profiles_col.create_product_sale_profile_if_not_exist_with_session = AsyncMock()

    with (
        patch(
            "kardex.core.product_register.product_type_lifecycle.BranchesTool"
        ) as mock_branches,
        patch(
            "kardex.core.product_register.product_type_lifecycle.MongoService"
        ) as mock_mongo,
        patch.object(ProductsCollection, "get_instance", return_value=products_col),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductAccountsCollection.get_instance",
            return_value=accounts_col,
        ),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductSaleProfilesCollection.get_instance",
            return_value=profiles_col,
        ),
    ):
        mock_branches.return_value.get_branch_by_id.return_value = branch
        mock_mongo.return_value.client = _fake_mongo_client()

        updated = await update_product_with_type_transition(
            "p1", UpdateProduct(productType="service", branchId="b1")
        )

    assert updated is not None
    assert updated.productType == "service"
    assert updated.branchId == "b1"
    accounts_col.reset_product_accounts_stock_and_cost_with_session.assert_awaited_once()
    profiles_col.create_product_sale_profile_if_not_exist_with_session.assert_awaited_once()
    saved_acc = accounts_col.create_product_account_if_not_exist_with_session.call_args.kwargs[
        "product_account"
    ]
    assert saved_acc["branchId"] == "b1"
    assert saved_acc["currentStock"] == 0


@pytest.mark.asyncio
async def test_transition_service_to_item_resets_reference_costs_and_returns_to_global():
    existing = {
        "id": "p1",
        "name": "Consulta",
        "unitName": "Unidad",
        "brandName": "",
        "tags": [],
        "productType": "service",
        "branchId": "b1",
        "createdAt": 1700000000,
    }
    products_col = MagicMock()
    products_col.fetch_product_by_id = AsyncMock(return_value=existing)
    products_col.update_product_by_id = AsyncMock(
        return_value={**existing, "productType": "item", "branchId": None}
    )
    accounts_col = MagicMock()
    accounts_col.reset_product_accounts_stock_and_cost_with_session = AsyncMock()

    with (
        patch(
            "kardex.core.product_register.product_type_lifecycle.MongoService"
        ) as mock_mongo,
        patch.object(ProductsCollection, "get_instance", return_value=products_col),
        patch(
            "kardex.core.product_register.product_type_lifecycle.ProductAccountsCollection.get_instance",
            return_value=accounts_col,
        ),
    ):
        mock_mongo.return_value.client = _fake_mongo_client()

        updated = await update_product_with_type_transition(
            "p1", UpdateProduct(productType="item")
        )

    assert updated is not None
    assert updated.productType == "item"
    assert updated.branchId is None
    accounts_col.reset_product_accounts_stock_and_cost_with_session.assert_awaited_once()
    # No se aprovisionan cuentas en otras sucursales
    accounts_col.create_product_account_if_not_exist_with_session.assert_not_called()


@pytest.mark.asyncio
async def test_invoice_mixed_cart_only_deducts_inventory_for_items():
    KardexConfig().followTransaction = True
    KardexConfig().letInvoiceWithNegative = False

    invoice = CreateInvoice(
        branchId="b1",
        clientId="c1",
        clientInfo=_client(),
        docNumber="INV-1",
        saleItems=[
            SaleItem(
                product=ProductItem(
                    id="p-item", name="Pastilla", unitName="Caja", productType="item"
                ),
                quantity=2,
                cost=0,
                price=1000,
                subTotal=2000,
                total=2000,
            ),
            SaleItem(
                product=ProductItem(
                    id="p-srv",
                    name="Consulta Médica",
                    unitName="Consulta",
                    productType="service",
                ),
                quantity=1,
                cost=0,
                price=5000,
                subTotal=5000,
                total=5000,
            ),
            SaleItem(
                product=ProductItem(
                    id="p-noninv",
                    name="Caramelo",
                    unitName="Unidad",
                    productType="nonInventory",
                ),
                quantity=3,
                cost=0,
                price=100,
                subTotal=300,
                total=300,
            ),
        ],
        status="paid",
        paymentType="cash",
        totalCost=0,
        total=7300,
        createdBy=_user(),
    )

    product_account_col = MagicMock()
    product_account_col.get_accounts_by_branch_id = AsyncMock(
        return_value=[
            {
                "productId": "p-item",
                "branchId": "b1",
                "currentStock": 10,
                "promiseStock": 0,
                "averageCost": 400,
                "lastCost": 400,
                "maximumCost": 400,
                "createdAt": 1700000000,
            },
            {
                "productId": "p-srv",
                "branchId": "b1",
                "currentStock": 0,
                "promiseStock": 0,
                "averageCost": 0,
                "lastCost": 0,
                "maximumCost": 0,
                "createdAt": 1700000000,
            },
            {
                "productId": "p-noninv",
                "branchId": "b1",
                "currentStock": 0,
                "promiseStock": 0,
                "averageCost": 50,
                "lastCost": 50,
                "maximumCost": 50,
                "createdAt": 1700000000,
            },
        ]
    )
    product_account_col.bulk_substract_product_account_data = AsyncMock()
    prd_tx_col = MagicMock()
    prd_tx_col.create_many_product_transactions_with_session = AsyncMock()

    with patch(
        "kardex.core.invoice_register.process_invoice.fetch_product_types_and_price_factors_map",
        new=AsyncMock(
            return_value=(
                {
                    "p-item": "item",
                    "p-srv": "service",
                    "p-noninv": "nonInventory",
                },
                {},
            )
        ),
    ):
        await _prepare_and_execute_invoice_inventory(
            create_invoice=invoice,
            invoice_id="inv-1",
            session=None,
            product_account_col=product_account_col,
            prd_transaction_col=prd_tx_col,
            is_order_fulfillment=False,
        )

    # Solo p-item descuenta stock y escribe kárdex
    product_account_col.bulk_substract_product_account_data.assert_awaited_once()
    sub_kwargs = product_account_col.bulk_substract_product_account_data.call_args.kwargs
    assert sub_kwargs["bulk_to_substrack"] == [("p-item", 2)]

    prd_tx_col.create_many_product_transactions_with_session.assert_awaited_once()
    txs = prd_tx_col.create_many_product_transactions_with_session.call_args.args[0]
    assert len(txs) == 1
    assert txs[0]["productId"] == "p-item"

    # Costos: item=400 (x2=800), service=0 (x1=0), nonInventory=50 (x3=150) => totalCost=950
    assert invoice.saleItems[0].cost == 400
    assert invoice.saleItems[1].cost == 0
    assert invoice.saleItems[2].cost == 50
    assert invoice.totalCost == 950


@pytest.mark.asyncio
async def test_ensure_inventory_products_blocks_services_and_non_inventory():
    products_col = MagicMock()
    products_col.fetch_product_by_ids = AsyncMock(
        return_value=[{"id": "p-srv", "name": "Consulta", "productType": "service"}]
    )

    with patch.object(ProductsCollection, "get_instance", return_value=products_col):
        with pytest.raises(InvalidOperation, match="Consulta"):
            await ensure_inventory_products(["p-srv"], "entradas de inventario")


@pytest.mark.asyncio
async def test_cancel_order_only_releases_promise_stock_for_items():
    order = OrderInDb(
        id="ord1",
        branchId="b1",
        clientId="c1",
        clientInfo=_client(),
        docNumber="ORD-1",
        saleItems=[
            SaleItem(
                product=ProductItem(
                    id="p-item", name="Item", unitName="U", productType="item"
                ),
                quantity=4,
                cost=100,
                price=200,
                subTotal=800,
                total=800,
            ),
            SaleItem(
                product=ProductItem(
                    id="p-srv", name="Servicio", unitName="Srv", productType="service"
                ),
                quantity=1,
                cost=0,
                price=500,
                subTotal=500,
                total=500,
            ),
        ],
        status="open",
        paymentType="cash",
        totalCost=400,
        total=1300,
        createdBy=_user(),
        createdAt=1700000000,
    )

    order_col = MagicMock()
    order_col.update_order_status = AsyncMock(
        return_value={**order.model_dump(), "status": "cancelled"}
    )
    acc_col = MagicMock()
    acc_col.bulk_substract_from_promise_stock = AsyncMock()

    with (
        patch(
            "kardex.core.order_register.cancel_order.MongoService"
        ) as mock_mongo,
        patch(
            "kardex.core.order_register.cancel_order.OrdersCollection.get_instance",
            return_value=order_col,
        ),
        patch(
            "kardex.core.order_register.cancel_order.ProductAccountsCollection.get_instance",
            return_value=acc_col,
        ),
        patch(
            "kardex.core.order_register.cancel_order.fetch_product_types_map",
            new=AsyncMock(return_value={"p-item": "item", "p-srv": "service"}),
        ),
    ):
        mock_mongo.return_value.client = _fake_mongo_client()
        cancelled = await cancel_order(order)

    assert cancelled.status == "cancelled"
    acc_col.bulk_substract_from_promise_stock.assert_awaited_once()
    assert acc_col.bulk_substract_from_promise_stock.call_args.kwargs["bulk_data"] == [
        ("p-item", 4)
    ]


@pytest.mark.asyncio
async def test_approve_credit_note_skips_stock_return_for_service():
    cn = CreditNoteInDb(
        id="cn1",
        branchId="b1",
        clientId="c1",
        clientInfo=_client(),
        docNumber="NC-1",
        originalInvoiceId="inv1",
        originalInvoiceDocNumber="INV-1",
        type="devolution",
        status="emitted",
        returnedItems=[
            SaleItem(
                product=ProductItem(
                    id="p-srv", name="Consulta", unitName="Srv", productType="service"
                ),
                quantity=1,
                cost=0,
                price=1000,
                subTotal=1000,
                total=1000,
            )
        ],
        amount=1000,
        createdBy=_user(),
        createdAt=1700000000,
    )

    cn_col = MagicMock()
    cn_col.fetch_credit_note_by_id = AsyncMock(
        side_effect=[cn.model_dump(), {**cn.model_dump(), "status": "approved"}]
    )
    cn_col.update_credit_note_fields_by_id = AsyncMock()
    acc_col = MagicMock()
    acc_col.update_product_account_balance_data = AsyncMock()
    tx_col = MagicMock()
    tx_col.create_many_product_transactions_with_session = AsyncMock()

    with (
        patch(
            "kardex.core.credit_note_register.approve_credit_note.MongoService"
        ) as mock_mongo,
        patch(
            "kardex.core.credit_note_register.approve_credit_note.CreditNotesCollection.get_instance",
            return_value=cn_col,
        ),
        patch(
            "kardex.core.credit_note_register.approve_credit_note.ProductAccountsCollection.get_instance",
            return_value=acc_col,
        ),
        patch(
            "kardex.core.credit_note_register.approve_credit_note.ProductTransactionsCollection.get_instance",
            return_value=tx_col,
        ),
        patch(
            "kardex.core.credit_note_register.approve_credit_note.fetch_product_types_map",
            new=AsyncMock(return_value={"p-srv": "service"}),
        ),
    ):
        mock_mongo.return_value.client = _fake_mongo_client()
        approved = await approve_credit_note("cn1", _user())

    assert approved.status == "approved"
    acc_col.update_product_account_balance_data.assert_not_awaited()
    tx_col.create_many_product_transactions_with_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_product_account_reference_cost_update_allowed_for_service_only():
    KardexConfig().followTransaction = True
    ds = MagicMock(spec=ProductAccountsDataSource)
    ds.update_product_account_stock_and_cost = AsyncMock(
        return_value={
            "productId": "p-srv",
            "branchId": "b1",
            "currentStock": 0,
            "promiseStock": 0,
            "averageCost": 500,
            "lastCost": 500,
            "maximumCost": 500,
            "createdAt": 1700000000,
        }
    )
    repo = ProductAccountsRepository(ds)

    products_col = MagicMock()
    products_col.fetch_product_by_id = AsyncMock(
        side_effect=[
            {"id": "p-srv", "productType": "service"},
            {"id": "p-item", "productType": "item"},
        ]
    )

    with patch.object(ProductsCollection, "get_instance", return_value=products_col):
        updated = await repo.update_product_account_stock_and_cost(
            "p-srv", "b1", averageCost=500
        )
        assert updated is not None
        assert updated.averageCost == 500

        with pytest.raises(DirectStockAdjustmentBlocked):
            await repo.update_product_account_stock_and_cost(
                "p-item", "b1", averageCost=500
            )

@pytest.mark.asyncio
async def test_update_product_same_type_does_not_change_branch():
    existing = {
        "id": "p1",
        "name": "Consulta",
        "unitName": "Unidad",
        "brandName": "",
        "tags": [],
        "productType": "service",
        "branchId": "b1",
        "createdAt": 1700000000,
    }
    products_col = MagicMock()
    products_col.fetch_product_by_id = AsyncMock(return_value=existing)
    products_col.update_product_by_id = AsyncMock(
        return_value={**existing, "name": "Consulta actualizada"}
    )

    with patch.object(ProductsCollection, "get_instance", return_value=products_col):
        updated = await update_product_with_type_transition(
            "p1", UpdateProduct.model_validate({"name": "Consulta actualizada", "branchId": "b2"})
        )

    assert updated is not None
    payload = products_col.update_product_by_id.call_args.args[1]
    assert "branchId" not in payload


@pytest.mark.asyncio
async def test_reverse_credit_note_skips_stock_for_service():
    cn = CreditNoteInDb(
        id="cn1",
        branchId="b1",
        clientId="c1",
        clientInfo=_client(),
        docNumber="NC-1",
        originalInvoiceId="inv1",
        originalInvoiceDocNumber="INV-1",
        type="devolution",
        status="approved",
        returnedItems=[
            SaleItem(
                product=ProductItem(
                    id="p-srv", name="Consulta", unitName="Srv", productType="service"
                ),
                quantity=1,
                cost=0,
                price=1000,
                subTotal=1000,
                total=1000,
            )
        ],
        amount=1000,
        createdBy=_user(),
        createdAt=1700000000,
    )

    cn_col = MagicMock()
    cn_col.fetch_credit_note_by_id = AsyncMock(return_value=cn.model_dump())
    cn_col.delete_credit_note_by_id_with_session = AsyncMock()
    acc_col = MagicMock()
    acc_col.substract_product_account_data = AsyncMock()
    tx_col = MagicMock()
    tx_col.delete_transactions_by_document_id_with_session = AsyncMock()

    with (
        patch(
            "kardex.core.credit_note_register.reverse_credit_note.MongoService"
        ) as mock_mongo,
        patch(
            "kardex.core.credit_note_register.reverse_credit_note.CreditNotesCollection.get_instance",
            return_value=cn_col,
        ),
        patch(
            "kardex.core.credit_note_register.reverse_credit_note.ProductAccountsCollection.get_instance",
            return_value=acc_col,
        ),
        patch(
            "kardex.core.credit_note_register.reverse_credit_note.ProductTransactionsCollection.get_instance",
            return_value=tx_col,
        ),
        patch(
            "kardex.core.credit_note_register.reverse_credit_note.fetch_product_types_map",
            new=AsyncMock(return_value={"p-srv": "service"}),
        ),
    ):
        mock_mongo.return_value.client = _fake_mongo_client()
        reversed_cn = await reverse_credit_note("cn1")

    assert reversed_cn.id == "cn1"
    acc_col.substract_product_account_data.assert_not_awaited()
    cn_col.delete_credit_note_by_id_with_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_inventory_products_rejects_missing_products():
    products_col = MagicMock()
    products_col.fetch_product_by_ids = AsyncMock(return_value=[])

    with patch.object(ProductsCollection, "get_instance", return_value=products_col):
        with pytest.raises(InvalidOperation, match="PRODUCT_NOT_FOUND"):
            await ensure_inventory_products(["p-inexistente"])


@pytest.mark.asyncio
async def test_product_types_map_ignores_deleted_products():
    products_col = MagicMock()
    products_col.fetch_product_by_ids = AsyncMock(
        return_value=[
            {"id": "p-del", "productType": "service", "isDeleted": True},
        ]
    )

    with patch.object(ProductsCollection, "get_instance", return_value=products_col):
        types_map = await fetch_product_types_map(["p-del"])

    assert types_map == {}

    with patch.object(ProductsCollection, "get_instance", return_value=products_col):
        with pytest.raises(InvalidOperation, match="PRODUCT_NOT_FOUND"):
            await ensure_inventory_products(["p-del"])


def test_update_product_account_rejects_negative_values():
    with pytest.raises(ValidationError):
        UpdateProductAccount(averageCost=-1)

    with pytest.raises(ValidationError):
        UpdateProductAccount(currentStock=-5)


@pytest.mark.asyncio
async def test_incoming_transfer_blocks_services():
    transfer = TransferInDb(
        id="t1",
        origin="b1",
        originName="Sucursal A",
        destination="b2",
        destinationName="Sucursal B",
        docNumber="TR-1",
        status="inTransit",
        items=[
            TransferItem(
                id="p-srv",
                name="Consulta",
                unitName="Unidad",
                brandName="",
                quantity=1,
                cost=0,
            )
        ],
        createdBy=_user(),
        createdAt=1700000000,
    )

    transfers_col = MagicMock()
    transfers_col.fetch_transfer_by_id_with_session = AsyncMock(
        return_value=transfer.model_dump()
    )
    acc_col = MagicMock()
    acc_col.get_accounts_by_branch_id = AsyncMock()

    with (
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.MongoService"
        ) as mock_mongo,
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.TransfersCollection.get_instance",
            return_value=transfers_col,
        ),
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.ProductAccountsCollection.get_instance",
            return_value=acc_col,
        ),
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.ProductStatsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.ProductSaleProfilesCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.ProductTransactionsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.transfer_manager.process_incoming_transfer.BranchesTool"
        ),
        patch(
            "kardex.core.inventory.product_type_guard.ProductsCollection.get_instance",
            return_value=MagicMock(
                fetch_product_by_ids=AsyncMock(
                    return_value=[
                        {"id": "p-srv", "name": "Consulta", "productType": "service"}
                    ]
                )
            ),
        ),
    ):
        mock_mongo.return_value.client = _fake_mongo_client()

        with pytest.raises(InvalidOperation, match="Consulta"):
            await process_incoming_transfer(
                "t1", ReceiveTransferIntent(receivedAt=1700000000, receivedBy=_user())
            )

    acc_col.get_accounts_by_branch_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_product_with_data_requires_existing_branch():
    body = CreateProductWithData(
        createProduct=CreateProduct(
            name="Consulta",
            unitName="Unidad",
            tags=[],
            productType="service",
            branchId="sucursal-inexistente",
        ),
        branchId="sucursal-inexistente",
        inventoryInfo=InventoryInfo(quantity=0, cost=0, price=0),
    )

    with (
        patch(
            "kardex.core.product_register.process_create_product_with_data.MongoService"
        ) as mock_mongo,
        patch(
            "kardex.core.product_register.process_create_product_with_data.ProductsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.product_register.process_create_product_with_data.ProductAccountsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.product_register.process_create_product_with_data.ProductSaleProfilesCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.product_register.process_create_product_with_data.ProductTransactionsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.product_register.process_create_product_with_data.ProductStatsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.product_register.process_create_product_with_data.BranchesRepository"
        ) as mock_repo,
        patch(
            "kardex.core.product_register.product_type_lifecycle.BranchesTool"
        ) as mock_branches,
    ):
        mock_mongo.return_value.client = _fake_mongo_client()
        mock_repo.return_value.get_all_branches = AsyncMock(return_value=[])
        mock_branches.return_value.get_branch_by_id.return_value = None

        with pytest.raises(BranchNotFound):
            await process_create_product_with_data(body)
