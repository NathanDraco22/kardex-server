# AI Agents Guide - Kardex Server

Welcome, Agent. This document contains the architectural rules, conventions, and tool usage for this project. **Read this before performing any modification.**

## 🏗 Project Architecture: Onion Architecture
The project follows a strict **Onion Architecture** (Clean Architecture) pattern. Data must flow from the outside in, never the reverse.

### Data Flow Pattern
`Router` (HTTP) → `Controller` (Orchestration) → `Repository` (Business Logic) → `DataSource` (DB/Persistence) → `Service` (External)

### Package (`packages/kardex-business/src/kardex/`)
Contains all business logic, repositories, data sources, domain models, and services. No FastAPI dependency — pure domain logic.

- **`repos/v1/`**: Repository layer — orchestrates business logic, delegates to DataSource.
    - `repository.py`: Business rules + singleton `get_instance()` pattern.
    - `data/datasource.py`: DB queries (MongoDB/Motor).
    - `models/`: Pydantic domain models (camelCase properties).
- **`core/`**: Complex business processes (inventory, invoices, orders, transfers, etc.).
- **`services/`**: MongoService, MongoCollection classes, indexes.
- **`tools/`**: Utilities: TimeTools, UuidTool, EtagTool, search, query builder.
    - `kardex_exceptions.py`: Domain exceptions (`InsufficientBalanceError`, `BranchNotFound`, etc.).
- **`lite/core/`**: Lite-specific core modules (e.g., product_register).

### Local (`app/`)
Thin web layer with FastAPI — imports everything from `kardex.*`.

- **`api/v1/`**: Controllers + routers — endpoints, request validation, response mapping.
- **`tools/`**: `__init__.py` re-exports from `kardex.tools.*`, plus local tools (`integration_tool.py`, `users_tool.py`).
- **`core/scheduler/`**: Scheduler + app_notifier (stays local).
- **`core/services_initializer.py`**: Startup initialization (calls package).
- **`services/`**: `excel_service.py`, `telgram_service.py` (local). `MongoService` re-exported from package.
- **`regis_exception_handlers.py`**: Centralized exception-to-HTTP mapping for all `KardexException` subclasses.
- **`app_middleware/`**: Auth middleware, cache headers.

---

## 📋 Coding Conventions
1. **Naming**:
    - Files/Folders: `snake_case`.
    - Classes: `PascalCase`.
    - Functions/Variables: `snake_case`.
    - **Pydantic Model Properties**: MUST use **`camelCase`** (to maintain consistency with Flutter/MongoDB standards). Example: `productId`, `branchId`.
2. **Entities**: Always use **singular** for entity names (`product`, not `products`).
3. **Database**: 
    - Use `MongoService` from `kardex.services` for DB access.
    - Collection names are tracked in `app/config/onion-config.toml`.
    - Do NOT hardcode collection names; use constants or configuration references.
4. **Validation**: Use **Pydantic** for all Request/Response models.
5. **Data Types**:
    - **Dates**: Always use `int` (Unix Timestamps).
    - **Currency/Money**: Always use `int` (centavos).
6. **Exceptions**: Business exceptions inherit from `KardexException`. HTTP mapping lives in `app/regis_exception_handlers.py`. Never raise `HTTPException` from the package.
7. **Repositories**: All repos implement `get_instance()` singleton + constructor injection.
8. **Dependencies**: Managed by `uv`. Add package deps using `uv add <package>`. Package has NO FastAPI dependency.

---

## ✅ Pre-commit Verification

After every modification, run these checks and fix any issues:

```powershell
# Lint (ruff)
$env:PYTHONPATH = "app;$env:PYTHONPATH"; .venv\Scripts\ruff.exe check packages/kardex-business/src/kardex/ app/

# Type check (ty)
$env:PYTHONPATH = "app;$env:PYTHONPATH"; .venv\Scripts\ty.exe check
```

Both must pass before finishing a task.

---

## 🤖 Agent Session Protocol
- **`GEMINI.md`**: After every session or major feature completion, YOU MUST update the `GEMINI.md` file at the root. Record the date, the objective, and a summary of the technical implementation.
- **Aesthetics**: When asked for Web App or UI changes, prioritize premium aesthetics, dynamic designs, rich UX.

---

## 🏗 Registry Reference
- **Main Entry Point**: `app/main.py`
- **Dependency/Startup**: `app/app_lifespan.py`
- **Global V1 Router**: `app/api/v1/router.py`
- **CLI Config**: `app/config/onion-config.toml`
- **Business Package**: `packages/kardex-business/src/kardex/`
- **Exception Handlers**: `app/regis_exception_handlers.py`

---

## 🔧 Onion CLI — Usage Guide

Onion CLI generates boilerplate code following the **Onion Architecture**. This guide explains every command, the naming conventions, and the expected workflows for both **FastAPI (Python)** and **Flutter (Dart)** projects.

---

### Naming Conventions

All entity names must be provided in **singular** form. The CLI automatically derives 4 name variations:

| Variation | Example (`product`) | Example (`category`) |
|---|---|---|
| `Name` (PascalCase) | `Product` | `Category` |
| `Name_plural` (PascalCase) | `Products` | `Categories` |
| `single_name` (snake_case) | `product` | `category` |
| `plural_name` (snake_case) | `products` | `categories` |

**Rules:**
- Plural names are **rejected** with an error. Use `product` not `products`.
- Hyphens, spaces, and underscores in input are normalized to PascalCase. `order-item` → `OrderItem`.
- The pluralization follows English grammar rules (irregular nouns like `person` → `people`, `leaf` → `leaves`, etc. are handled).

---

### Output Directory

All FastAPI CRUD commands accept a `--output-dir` option that controls where files are created:

- **Without `--output-dir`** (default): creates `app/api/...`, `app/repos/...`, etc. (current behavior, backwards compatible).
- **With `--output-dir <DIR>`**: `<DIR>` replaces `app/` as the base folder. For example, `--output-dir ./src` creates `src/api/...`, `src/repos/...`, `src/services/...`, `src/config/...`.
- For the `repo` command without `--version`: `<DIR>` replaces `generated_output/`.

The project scaffolding commands (`project`) have their own `OUTPUT_DIR` argument that works as the target project root.

---

### FastAPI Commands

#### Scaffolding

##### `onion project fastapi-app`

Copies the `app/` folder from the FastAPI template. Placeholder `example`/`examples` is replaced with your entity name.

```bash
# Inside your project root:
onion project fastapi-app . --force
```

**Structure created:**
```
app/
├── api/v1/examples/
│   ├── examples_controller.py
│   └── examples_router.py
├── repos/v1/examples/
│   ├── data/examples_datasource.py
│   ├── models/example_model.py
│   └── examples_repository.py
├── core/
├── config/
├── services/
├── tools/
└── main.py
```

##### `onion project fastapi-init`

Copies a **complete** FastAPI project (root files, Dockerfile, tests, configs, etc.).

```bash
onion project fastapi-init ./my-new-project
```

**Structure created:**
```
my-new-project/
├── app/           (same as fastapi-app above)
├── test/
├── Dockerfile
├── pyproject.toml
├── .dockerignore
├── .gitignore
└── runtime.txt
```

---

#### CRUD Generation

There are 3 tiers of CRUD generation. Choose the one that fits your needs:

| Command | Router + Controller | Repo + Datasource + Model | Mongo Collection |
|---|---|---|---|
| `router` | ✅ | ❌ | ❌ |
| `crud` | ✅ | ✅ | ❌ |
| `repo` | ❌ | ✅ | ❌ |
| `crud-mongo` | ✅ | ✅ | ✅ |
| `repo-mongo` | ❌ | ✅ | ✅ |

All CRUD commands accept one or more entity names. The `--version` flag is **required**.

```bash
# Single entity
onion crud product --version 1

# Multiple entities at once
onion crud product category supplier --version 1

# Custom output directory
onion crud product --version 1 --output-dir ./src
```

| Global Option | Default | Description |
|---|---|---|
| `--version` | | **Required.** API version number |
| `--output-dir` | `""` | Output directory (replaces `app/` or `generated_output/`) |

##### `onion crud`

Creates router, controller, repository, datasource, and model.

```bash
onion crud product --version 1
```

**Generated files (with default output):**
```
app/
├── api/v1/products/
│   ├── products_router.py        # FastAPI router with CRUD endpoints
│   ├── products_controller.py    # Controller wired to repository
│   └── __init__.py
└── repos/v1/products/
    ├── products_repository.py    # Repository (singleton, calls datasource)
    ├── data/products_datasource.py  # Data source (stub to implement)
    ├── models/product_model.py   # Pydantic models: BaseProduct, CreateProduct, UpdateProduct, ProductInDb
    └── __init__.py               # Re-exports all classes
```

The version router `app/api/v1/router.py` is also auto-created/updated with `include_router()` lines.

**Number of files created:** 6

##### `onion router`

Creates **only** the router and controller (no repository layer).

```bash
onion router product --version 1
```

**Generated files:**
```
app/api/v1/products/
├── products_router.py       # Router with Any types (no typed models)
├── products_controller.py   # Basic controller with NotImplementedError stubs
└── __init__.py
```

**Use case:** For endpoints that don't need a database (e.g., health checks, external API proxies).

**Number of files created:** 2 (+ auto-update to `router.py`)

##### `onion repo`

Creates **only** the repository layer (no router/controller).

```bash
onion repo product --version 1
```

**Generated files:**
```
app/repos/v1/products/
├── products_repository.py
├── data/products_datasource.py
├── models/product_model.py
└── __init__.py
```

**Use case:** When you need the data layer but want to wire the router manually.

**Number of files created:** 4

##### `onion crud-mongo`

Full CRUD + MongoDB collection + MongoDB service.

```bash
onion crud-mongo product --version 1
```

**Generated files:** Everything from `crud` plus:
```
app/services/
├── mongo_service.py                       # Singleton MongoDB client (Motor)
├── base_mongo_collection.py               # Base class with singleton pattern
└── mongo_collections/v1/
    ├── products_collection.py             # Collection class (extends BaseMongoCollection)
    └── __init__.py
app/config/
└── onion-config.toml                      # Tracks registered collections
```

The datasource is wired to use the MongoDB collection (instead of leaving NotImplementedError).

**Number of files created:** 10

##### `onion repo-mongo`

Repository layer + MongoDB collection (no router/controller).

```bash
onion repo-mongo product --version 1
```

**Generated files:** Everything from `repo` plus `mongo_service.py`, `base_mongo_collection.py`, `mongo_collections/v1/products_collection.py`, and `onion-config.toml`.

**Number of files created:** 8

---

#### Generated Code Structure (FastAPI)

##### Router (`products_router.py`)

```python
@products_router.post("")           # POST /products
@products_router.get("")            # GET /products
@products_router.get("/{product_id}")   # GET /products/{product_id}
@products_router.patch("/{product_id}") # PATCH /products/{product_id}
@products_router.delete("/{product_id}")# DELETE /products/{product_id}
```

When generated via `crud` or `crud-mongo`, endpoints are fully typed with `CreateProduct`, `UpdateProduct`, `ProductInDb`. With `router` alone, they use `Any`.

##### Controller (`products_controller.py`)

Wired to the repository via singleton pattern. Delegates all calls to `ProductsRepository`.

##### Repository (`products_repository.py`)

Singleton with `get_instance()`. Calls the datasource and validates results into Pydantic models.

##### Datasource (`products_datasource.py`)

- Without MongoDB: stub with `NotImplementedError`.
- With MongoDB: calls `ProductsCollection.get_instance()` methods.

##### MongoDB Collection (`products_collection.py`)

Extends `BaseMongoCollection` which provides:
- Singleton pattern via `get_instance()` classmethod
- `self._collection` — the Motor collection instance

The generated class only defines `collection_name` and CRUD methods:
```python
class ProductsCollection(BaseMongoCollection):
    collection_name = "Products"

    async def create_product(self, product: dict) -> None: ...
    async def fetch_all_products(self) -> list[dict[str, Any]]: ...
    async def fetch_product_by_id(self, product_id: str) -> dict[str, Any] | None: ...
    async def update_product_by_id(...): ...
    async def delete_product_by_id(...): ...
```

##### BaseMongoCollection (`services/base_mongo_collection.py`)

Abstract base class auto-generated alongside `mongo_service.py`. Handles the singleton and MongoService wiring so collection subclasses only write CRUD logic:

```python
class BaseMongoCollection:
    collection_name: str = ""
    _instance: "BaseMongoCollection|None" = None

    def __init__(self) -> None:
        mongo_service = MongoService()
        self._collection = mongo_service.get_collection(self.collection_name)

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

##### Model (`product_model.py`)

```python
class BaseProduct(BaseModel): pass     # Common fields
class CreateProduct(BaseProduct): pass # POST body
class UpdateProduct(BaseModel): pass   # PATCH body
class ProductInDb(BaseProduct):        # Response (id, created_at, updated_at)
```

##### Version Router (`app/api/v1/router.py`)

Auto-generated with `include_router()` for each module.

---

### Dart / Flutter Commands

All Dart commands assume you are inside a Flutter project.

#### `onion dart`

Generates model + datasource + repository for one entity.

```bash
# Inside a Flutter project:
onion dart product
```

**Generated files:**
```
lib/src/
├── models/product_model.dart              # BaseProduct, CreateProduct, UpdateProduct, ProductInDb
├── data/
│   ├── products_data_source.dart          # Data source (HttpService) with full CRUD+search
│   └── data_sources.dart                  # Barrel file
└── domain/repositories/
    ├── products_repository.dart           # Repository with local caching
    └── repositories.dart                  # Barrel file
```

**Number of files created:** 5

**Default output:** `./lib/src`. Override with `--output-dir`.

#### `onion dart-model`

Creates model classes only.

```bash
onion dart-model product --output-dir "./lib/src"
```

**Generated:**
```
lib/src/models/product_model.dart
```

Contains 4 classes: `BaseProduct`, `CreateProduct`, `UpdateProduct`, `ProductInDb`.

#### `onion dart-cubit`

Creates cubit + state files for Flutter Bloc state management.

```bash
# Create both read and write cubits (default):
onion dart-cubit product

# Read-only:
onion dart-cubit product --read-only

# Write-only:
onion dart-cubit product --write-only
```

**Generated:** `{output_dir}/{name}_cubit/` with:
- `read_products_cubit.dart` + `read_products_state.dart`
- `write_products_cubit.dart` + `write_products_state.dart`

**States (Read):** `ReadProductInitial`, `ReadProductLoading`, `ReadProductSuccess` (with lists for items/new/updated/deleted), `ReadProductSearching`, `HighlightedProductItem`, `ReadProductError`.

**States (Write):** `WriteProductInitial`, `WritingProduct`, `WriteProductSuccess`, `ProductCreated`, `ProductUpdated`, `ProductDeleted`, `WriteProductError`.

#### `onion flutter-module`

Creates a complete feature module folder structure.

```bash
onion flutter-module product
```

**Generated:** `lib/src/modules/products/` with:
```
cubit/
├── read_products_cubit.dart
├── read_products_state.dart
├── write_products_cubit.dart
└── write_products_state.dart
dialogs/products_dialogs.dart      # Stub
view/products_view.dart            # Stub
widgets/products_widgets.dart      # Stub
```

**Number of files created:** 6

#### `onion barrel`

Creates a Dart barrel file (re-export) for any directory.

```bash
# Re-export all .dart files in lib/src/models:
onion barrel ./lib/src/models --filename export.dart
```

**Generated:** `{directory}/export.dart` with `export '...';` lines for every `.dart` file.

---

### Generated Code Structure (Dart)

#### Data Source (`products_data_source.dart`)

Singleton with `HttpService` mixin. Endpoints:
- `POST /products` → `createProduct()`
- `GET /products` → `getAllProducts()`
- `GET /products/{id}` → `getProductById()`
- `GET /products/search/{keyword}` → `searchProductByKeyword()`
- `PATCH /products/{id}` → `updateProductById()`
- `DELETE /products/{id}` → `deleteProductById()`

#### Repository (`products_repository.dart`)

Wraps the data source, maintains an in-memory `_products` list. Adds:
- `searchByKeywordLocal()` — client-side filtering on cached data
- Automatic list update after create/update/delete

#### Models (`product_model.dart`)

4 classes: `BaseProduct`, `CreateProduct`, `UpdateProduct`, `ProductInDb` (with `fromJson`).

---

### Flutter Project Scaffolding

#### `onion project flutter-lib`

Copies the Flutter template and replaces placeholder names.

```bash
onion project flutter-lib ./my-flutter-app --package "com.company.app" --force
```

**What is replaced:**
- `sample` → your entity name (snake_case)
- `Sample` → PascalCase
- `sample_entity` / `SampleEntity` → derived variations
- `kardex_app_front` → package name (with dots replaced by underscores)

Filenames containing `sample`/`Sample` are also renamed.

---

### Workflows

#### Typical FastAPI Project Setup

```bash
# 1. Initialize a complete FastAPI project
onion project fastapi-init ./my-api

# 2. Generate CRUD for entities
cd ./my-api
onion crud product --version 1
onion crud category --version 1
onion crud-mongo order --version 1   # if using MongoDB

# 3. Implement the datasource logic
# Edit: app/repos/v1/products/data/products_datasource.py
# Edit: app/repos/v1/categories/data/categories_datasource.py
```

#### Typical Flutter Project Setup

```bash
# 1. Initialize Flutter template
onion project flutter-lib ./my-app --package "com.company.app"

# 2. Generate data layer for entities
cd ./my-app
onion dart product
onion dart category

# 3. Generate cubits for state management
onion dart-cubit product
onion dart-cubit category

# 4. Or generate a complete module at once
onion flutter-module product
```

#### Adding a New Entity to an Existing Project

```bash
# FastAPI with plain CRUD:
onion crud supplier --version 1

# FastAPI with MongoDB:
onion crud-mongo supplier --version 1

# FastAPI, data layer only:
onion repo supplier --version 1

# FastAPI, endpoints only:
onion router supplier --version 1
```

---

### Summary File Counts

| Command | Files Created | Category |
|---|---|---|
| `project fastapi-app` | ~15 | Scaffolding |
| `project fastapi-init` | ~25 | Scaffolding |
| `project flutter-lib` | ~20 | Scaffolding |
| `crud` | 6 | CRUD |
| `crud-mongo` | 10 | CRUD + Mongo |
| `repo` | 4 | Data Layer |
| `repo-mongo` | 8 | Data Layer + Mongo |
| `router` | 2 | Endpoints |
| `dart` | 5 | Dart Data Layer |
| `dart-model` | 1 | Dart Model |
| `dart-cubit` | 4 | Dart State |
| `flutter-module` | 6 | Dart Module |
| `barrel` | 1 | Utility |
