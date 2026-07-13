# kardex-business

Capa de lógica de negocio y acceso a datos para **Kardex Server** (backend REST FastAPI). Paquete Python puro (sin dependencia de FastAPI) que contiene **35 repositorios**, **19 módulos de negocio core**, **34 colecciones MongoDB** y un conjunto completo de herramientas siguiendo una estricta **Arquitectura Onion (Clean)**.

---

## Tabla de Contenidos

1. [Requisitos e Instalación](#requisitos-e-instalación)
2. [Arquitectura General](#arquitectura-general)
3. [Cómo Funciona](#cómo-funciona)
4. [Catálogo de Repositorios](#catálogo-de-repositorios)
   - [Productos e Inventario](#41-productos-e-inventario)
   - [Entradas y Salidas](#42-entradas-y-salidas)
   - [Clientes y Transacciones](#43-clientes-y-transacciones)
   - [Órdenes, Facturas, Recibos y Devoluciones](#44-órdenes-facturas-recibos-y-devoluciones)
   - [Transferencias](#45-transferencias)
   - [Proveedores](#46-proveedores)
   - [Gastos](#47-gastos)
   - [Reportes y Dashboard](#48-reportes-y-dashboard)
   - [Sistema y Utilidades](#49-sistema-y-utilidades)
   - [Autenticación y Usuarios](#410-autenticación-y-usuarios)
5. [Módulos Core de Negocio](#5-módulos-core-de-negocio)
6. [Colecciones MongoDB](#6-colecciones-mongodb)
7. [Herramientas y Utilidades](#7-herramientas-y-utilidades)
8. [Parámetros de Filtro](#8-parámetros-de-filtro)
9. [Modelos Comunes](#9-modelos-comunes)
10. [Excepciones](#10-excepciones)
11. [Ejemplo de Uso](#11-ejemplo-de-uso)

---

## Requisitos e Instalación

- **Python**: `>=3.12`
- **Dependencias**: `pymongo>=4.17.0`, `argon2-cffi>=25.1.0`, `pyjwt>=2.12.1`, `pytz>=2026.2`

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

El paquete **no tiene dependencia de FastAPI** — es consumido por la capa `app/` donde viven los routers y controladores FastAPI.

---

## Arquitectura General

El paquete sigue una estricta **Arquitectura Onion (Clean)**. Los datos fluyen desde afuera hacia adentro, nunca al revés:

```
┌─────────────────────────────────────────────────────────┐
│ Capa Web (FastAPI - app/)                               │
│  Router → Controller (orquestación ligera)              │
├─────────────────────────────────────────────────────────┤
│ Capa de Dominio (kardex-business)                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Repositories (repos/v1/)                          │  │
│  │  → Reglas de negocio + validación Pydantic        │  │
│  │  → Patrón singleton get_instance()                │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ Data Sources (repos/v1/*/data/)                   │  │
│  │  → Delega a MongoCollection                       │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ Core (core/)                                      │  │
│  │  → Procesos de negocio complejos transversales    │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ Capa de Infraestructura                                  │
│  → MongoService (singleton, Motor/PyMongo)               │
│  → BaseMongoCollection → 34 clases Collection            │
│  → Tools (TimeTools, UuidTool, TokenManager, etc.)       │
└─────────────────────────────────────────────────────────┘
```

### Patrones de Diseño

| Patrón | Uso |
|---|---|
| **Singleton** | Cada Repository, DataSource y MongoCollection usa `get_instance()` |
| **Inyección por Constructor** | Los Repos reciben DataSources; los DataSources reciben Collections |
| **Sin Contenedor DI** | Todo el wiring es hardcodeado — sin framework de inyección |
| **Sin ORM** | PyMongo (Motor) crudo con operaciones `dict`. Tipos validados en el Repository vía Pydantic |
| **Transacciones MongoDB** | Operaciones multi-documento usan `start_session()` + `with_transaction()` |

### Reglas Arquitectónicas Clave

- **El paquete NO debe importar FastAPI** ni ningún framework web.
- **Excepciones de negocio** heredan de `KardexException` (en `tools/kardex_exceptions.py`). Nunca lanzar `HTTPException` desde dentro del paquete.
- **Moneda/Dinero**: siempre `int` (centavos).
- **Fechas**: siempre `int` (timestamps Unix).
- **Propiedades de modelos Pydantic** usan `camelCase`.
- **Nombres de entidades**: siempre en singular.

---

## Cómo Funciona

### Flujo de Datos

```
Router (POST /products)
  → Controller.create_product()
    → ProductsRepository.get_instance().create_product(CreateProduct(...))
      → ProductsDataSource.get_instance().create_product(dict)
        → ProductsCollection.get_instance().create_product(dict)
          → self._collection.insert_one(dict)   # PyMongo/Motor
```

### Cableado de Dependencias

Cada clase usa el mismo patrón:

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

### Conexión MongoDB

**MongoService** es el singleton de más alto nivel:

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

### Configuración

**`KardexConfig`** singleton con flags de funcionalidad:

| Flag | Descripción |
|---|---|
| `followTransaction` | Cuando es True, los ajustes directos de stock lanzan `DirectStockAdjustmentBlocked` |
| `createFullProductProfile` | Cuando es True, la creación de producto también crea cuentas + perfiles de venta en todas las sucursales (transacción MongoDB) |
| `letInvoiceWithNegative` | Si se permite facturar cuando el stock queda negativo |

**`KardexContext`**: `contextvars.ContextVar` que provee `businessNickname` y `branchId` por request.

### Inicialización

Al iniciar, `services_initializer.py` ejecuta:

```python
await init_business_services()
# → MongoService().init_service()
# → create_indexes()  # Crea índices en más de 25 colecciones
# → set_new_values()  # Inicializa valores por defecto
```

---

## Catálogo de Repositorios

> **Leyenda**: `Full CRUD` Todas las operaciones CRUD implementadas | `Sólo lectura` Sin create/update/delete | `△` Tiene streaming | `Σ` Tiene agregación | `T` Transaccional | `⇢` Tiene stubs pendientes (no implementado aún)

Cada repositorio vive en `src/kardex/repos/v1/{entidad}/` con la estructura:
```
{entidad}/
├── {entidad}_repository.py
├── data/{entidad}_datasource.py
├── models/{entidad}_model.py
└── __init__.py
```

---

### 4.1 Productos e Inventario

#### ProductsRepository `△`

**Propósito**: Catálogo central de productos. Gestiona el ciclo completo del producto: creación (incluyendo perfil completo en todas las sucursales), consultas paginadas, búsqueda por palabra clave con generación de prefijos, consultas de inventario por sucursal y lecturas con streaming asíncrono para grandes volúmenes de datos.

**Modelos**: `ProductInDb`, `ProductInDbWithAccounts`, `ProductInDbInBranch`, `CreateProduct`, `UpdateProduct`

| Método | CRUD | Descripción |
|---|---|---|
| `create_product(product: CreateProduct) -> ProductInDb` | CREATE | Crea un producto. Cuando `createFullProductProfile` está activo, crea producto + cuentas + perfiles de venta en una transacción MongoDB con código auto-asignado vía `CounterManager`. |
| `get_all_products() -> list[ProductInDb]` | READ | Obtiene todos los productos. |
| `get_all_products_with_accounts(branch_id, page, limit) -> list[ProductInDbWithAccounts]` | READ | Obtiene productos con datos contables (agregación). |
| `get_paginated_products(offset, limit) -> list[ProductInDb]` | READ | Paginación offset/limit. |
| `get_product_by_id(product_id: str) -> ProductInDb \| None` | READ | Obtiene por ID. |
| `get_product_by_code(product_code: str) -> ProductInDb \| None` | READ | Obtiene por código auto-asignado. |
| `search_product_by_text(text_query: str) -> list[ProductInDb]` | SEARCH | Búsqueda textual usando generación de prefijos. |
| `get_product_by_ids(product_ids: list[str]) -> list[ProductInDb]` | READ | Obtiene múltiples productos por IDs. |
| `search_product_in_branch(branch_id, text_query) -> list[ProductInDbInBranch]` | SEARCH | Busca productos dentro de una sucursal específica. |
| `get_products_in_branch_by_ids(branch_id, product_ids) -> list[ProductInDbInBranch]` | READ | Obtiene múltiples productos por IDs en una sucursal. |
| `get_all_product_in_branch(params: ProductFilterParams) -> list[ProductInDbInBranch]` | READ | Obtiene todos los productos en una sucursal con datos de inventario. |
| `get_all_product_in_branch_streamed(params) -> AsyncIterable[ProductInDbInBranch]` | READ `△` | Generador asíncrono para lecturas grandes de inventario. |
| `get_product_in_branch_by_id(product_id, branch_id) -> ProductInDbInBranch \| None` | READ | Obtiene datos de producto en contexto de sucursal (stock, precio, perfil). |
| `update_product_by_id(product_id, product: UpdateProduct) -> ProductInDb \| None` | UPDATE | Actualiza datos maestros del producto. |
| `delete_product_by_id(product_id: str) -> ProductInDb \| None` | DELETE | Soft-delete de un producto. |

---

#### ProductCategoriesRepository

**Propósito**: Jerarquía de categorías de productos. Full CRUD para organizar el catálogo en categorías para filtrado y reportes.

**Modelos**: `ProductCategoryInDb`, `CreateProductCategory`, `UpdateProductCategory`

| Método | CRUD | Descripción |
|---|---|---|
| `create_product_category(cat: CreateProductCategory) -> ProductCategoryInDb` | CREATE | Crea una nueva categoría. |
| `get_all_product_categories() -> list[ProductCategoryInDb]` | READ | Obtiene todas las categorías. |
| `get_product_category_by_id(category_id) -> ProductCategoryInDb \| None` | READ | Obtiene por ID. |
| `update_product_category_by_id(category_id, cat) -> ProductCategoryInDb \| None` | UPDATE | Actualiza una categoría. |
| `delete_product_category_by_id(category_id) -> ProductCategoryInDb \| None` | DELETE | Elimina una categoría. |

---

#### ProductPricesRepository

**Propósito**: Gestión de precios de venta. Define y administra precios asociados a productos para listas de precios, perfiles de venta y facturación.

**Modelos**: `ProductPriceInDb`, `CreateProductPrice`, `UpdateProductPrice`

| Método | CRUD | Descripción |
|---|---|---|
| `create_product_price(price: CreateProductPrice) -> ProductPriceInDb` | CREATE | Crea un nuevo precio. |
| `get_all_product_prices() -> list[ProductPriceInDb]` | READ | Obtiene todos los precios. |
| `get_product_price_by_id(price_id) -> ProductPriceInDb \| None` | READ | Obtiene por ID. |
| `update_product_price_by_id(price_id, price) -> ProductPriceInDb \| None` | UPDATE | Actualiza un precio. |
| `delete_product_price_by_id(price_id) -> ProductPriceInDb \| None` | DELETE | Elimina un precio. |

---

#### ProductStatsRepository `Σ`

**Propósito**: Analítica y estadísticas de productos. Proporciona datos de rendimiento, proyecciones de inventario y capacidades de actualización batch para el motor de estimación.

**Modelos**: `ProductStatInDb`, `ProductStatInDbWithInfo`, `ProductStatInDbWithAccount`, `UpdateProductStatBatchItem`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_product_stats(params) -> list[ProductStatInDb]` | READ | Obtiene estadísticas base de todos los productos. |
| `get_all_product_stats_with_info(params) -> list[ProductStatInDbWithInfo]` | READ | Obtiene estadísticas con info de ventas/rotación. |
| `get_all_product_stats_with_account(params) -> list[ProductStatInDbWithAccount]` | READ | Obtiene estadísticas con datos contables. |
| `get_product_stats_with_transaction() -> list[ProductStatInDb]` | READ | Obtiene stats con transacciones pendientes. |
| `get_product_stat_by_id(stat_id) -> ProductStatInDb \| None` | READ | Obtiene por ID. |
| `set_no_transaction_product_stats(last_estimation: int) -> None` | BATCH UPDATE | Marca stats como procesados tras estimación. |
| `update_product_batch(stats: list[UpdateProductStatBatchItem]) -> None` | BATCH UPDATE `Σ` | Actualización masiva de estadísticas. |

---

#### ProductAccountsRepository

**Propósito**: Contabilidad de inventario por producto (el kárdex contable). Registra entradas y salidas de stock con seguimiento de costo promedio. Cuando `followTransaction` está activo, los ajustes directos de stock se bloquean a favor de operaciones transaccionales.

**Modelos**: `ProductAccountInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `create_product_account(account: ProductAccountInDb) -> ProductAccountInDb` | CREATE | Crea un registro contable de producto. |
| `get_product_account_by_product_and_branch_id(product_id, branch_id) -> ProductAccountInDb \| None` | READ | Obtiene datos contables de un producto en una sucursal. |
| `update_product_account_stock_and_cost(product_id, branch_id, **kwargs) -> ProductAccountInDb \| None` | UPDATE | Actualiza stock y costo promedio. |
| `add_product_account_stock(product_id, branch_id, **kwargs) -> ProductAccountInDb \| None` | SPECIAL | Incrementa stock (operación de entrada). |
| `substract_product_account_stock(product_id, branch_id, **kwargs) -> ProductAccountInDb \| None` | SPECIAL | Decrementa stock (operación de salida). |
| `get_product_accounts_by_product(product_id) -> list[ProductAccountInDb]` | READ | Obtiene historial contable completo de un producto. |

---

#### ProductSaleProfilesRepository

**Propósito**: Configuración de venta de producto por sucursal. Define cómo se vende un producto en cada sucursal (visibilidad, configuración específica). Une datos del producto en la respuesta.

**Modelos**: `ProductSaleProfileInDb`, `ProductSaleProfileInDbWithProduct`, `UpdateProductSaleProfile`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_product_sale_profiles(branch_id) -> list[ProductSaleProfileInDbWithProduct]` | READ | Obtiene todos los perfiles de venta de una sucursal con datos del producto. |
| `update_product_sale_profile_by_id(product_id, branch_id, profile) -> ProductSaleProfileInDb \| None` | UPDATE | Actualiza un perfil. |
| `delete_product_sale_profile_by_id(profile_id) -> ProductSaleProfileInDb \| None` | DELETE | Elimina un perfil. |

---

#### ProductTransactionsRepository `Σ`

**Propósito**: Historial de transacciones de productos. Registro de sólo lectura de todos los movimientos de inventario. También provee el método `estimate_product_stats` para el motor de estimación.

**Modelos**: `ProductTransactionInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_product_transactions(params: ProductTransactionFilterParams) -> list[ProductTransactionInDb]` | READ | Obtiene historial transaccional paginado. |
| `get_product_transaction_by_id(transaction_id) -> ProductTransactionInDb \| None` | READ | Obtiene por ID. |
| `estimate_product_stats(**kwargs)` | SPECIAL `Σ` | Dispara estimación de estadísticas vía agregación. |

---

#### UnitsRepository

**Propósito**: Unidades de medida (unidad, caja, kg, litro, etc.). Full CRUD para unidades de medición de inventario.

**Modelos**: `UnitInDb`, `CreateUnit`, `UpdateUnit`

| Método | CRUD | Descripción |
|---|---|---|
| `create_unit(unit: CreateUnit) -> UnitInDb` | CREATE | Crea una nueva unidad. |
| `get_all_units() -> list[UnitInDb]` | READ | Obtiene todas las unidades. |
| `get_unit_by_id(unit_id) -> UnitInDb \| None` | READ | Obtiene por ID. |
| `update_unit_by_id(unit_id, unit) -> UnitInDb \| None` | UPDATE | Actualiza una unidad. |
| `delete_unit_by_id(unit_id) -> UnitInDb \| None` | DELETE | Elimina una unidad. |

---

#### InventoriesRepository `△`

**Propósito**: Estado actual del inventario. Repositorio de sólo lectura con streaming que devuelve items de inventario vía generador asíncrono para una sucursal dada. También provee agregación de stock total.

**Modelos**: `InventoryInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_inventories_by_branch(branch_id) -> AsyncGenerator[InventoryInDb, None]` | READ `△` | Lectura con streaming vía generador asíncrono de todo el inventario de una sucursal. |
| `get_total_current_stock(branch_id) -> int` | READ `Σ` | Retorna el stock total sumado de una sucursal. |

---

### 4.2 Entradas y Salidas

#### EntryDocsRepository

**Propósito**: Documentos de entrada de mercancía (compras a proveedores, devoluciones entrantes). Capa de datos de sólo lectura. Los documentos de entrada son **creados** por el módulo `core/inventory/`.

**Modelos**: `EntryDocInDb`, `EntryHistoryInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_entry_docs() -> list[EntryDocInDb]` | READ | Obtiene todos los documentos de entrada. |
| `get_paginated_entry_docs(params: EntryDocFilterParams) -> list[EntryDocInDb]` | READ | Documentos de entrada paginados. |
| `get_entry_doc_by_id(doc_id) -> EntryDocInDb \| None` | READ | Obtiene por ID. |
| `get_entry_doc_by_doc_number(doc_number) -> EntryDocInDb \| None` | READ | Obtiene por número de documento. |
| `get_entry_doc_by_doc_number_and_supplier(supplier_id, doc_number) -> EntryDocInDb \| None` | READ | Obtiene por proveedor + número de documento. |
| `get_entry_history(params: EntryDocFilterParams) -> list[EntryHistoryInDb]` | HISTORY | Obtiene historial de entradas (nivel línea). |
| `get_entry_history_by_id_with_supplier(doc_id) -> EntryHistoryInDb \| None` | HISTORY | Obtiene línea de historial con info del proveedor. |
| `get_entry_history_by_doc_number_and_branch_id(doc_number, branch_id) -> EntryHistoryInDb \| None` | HISTORY | Obtiene línea de historial por documento y sucursal. |

---

#### EntryHistoriesRepository

**Propósito**: Historial detallado de entradas (nivel línea). Repositorio de sólo lectura que expone cada entrada individual de producto: qué producto, cantidad, costo, fecha y proveedor.

**Modelos**: `EntryHistoryInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_entry_history(params: EntryHistoryFilterParams) -> list[EntryHistoryInDb]` | READ | Obtiene líneas de historial de entrada con filtros. |
| `get_entry_history_by_id_with_supplier(doc_id) -> EntryHistoryInDb \| None` | READ | Obtiene línea de historial con info del proveedor. |
| `get_entry_docs_by_product_id(product_id) -> list[EntryHistoryInDb]` | READ | Obtiene todo el historial de entrada de un producto. |
| `get_entry_history_by_doc_number_and_branch_id(doc_number, branch_id) -> EntryHistoryInDb \| None` | READ | Obtiene por número de documento y sucursal. |

---

#### ExitDocsRepository

**Propósito**: Documentos de salida de mercancía (ventas a clientes, ajustes negativos). Capa de datos de sólo lectura. Los documentos de salida son **creados** por `core/inventory/` y `core/invoice_register/`.

**Modelos**: `ExitDocInDb`, `ExitHistoryInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_exit_docs() -> list[ExitDocInDb]` | READ | Obtiene todos los documentos de salida. |
| `get_paginated_exit_docs(params: ExitDocFilterParams) -> list[ExitDocInDb]` | READ | Documentos de salida paginados. |
| `get_exit_doc_by_id(doc_id) -> ExitDocInDb \| None` | READ | Obtiene por ID. |
| `get_exit_doc_by_doc_number(doc_number) -> ExitDocInDb \| None` | READ | Obtiene por número de documento. |
| `get_exit_doc_by_doc_number_and_client(client_id, doc_number) -> ExitDocInDb \| None` | READ | Obtiene por cliente + número de documento. |
| `get_exit_history(params: ExitDocFilterParams) -> list[ExitHistoryInDb]` | HISTORY | Obtiene historial de salidas (nivel línea). |
| `get_exit_history_by_id_with_client(doc_id) -> ExitHistoryInDb \| None` | HISTORY | Obtiene línea de historial con info del cliente. |
| `get_exit_history_by_doc_number_and_branch_id(doc_number, branch_id) -> ExitHistoryInDb \| None` | HISTORY | Obtiene por documento y sucursal. |

---

#### ExitHistoriesRepository

**Propósito**: Historial detallado de salidas (nivel línea). Repositorio de sólo lectura que expone cada salida de producto: producto, cantidad, precio de venta, fecha y cliente asociado.

**Modelos**: `ExitHistoryInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_exit_history(params: ExitHistoryFilterParams) -> list[ExitHistoryInDb]` | READ | Obtiene líneas de historial de salida con filtros. |
| `get_exit_doc_history_by_id_with_client(doc_id) -> ExitHistoryInDb \| None` | READ | Obtiene línea de historial con info del cliente. |
| `get_exit_history_by_doc_number_and_branch_id(doc_number, branch_id) -> ExitHistoryInDb \| None` | READ | Obtiene por número de documento y sucursal. |

---

#### AdjustEntriesRepository `⇢`

**Propósito**: Ajustes de entrada al inventario (incrementos manuales de stock). Implementación parcial — el create lo maneja `core/adjust_ledger/`. El update es un stub pendiente.

**Modelos**: `AdjustEntryInDb`, `UpdateAdjustEntry`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_adjust_entries(params: AdjustFilterParams) -> list[AdjustEntryInDb]` | READ | Obtiene ajustes de entrada con filtros. |
| `get_adjust_entry_by_id(entry_id) -> AdjustEntryInDb \| None` | READ | Obtiene por ID. |
| `get_adjust_entry_by_doc_number(doc_number, branch_id) -> AdjustEntryInDb \| None` | READ | Obtiene por número de documento y sucursal. |
| `update_adjust_entry_by_id(entry_id, entry) -> AdjustEntryInDb \| None` `⇢` | UPDATE | Stub pendiente (`NotImplementedError`). |
| `delete_adjust_entry_by_id(entry_id) -> AdjustEntryInDb \| None` | DELETE | Elimina un ajuste. |

---

#### AdjustExitsRepository `⇢`

**Propósito**: Ajustes de salida del inventario (decrementos manuales de stock). Implementación parcial — create y update son stubs.

**Modelos**: `AdjustExitInDb`, `CreateAdjustExit`, `UpdateAdjustExit`

| Método | CRUD | Descripción |
|---|---|---|
| `create_adjust_exit(exit: CreateAdjustExit) -> AdjustExitInDb` `⇢` | CREATE | Stub pendiente. |
| `get_all_adjust_exits(params: AdjustFilterParams) -> list[AdjustExitInDb]` | READ | Obtiene ajustes de salida con filtros. |
| `get_adjust_exit_by_id(exit_id) -> AdjustExitInDb \| None` | READ | Obtiene por ID. |
| `get_adjust_exit_by_doc_number(doc_number, branch_id) -> AdjustExitInDb \| None` | READ | Obtiene por número de documento y sucursal. |
| `update_adjust_exit_by_id(exit_id, exit) -> AdjustExitInDb \| None` `⇢` | UPDATE | Stub pendiente. |
| `delete_adjust_exit_by_id(exit_id) -> AdjustExitInDb \| None` | DELETE | Elimina un ajuste. |

---

### 4.3 Clientes y Transacciones

#### ClientsRepository `T`

**Propósito**: Administración de clientes. Full CRUD con número de cliente auto-asignado, búsqueda textual con generación de prefijos, soft delete, renombrado de grupos y operaciones financieras (creación de saldo inicial). Las operaciones de balance delegan a `core/client/process_create_client.py` que ejecuta **transacciones MongoDB**.

**Modelos**: `ClientInDb`, `CreateClient`, `UpdateClient`

| Método | CRUD | Descripción |
|---|---|---|
| `create_client(client: CreateClient) -> ClientInDb` | CREATE | Crea un cliente con número auto-asignado del `CounterManager`. |
| `create_initial_balance(client, initial_balance, branch_id, product_name) -> ClientInDb` | SPECIAL `T` | Crea saldo financiero inicial para un cliente (transacción MongoDB). |
| `create_multiple_initial_balance(balances: list[InitialBalanceClient]) -> list[ClientInDb]` | BATCH `T` | Saldo inicial masivo para múltiples clientes. |
| `get_all_clients(params: ClientFilterParams) -> list[ClientInDb]` | READ | Obtiene clientes con paginación/filtros. |
| `get_all_clients_with_balance(params: ClientFilterParams) -> list[ClientInDb]` | READ | Obtiene clientes con su saldo financiero actual. |
| `get_client_by_id(client_id) -> ClientInDb \| None` | READ | Obtiene por ID. |
| `get_client_by_card_id(card_id) -> ClientInDb \| None` | READ | Obtiene por código de tarjeta de fidelización. |
| `search_client_by_text(text_query) -> list[ClientInDb]` | SEARCH | Búsqueda textual con generación de prefijos. |
| `search_clients_with_balance(text_query) -> list[ClientInDb]` | SEARCH | Busca clientes incluyendo saldo financiero. |
| `update_client_by_id(client_id, client) -> ClientInDb \| None` | UPDATE | Actualiza un cliente. |
| `update_group(old_group, new_group) -> None` | SPECIAL | Renombra un grupo de clientes en todos los registros. |
| `delete_client_by_id(client_id) -> ClientInDb \| None` | DELETE | Soft delete de un cliente. |

---

#### ClientGroupsRepository

**Propósito**: Agrupación/segmentación de clientes. Full CRUD para organizar clientes en categorías (Mayoristas, Minoristas, VIP, etc.).

**Modelos**: `ClientGroupInDb`, `CreateClientGroup`, `UpdateClientGroup`

| Método | CRUD | Descripción |
|---|---|---|
| `create_client_group(group: CreateClientGroup) -> ClientGroupInDb` | CREATE | Crea un nuevo grupo. |
| `get_all_client_groups() -> list[ClientGroupInDb]` | READ | Obtiene todos los grupos. |
| `get_client_group_by_id(group_id) -> ClientGroupInDb \| None` | READ | Obtiene por ID. |
| `update_client_group_by_id(group_id, group) -> ClientGroupInDb \| None` | UPDATE | Actualiza un grupo. |
| `delete_client_group_by_id(group_id) -> ClientGroupInDb \| None` | DELETE | Elimina un grupo. |

---

#### ClientTransactionsRepository

**Propósito**: Historial de transacciones de clientes. Registro de sólo lectura de todos los movimientos contables de clientes (créditos, débitos, pagos, ajustes de saldo). Las transacciones son **creadas** por el motor `core/finance/`.

**Modelos**: `ClientTransactionInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_client_transactions(params: ClientTransactionFilterParams) -> list[ClientTransactionInDb]` | READ | Obtiene transacciones de clientes paginadas. |
| `get_client_transaction_by_id(transaction_id) -> ClientTransactionInDb \| None` | READ | Obtiene por ID. |

---

### 4.4 Órdenes, Facturas, Recibos y Devoluciones

#### OrdersRepository `Σ`

**Propósito**: Ciclo de vida de pedidos de venta. Los pedidos se crean como borradores, pueden actualizarse y luego **convertirse en facturas** por el módulo `core/order_register/`. Proporciona agregación por producto y análisis de demanda vs stock.

**Modelos**: `OrderInDb`, `CreateOrder`, `UpdateOrder`, `ProductSalesTotal`, `ProductStockDemand`

| Método | CRUD | Descripción |
|---|---|---|
| `create_draft_order(order: CreateOrder) -> OrderInDb` | CREATE | Crea un nuevo pedido borrador con número auto-asignado. |
| `get_paginated_orders(params: OrderFilterParams) -> list[OrderInDb]` | READ | Obtiene pedidos paginados con filtros de estado/fecha. |
| `get_products_in_orders(params: OrderFilterParams) -> list[ProductSalesTotal]` | READ `Σ` | Datos agregados de productos en pedidos (cantidades, totales). |
| `get_demand_vs_stock(params: OrderFilterParams) -> list[ProductStockDemand]` | READ `Σ` | Compara stock actual vs demanda de pedidos pendientes. |
| `get_order_by_id(order_id) -> OrderInDb \| None` | READ | Obtiene por ID. |
| `get_order_by_doc_number(doc_number) -> OrderInDb \| None` | READ | Obtiene por número de documento. |
| `update_order_draft_by_id(order_id, order) -> OrderInDb \| None` | UPDATE | Actualiza un pedido borrador. |
| `delete_order_draft_by_id(order_id) -> OrderInDb \| None` | DELETE | Elimina un pedido borrador. |

---

#### InvoicesRepository `Σ` `△` `⇢`

**Propósito**: Capa de datos de facturación. El repositorio más rico con agregación, streaming, totales, desglose por tipo de pago, ventas por producto, historial, resúmenes de portafolio e informes de facturas pendientes por sucursal. El **create** lo maneja `core/invoice_register/`. `update_invoice_by_id` es un stub pendiente.

**Modelos**: `InvoiceInDb`, `CreateInvoice`, `UpdateInvoice`, `InvoiceTotals`, `BranchPortfolioSummary`, `PendingInvoiceTotalsByBranch`, `ProductSalesTotal`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_invoices(params: InvoiceFilterParams) -> list[InvoiceInDb]` | READ | Obtiene facturas con paginación y filtros. |
| `get_all_invoices_by_product(product_id, params) -> list[InvoiceInDb]` | READ | Obtiene facturas que contienen un producto específico. |
| `get_all_product_sales(params: InvoiceFilterParams) -> list[ProductSalesTotal]` | READ `Σ` | Ventas agregadas por producto desde facturas. |
| `get_all_invoices_stream(params: InvoiceFilterParams) -> AsyncGenerator[InvoiceInDb, None]` | READ `△` | Streaming de facturas vía generador asíncrono. |
| `get_totals_from_invoices(params: InvoiceFilterParams) -> InvoiceTotals` | READ `Σ` | Totales agregados de facturación (monto, impuesto, descuentos). |
| `get_totals_invoices_by_payment_type(params: TotalsFilterParams) -> list[InvoiceTotals]` | READ `Σ` | Totales desglosados por tipo de pago. |
| `get_invoice_by_id(invoice_id) -> InvoiceInDb \| None` | READ | Obtiene por ID. |
| `get_invoice_by_doc_number(doc_number) -> InvoiceInDb \| None` | READ | Obtiene por número de documento. |
| `get_invoice_by(client_id, offset, limit) -> list[InvoiceInDb]` | READ | Obtiene facturas de un cliente específico. |
| `get_pending_to_paid_invoices(client_id) -> list[InvoiceInDb]` | READ | Obtiene facturas pendientes de pago de un cliente. |
| `update_invoice_by_id(invoice_id, invoice) -> InvoiceInDb \| None` `⇢` | UPDATE | Stub pendiente. |
| `get_invoice_history(params: HistoryClientParams) -> list[InvoiceInDb]` | HISTORY | Obtiene historial de facturas. |
| `get_invoice_summary(**kwargs) -> list[BranchPortfolioSummary]` | READ `Σ` | Resumen de portafolio por sucursal. |
| `get_pending_invoice_totals_by_branch(**kwargs) -> list[PendingInvoiceTotalsByBranch]` | READ `Σ` | Totales de facturas pendientes agrupados por sucursal. |

---

#### ReceiptsRepository `Σ` `⇢`

**Propósito**: Capa de datos de recibos de pago. Gestiona consultas de recibos, totales agregados por método de pago, historial y resúmenes de montos aplicados por sucursal. El **create** lo maneja `core/receipt_register/`. Create/update son stubs pendientes.

**Modelos**: `ReceiptInDb`, `CreateReceipt`, `UpdateReceipt`, `ReceiptTotal`, `BranchAppliedReceiptsAmountsSummary`

| Método | CRUD | Descripción |
|---|---|---|
| `create_receipt(receipt: CreateReceipt) -> ReceiptInDb` `⇢` | CREATE | Stub pendiente. |
| `get_all_receipts(params: ReceiptFilterParams) -> list[ReceiptInDb]` | READ | Obtiene recibos paginados. |
| `get_receipts_by_invoice_id(invoice_id) -> list[ReceiptInDb]` | READ | Obtiene recibos de una factura. |
| `get_totals_from_receipts(params: ReceiptFilterParams) -> ReceiptTotal` | READ `Σ` | Totales agregados de recibos. |
| `get_totals_from_receipts_by_payment_method(params: TotalsFilterParams) -> list[ReceiptTotal]` | READ `Σ` | Totales desglosados por método de pago. |
| `get_receipt_by_id(receipt_id) -> ReceiptInDb \| None` | READ | Obtiene por ID. |
| `get_receipt_by_doc_number(doc_number) -> ReceiptInDb \| None` | READ | Obtiene por número de documento. |
| `update_receipt_by_id(receipt_id, receipt) -> ReceiptInDb \| None` `⇢` | UPDATE | Stub pendiente. |
| `delete_receipt_by_id(receipt_id) -> ReceiptInDb \| None` | DELETE | Elimina un recibo. |
| `get_receipt_history(params: HistoryClientParams) -> list[ReceiptInDb]` | HISTORY | Obtiene historial de recibos. |
| `get_branch_receipt_amounts_summary(**kwargs) -> list[BranchAppliedReceiptsAmountsSummary]` | READ `Σ` | Resumen de montos aplicados por sucursal. |

---

#### DevolutionsRepository

**Propósito**: Devoluciones de productos. Full CRUD con número de documento auto-asignado. Soporta consultas de devoluciones activas (pendientes de confirmación) y seguimiento de historial.

**Modelos**: `DevolutionInDb`, `CreateDevolution`, `UpdateDevolution`

| Método | CRUD | Descripción |
|---|---|---|
| `create_devolution(devolution: CreateDevolution) -> DevolutionInDb` | CREATE | Crea una nueva devolución con número de doc auto-asignado. |
| `get_all_devolutions(params: DevolutionFilterParams) -> list[DevolutionInDb]` | READ | Obtiene todas las devoluciones con filtros. |
| `get_all_active_devolutions(params: DevolutionFilterParams) -> list[DevolutionInDb]` | READ | Obtiene devoluciones activas (no confirmadas). |
| `get_devolution_by_id(devolution_id) -> DevolutionInDb \| None` | READ | Obtiene por ID. |
| `get_devolution_by_invoice_id(invoice_id, client_id) -> list[DevolutionInDb]` | READ | Obtiene devoluciones de una factura. |
| `get_devolution_by_doc_number(doc_number) -> DevolutionInDb \| None` | READ | Obtiene por número de documento. |
| `update_devolution_by_id(devolution_id, devolution) -> DevolutionInDb \| None` | UPDATE | Actualiza una devolución. |
| `delete_devolution_by_id(devolution_id) -> DevolutionInDb \| None` | DELETE | Elimina una devolución. |
| `get_devolution_history(params: HistoryClientParams) -> list[DevolutionInDb]` | HISTORY | Obtiene historial de devoluciones. |

---

### 4.5 Transferencias

#### TransfersRepository

**Propósito**: Transferencias de stock entre sucursales. Repositorio de **sólo lectura**. Las transferencias son creadas y gestionadas por `core/transfer_manager/` que maneja la máquina de estados completa (crear, recibir, cancelar).

**Modelos**: `TransferInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `get_all_transfers(params: TransferFilterParams) -> list[TransferInDb]` | READ | Obtiene todas las transferencias con filtros. |
| `get_transfer_by_id(transfer_id) -> TransferInDb \| None` | READ | Obtiene por ID. |
| `get_transfer_by_doc_number(doc_number) -> TransferInDb \| None` | READ | Obtiene por número de documento. |

---

### 4.6 Proveedores

#### SuppliersRepository

**Propósito**: Administración de proveedores. Full CRUD con número auto-asignado, búsqueda textual con generación de prefijos y soft delete.

**Modelos**: `SupplierInDb`, `CreateSupplier`, `UpdateSupplier`

| Método | CRUD | Descripción |
|---|---|---|
| `create_supplier(supplier: CreateSupplier) -> SupplierInDb` | CREATE | Crea un proveedor con número auto-asignado. |
| `get_all_suppliers() -> list[SupplierInDb]` | READ | Obtiene todos los proveedores. |
| `get_supplier_by_id(supplier_id) -> SupplierInDb \| None` | READ | Obtiene por ID. |
| `search_supplier_by_text(text_query) -> list[SupplierInDb]` | SEARCH | Búsqueda textual con generación de prefijos. |
| `update_supplier_by_id(supplier_id, supplier) -> SupplierInDb \| None` | UPDATE | Actualiza un proveedor. |
| `delete_supplier_by_id(supplier_id) -> SupplierInDb \| None` | DELETE | Soft delete de un proveedor. |

---

### 4.7 Gastos

#### ExpensesRepository `Σ`

**Propósito**: Registro de gastos operativos. Full CRUD con número auto-asignado, búsqueda por número de documento, seguimiento de pagos parciales (`add_to_amount_paid`) y resumen agregado por rango de fechas.

**Modelos**: `ExpenseInDb`, `CreateExpense`, `UpdateExpense`

| Método | CRUD | Descripción |
|---|---|---|
| `create_expense(expense: CreateExpense) -> ExpenseInDb` | CREATE | Crea un gasto con número auto-asignado. |
| `get_all_expenses(params: ExpensesFilterParams) -> list[ExpenseInDb]` | READ | Obtiene todos los gastos con filtros. |
| `get_expense_by_id(expense_id) -> ExpenseInDb \| None` | READ | Obtiene por ID. |
| `get_expense_by_doc_number(doc_number) -> ExpenseInDb \| None` | READ | Obtiene por número de documento. |
| `update_expense_by_id(expense_id, expense) -> ExpenseInDb \| None` | UPDATE | Actualiza un gasto. |
| `delete_expense_by_id(expense_id) -> ExpenseInDb \| None` | DELETE | Elimina un gasto. |
| `add_to_amount_paid(expense_id, amount_paid) -> ExpenseInDb \| None` | SPECIAL | Registra un pago parcial hacia un gasto. |
| `get_expenses_summary_in_range(start_date, end_date) -> dict[str, Any]` | READ `Σ` | Resumen de gastos agregado por rango de fechas. |

---

#### ExpenseCategoriesRepository

**Propósito**: Categorización de gastos. Full CRUD para clasificar gastos en rubros contables.

**Modelos**: `ExpenseCategoryInDb`, `CreateExpenseCategory`, `UpdateExpenseCategory`

| Método | CRUD | Descripción |
|---|---|---|
| `create_expense_category(cat: CreateExpenseCategory) -> ExpenseCategoryInDb` | CREATE | Crea una nueva categoría. |
| `get_all_expense_categories() -> list[ExpenseCategoryInDb]` | READ | Obtiene todas las categorías. |
| `get_expense_category_by_id(category_id) -> ExpenseCategoryInDb \| None` | READ | Obtiene por ID. |
| `update_expense_category_by_id(category_id, cat) -> ExpenseCategoryInDb \| None` | UPDATE | Actualiza una categoría. |
| `delete_expense_category_by_id(category_id) -> ExpenseCategoryInDb \| None` | DELETE | Elimina una categoría. |

---

### 4.8 Reportes y Dashboard

#### DailySummariesRepository

**Propósito**: Resúmenes diarios de operaciones. Vista consolidada histórica día a día de la actividad del negocio. Sólo lectura/creación — los resúmenes son generados por módulos core.

**Modelos**: `DailySummaryInDb`, `CreateDailySummary`

| Método | CRUD | Descripción |
|---|---|---|
| `create_daily_summary(summary: CreateDailySummary) -> DailySummaryInDb` | CREATE | Crea una instantánea de resumen diario. |
| `get_all_daily_summaries(params: DailySummaryFilterParams) -> list[DailySummaryInDb]` | READ | Obtiene resúmenes con filtros. |
| `get_daily_summary_by_start_date_range(startDate, endDate) -> list[DailySummaryInDb]` | READ | Obtiene resúmenes en un rango de fechas. |
| `get_daily_summary_by_id(summary_id) -> DailySummaryInDb \| None` | READ | Obtiene por ID. |
| `get_daily_summary_by_date_id(date_id) -> DailySummaryInDb \| None` | READ | Obtiene por ID de fecha. |

---

#### ExecutiveSummariesRepository

**Propósito**: Resúmenes ejecutivos. Datos agregados de nivel gerencial para toma de decisiones estratégicas. Soporta filtrado por tipo (diario, semanal, mensual).

**Modelos**: `ExecutiveSummaryInDb`, `CreateExecutiveSummary`, `SummaryType`

| Método | CRUD | Descripción |
|---|---|---|
| `create_executive_summary(summary: CreateExecutiveSummary) -> ExecutiveSummaryInDb` | CREATE | Crea un resumen ejecutivo. |
| `get_all_executive_summaries(params: ExecutiveSummaryFilterParams) -> list[ExecutiveSummaryInDb]` | READ | Obtiene resúmenes con filtros de tipo y fecha. |
| `get_executive_summary_by_id(summary_id) -> ExecutiveSummaryInDb \| None` | READ | Obtiene por ID. |
| `get_executive_summary_by_date_id_and_type(date_id, type: SummaryType) -> ExecutiveSummaryInDb \| None` | READ | Obtiene por ID de fecha y tipo de resumen. |

---

### 4.9 Sistema y Utilidades

#### BranchesRepository

**Propósito**: Gestión de sucursales. Full CRUD con invalidación de caché basada en ETags para datos dependientes de sucursal.

**Modelos**: `BranchInDb`, `CreateBranch`, `UpdateBranch`

| Método | CRUD | Descripción |
|---|---|---|
| `create_branch(branch: CreateBranch) -> BranchInDb` | CREATE | Crea una nueva sucursal. Invalida ETags de sucursales. |
| `get_all_branches() -> list[BranchInDb]` | READ | Obtiene todas las sucursales. |
| `get_all_commerce_branches() -> list[BranchInDb]` | READ | Obtiene sólo sucursales de tipo comercio. |
| `get_branch_by_id(branch_id) -> BranchInDb \| None` | READ | Obtiene por ID. |
| `update_branch_by_id(branch_id, branch) -> BranchInDb \| None` | UPDATE | Actualiza una sucursal. Invalida ETags. |
| `delete_branch_by_id(branch_id) -> BranchInDb \| None` | DELETE | Hard delete de una sucursal. |

---

#### IntegrationsRepository

**Propósito**: Configuración de integraciones externas (Telegram, notificaciones, etc.). Usa upsert en creación para evitar duplicados. Sin delete en sentido CRUD tradicional.

**Modelos**: `IntegrationInDb`, `CreateIntegration`, `UpdateIntegration`

| Método | CRUD | Descripción |
|---|---|---|
| `create_integration_if_absent(integration: CreateIntegration) -> IntegrationInDb` | UPSERT | Crea sólo si no existe; si existe, retorna el existente. |
| `get_all_integrations() -> list[IntegrationInDb]` | READ | Obtiene todas las integraciones. |
| `get_integration_by_id(integration_id) -> IntegrationInDb \| None` | READ | Obtiene por ID. |
| `update_integration_by_id(integration_id, integration) -> IntegrationInDb \| None` | UPDATE | Actualiza configuración. |
| `delete_integration_by_id(integration_id) -> IntegrationInDb \| None` | DELETE | Elimina una integración. |

---

#### ExpirationLogsRepository `Σ`

**Propósito**: Seguimiento de caducidades de productos. Gestiona alertas de caducidad, creación batch y verificación de proximidad (`has_near_expiration_date`). Útil para inventario perecedero.

**Modelos**: `ExpirationLogInDb`, `CreateExpirationLog`, `UpdateExpirationLog`

| Método | CRUD | Descripción |
|---|---|---|
| `create_expiration_log(log: CreateExpirationLog) -> ExpirationLogInDb` | CREATE | Crea una alerta de caducidad individual. |
| `create_many_expiration_logs(logs: list[CreateExpirationLog])` | BATCH CREATE | Crea múltiples alertas a la vez. |
| `get_all_expiration_logs(params: ExpirationLogFilterParams) -> list[ExpirationLogInDb]` | READ | Obtiene todas las alertas con filtros. |
| `get_expiration_log_by_id(log_id) -> ExpirationLogInDb \| None` | READ | Obtiene por ID. |
| `update_expiration_log_by_id(log_id, log) -> ExpirationLogInDb \| None` `⇢` | UPDATE | Stub pendiente. |
| `delete_expiration_log_by_id(log_id) -> ExpirationLogInDb \| None` | DELETE | Elimina una alerta. |
| `has_near_expiration_date(target_date, branch_id) -> bool` | SPECIAL `Σ` | Verifica si hay productos próximos a vencer en una sucursal. |

---

#### CountersRepository `T`

**Propósito**: Gestión atómica de contadores para numeración de documentos. Provee operaciones de incremento y set **seguras en transacciones**. Usado por `CounterManager` para generar números secuenciales de facturas, recibos, pedidos, devoluciones, productos, usuarios, clientes, transferencias, proveedores, ajustes y gastos.

**Modelos**: `CounterInDb`

| Método | CRUD | Descripción |
|---|---|---|
| `increment_counter(counter_name, session: Any) -> CounterInDb` | ATOMIC INC `T` | Incrementa atómicamente un contador dentro de una sesión MongoDB. |
| `set_counter(counter_name, value: int, session: Any) -> CounterInDb` | SET `T` | Establece un contador a un valor específico dentro de una sesión. |

---

#### CoreSettingsRepository

**Propósito**: Configuraciones centrales del sistema y licenciamiento. Gestiona valores de configuración de la aplicación. Incluye verificación de token EdDSA durante la creación por seguridad.

**Modelos**: `CoreSettingInDb`, `CreateCoreSetting`, `DecodedCoreSetting`, `UpdateCoreSetting`

| Método | CRUD | Descripción |
|---|---|---|
| `create_core_setting(setting: CreateCoreSetting) -> DecodedCoreSetting \| None` | CREATE | Crea una configuración con verificación de super token. |
| `get_all_core_settings() -> list[CoreSettingInDb]` | READ | Obtiene todas las configuraciones. |
| `get_core_setting_by_id(setting_id) -> CoreSettingInDb \| None` | READ | Obtiene por ID. |
| `update_core_setting_by_nickname(setting_id, setting) -> CoreSettingInDb \| None` | UPDATE | Actualiza una configuración por su nickname. |
| `delete_core_setting_by_id(setting_id) -> CoreSettingInDb \| None` | DELETE | Elimina una configuración. |

---

### 4.10 Autenticación y Usuarios

#### UsersRepository

**Propósito**: Administración de usuarios del sistema. Ciclo completo de usuario con hashing de contraseñas (argon2 vía `SysPasswordHasher`), consultas de usuarios activos por sucursal, número de usuario auto-asignado y seguimiento de usuarios inactivos.

**Modelos**: `UserInDb`, `UserInDbWithRole`, `CreateUser`, `UpdateUser`

| Método | CRUD | Descripción |
|---|---|---|
| `create_user_directly(new_user: UserInDb) -> UserInDb` | CREATE | Crea un usuario desde un objeto `UserInDb` pre-construido (inserción cruda). |
| `create_user(user: CreateUser) -> UserInDb` | CREATE | Crea un usuario con hashing de contraseña y número auto-asignado. |
| `get_all_users() -> list[UserInDbWithRole]` | READ | Obtiene todos los usuarios con su rol. |
| `get_all_active_users_by_branch_id(branch_id) -> list[UserInDbWithRole]` | READ | Obtiene usuarios activos filtrados por sucursal. |
| `get_all_inactive_users() -> list[UserInDb]` | READ | Obtiene todos los usuarios inactivos (cacheado para verificaciones de auth). |
| `get_user_by_id(user_id) -> UserInDbWithRole \| None` | READ | Obtiene un usuario con rol por ID. |
| `update_user_by_id(user_id, user) -> UserInDb \| None` | UPDATE | Actualiza un usuario. |
| `change_password(user_id, password) -> UserInDb \| None` | SPECIAL | Hashea y actualiza la contraseña de un usuario. |
| `delete_user_by_id(user_id) -> UserInDb \| None` | DELETE | Elimina un usuario. |

---

#### UserRolesRepository

**Propósito**: Control de acceso basado en roles. Full CRUD para definir niveles de permiso asignables a usuarios.

**Modelos**: `UserRoleInDb`, `CreateUserRole`, `UpdateUserRole`

| Método | CRUD | Descripción |
|---|---|---|
| `create_user_role(role: CreateUserRole) -> UserRoleInDb` | CREATE | Crea un nuevo rol. |
| `get_all_user_roles() -> list[UserRoleInDb]` | READ | Obtiene todos los roles. |
| `get_user_role_by_id(role_id) -> UserRoleInDb \| None` | READ | Obtiene por ID. |
| `update_user_role_by_id(role_id, role) -> UserRoleInDb \| None` | UPDATE | Actualiza un rol. |
| `delete_user_role_by_id(role_id) -> UserRoleInDb \| None` | DELETE | Elimina un rol. |

---

## 5. Módulos Core de Negocio

Los procesos de negocio complejos y transversales viven en `src/kardex/core/`. Estos módulos orquestan múltiples repositorios dentro de una sola transacción de negocio, frecuentemente usando **transacciones MongoDB** para atomicidad.

| Módulo | Ruta | Propósito |
|---|---|---|
| **Adjust Ledger** | `core/adjust_ledger/` | Procesa ajustes de inventario (entradas y salidas) con conciliación de stock |
| **Client** | `core/client/` | Creación de cliente con saldo inicial (crea factura + movimiento financiero en transacción) |
| **Counter Manager** | `core/counter_manager/` | Numeración secuencial centralizada: números de factura, recibo, pedido, devolución, producto, usuario, cliente, transferencia, proveedor, ajuste y gasto |
| **Default Values** | `core/default_values/` | Inicializa datos por defecto del sistema en el primer arranque |
| **Devolution Register** | `core/devolution_register/` | Procesa devoluciones de productos con restauración de stock |
| **Finance** | `core/finance/` | Motor financiero de clientes (`ClientFinanceEngine.process_movement()`) — maneja créditos, débitos y actualizaciones de saldo |
| **Imports** | `core/imports/` | Lógica de importación de datos para operaciones masivas |
| **Inventory** | `core/inventory/` | Gestión central de inventario — procesa entradas y salidas de stock |
| **Invoice Register** | `core/invoice_register/` | Creación de facturas con deducción automática de stock del inventario |
| **On Start Actions** | `core/on_start_actions/` | Rutinas de inicialización al arranque |
| **Order Register** | `core/order_register/` | Lógica de conversión de pedido a factura |
| **Product Ledger** | `core/product_ledger/` | Libro contable de productos (kárdex) |
| **Product Register** | `core/product_register/` | Creación de perfil completo de producto (producto + cuentas + perfiles de venta en todas las sucursales) |
| **Receipt Register** | `core/receipt_register/` | Procesamiento de recibos con liquidación de pago de factura |
| **Report Manager** | `core/report_manager/` | Motor de generación de reportes |
| **Role Manager** | `core/role_manager/` | Lógica de control de acceso basado en roles |
| **Security** | `core/security/` | `SysPasswordHasher` (argon2), `TokenManager` (JWT con HS256 + EdDSA) |
| **Transfer Manager** | `core/transfer_manager/` | Máquina de estados de transferencia de stock entre sucursales (crear, recibir, cancelar) |
| **Lite Product Register** | `lite/core/product_register/` | Flujo ligero/especializado de registro de productos |

---

## 6. Colecciones MongoDB

Todo el acceso a base de datos pasa por clases de colección en `src/kardex/services/mongo_collections/v1/`. Cada clase extiende `BaseMongoCollection` y define:

- `collection_name: str` — el nombre de la colección MongoDB
- Métodos CRUD personalizados usando `self._collection` (Motor `AsyncCollection`)

**34 colecciones MongoDB** (indexadas alfabéticamente; las dos primeras son usadas internamente por el motor financiero):

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

## 7. Herramientas y Utilidades

Todas las herramientas viven en `src/kardex/tools/`.

### TimeTools

Utilidad estática para gestión de timestamps. Zona horaria: `America/Managua`.

| Método | Descripción |
|---|---|
| `get_now_in_milliseconds() -> int` | Hora UTC actual en milisegundos |
| `seconds_until_next_midnight() -> int` | Segundos restantes hasta la próxima medianoche |
| `get_now_in_100days_in_milliseconds() -> int` | Hora actual + 100 días en milisegundos |

### UuidTool

Utilidad estática para generación de UUIDs.

| Método | Descripción |
|---|---|
| `generate_uuid() -> str` | Retorna `str(uuid.uuid4())` |

### SearchTools

Utilidad de búsqueda textual para búsqueda por prefijos en MongoDB.

| Función | Descripción |
|---|---|
| `generate_prefixes(text, min_size, max_size) -> list[str]` | Genera prefijos de palabras para búsqueda textual (ej: "Hola Mundo" → `["ho", "hol", "hola", "mu", "mun", "mund", "mundo"]`) |

### QueryBuilder

Utilidad de construcción de filtros MongoDB.

| Función | Descripción |
|---|---|
| `build_query(date_field, **kwargs) -> QueryResult` | Construye un dict de filtro MongoDB + offset/limit a partir de keyword args (`clientId`, `supplierId`, `branchId`, `status`, `startDate`, `endDate`, `createdBy`). Retorna `QueryResult(query, offset, limit)`. |

### EtagTool

Singleton de caché para HTTP caching basado en ETags. Rastrea tags de invalidación para sucursales, proyecciones y estimaciones.

| Método | Descripción |
|---|---|
| `set_tag(key, branch_id)` | Establece un valor ETag |
| `get_etag(key) -> str \| None` | Obtiene un valor ETag |
| `get_branches_etag() -> str` | Obtiene ETag compuesto para todas las sucursales |
| `update_branches_etags(action)` | Invalida ETags de sucursales en create/update/delete |

### BranchesTool

Singleton de caché en memoria de sucursales.

| Método | Descripción |
|---|---|
| `refresh_current_branches() -> None` | Refresca caché de sucursales desde DB |
| `get_branch_by_id(branch_id) -> BranchInDb \| None` | Obtiene una sucursal cacheada por ID |

### IntegrationTool

Singleton de caché para la configuración de integración actual.

| Método | Descripción |
|---|---|
| `get_current_integration() -> IntegrationInDb \| None` | Obtiene integración cacheada |
| `refresh_current_integration() -> None` | Refresca caché desde DB |

### UsersTool

Singleton de caché de usuarios inactivos (usado por el middleware de auth para rechazo rápido).

| Método | Descripción |
|---|---|
| `refresh_inactive_users() -> None` | Refresca caché de usuarios inactivos |
| `get_inactive_user_by_id(user_id) -> UserInDb \| None` | Verifica si un usuario está inactivo |

---

## 8. Parámetros de Filtro

Clases Pydantic tipadas para construir consultas MongoDB de forma segura. Ubicadas en `src/kardex/repos/v1/common/filter_params/`.

| Clase | Campos | Usado por |
|---|---|---|
| `BaseFilterParams` | `offset: int = 0`, `limit: int = 50` | Clase base para la mayoría |
| `ProductFilterParams` | Base + `branchId`, `startDate`, `endDate`, `paymentMethod`, `nePaymentMethod` | `ProductsRepository` |
| `ClientFilterParams` | Extiende BaseFilterParams | `ClientsRepository` |
| `ClientTransactionFilterParams` | + método `to_query()` | `ClientTransactionsRepository` |
| `DailySummaryFilterParams` | Extiende BaseFilterParams | `DailySummariesRepository` |
| `DevolutionFilterParams` | Extiende BaseFilterParams | `DevolutionsRepository` |
| `EntryDocFilterParams` | `offset`, `limit`, `branch_id`, `supplierId`, `startDate`, `endDate` | `EntryDocsRepository` |
| `EntryHistoryFilterParams` | + `to_query_params()` | `EntryHistoriesRepository` |
| `ExitDocFilterParams` | `offset`, `limit`, `branch_id`, `clientId`, `startDate`, `endDate` | `ExitDocsRepository` |
| `ExitHistoryFilterParams` | + `to_query_params()` | `ExitHistoriesRepository` |
| `ExpirationLogFilterParams` | Extiende BaseFilterParams | `ExpirationLogsRepository` |
| `ExpensesFilterParams` | + `to_query_params()` | `ExpensesRepository` |
| `InvoiceFilterParams` | Base + rango de fechas + `byPaidAt` | `InvoicesRepository` |
| `AdjustFilterParams` | Extiende InvoiceFilterParams | `AdjustEntriesRepository`, `AdjustExitsRepository` |
| `OrderFilterParams` | Base + `branchId`, `status`, `startDate`, `endDate` | `OrdersRepository` |
| `ProductStatFilterParams` / `ReadProductStatFilterParams` | Parámetros de consulta de agregación | `ProductStatsRepository` |
| `ProductTransactionFilterParams` | Extiende BaseFilterParams | `ProductTransactionsRepository` |
| `ReceiptFilterParams` | Extiende BaseFilterParams | `ReceiptsRepository` |
| `TransferFilterParams` | Extiende BaseFilterParams | `TransfersRepository` |
| `ExecutiveSummaryFilterParams` | Base + `type`, `startDate`, `endDate` | `ExecutiveSummariesRepository` |
| `TotalsFilterParams` | + filtrado por tipo de pago | `InvoicesRepository`, `ReceiptsRepository` |

**History Params** (`common/models/history_params.py`): `HistoryParams`, `HistoryBranchParams`, `HistoryClientParams` — con `to_query_params()` para construir consultas de rango de fechas en MongoDB.

---

## 9. Modelos Comunes

Modelos de dominio compartidos en `src/kardex/repos/v1/common/models/`.

| Modelo | Propósito |
|---|---|
| `SaleItem` | Línea de factura (producto, cantidad, precio, descuento, totales) |
| `ProductItem` | Referencia de producto dentro de un item de venta |
| `ClientInfo` | Info de cliente embebida en documentos |
| `UserInfo` | Info de usuario embebida en documentos |
| `CommercialBranchDetail` | Detalle de sucursal de tipo comercio |
| `InventoryBranchDetail` | Detalle de sucursal de tipo inventario |
| `TransferItem` | Línea de transferencia |
| `EntryItem` | Línea de documento de entrada |
| `ExitItem` | Línea de documento de salida |
| `Coordinates` | Coordenadas GPS |
| `ProductStockDemand` | Resultado de análisis stock vs demanda |
| `ProductSalesTotal` | Total de ventas agregado por producto |
| `PaymentType` | Alias de tipo literal para strings de método de pago |

---

## 10. Excepciones

Todas las excepciones de negocio heredan de `KardexException` (`tools/kardex_exceptions.py`). La capa FastAPI las mapea a códigos HTTP en `app/regis_exception_handlers.py`.

| Excepción | Descripción |
|---|---|
| `KardexException` | Excepción base para todos los errores de dominio |
| `InsufficientBalanceError` | El cliente no tiene crédito/fondos suficientes |
| `BranchNotFound` | La sucursal referenciada no existe |
| `DocumentAlreadyExists` | Número de documento duplicado detectado |
| `ProductNotFound` | El producto referenciado no existe |
| `ClientNotFound` | El cliente referenciado no existe |
| `ReceiptNotFound` | El recibo referenciado no existe |
| `ReceiptAlreadyDeleted` | Intento de eliminar un recibo ya eliminado |
| `SameBranchTransferError` | Transferencia entre la misma sucursal origen y destino |
| `InvalidOperation` | Operación de negocio inválida |
| `DirectStockAdjustmentBlocked` | Modificación directa de stock bloqueada cuando `followTransaction` está activo |
| `MongoMigrationException` | Error de migración de índices/datos MongoDB |
| `NotModified` | Soporte HTTP 304 (en `tools/app_exceptions.py`) |

---

## 11. Ejemplo de Uso

```python
from kardex.repos.v1.products.products_repository import ProductsRepository
from kardex.repos.v1.products.models.product_model import CreateProduct
from kardex.repos.v1.clients.clients_repository import ClientsRepository
from kardex.repos.v1.clients.models.client_model import CreateClient
from kardex.repos.v1.invoices.invoices_repository import InvoicesRepository
from kardex.repos.v1.common.filter_params.invoice_filter_params import InvoiceFilterParams
from kardex.core.counter_manager import CounterManager
from kardex.tools.kardex_exceptions import InsufficientBalanceError

async def ejemplo_flujo() -> None:
    # 1. Obtener instancias de repositorios (singletons)
    products_repo = ProductsRepository.get_instance()
    clients_repo = ClientsRepository.get_instance()
    invoices_repo = InvoicesRepository.get_instance()

    # 2. Crear un producto
    nuevo_producto = await products_repo.create_product(CreateProduct(
        name="Widget Pro",
        code="WGT-001",
        category="Electrónica",
    ))

    # 3. Crear un cliente
    nuevo_cliente = await clients_repo.create_client(CreateClient(
        name="Acme Corp",
        phone="50588889999",
        group="Corporativo",
    ))

    # 4. Consultar productos en una sucursal (streaming para inventario grande)
    async for producto in products_repo.get_all_product_in_branch_streamed(
        ProductFilterParams(branchId="sucursal-001")
    ):
        print(f"Producto: {producto['name']}, Stock: {producto['currentStock']}")

    # 5. Obtener totales de facturación
    totales = await invoices_repo.get_totals_from_invoices(
        InvoiceFilterParams(startDate=1717200000000, endDate=1719878400000)
    )
    print(f"Total facturado: {totales.totalAmount} centavos")

    # 6. Generar un número de documento
    counter = CounterManager.get_instance()
    sig_factura = await counter.next_invoice_number()
    print(f"Siguiente número de factura: {sig_factura}")

    # 7. Manejar excepciones de negocio
    try:
        # ... alguna operación que podría fallar
        pass
    except InsufficientBalanceError as e:
        print(f"Cliente sin saldo suficiente: {e}")
    except ProductNotFound as e:
        print(f"Producto no encontrado: {e}")
```

---

## Resumen Estadístico

| Métrica | Cantidad |
|---|---|
| Repositorios totales | **35** |
| Colecciones MongoDB | **34** (+ 1 para cuentas internas) |
| Módulos Core de Negocio | **19** |
| Clases de Parámetros de Filtro | **21** |
| Modelos Compartidos | **13** |
| Repositorios con Full CRUD | ~18 |
| Repositorios de sólo lectura | 7 |
| Repositorios con Streaming (`△`) | 3 |
| Repositorios con Agregación (`Σ`) | 6 |
| Repositorios con Stubs pendientes (`⇢`) | 4 |
| Repositorios Transaccionales (`T`) | 3 |
| Tipos de Excepciones de Negocio | **13** |
| Clases de Herramientas/Utilidades | **9** |
| Uso del Patrón Singleton | Universal (todos Repos, DataSources, Collections, Tools) |
| Patrón DI | Inyección por constructor, cableado manual |
| ORM | Ninguno — PyMongo (Motor) crudo con operaciones dict |
| Validación de Datos | Pydantic en el límite del Repository |
| Zona Horaria | `America/Managua` |
