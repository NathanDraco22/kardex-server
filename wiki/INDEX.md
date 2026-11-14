# INDEX — Contexto rápido de `kardex-server`

Punto de entrada de la wiki del backend. **Lee esto antes de explorar el código.** Aquí está la estructura, qué hace cada carpeta y los enlaces para profundizar solo en lo que necesites.

> Si llegaste aquí desde [`../AGENTS.md`](../AGENTS.md): estás en el lugar correcto. Sigue con la sección que corresponda a tu tarea.

---

## 1. Qué es este proyecto

`kardex-server` es el backend empresarial de **Kardex App**: kárdex transaccional, facturación, inventario, compras, cuentas por cobrar, gastos y reportes. Está construido con **Python + FastAPI + MongoDB asíncrono** bajo **Onion Architecture**, con el dominio puro en `packages/kardex-business`.

| Dato | Valor |
| :--- | :--- |
| Rama de trabajo | `main` |
| Entrada HTTP | `app/main.py` → prefijo global `/api/v1` |
| Base de datos | MongoDB, base `LedgerDB` (env `DB_NAME`) |
| Modo dual | `LITE_MODE` (reglas de inventario/facturación distintas) |
| Paquete de dominio | `packages/kardex-business/src/kardex/` |

---

## 2. Mapa de un vistazo

| Carpeta | Qué hace |
| :--- | :--- |
| `app/` | Capa web FastAPI (delgada). Routers, controllers, middleware, scheduler y servicios externos. |
| `app/api/v1/` | Un subdirectorio por módulo: `<modulo>_router.py` + `<modulo>_controller.py`. |
| `app/app_middleware/depends/` | Guards: JWT, API Key, super-token y contexto de tenant. |
| `app/core/` | Scheduler, recordatorios, notificador y arranque de servicios. |
| `app/services/` | Servicios locales: generación de Excel y Telegram. |
| `app/responses/v1/` | `ListResponse[T]` compartido. |
| `app/params/` | Parámetros de paginación. |
| `app/config/onion-config.toml` | Registro de colecciones Mongo de la CLI Onion. |
| `packages/kardex-business/src/kardex/repos/v1/` | Repositorios, datasources y modelos por entidad. |
| `.../repos/v1/common/` | `filter_params` y modelos compartidos entre entidades. |
| `.../core/` | Procesos de negocio atómicos que cruzan varias entidades (facturar, transferir, aprobar, etc.). |
| `.../services/mongo_collections/v1/` | Una clase de colección por archivo (`collection_name`). |
| `.../tools/` | Utilidades: `TimeTools`, `UuidTool`, `EtagTool`, búsqueda, `AppSettingsTool`, excepciones. |
| `.../lite/core/` | Variantes exclusivas de la edición Lite. |
| `.../kardex_config.py` | `KardexConfig` (banderas) y `kardexCtx` (tenant/sucursal). |
| `test/` | Suite `pytest`. |
| `wiki/` | Esta documentación. |
| `app/repos/v1/` | **Vacío**: residuo de la plantilla Onion. No agregar código ahí. |

---

## 3. Dónde está cada cosa

| Si buscas… | Ve a… |
| :--- | :--- |
| Un endpoint HTTP | `app/api/v1/<modulo>/<modulo>_router.py` |
| La orquestación de un caso de uso | `app/api/v1/<modulo>/<modulo>_controller.py` |
| Reglas de negocio de una entidad | `kardex/repos/v1/<entidad>/<entidad>_repository.py` |
| Una consulta o escritura a Mongo | `kardex/repos/v1/<entidad>/data/<entidad>_datasource.py` |
| El nombre de una colección | `kardex/services/mongo_collections/v1/<entidad>_collection.py` |
| Un proceso que toca varias entidades | `kardex/core/<proceso>/` |
| Modelos y validaciones | `kardex/repos/v1/<entidad>/models/` y `repos/v1/common/models/` |
| Filtros y paginación | `kardex/repos/v1/common/filter_params/` |
| Utilidades transversales | `kardex/tools/` |
| Auth, API keys o tenant | `app/app_middleware/depends/` |
| Excepciones de negocio | `kardex/tools/kardex_exceptions.py` |
| Mapeo de excepción a HTTP | `app/regis_exception_handlers.py` |
| Tareas programadas | `app/core/scheduler/` |
| Datos semilla al arrancar | `app/core/services_initializer.py` |
| Banderas de negocio | `kardex/kardex_config.py` |
| Tests | `test/` |
| Configuración de entorno | `../AGENTS.md` y [`operations.md`](./operations.md) |

> Las rutas que empiezan con `kardex/...` son abreviatura de `packages/kardex-business/src/kardex/...`.

---

## 4. Catálogo de enlaces

### 🧭 Para empezar

| Enlace | Qué encontrarás |
| :--- | :--- |
| [`../AGENTS.md`](../AGENTS.md) | Reglas de arquitectura, convenciones y guía de la CLI Onion. **Obligatorio.** |
| [`../README.md`](../README.md) | Descripción de la plantilla y comandos de la CLI. |
| [`project_index.md`](./project_index.md) | Visión histórica del proyecto y convenciones de datos (documento heredado). |

### 🏗️ Arquitectura y decisiones

| Enlace | Qué encontrarás |
| :--- | :--- |
| [`architecture.md`](./architecture.md) | Capas, flujo de una petición, árbol de carpetas, multi-tenant y flujos de negocio (facturación, notas de crédito, recibos, ajustes, importaciones, scheduler, Lite). |
| [`conventions.md`](./conventions.md) | Naming, `camelCase`, centavos, timestamps, repositorios, excepciones, colecciones, filtros, tests y pre-commit. |
| [`security.md`](./security.md) | Guards, headers de tenant/sucursal, routers sin guard y cómo proteger un módulo nuevo. |
| [`operations.md`](./operations.md) | Instalación, ejecución, Docker, variables de entorno, OpenAPI, scheduler y problemas comunes. |

### 🗂️ Módulos del API

| Enlace | Qué encontrarás |
| :--- | :--- |
| [`modules/INDEX.md`](./modules/INDEX.md) | Catálogo de los **48 módulos**: prefijo, router/controller, repo, colección, proceso y guard. |
| [`modules/credit_notes.md`](./modules/credit_notes.md) | Notas de crédito: estados, emisión/aprobación/rechazo y trazabilidad. |
| [`modules/composite.md`](./modules/composite.md) | Endpoints agregados (BFF) para cobranza. |
| [`modules/app_settings.md`](./modules/app_settings.md) | Parámetros globales y `AppSettingsTool`. |
| [`modules/unit_scales.md`](./modules/unit_scales.md) | Escalas de conversión de unidades. |

### 📋 Documentos de trabajo (fuera de la wiki)

| Enlace | Qué encontrarás |
| :--- | :--- |
| [`../GEMINI.md`](../GEMINI.md) | Bitácora cronológica de cambios y contexto de sesiones. |
| [`../../Hallazgos/reporte-cambios-unidades-facturacion-inventario.md`](../../Hallazgos/reporte-cambios-unidades-facturacion-inventario.md) | Reporte de cambios de unidades/facturación/inventario. |
| [`../../Hallazgos/`](../../Hallazgos/) | Auditorías, hallazgos y planes de corrección. |

---

## 5. Rutas rápidas por tarea

| Tarea | Archivos a abrir |
| :--- | :--- |
| Facturación / POS | `app/api/v1/invoices/`, `kardex/core/invoice_register/`, `kardex/core/product_ledger/` |
| Pedidos / cotizaciones | `app/api/v1/orders/`, `kardex/core/order_register/` |
| Notas de crédito | [`modules/credit_notes.md`](./modules/credit_notes.md), `kardex/core/credit_note_register/` |
| Cobros / recibos | `app/api/v1/receipts/`, `kardex/core/receipt_register/` |
| Devoluciones legacy | `app/api/v1/devolutions/`, `kardex/core/devolution_register/` |
| Entradas / salidas de inventario | `app/api/v1/entry_docs/`, `app/api/v1/exit_docs/`, `kardex/core/product_ledger/` |
| Stock en tiempo real | `kardex/core/inventory/inventory_engine.py`, `ProductAccountsCollection` |
| Ajustes de inventario | `app/api/v1/adjust_entries/`, `app/api/v1/adjust_exits/`, `kardex/core/adjust_ledger/` |
| Solicitudes de ajuste | `app/api/v1/adjustment_requests/`, `kardex/core/adjustment_requests/` |
| Transferencias entre sucursales | `app/api/v1/transfers/`, `kardex/core/transfer_manager/` |
| Compras / proveedores | `app/api/v1/entry_docs/`, `app/api/v1/suppliers/` |
| Gastos | `app/api/v1/expenses/`, `app/api/v1/expense_categories/` |
| Cuentas por cobrar | `app/api/v1/clients/`, `app/api/v1/client_transactions/`, `kardex/core/finance/` |
| Cierres y reportes | `app/api/v1/daily_summaries/`, `app/api/v1/executive_summaries/`, `app/api/v1/reports/`, `kardex/core/report_manager/` |
| Importaciones CSV | `app/api/v1/imports/`, `kardex/core/imports/` |
| Configuración global | [`modules/app_settings.md`](./modules/app_settings.md), `kardex/core/default_values/` |
| Escalas / unidades | [`modules/unit_scales.md`](./modules/unit_scales.md), `kardex/repos/v1/unit_scales/` |
| Agregados BFF | [`modules/composite.md`](./modules/composite.md), `app/api/v1/composite/` |
| Auth / usuarios / roles | `app/api/v1/auths/`, `app/api/v1/users/`, `app/api/v1/user_roles/`, `kardex/core/security/` |

---

## 6. Observaciones conocidas

| Observación | Impacto |
| :--- | :--- |
| Solo **4 de 48** módulos tienen ficha propia en `wiki/modules/`. | Usa [`modules/INDEX.md`](./modules/INDEX.md) para ubicar el resto. |
| `app/repos/v1/` está vacío. | Residuo de plantilla; la capa real está en `packages/kardex-business`. |
| `test/test_demo.py` está vacío (0 bytes). | No lo tomes como suite de referencia. |
| `expiration_logs_collection.py` declara `collection_name = "ExpirationLog"` y `onion-config.toml` registra `ExpirationLogs`. | Verifica el nombre antes de consultar esa colección directamente. |
| 14 routers no declaran guard a nivel de router. | Revisa [`security.md`](./security.md) antes de asumir que un endpoint es público. |
| El scheduler no corre con `MODE=DEV`. | Tareas programadas y recordatorios no se ejecutan en local. |

---

## 7. Cómo mantener esta wiki

1. **Módulo nuevo:** agrégalo a [`modules/INDEX.md`](./modules/INDEX.md) y registra su router en `app/api/v1/router.py`.
2. **Módulo complejo:** crea su ficha en `wiki/modules/` y enlázala desde aquí y desde el catálogo.
3. **Cambio de arquitectura, convención o seguridad:** actualiza el documento correspondiente (`architecture.md`, `conventions.md`, `security.md`) y, si afecta el arranque, `operations.md`.
4. **No dupliques contenido:** este INDEX enlaza; los detalles viven en el documento de su tema.
