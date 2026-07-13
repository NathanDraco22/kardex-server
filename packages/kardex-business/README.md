# kardex-business

Business logic and data access layer for the **Kardex Server** (FastAPI REST backend). A pure Python package (no FastAPI dependency) containing **35 repositories**, **19 core business modules**, **32 MongoDB collections**, and a complete toolset following strict **Onion (Clean) Architecture**.

---

## Table of Contents

1. [Requirements & Installation](#requirements--installation)
2. [Architecture Overview](#architecture-overview)
3. [How It Works](#how-it-works)
4. [Repository Catalog](#repository-catalog)
   - [Products & Inventory](#41-products--inventory)
   - [Entries & Exits](#42-entries--exits)
   - [Clients & Transactions](#43-clients--transactions)
   - [Orders, Invoices, Receipts & Returns](#44-orders-invoices-receipts--returns)
   - [Transfers](#45-transfers)
   - [Suppliers](#46-suppliers)
   - [Expenses](#47-expenses)
   - [Reports & Dashboard](#48-reports--dashboard)
   - [System & Utilities](#49-system--utilities)
   - [Authentication & Users](#410-authentication--users)
5. [Core Business Modules](#5-core-business-modules)
6. [MongoDB Collections](#6-mongodb-collections)
7. [Tools & Utilities](#7-tools--utilities)
8. [Filter Parameters](#8-filter-parameters)
9. [Common Models](#9-common-models)
10. [Exceptions](#10-exceptions)
11. [Usage Example](#11-usage-example)

---

## Requirements & Installation

- **Python**: `>=3.12`
- **Dependencies**: `pymongo>=4.17.0`, `argon2-cffi>=25.1.0`, `pyjwt>=2.12.1`, `pytz>=2026.2`

```toml
# pyproject.toml
[project]
name = "kardex-business"
version = "0.1.0"
description = "Business logic and data access layer for Kardex server"
requires-python = ">=3.12"
dependencies = [
    "argon2-cffi>=25.1.0",
    "pyjwt>=2.12.1",
    "pymongo>=4.17.0",
    "pytz>=2026.2",
]
```

The package has **no FastAPI dependency** — it is consumed by the `app/` layer where FastAPI routers and controllers live.

---

## Architecture Overview

The package follows a strict **Onion (Clean) Architecture** pattern. Data flows from the outside in, never the reverse:

```
┌─────────────────────────────────────────────────────────┐
│ Web Layer (FastAPI - app/)                              │
│  Router → Controller (thin orchestration)               │
├─────────────────────────────────────────────────────────┤
│ Domain Layer (kardex-business)                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Repositories (repos/v1/)                          │  │
│  │  → Business rules + Pydantic validation           │  │
│  │  → Singleton get_instance() pattern               │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ Data Sources (repos/v1/*/data/)                   │  │
│  │  → Delegates to MongoCollection                   │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ Core (core/)                                      │  │
│  │  → Complex cross-cutting business processes       │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ Infrastructure Layer                                    │
│  → MongoService (singleton, Motor/PyMongo)              │
│  → BaseMongoCollection → 32 Collection classes          │
│  → Tools (TimeTools, UuidTool, TokenManager, etc.)      │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns

| Pattern | Usage |
|---|---|
| **Singleton** | Every Repository, DataSource, and MongoCollection uses `get_instance()` classmethod |
| **Constructor Injection** | Repositories receive DataSources; DataSources receive Collections |
| **No DI Container** | All wiring is hardcoded — no framework dependency injection |
| **No ORM** | Raw PyMongo (Motor) with manual `dict` operations. Types validated at the Repository boundary via Pydantic |
| **MongoDB Transactions** | Multi-document operations use `start_session()` + `with_transaction()` |

### Key Architectural Rules

- **Package must NOT import FastAPI** or any web framework.
- **Business exceptions** inherit from `KardexException` (in `tools/kardex_exceptions.py`). Never raise `HTTPException` from within the package.
- **Currency/Money**: always `int` (cents).
- **Dates**: always `int` (Unix timestamps).
- **Pydantic model properties** use `camelCase`.
- **Entity naming**: always singular.

---

## How It Works

### Data Flow

```
Router (POST /products)
  → Controller.create_product()
    → ProductsRepository.get_instance().create_product(CreateProduct(...))
      → ProductsDataSource.get_instance().create_product(dict)
        → ProductsCollection.get_instance().create_product(dict)
          → self._collection.insert_one(dict)   # PyMongo/Motor
```

### Dependency Wiring

Every class uses the same pattern:

```python
class SomeRepository:
    _instance: "SomeRepository | None" = None

    def __init__(self, some_ds: SomeDataSource) -> None:
        self.some_ds = some_ds

    @classmethod
    def get_instance(cls) -> "SomeRepository":
        if cls._instance is None:
            cls._instance = cls(some_ds=SomeDataSource())
        return cls._instance
```

### MongoDB Connection

**MongoService** is the top-level singleton:

```python
class MongoService:
    def __init__(self) -> None:
        self._client = AsyncIOMotorClient(
            os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        )
        self._db_name = os.environ.get("DB_NAME", "LedgerDB")

    def get_collection(self, name: str) -> AsyncCollection:
        return self._client[self._db_name][name]
```

### Configuration

**`KardexConfig`** singleton with feature flags:

| Flag | Description |
|---|---|
| `followTransaction` | When True, direct stock adjustments raise `DirectStockAdjustmentBlocked` |
| `createFullProductProfile` | When True, product creation also creates accounts + sale profiles in all branches (MongoDB transaction) |
| `letInvoiceWithNegative` | Whether to allow invoices when stock goes negative |

**`KardexContext`**: `contextvars.ContextVar` providing per-request `businessNickname` and `branchId`.

### Initialization

On startup, `services_initializer.py` calls:

```python
await init_business_services()
# → MongoService().init_service()
# → create_indexes()  # Creates indexes on all 25+ collections
# → set_new_values()  # Initializes default values
```

---

## Repository Catalog

> **Legend**: `Full CRUD` All CRUD operations implemented | `Read-only` No create/update/delete | `△` Has streaming methods | `Σ` Has aggregation methods | `T` Transaction-aware | `⇢` Has TODO stubs (not yet implemented)

Each repository lives at `src/kardex/repos/v1/{entity}/` with the structure:
```
{entity}/
├── {entity}_repository.py
├── data/{entity}_datasource.py
├── models/{entity}_model.py
└── __init__.py
```

---

### 4.1 Products & Inventory

#### ProductsRepository `△`

**Purpose**: Central product catalog. Manages the full product lifecycle: creation (including full profile creation across all branches), paginated queries, keyword search with prefix generation, branch-scoped inventory queries, and async-streamed reads for large datasets.

**Models**: `ProductInDb`, `ProductInDbWithAccounts`, `ProductInDbInBranch`, `CreateProduct`, `UpdateProduct`

| Method | CRUD | Description |
|---|---|---|
| `create_product(product: CreateProduct) -> ProductInDb` | CREATE | Creates a product. When `createFullProductProfile` is enabled, creates product + accounts + sale profiles in a MongoDB transaction with auto-assigned code via `CounterManager`. |
| `get_all_products() -> list[ProductInDb]` | READ | Gets all products. |
| `get_all_products_with_accounts(branch_id, page, limit) -> list[ProductInDbWithAccounts]` | READ | Gets products with accounting data (aggregation). |
| `get_paginated_products(offset, limit) -> list[ProductInDb]` | READ | Offset/limit pagination. |
| `get_product_by_id(product_id: str) -> ProductInDb \| None` | READ | Gets a product by ID. |
| `get_product_by_code(product_code: str) -> ProductInDb \| None` | READ | Gets a product by its auto-assigned code. |
| `search_product_by_text(text_query: str) -> list[ProductInDb]` | SEARCH | Full-text search using word prefix generation. |
| `get_product_by_ids(product_ids: list[str]) -> list[ProductInDb]` | READ | Batch fetch by IDs. |
| `search_product_in_branch(branch_id, text_query) -> list[ProductInDbInBranch]` | SEARCH | Searches products within a specific branch (inventory data). |
| `get_products_in_branch_by_ids(branch_id, product_ids) -> list[ProductInDbInBranch]` | READ | Batch fetch by IDs within a branch. |
| `get_all_product_in_branch(params: ProductFilterParams) -> list[ProductInDbInBranch]` | READ | Gets all products in a branch with inventory/pricing data. |
| `get_all_product_in_branch_streamed(params) -> AsyncIterable[ProductInDbInBranch]` | READ `△` | Async generator for large inventory reads. |
| `get_product_in_branch_by_id(product_id, branch_id) -> ProductInDbInBranch \| None` | READ | Gets a product's branch-scoped data (stock, price, sale profile). |
| `update_product_by_id(product_id, product: UpdateProduct) -> ProductInDb \| None` | UPDATE | Updates a product's master data. |
| `delete_product_by_id(product_id: str) -> ProductInDb \| None` | DELETE | Soft-deletes a product. |

---

#### ProductCategoriesRepository

**Purpose**: Product categorization hierarchy. Full CRUD for organizing the catalog into categories for filtering and reporting.

**Models**: `ProductCategoryInDb`, `CreateProductCategory`, `UpdateProductCategory`

| Method | CRUD | Description |
|---|---|---|
| `create_product_category(cat: CreateProductCategory) -> ProductCategoryInDb` | CREATE | Creates a new category. |
| `get_all_product_categories() -> list[ProductCategoryInDb]` | READ | Gets all categories. |
| `get_product_category_by_id(category_id) -> ProductCategoryInDb \| None` | READ | Gets by ID. |
| `update_product_category_by_id(category_id, cat) -> ProductCategoryInDb \| None` | UPDATE | Updates a category. |
| `delete_product_category_by_id(category_id) -> ProductCategoryInDb \| None` | DELETE | Deletes a category. |

---

#### ProductPricesRepository

**Purpose**: Product sale price management. Defines and administers sale prices associated with products for price lists, sale profiles, and invoicing.

**Models**: `ProductPriceInDb`, `CreateProductPrice`, `UpdateProductPrice`

| Method | CRUD | Description |
|---|---|---|
| `create_product_price(price: CreateProductPrice) -> ProductPriceInDb` | CREATE | Creates a new product price. |
| `get_all_product_prices() -> list[ProductPriceInDb]` | READ | Gets all prices. |
| `get_product_price_by_id(price_id) -> ProductPriceInDb \| None` | READ | Gets by ID. |
| `update_product_price_by_id(price_id, price) -> ProductPriceInDb \| None` | UPDATE | Updates a price. |
| `delete_product_price_by_id(price_id) -> ProductPriceInDb \| None` | DELETE | Deletes a price. |

---

#### ProductStatsRepository `Σ`

**Purpose**: Product analytics and statistics. Provides performance data, inventory projections, and batch update capabilities for the product estimation engine.

**Models**: `ProductStatInDb`, `ProductStatInDbWithInfo`, `ProductStatInDbWithAccount`, `UpdateProductStatBatchItem`

| Method | CRUD | Description |
|---|---|---|
| `get_all_product_stats(params) -> list[ProductStatInDb]` | READ | Gets base statistics for all products. |
| `get_all_product_stats_with_info(params) -> list[ProductStatInDbWithInfo]` | READ | Gets statistics with sale/rotation info. |
| `get_all_product_stats_with_account(params) -> list[ProductStatInDbWithAccount]` | READ | Gets statistics with accounting data. |
| `get_product_stats_with_transaction() -> list[ProductStatInDb]` | READ | Gets stats that have pending transactions. |
| `get_product_stat_by_id(stat_id) -> ProductStatInDb \| None` | READ | Gets by ID. |
| `set_no_transaction_product_stats(last_estimation: int) -> None` | BATCH UPDATE | Marks stats as processed after estimation. |
| `update_product_batch(stats: list[UpdateProductStatBatchItem]) -> None` | BATCH UPDATE `Σ` | Bulk updates product statistics. |

---

#### ProductAccountsRepository

**Purpose**: Per-product inventory accounting (the Kardex ledger). Records stock additions and subtractions with average cost tracking. When `followTransaction` is enabled, direct stock adjustments are blocked in favor of transaction-based operations.

**Models**: `ProductAccountInDb`

| Method | CRUD | Description |
|---|---|---|
| `create_product_account(account: ProductAccountInDb) -> ProductAccountInDb` | CREATE | Creates a product account record. |
| `get_product_account_by_product_and_branch_id(product_id, branch_id) -> ProductAccountInDb \| None` | READ | Gets account data for a product in a branch. |
| `update_product_account_stock_and_cost(product_id, branch_id, **kwargs) -> ProductAccountInDb \| None` | UPDATE | Updates stock and average cost. |
| `add_product_account_stock(product_id, branch_id, **kwargs) -> ProductAccountInDb \| None` | SPECIAL | Increases stock (entry operation). |
| `substract_product_account_stock(product_id, branch_id, **kwargs) -> ProductAccountInDb \| None` | SPECIAL | Decreases stock (exit operation). |
| `get_product_accounts_by_product(product_id) -> list[ProductAccountInDb]` | READ | Gets full accounting history for a product. |

---

#### ProductSaleProfilesRepository

**Purpose**: Per-branch product sale configuration. Defines how a product is sold at each branch (visibility, branch-specific settings). Joins product data into the response.

**Models**: `ProductSaleProfileInDb`, `ProductSaleProfileInDbWithProduct`, `UpdateProductSaleProfile`

| Method | CRUD | Description |
|---|---|---|
| `get_all_product_sale_profiles(branch_id) -> list[ProductSaleProfileInDbWithProduct]` | READ | Gets all sale profiles for a branch with joined product data. |
| `update_product_sale_profile_by_id(product_id, branch_id, profile) -> ProductSaleProfileInDb \| None` | UPDATE | Updates a profile. |
| `delete_product_sale_profile_by_id(profile_id) -> ProductSaleProfileInDb \| None` | DELETE | Deletes a profile. |

---

#### ProductTransactionsRepository `Σ`

**Purpose**: Product transaction history. Read-only log of all inventory movements. Also provides the `estimate_product_stats` method for the estimation engine.

**Models**: `ProductTransactionInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_all_product_transactions(params: ProductTransactionFilterParams) -> list[ProductTransactionInDb]` | READ | Gets paginated transaction history. |
| `get_product_transaction_by_id(transaction_id) -> ProductTransactionInDb \| None` | READ | Gets by ID. |
| `estimate_product_stats(**kwargs)` | SPECIAL `Σ` | Triggers aggregation-based estimation of product statistics. |

---

#### UnitsRepository

**Purpose**: Units of measure (unit, box, kg, liter, etc.). Full CRUD for inventory measurement units.

**Models**: `UnitInDb`, `CreateUnit`, `UpdateUnit`

| Method | CRUD | Description |
|---|---|---|
| `create_unit(unit: CreateUnit) -> UnitInDb` | CREATE | Creates a new unit. |
| `get_all_units() -> list[UnitInDb]` | READ | Gets all units. |
| `get_unit_by_id(unit_id) -> UnitInDb \| None` | READ | Gets by ID. |
| `update_unit_by_id(unit_id, unit) -> UnitInDb \| None` | UPDATE | Updates a unit. |
| `delete_unit_by_id(unit_id) -> UnitInDb \| None` | DELETE | Deletes a unit. |

---

#### InventoriesRepository `△`

**Purpose**: Current inventory status. Read-only, streaming-only repository that yields inventory items via async generator for a given branch. Also provides total stock aggregation.

**Models**: `InventoryInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_all_inventories_by_branch(branch_id) -> AsyncGenerator[InventoryInDb, None]` | READ `△` | Async-generator-based streaming read of all inventory for a branch. |
| `get_total_current_stock(branch_id) -> int` | READ `Σ` | Returns the summed total stock for a branch. |

---

### 4.2 Entries & Exits

#### EntryDocsRepository

**Purpose**: Goods entry documents (supplier purchases, incoming returns). Read-only data layer for entry documents and their history. Entry docs are **created** by the `core/inventory/` business module.

**Models**: `EntryDocInDb`, `EntryHistoryInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_all_entry_docs() -> list[EntryDocInDb]` | READ | Gets all entry documents. |
| `get_paginated_entry_docs(params: EntryDocFilterParams) -> list[EntryDocInDb]` | READ | Paginated entry docs. |
| `get_entry_doc_by_id(doc_id) -> EntryDocInDb \| None` | READ | Gets by ID. |
| `get_entry_doc_by_doc_number(doc_number) -> EntryDocInDb \| None` | READ | Gets by document number. |
| `get_entry_doc_by_doc_number_and_supplier(supplier_id, doc_number) -> EntryDocInDb \| None` | READ | Gets by supplier + document number. |
| `get_entry_history(params: EntryDocFilterParams) -> list[EntryHistoryInDb]` | HISTORY | Gets entry history (line-item level). |
| `get_entry_history_by_id_with_supplier(doc_id) -> EntryHistoryInDb \| None` | HISTORY | Gets history line with supplier info. |
| `get_entry_history_by_doc_number_and_branch_id(doc_number, branch_id) -> EntryHistoryInDb \| None` | HISTORY | Gets history line by document and branch. |

---

#### EntryHistoriesRepository

**Purpose**: Detailed entry history (line-item level). Read-only repository exposing each individual product entry: what product, quantity, cost, date, and supplier.

**Models**: `EntryHistoryInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_entry_history(params: EntryHistoryFilterParams) -> list[EntryHistoryInDb]` | READ | Gets entry history lines with filters. |
| `get_entry_history_by_id_with_supplier(doc_id) -> EntryHistoryInDb \| None` | READ | Gets a history line with supplier info. |
| `get_entry_docs_by_product_id(product_id) -> list[EntryHistoryInDb]` | READ | Gets all entry history for a specific product. |
| `get_entry_history_by_doc_number_and_branch_id(doc_number, branch_id) -> EntryHistoryInDb \| None` | READ | Gets by document number and branch. |

---

#### ExitDocsRepository

**Purpose**: Goods exit documents (customer sales, negative adjustments). Read-only data layer. Exit docs are **created** by `core/inventory/` and `core/invoice_register/`.

**Models**: `ExitDocInDb`, `ExitHistoryInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_all_exit_docs() -> list[ExitDocInDb]` | READ | Gets all exit documents. |
| `get_paginated_exit_docs(params: ExitDocFilterParams) -> list[ExitDocInDb]` | READ | Paginated exit docs. |
| `get_exit_doc_by_id(doc_id) -> ExitDocInDb \| None` | READ | Gets by ID. |
| `get_exit_doc_by_doc_number(doc_number) -> ExitDocInDb \| None` | READ | Gets by document number. |
| `get_exit_doc_by_doc_number_and_client(client_id, doc_number) -> ExitDocInDb \| None` | READ | Gets by client + document number. |
| `get_exit_history(params: ExitDocFilterParams) -> list[ExitHistoryInDb]` | HISTORY | Gets exit history (line-item level). |
| `get_exit_history_by_id_with_client(doc_id) -> ExitHistoryInDb \| None` | HISTORY | Gets history line with client info. |
| `get_exit_history_by_doc_number_and_branch_id(doc_number, branch_id) -> ExitHistoryInDb \| None` | HISTORY | Gets by document and branch. |

---

#### ExitHistoriesRepository

**Purpose**: Detailed exit history (line-item level). Read-only repository exposing each product exit: product, quantity, sale price, date, and associated client.

**Models**: `ExitHistoryInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_exit_history(params: ExitHistoryFilterParams) -> list[ExitHistoryInDb]` | READ | Gets exit history lines with filters. |
| `get_exit_doc_history_by_id_with_client(doc_id) -> ExitHistoryInDb \| None` | READ | Gets a history line with client info. |
| `get_exit_history_by_doc_number_and_branch_id(doc_number, branch_id) -> ExitHistoryInDb \| None` | READ | Gets by document number and branch. |

---

#### AdjustEntriesRepository `⇢`

**Purpose**: Inventory entry adjustments (manual stock increases). Partial implementation — create is handled by `core/adjust_ledger/`. Update has a TODO stub.

**Models**: `AdjustEntryInDb`, `UpdateAdjustEntry`

| Method | CRUD | Description |
|---|---|---|
| `get_all_adjust_entries(params: AdjustFilterParams) -> list[AdjustEntryInDb]` | READ | Gets all entry adjustments with filters. |
| `get_adjust_entry_by_id(entry_id) -> AdjustEntryInDb \| None` | READ | Gets by ID. |
| `get_adjust_entry_by_doc_number(doc_number, branch_id) -> AdjustEntryInDb \| None` | READ | Gets by document number and branch. |
| `update_adjust_entry_by_id(entry_id, entry) -> AdjustEntryInDb \| None` `⇢` | UPDATE | TODO stub (`NotImplementedError`). |
| `delete_adjust_entry_by_id(entry_id) -> AdjustEntryInDb \| None` | DELETE | Deletes an adjustment. |

---

#### AdjustExitsRepository `⇢`

**Purpose**: Inventory exit adjustments (manual stock decreases). Partial implementation — create and update are stubs.

**Models**: `AdjustExitInDb`, `CreateAdjustExit`, `UpdateAdjustExit`

| Method | CRUD | Description |
|---|---|---|
| `create_adjust_exit(exit: CreateAdjustExit) -> AdjustExitInDb` `⇢` | CREATE | TODO stub. |
| `get_all_adjust_exits(params: AdjustFilterParams) -> list[AdjustExitInDb]` | READ | Gets all exit adjustments with filters. |
| `get_adjust_exit_by_id(exit_id) -> AdjustExitInDb \| None` | READ | Gets by ID. |
| `get_adjust_exit_by_doc_number(doc_number, branch_id) -> AdjustExitInDb \| None` | READ | Gets by document number and branch. |
| `update_adjust_exit_by_id(exit_id, exit) -> AdjustExitInDb \| None` `⇢` | UPDATE | TODO stub. |
| `delete_adjust_exit_by_id(exit_id) -> AdjustExitInDb \| None` | DELETE | Deletes an adjustment. |

---

### 4.3 Clients & Transactions

#### ClientsRepository `T`

**Purpose**: Client management. Full CRUD with auto-assigned client number, text search with prefix generation, soft delete, group renaming, and financial operations (initial balance creation). Balance operations delegate to `core/client/process_create_client.py` which runs **MongoDB transactions**.

**Models**: `ClientInDb`, `CreateClient`, `UpdateClient`

| Method | CRUD | Description |
|---|---|---|
| `create_client(client: CreateClient) -> ClientInDb` | CREATE | Creates a client with auto-assigned number from `CounterManager`. |
| `create_initial_balance(client, initial_balance, branch_id, product_name) -> ClientInDb` | SPECIAL `T` | Creates initial financial balance for a client (MongoDB transaction). |
| `create_multiple_initial_balance(balances: list[InitialBalanceClient]) -> list[ClientInDb]` | BATCH `T` | Batch initial balance for multiple clients. |
| `get_all_clients(params: ClientFilterParams) -> list[ClientInDb]` | READ | Gets all clients with pagination/filters. |
| `get_all_clients_with_balance(params: ClientFilterParams) -> list[ClientInDb]` | READ | Gets clients with their current financial balance. |
| `get_client_by_id(client_id) -> ClientInDb \| None` | READ | Gets by ID. |
| `get_client_by_card_id(card_id) -> ClientInDb \| None` | READ | Gets by loyalty card ID. |
| `search_client_by_text(text_query) -> list[ClientInDb]` | SEARCH | Full-text search with prefix generation. |
| `search_clients_with_balance(text_query) -> list[ClientInDb]` | SEARCH | Searches clients and includes financial balance. |
| `update_client_by_id(client_id, client) -> ClientInDb \| None` | UPDATE | Updates a client. |
| `update_group(old_group, new_group) -> None` | SPECIAL | Renames a client group across all clients. |
| `delete_client_by_id(client_id) -> ClientInDb \| None` | DELETE | Soft deletes a client. |

---

#### ClientGroupsRepository

**Purpose**: Client grouping/segmentation. Full CRUD for organizing clients into categories (Wholesale, Retail, VIP, etc.).

**Models**: `ClientGroupInDb`, `CreateClientGroup`, `UpdateClientGroup`

| Method | CRUD | Description |
|---|---|---|
| `create_client_group(group: CreateClientGroup) -> ClientGroupInDb` | CREATE | Creates a new group. |
| `get_all_client_groups() -> list[ClientGroupInDb]` | READ | Gets all groups. |
| `get_client_group_by_id(group_id) -> ClientGroupInDb \| None` | READ | Gets by ID. |
| `update_client_group_by_id(group_id, group) -> ClientGroupInDb \| None` | UPDATE | Updates a group. |
| `delete_client_group_by_id(group_id) -> ClientGroupInDb \| None` | DELETE | Deletes a group. |

---

#### ClientTransactionsRepository

**Purpose**: Client transaction history. Read-only log of all client accounting movements (credits, debits, payments, balance adjustments). Transactions are **created** by the `core/finance/` engine.

**Models**: `ClientTransactionInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_all_client_transactions(params: ClientTransactionFilterParams) -> list[ClientTransactionInDb]` | READ | Gets paginated client transactions. |
| `get_client_transaction_by_id(transaction_id) -> ClientTransactionInDb \| None` | READ | Gets by ID. |

---

### 4.4 Orders, Invoices, Receipts & Returns

#### OrdersRepository `Σ`

**Purpose**: Sales order lifecycle. Orders are created as drafts, can be updated, and later **converted to invoices** by the `core/order_register/` module. Provides product-level aggregation and demand-vs-stock analysis.

**Models**: `OrderInDb`, `CreateOrder`, `UpdateOrder`, `ProductSalesTotal`, `ProductStockDemand`

| Method | CRUD | Description |
|---|---|---|
| `create_draft_order(order: CreateOrder) -> OrderInDb` | CREATE | Creates a new draft order with auto-assigned number. |
| `get_paginated_orders(params: OrderFilterParams) -> list[OrderInDb]` | READ | Gets paginated orders with status/date filters. |
| `get_products_in_orders(params: OrderFilterParams) -> list[ProductSalesTotal]` | READ `Σ` | Aggregated product data from orders (quantities, totals). |
| `get_demand_vs_stock(params: OrderFilterParams) -> list[ProductStockDemand]` | READ `Σ` | Compares current stock vs pending order demand. |
| `get_order_by_id(order_id) -> OrderInDb \| None` | READ | Gets by ID. |
| `get_order_by_doc_number(doc_number) -> OrderInDb \| None` | READ | Gets by document number. |
| `update_order_draft_by_id(order_id, order) -> OrderInDb \| None` | UPDATE | Updates a draft order. |
| `delete_order_draft_by_id(order_id) -> OrderInDb \| None` | DELETE | Deletes a draft order. |

---

#### InvoicesRepository `Σ` `△` `⇢`

**Purpose**: Invoicing data layer. The richest repository with aggregation, streaming, totals, payment-type breakdowns, product-level sales, history, portfolio summaries, and branch-level pending invoice reports. **Create** is handled by `core/invoice_register/`. `update_invoice_by_id` is a TODO stub.

**Models**: `InvoiceInDb`, `CreateInvoice`, `UpdateInvoice`, `InvoiceTotals`, `BranchPortfolioSummary`, `PendingInvoiceTotalsByBranch`, `ProductSalesTotal`

| Method | CRUD | Description |
|---|---|---|
| `get_all_invoices(params: InvoiceFilterParams) -> list[InvoiceInDb]` | READ | Gets invoices with pagination and filters. |
| `get_all_invoices_by_product(product_id, params) -> list[InvoiceInDb]` | READ | Gets invoices containing a specific product. |
| `get_all_product_sales(params: InvoiceFilterParams) -> list[ProductSalesTotal]` | READ `Σ` | Aggregated product sales from invoices. |
| `get_all_invoices_stream(params: InvoiceFilterParams) -> AsyncGenerator[InvoiceInDb, None]` | READ `△` | Streams invoices via async generator. |
| `get_totals_from_invoices(params: InvoiceFilterParams) -> InvoiceTotals` | READ `Σ` | Aggregated invoice totals (amount, tax, discounts). |
| `get_totals_invoices_by_payment_type(params: TotalsFilterParams) -> list[InvoiceTotals]` | READ `Σ` | Totals broken down by payment type. |
| `get_invoice_by_id(invoice_id) -> InvoiceInDb \| None` | READ | Gets by ID. |
| `get_invoice_by_doc_number(doc_number) -> InvoiceInDb \| None` | READ | Gets by document number. |
| `get_invoice_by(client_id, offset, limit) -> list[InvoiceInDb]` | READ | Gets invoices for a specific client. |
| `get_pending_to_paid_invoices(client_id) -> list[InvoiceInDb]` | READ | Gets pending payment invoices for a client. |
| `update_invoice_by_id(invoice_id, invoice) -> InvoiceInDb \| None` `⇢` | UPDATE | TODO stub. |
| `get_invoice_history(params: HistoryClientParams) -> list[InvoiceInDb]` | HISTORY | Gets invoice history. |
| `get_invoice_summary(**kwargs) -> list[BranchPortfolioSummary]` | READ `Σ` | Portfolio summary by branch. |
| `get_pending_invoice_totals_by_branch(**kwargs) -> list[PendingInvoiceTotalsByBranch]` | READ `Σ` | Pending invoice totals grouped by branch. |

---

#### ReceiptsRepository `Σ` `⇢`

**Purpose**: Payment receipt data layer. Manages receipt queries, totals aggregation by payment method, history, and branch-level applied amounts summaries. **Create** is handled by `core/receipt_register/`. Create/update are TODO stubs.

**Models**: `ReceiptInDb`, `CreateReceipt`, `UpdateReceipt`, `ReceiptTotal`, `BranchAppliedReceiptsAmountsSummary`

| Method | CRUD | Description |
|---|---|---|
| `create_receipt(receipt: CreateReceipt) -> ReceiptInDb` `⇢` | CREATE | TODO stub. |
| `get_all_receipts(params: ReceiptFilterParams) -> list[ReceiptInDb]` | READ | Gets paginated receipts. |
| `get_receipts_by_invoice_id(invoice_id) -> list[ReceiptInDb]` | READ | Gets receipts for an invoice. |
| `get_totals_from_receipts(params: ReceiptFilterParams) -> ReceiptTotal` | READ `Σ` | Aggregated receipt totals. |
| `get_totals_from_receipts_by_payment_method(params: TotalsFilterParams) -> list[ReceiptTotal]` | READ `Σ` | Totals broken down by payment method. |
| `get_receipt_by_id(receipt_id) -> ReceiptInDb \| None` | READ | Gets by ID. |
| `get_receipt_by_doc_number(doc_number) -> ReceiptInDb \| None` | READ | Gets by document number. |
| `update_receipt_by_id(receipt_id, receipt) -> ReceiptInDb \| None` `⇢` | UPDATE | TODO stub. |
| `delete_receipt_by_id(receipt_id) -> ReceiptInDb \| None` | DELETE | Deletes a receipt. |
| `get_receipt_history(params: HistoryClientParams) -> list[ReceiptInDb]` | HISTORY | Gets receipt history. |
| `get_branch_receipt_amounts_summary(**kwargs) -> list[BranchAppliedReceiptsAmountsSummary]` | READ `Σ` | Applied amounts summary by branch. |

---

#### DevolutionsRepository

**Purpose**: Product returns (devolutions). Full CRUD with auto-assigned document number. Supports queries for active returns (pending confirmation) and history tracking.

**Models**: `DevolutionInDb`, `CreateDevolution`, `UpdateDevolution`

| Method | CRUD | Description |
|---|---|---|
| `create_devolution(devolution: CreateDevolution) -> DevolutionInDb` | CREATE | Creates a new return with auto-assigned doc number. |
| `get_all_devolutions(params: DevolutionFilterParams) -> list[DevolutionInDb]` | READ | Gets all returns with filters. |
| `get_all_active_devolutions(params: DevolutionFilterParams) -> list[DevolutionInDb]` | READ | Gets active (unconfirmed) returns. |
| `get_devolution_by_id(devolution_id) -> DevolutionInDb \| None` | READ | Gets by ID. |
| `get_devolution_by_invoice_id(invoice_id, client_id) -> list[DevolutionInDb]` | READ | Gets returns for an invoice. |
| `get_devolution_by_doc_number(doc_number) -> DevolutionInDb \| None` | READ | Gets by document number. |
| `update_devolution_by_id(devolution_id, devolution) -> DevolutionInDb \| None` | UPDATE | Updates a return. |
| `delete_devolution_by_id(devolution_id) -> DevolutionInDb \| None` | DELETE | Deletes a return. |
| `get_devolution_history(params: HistoryClientParams) -> list[DevolutionInDb]` | HISTORY | Gets return history. |

---

### 4.5 Transfers

#### TransfersRepository

**Purpose**: Inter-branch stock transfers. **Read-only** repository. Transfers are created and managed by `core/transfer_manager/` which handles the full state machine (create, receive, cancel).

**Models**: `TransferInDb`

| Method | CRUD | Description |
|---|---|---|
| `get_all_transfers(params: TransferFilterParams) -> list[TransferInDb]` | READ | Gets all transfers with filters. |
| `get_transfer_by_id(transfer_id) -> TransferInDb \| None` | READ | Gets by ID. |
| `get_transfer_by_doc_number(doc_number) -> TransferInDb \| None` | READ | Gets by document number. |

---

### 4.6 Suppliers

#### SuppliersRepository

**Purpose**: Supplier management. Full CRUD with auto-assigned number, text search with prefix generation, and soft delete.

**Models**: `SupplierInDb`, `CreateSupplier`, `UpdateSupplier`

| Method | CRUD | Description |
|---|---|---|
| `create_supplier(supplier: CreateSupplier) -> SupplierInDb` | CREATE | Creates a supplier with auto-assigned number. |
| `get_all_suppliers() -> list[SupplierInDb]` | READ | Gets all suppliers. |
| `get_supplier_by_id(supplier_id) -> SupplierInDb \| None` | READ | Gets by ID. |
| `search_supplier_by_text(text_query) -> list[SupplierInDb]` | SEARCH | Full-text search with prefix generation. |
| `update_supplier_by_id(supplier_id, supplier) -> SupplierInDb \| None` | UPDATE | Updates a supplier. |
| `delete_supplier_by_id(supplier_id) -> SupplierInDb \| None` | DELETE | Soft deletes a supplier. |

---

### 4.7 Expenses

#### ExpensesRepository `Σ`

**Purpose**: Operating expense registry. Full CRUD with auto-assigned number, document number lookup, partial payment tracking (`add_to_amount_paid`), and summary aggregation by date range.

**Models**: `ExpenseInDb`, `CreateExpense`, `UpdateExpense`

| Method | CRUD | Description |
|---|---|---|
| `create_expense(expense: CreateExpense) -> ExpenseInDb` | CREATE | Creates an expense with auto-assigned number. |
| `get_all_expenses(params: ExpensesFilterParams) -> list[ExpenseInDb]` | READ | Gets all expenses with filters. |
| `get_expense_by_id(expense_id) -> ExpenseInDb \| None` | READ | Gets by ID. |
| `get_expense_by_doc_number(doc_number) -> ExpenseInDb \| None` | READ | Gets by document number. |
| `update_expense_by_id(expense_id, expense) -> ExpenseInDb \| None` | UPDATE | Updates an expense. |
| `delete_expense_by_id(expense_id) -> ExpenseInDb \| None` | DELETE | Deletes an expense. |
| `add_to_amount_paid(expense_id, amount_paid) -> ExpenseInDb \| None` | SPECIAL | Records a partial payment toward an expense. |
| `get_expenses_summary_in_range(start_date, end_date) -> dict[str, Any]` | READ `Σ` | Aggregated expense summary by date range. |

---

#### ExpenseCategoriesRepository

**Purpose**: Expense categorization. Full CRUD for classifying expenses into accounting categories.

**Models**: `ExpenseCategoryInDb`, `CreateExpenseCategory`, `UpdateExpenseCategory`

| Method | CRUD | Description |
|---|---|---|
| `create_expense_category(cat: CreateExpenseCategory) -> ExpenseCategoryInDb` | CREATE | Creates a new category. |
| `get_all_expense_categories() -> list[ExpenseCategoryInDb]` | READ | Gets all categories. |
| `get_expense_category_by_id(category_id) -> ExpenseCategoryInDb \| None` | READ | Gets by ID. |
| `update_expense_category_by_id(category_id, cat) -> ExpenseCategoryInDb \| None` | UPDATE | Updates a category. |
| `delete_expense_category_by_id(category_id) -> ExpenseCategoryInDb \| None` | DELETE | Deletes a category. |

---

### 4.8 Reports & Dashboard

#### DailySummariesRepository

**Purpose**: Daily operations summaries. Historical day-by-day consolidated view of business activity. Read/create only — summaries are generated by core modules.

**Models**: `DailySummaryInDb`, `CreateDailySummary`

| Method | CRUD | Description |
|---|---|---|
| `create_daily_summary(summary: CreateDailySummary) -> DailySummaryInDb` | CREATE | Creates a daily summary snapshot. |
| `get_all_daily_summaries(params: DailySummaryFilterParams) -> list[DailySummaryInDb]` | READ | Gets summaries with filters. |
| `get_daily_summary_by_start_date_range(startDate, endDate) -> list[DailySummaryInDb]` | READ | Gets summaries within a date range. |
| `get_daily_summary_by_id(summary_id) -> DailySummaryInDb \| None` | READ | Gets by ID. |
| `get_daily_summary_by_date_id(date_id) -> DailySummaryInDb \| None` | READ | Gets by date ID. |

---

#### ExecutiveSummariesRepository

**Purpose**: Executive summaries. Management-level aggregated data for strategic decision-making. Supports type-based filtering (daily, weekly, monthly).

**Models**: `ExecutiveSummaryInDb`, `CreateExecutiveSummary`, `SummaryType`

| Method | CRUD | Description |
|---|---|---|
| `create_executive_summary(summary: CreateExecutiveSummary) -> ExecutiveSummaryInDb` | CREATE | Creates an executive summary. |
| `get_all_executive_summaries(params: ExecutiveSummaryFilterParams) -> list[ExecutiveSummaryInDb]` | READ | Gets summaries with type and date filters. |
| `get_executive_summary_by_id(summary_id) -> ExecutiveSummaryInDb \| None` | READ | Gets by ID. |
| `get_executive_summary_by_date_id_and_type(date_id, type: SummaryType) -> ExecutiveSummaryInDb \| None` | READ | Gets by date ID and summary type. |

---

### 4.9 System & Utilities

#### BranchesRepository

**Purpose**: Branch (location) management. Full CRUD with ETag-based cache invalidation for branch-dependent data.

**Models**: `BranchInDb`, `CreateBranch`, `UpdateBranch`

| Method | CRUD | Description |
|---|---|---|
| `create_branch(branch: CreateBranch) -> BranchInDb` | CREATE | Creates a new branch. Invalidates branch ETags. |
| `get_all_branches() -> list[BranchInDb]` | READ | Gets all branches. |
| `get_all_commerce_branches() -> list[BranchInDb]` | READ | Gets commerce-type branches only. |
| `get_branch_by_id(branch_id) -> BranchInDb \| None` | READ | Gets by ID. |
| `update_branch_by_id(branch_id, branch) -> BranchInDb \| None` | UPDATE | Updates a branch. Invalidates ETags. |
| `delete_branch_by_id(branch_id) -> BranchInDb \| None` | DELETE | Hard deletes a branch. |

---

#### IntegrationsRepository

**Purpose**: External integrations configuration (Telegram, notifications, etc.). Uses upsert-on-create to avoid duplicates. No delete in standard CRUD sense.

**Models**: `IntegrationInDb`, `CreateIntegration`, `UpdateIntegration`

| Method | CRUD | Description |
|---|---|---|
| `create_integration_if_absent(integration: CreateIntegration) -> IntegrationInDb` | UPSERT | Creates only if not present, otherwise returns existing. |
| `get_all_integrations() -> list[IntegrationInDb]` | READ | Gets all integrations. |
| `get_integration_by_id(integration_id) -> IntegrationInDb \| None` | READ | Gets by ID. |
| `update_integration_by_id(integration_id, integration) -> IntegrationInDb \| None` | UPDATE | Updates configuration. |
| `delete_integration_by_id(integration_id) -> IntegrationInDb \| None` | DELETE | Deletes an integration. |

---

#### ExpirationLogsRepository `Σ`

**Purpose**: Product expiration tracking. Manages expiration alerts, batch creation, and proximity checks (`has_near_expiration_date`). Useful for perishable inventory.

**Models**: `ExpirationLogInDb`, `CreateExpirationLog`, `UpdateExpirationLog`

| Method | CRUD | Description |
|---|---|---|
| `create_expiration_log(log: CreateExpirationLog) -> ExpirationLogInDb` | CREATE | Creates a single expiration alert. |
| `create_many_expiration_logs(logs: list[CreateExpirationLog])` | BATCH CREATE | Creates multiple alerts at once. |
| `get_all_expiration_logs(params: ExpirationLogFilterParams) -> list[ExpirationLogInDb]` | READ | Gets all alerts with filters. |
| `get_expiration_log_by_id(log_id) -> ExpirationLogInDb \| None` | READ | Gets by ID. |
| `update_expiration_log_by_id(log_id, log) -> ExpirationLogInDb \| None` `⇢` | UPDATE | TODO stub. |
| `delete_expiration_log_by_id(log_id) -> ExpirationLogInDb \| None` | DELETE | Deletes an alert. |
| `has_near_expiration_date(target_date, branch_id) -> bool` | SPECIAL `Σ` | Checks if any products are near expiration for a branch. |

---

#### CountersRepository `T`

**Purpose**: Atomic counter management for document numbering. Provides **transaction-safe** increment and set operations. Used by `CounterManager` to generate sequential numbers for invoices, receipts, orders, returns, products, users, clients, transfers, suppliers, adjustments, and expenses.

**Models**: `CounterInDb`

| Method | CRUD | Description |
|---|---|---|
| `increment_counter(counter_name, session: Any) -> CounterInDb` | ATOMIC INC `T` | Atomically increments a counter within a MongoDB session. |
| `set_counter(counter_name, value: int, session: Any) -> CounterInDb` | SET `T` | Sets a counter to a specific value within a session. |

---

#### CoreSettingsRepository

**Purpose**: Core system settings and licensing. Manages application configuration values. Includes EdDSA token verification during creation for security.

**Models**: `CoreSettingInDb`, `CreateCoreSetting`, `DecodedCoreSetting`, `UpdateCoreSetting`

| Method | CRUD | Description |
|---|---|---|
| `create_core_setting(setting: CreateCoreSetting) -> DecodedCoreSetting \| None` | CREATE | Creates a setting with super token verification. |
| `get_all_core_settings() -> list[CoreSettingInDb]` | READ | Gets all settings. |
| `get_core_setting_by_id(setting_id) -> CoreSettingInDb \| None` | READ | Gets by ID. |
| `update_core_setting_by_nickname(setting_id, setting) -> CoreSettingInDb \| None` | UPDATE | Updates a setting by its nickname identifier. |
| `delete_core_setting_by_id(setting_id) -> CoreSettingInDb \| None` | DELETE | Deletes a setting. |

---

### 4.10 Authentication & Users

#### UsersRepository

**Purpose**: System user administration. Full user lifecycle with password hashing (argon2 via `SysPasswordHasher`), branch-scoped active user queries, auto-assigned user number, and inactive user tracking.

**Models**: `UserInDb`, `UserInDbWithRole`, `CreateUser`, `UpdateUser`

| Method | CRUD | Description |
|---|---|---|
| `create_user_directly(new_user: UserInDb) -> UserInDb` | CREATE | Creates a user from a pre-built `UserInDb` object (raw insert). |
| `create_user(user: CreateUser) -> UserInDb` | CREATE | Creates a user with password hashing and auto-assigned number. |
| `get_all_users() -> list[UserInDbWithRole]` | READ | Gets all users with their role data joined. |
| `get_all_active_users_by_branch_id(branch_id) -> list[UserInDbWithRole]` | READ | Gets active users filtered by branch. |
| `get_all_inactive_users() -> list[UserInDb]` | READ | Gets all inactive users (cached for auth checks). |
| `get_user_by_id(user_id) -> UserInDbWithRole \| None` | READ | Gets a user with role by ID. |
| `update_user_by_id(user_id, user) -> UserInDb \| None` | UPDATE | Updates a user. |
| `change_password(user_id, password) -> UserInDb \| None` | SPECIAL | Hashes and updates a user's password. |
| `delete_user_by_id(user_id) -> UserInDb \| None` | DELETE | Deletes a user. |

---

#### UserRolesRepository

**Purpose**: Role-based access control. Full CRUD for defining permission levels assigned to users.

**Models**: `UserRoleInDb`, `CreateUserRole`, `UpdateUserRole`

| Method | CRUD | Description |
|---|---|---|
| `create_user_role(role: CreateUserRole) -> UserRoleInDb` | CREATE | Creates a new role. |
| `get_all_user_roles() -> list[UserRoleInDb]` | READ | Gets all roles. |
| `get_user_role_by_id(role_id) -> UserRoleInDb \| None` | READ | Gets by ID. |
| `update_user_role_by_id(role_id, role) -> UserRoleInDb \| None` | UPDATE | Updates a role. |
| `delete_user_role_by_id(role_id) -> UserRoleInDb \| None` | DELETE | Deletes a role. |

---

## 5. Core Business Modules

Complex cross-cutting business processes live in `src/kardex/core/`. These modules orchestrate multiple repositories within a single business transaction, often using **MongoDB transactions** for atomicity.

| Module | Path | Purpose |
|---|---|---|
| **Adjust Ledger** | `core/adjust_ledger/` | Processes inventory adjustments (entries and exits) with stock reconciliation |
| **Client** | `core/client/` | Client creation with initial balance setup (creates invoice + financial movement in a transaction) |
| **Counter Manager** | `core/counter_manager/` | Centralized sequential document numbering: invoice, receipt, order, return, product, user, client, transfer, supplier, adjustment, and expense numbers |
| **Default Values** | `core/default_values/` | Initializes system default data on first run |
| **Devolution Register** | `core/devolution_register/` | Processes product returns with stock restoration |
| **Finance** | `core/finance/` | Client financial engine (`ClientFinanceEngine.process_movement()`) — handles credits, debits, and balance updates |
| **Imports** | `core/imports/` | Data import logic for bulk operations |
| **Inventory** | `core/inventory/` | Core inventory management — processes stock entries and exits |
| **Invoice Register** | `core/invoice_register/` | Invoice creation with automatic stock deduction from inventory |
| **On Start Actions** | `core/on_start_actions/` | Startup initialization routines |
| **Order Register** | `core/order_register/` | Order-to-invoice conversion logic |
| **Product Ledger** | `core/product_ledger/` | Product accounting ledger (kardex) |
| **Product Register** | `core/product_register/` | Full product profile creation (product + accounts + sale profiles across all branches) |
| **Receipt Register** | `core/receipt_register/` | Receipt processing with invoice payment settlement |
| **Report Manager** | `core/report_manager/` | Report generation engine |
| **Role Manager** | `core/role_manager/` | Role-based access control logic |
| **Security** | `core/security/` | `SysPasswordHasher` (argon2), `TokenManager` (JWT with HS256 + EdDSA) |
| **Transfer Manager** | `core/transfer_manager/` | Inter-branch stock transfer state machine (create, receive, cancel) |
| **Lite Product Register** | `lite/core/product_register/` | Lightweight/specialized product registration flow |

---

## 6. MongoDB Collections

All database access goes through collection classes at `src/kardex/services/mongo_collections/v1/`. Each class extends `BaseMongoCollection` and defines:

- `collection_name: str` — the MongoDB collection name
- Custom CRUD methods using `self._collection` (Motor `AsyncCollection`)

**32 MongoDB collections** (indexed alphabetically; the first two are used internally by the finance engine):

1. `AccountBalancesCollection`
2. `AccountsCollection`
3. `AdjustEntriesCollection`
4. `AdjustExitsCollection`
5. `BranchesCollection`
6. `ClientGroupsCollection`
7. `ClientTransactionsCollection`
8. `ClientsCollection`
9. `CoreSettingsCollection`
10. `CountersCollection`
11. `DailySummariesCollection`
12. `DevolutionsCollection`
13. `EntryDocsCollection`
14. `ExecutiveSummariesCollection`
15. `ExitDocsCollection`
16. `ExpirationLogsCollection`
17. `ExpenseCategoriesCollection`
18. `ExpensesCollection`
19. `IntegrationsCollection`
20. `InvoicesCollection`
21. `OrdersCollection`
22. `ProductAccountsCollection`
23. `ProductCategoriesCollection`
24. `ProductPricesCollection`
25. `ProductSaleProfilesCollection`
26. `ProductStatsCollection`
27. `ProductTransactionsCollection`
28. `ProductsCollection`
29. `ReceiptsCollection`
30. `SuppliersCollection`
31. `TransactionsCollection`
32. `TransfersCollection`
33. `UnitsCollection`
34. `UserRolesCollection`
35. `UsersCollection`

---

## 7. Tools & Utilities

All tools live in `src/kardex/tools/`.

### TimeTools

Static utility for timestamp management. Timezone: `America/Managua`.

| Method | Description |
|---|---|
| `get_now_in_milliseconds() -> int` | Current UTC time in milliseconds |
| `seconds_until_next_midnight() -> int` | Seconds remaining until the next midnight |
| `get_now_in_100days_in_milliseconds() -> int` | Current time + 100 days in milliseconds |

### UuidTool

Static utility for UUID generation.

| Method | Description |
|---|---|
| `generate_uuid() -> str` | Returns `str(uuid.uuid4())` |

### SearchTools

Text search utility for MongoDB prefix-based search.

| Function | Description |
|---|---|
| `generate_prefixes(text, min_size, max_size) -> list[str]` | Generates word prefixes for text search (e.g., "Hello World" → `["he", "hel", "hell", "hello", "wo", "wor", "worl", "world"]`) |

### QueryBuilder

MongoDB filter construction utility.

| Function | Description |
|---|---|
| `build_query(date_field, **kwargs) -> QueryResult` | Builds a MongoDB filter dict + offset/limit from keyword args (`clientId`, `supplierId`, `branchId`, `status`, `startDate`, `endDate`, `createdBy`). Returns `QueryResult(query, offset, limit)`. |

### EtagTool

Singleton cache for ETag-based HTTP caching. Tracks invalidation tags for branches, projections, and estimations.

| Method | Description |
|---|---|
| `set_tag(key, branch_id)` | Sets an ETag value |
| `get_etag(key) -> str \| None` | Gets an ETag value |
| `get_branches_etag() -> str` | Gets composite ETag for all branches |
| `update_branches_etags(action)` | Invalidates branch ETags on create/update/delete |

### BranchesTool

Singleton in-memory cache of branches.

| Method | Description |
|---|---|
| `refresh_current_branches() -> None` | Refreshes branch cache from DB |
| `get_branch_by_id(branch_id) -> BranchInDb \| None` | Gets a cached branch by ID |

### IntegrationTool

Singleton cache for the current integration configuration.

| Method | Description |
|---|---|
| `get_current_integration() -> IntegrationInDb \| None` | Gets cached integration |
| `refresh_current_integration() -> None` | Refreshes cache from DB |

### UsersTool

Singleton cache of inactive users (used by auth middleware for quick rejection).

| Method | Description |
|---|---|
| `refresh_inactive_users() -> None` | Refreshes inactive user cache |
| `get_inactive_user_by_id(user_id) -> UserInDb \| None` | Checks if a user is inactive |

---

## 8. Filter Parameters

Typed Pydantic parameter classes for building MongoDB queries safely. Located at `src/kardex/repos/v1/common/filter_params/`.

| Class | Fields | Used By |
|---|---|---|
| `BaseFilterParams` | `offset: int = 0`, `limit: int = 50` | Base class for most filter params |
| `ProductFilterParams` | Base + `branchId`, `startDate`, `endDate`, `paymentMethod`, `nePaymentMethod` | `ProductsRepository` |
| `ClientFilterParams` | Extends BaseFilterParams | `ClientsRepository` |
| `ClientTransactionFilterParams` | + `to_query()` method | `ClientTransactionsRepository` |
| `DailySummaryFilterParams` | Extends BaseFilterParams | `DailySummariesRepository` |
| `DevolutionFilterParams` | Extends BaseFilterParams | `DevolutionsRepository` |
| `EntryDocFilterParams` | `offset`, `limit`, `branch_id`, `supplierId`, `startDate`, `endDate` | `EntryDocsRepository` |
| `EntryHistoryFilterParams` | + `to_query_params()` | `EntryHistoriesRepository` |
| `ExitDocFilterParams` | `offset`, `limit`, `branch_id`, `clientId`, `startDate`, `endDate` | `ExitDocsRepository` |
| `ExitHistoryFilterParams` | + `to_query_params()` | `ExitHistoriesRepository` |
| `ExpirationLogFilterParams` | Extends BaseFilterParams | `ExpirationLogsRepository` |
| `ExpensesFilterParams` | + `to_query_params()` | `ExpensesRepository` |
| `InvoiceFilterParams` | Base + date range + `byPaidAt` | `InvoicesRepository` |
| `AdjustFilterParams` | Extends InvoiceFilterParams | `AdjustEntriesRepository`, `AdjustExitsRepository` |
| `OrderFilterParams` | Base + `branchId`, `status`, `startDate`, `endDate` | `OrdersRepository` |
| `ProductStatFilterParams` / `ReadProductStatFilterParams` | Aggregation query params | `ProductStatsRepository` |
| `ProductTransactionFilterParams` | Extends BaseFilterParams | `ProductTransactionsRepository` |
| `ReceiptFilterParams` | Extends BaseFilterParams | `ReceiptsRepository` |
| `TransferFilterParams` | Extends BaseFilterParams | `TransfersRepository` |
| `ExecutiveSummaryFilterParams` | Base + `type`, `startDate`, `endDate` | `ExecutiveSummariesRepository` |
| `TotalsFilterParams` | + payment type filtering | `InvoicesRepository`, `ReceiptsRepository` |

**History Params** (`common/models/history_params.py`): `HistoryParams`, `HistoryBranchParams`, `HistoryClientParams` — with `to_query_params()` for MongoDB date range query building.

---

## 9. Common Models

Shared domain models at `src/kardex/repos/v1/common/models/`.

| Model | Purpose |
|---|---|
| `SaleItem` | Invoice line item (product, quantity, price, discount, totals) |
| `ProductItem` | Product reference inside a sale item |
| `ClientInfo` | Embedded client info in documents |
| `UserInfo` | Embedded user info in documents |
| `CommercialBranchDetail` | Commerce-specific branch detail |
| `InventoryBranchDetail` | Inventory-specific branch detail |
| `TransferItem` | Transfer line item |
| `EntryItem` | Entry document line item |
| `ExitItem` | Exit document line item |
| `Coordinates` | GPS coordinates |
| `ProductStockDemand` | Stock vs. demand analysis result |
| `ProductSalesTotal` | Aggregated product sales total |
| `PaymentType` | Literal type alias for payment method strings |

---

## 10. Exceptions

All business exceptions inherit from `KardexException` (`tools/kardex_exceptions.py`). The FastAPI layer maps these to HTTP status codes in `app/regis_exception_handlers.py`.

| Exception | Description |
|---|---|
| `KardexException` | Base exception for all domain errors |
| `InsufficientBalanceError` | Client has insufficient credit/funds |
| `BranchNotFound` | Referenced branch does not exist |
| `DocumentAlreadyExists` | Duplicate document number detected |
| `ProductNotFound` | Referenced product does not exist |
| `ClientNotFound` | Referenced client does not exist |
| `ReceiptNotFound` | Referenced receipt does not exist |
| `ReceiptAlreadyDeleted` | Attempt to delete an already-deleted receipt |
| `SameBranchTransferError` | Transfer between the same source and destination branch |
| `InvalidOperation` | Invalid business operation attempted |
| `DirectStockAdjustmentBlocked` | Direct stock modification blocked when `followTransaction` is enabled |
| `MongoMigrationException` | MongoDB index/data migration error |
| `NotModified` | HTTP 304 support (in `tools/app_exceptions.py`) |

---

## 11. Usage Example

```python
from kardex.repos.v1.products.products_repository import ProductsRepository
from kardex.repos.v1.products.models.product_model import CreateProduct
from kardex.repos.v1.clients.clients_repository import ClientsRepository
from kardex.repos.v1.clients.models.client_model import CreateClient
from kardex.repos.v1.invoices.invoices_repository import InvoicesRepository
from kardex.repos.v1.common.filter_params.invoice_filter_params import InvoiceFilterParams
from kardex.core.counter_manager import CounterManager
from kardex.tools.kardex_exceptions import InsufficientBalanceError

async def example_flow() -> None:
    # 1. Get repository instances (singletons)
    products_repo = ProductsRepository.get_instance()
    clients_repo = ClientsRepository.get_instance()
    invoices_repo = InvoicesRepository.get_instance()

    # 2. Create a product
    new_product = await products_repo.create_product(CreateProduct(
        name="Widget Pro",
        code="WGT-001",
        category="Electronics",
    ))

    # 3. Create a client
    new_client = await clients_repo.create_client(CreateClient(
        name="Acme Corp",
        phone="50588889999",
        group="Corporate",
    ))

    # 4. Query products in a branch (streaming for large inventory)
    async for product in products_repo.get_all_product_in_branch_streamed(
        ProductFilterParams(branchId="branch-001")
    ):
        print(f"Product: {product['name']}, Stock: {product['currentStock']}")

    # 5. Get invoice totals
    totals = await invoices_repo.get_totals_from_invoices(
        InvoiceFilterParams(startDate=1717200000000, endDate=1719878400000)
    )
    print(f"Total invoiced: {totals.totalAmount} cents")

    # 6. Generate a document number
    counter = CounterManager.get_instance()
    next_inv = await counter.next_invoice_number()
    print(f"Next invoice number: {next_inv}")

    # 7. Handle business exceptions
    try:
        # ... some operation that might fail
        pass
    except InsufficientBalanceError as e:
        print(f"Client has insufficient balance: {e}")
    except ProductNotFound as e:
        print(f"Product not found: {e}")
```

---

## Summary Statistics

| Metric | Count |
|---|---|
| Total Repositories | **35** |
| MongoDB Collections | **34** (+ 1 for internal accounts) |
| Core Business Modules | **19** |
| Filter Parameter Classes | **21** |
| Common Shared Models | **13** |
| Repositories with Full CRUD | ~18 |
| Read-only Repositories | 7 |
| Repositories with Streaming (`△`) | 3 |
| Repositories with Aggregation (`Σ`) | 6 |
| Repositories with TODO Stubs (`⇢`) | 4 |
| Transaction-aware Repositories (`T`) | 3 |
| Business Exception Types | **13** |
| Tool/Utility Classes | **9** |
| Singleton Pattern Usage | Universal (all Repos, DataSources, Collections, Tools) |
| DI Pattern | Constructor injection, manually wired |
| ORM | None — raw PyMongo (Motor) with dict operations |
| Data Validation | Pydantic at Repository boundary |
| Timezone | `America/Managua` |
