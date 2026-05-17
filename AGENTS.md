# AI Agents Guide - Kardex Server

Welcome, Agent. This document contains the architectural rules, conventions, and tool usage for this project. **Read this before performing any modification.**

## 🏗 Project Architecture: Onion Architecture
The project follows a strict **Onion Architecture** (Clean Architecture) pattern. Data must flow from the outside in, never the reverse.

### Data Flow Pattern
`Router` (HTTP) → `Controller` (Orchestration) → `Repository` (Business Logic) → `DataSource` (DB/Persistence) → `Service` (External)

### Layer Responsibilities
- **`app/api/vX/`**: 
    - `router.py`: Endpoint definitions using FastAPI.
    - `controller.py`: Validates inputs, calls repositories, and maps responses.
- **`app/repos/vX/`**:
    - `repository.py`: Orchestrates business logic and domain rules.
    - `data/`: `datasource.py` implements specific DB queries (MongoDB/Motor).
    - `models/`: Domain Pydantic models.
- **`app/core/`**: Shared complex business processes (e.g., invoice processing, report generation).
- **`app/services/`**: Outermost layer for external world (Database connections, file storage, etc.).
- **`app/tools/`**: Pure utilities and auxiliary helpers.

---

## 🛠 Tooling: Onion CLI
This project uses a custom CLI called `onion` to automate boilerplate creation.

### Common Commands
- `onion crud <entity> --version 1`: Creates Router, Controller, Repo, DataSource, and Model.
- `onion crud-mongo <entity> --version 1`: Same as above + MongoDB collection setup in `onion-config.toml`.
- `onion repo <entity> --version 1`: Creates only the repository and data layers.

### Manual Steps After Generation
1. **Registration**: Every new router MUST be manually imported and included in `app/api/v1/router.py`:
   ```python
   from .my_entity.my_entity_router import my_entity_router
   router_v1.include_router(my_entity_router, prefix="/my-entity")
   ```
2. **Main Router**: If creating a NEW API version (e.g., `v2`), it must be included in `app/main.py`.

---

## 📋 Coding Conventions
1. **Naming**:
    - Files/Folders: `snake_case`.
    - Classes: `PascalCase`.
    - Functions/Variables: `snake_case`.
    - **Pydantic Model Properties**: MUST use **`camelCase`** (to maintain consistency with Flutter/MongoDB standards). Example: `productId`, `branchId`.
2. **Entities**: Always use **singular** for entity names (`product`, not `products`).
3. **Database**: 
    - Use `MongoService` for DB access.
    - Collection names are tracked in `app/config/onion-config.toml`.
    - Do NOT hardcode collection names; use constants or configuration references.
4. **Validation**: Use **Pydantic** models for all Request/Response bodies.
5. **Data Types**:
    - **Dates**: Always use `int` (Unix Timestamps).
    - **Currency/Money**: Always use `int` (to avoid floating-point errors, usually representing cents or the smallest unit).
6. **Dependencies**: Managed by `uv`. Add dependencies using `uv add <package>`.

---

## 🤖 Agent Session Protocol
- **`GEMINI.md`**: After every session or major feature completion, YOU MUST update the `GEMINI.md` file at the root. Record the date, the objective, and a summary of the technical implementation.
- **Aesthetics**: When asked for Web App or UI changes, prioritize premium aesthetics, dynamic designs, rich UX.

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

## 🏗 Registry Reference
- **Main Entry Point**: `app/main.py`
- **Dependency/Startup**: `app/app_lifespan.py`
- **Global V1 Router**: `app/api/v1/router.py`
- **CLI Config**: `app/config/onion-config.toml`
