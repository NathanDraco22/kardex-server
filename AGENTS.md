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

## 🔧 Onion CLI — Entity Generation

Use the `onion` CLI to generate boilerplate for new entities. **Always use `--version 1`**. Entity names must be **singular**.

### CLI Commands

| Command | Produces |
|---|---|
| `onion crud-mongo <entity> --version 1` | Router + Controller + Repo + Datasource + Model + MongoCollection (full stack) |
| `onion crud <entity> --version 1` | Router + Controller + Repo + Datasource + Model (no MongoCollection) |
| `onion repo-mongo <entity> --version 1` | Repo + Datasource + Model + MongoCollection (data layer only) |
| `onion repo <entity> --version 1` | Repo + Datasource + Model (no collection) |
| `onion router <entity> --version 1` | Router + Controller only (no data layer) |

### Examples
```bash
onion crud-mongo product --version 1          # Full stack with MongoDB
onion crud product category --version 1        # Multiple entities
onion repo supplier --version 1                # Data layer only
```

### Generated Structure (for `crud-mongo`)
```
app/
├── api/v1/{entities}/
│   ├── {entities}_router.py        # FastAPI router (CRUD endpoints)
│   └── {entities}_controller.py    # Wired to repository
├── repos/v1/{entities}/
│   ├── {entities}_repository.py    # Singleton + constructor injection
│   ├── data/{entities}_datasource.py  # Calls collection via get_instance()
│   └── models/{entity}_model.py    # BaseX, CreateX, UpdateX, XInDb
└── services/mongo_collections/v1/
    └── {entities}_collection.py    # Extends BaseMongoCollection
```

### Naming Rules
- **Input**: always singular (`product`, not `products`). The CLI rejects plurals.
- **Derived variations**:
  | Variation | Example |
  |---|---|
  | `Name` (PascalCase) | `Product` |
  | `Name_plural` (PascalCase) | `Products` |
  | `single_name` (snake_case) | `product` |
  | `plural_name` (snake_case) | `products` |
- Hyphens/spaces are normalized: `order-item` → `OrderItem`.

### Workflow: Adding a New Entity
```bash
# 1. Generate the full stack
onion crud-mongo <entity> --version 1

# 2. Move files from app/ to packages/kardex-business/src/kardex/
#    (repos/ → repos/, services/mongo_collections/ → services/mongo_collections/)

# 3. Fix imports (replace from app. with kardex. or kardex. as needed)

# 4. Implement datasource CRUD logic

# 5. Register in __init__.py barrel files

# 6. Run lint & typecheck
```
