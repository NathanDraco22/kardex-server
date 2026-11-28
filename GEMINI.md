# Contexto de Conversación - Code Review Transfer Optimization

## Fecha: 2026-11-27 (Lote 3 — Policy Object en notas de crédito y devoluciones)
### Objetivo
Extraer a policies puras las reglas de cabecera, estados y transiciones de notas de crédito y devoluciones, además del redondeo de importes de factura, preservando exactamente el comportamiento y el orden de validación existentes.

### Resumen Técnico
- **`PolicyDecision`:** nueva decisión genérica `allowed`/`reason` en `core/policies/policy_decision.py`; un rechazo sin motivo lanza `ValueError`. Exportada desde `core/policies/__init__.py`.
- **`CreditNotePolicy`:** métodos `amount_request_decision`, `devolution_request_decision`, `devolution_invoice_decision`, `devolution_items_decision`, `approval_decision`, `rejection_decision`, `reversal_decision` y `recalculated_total_decision`. Integrada en `credit_note_register.py`, `approve_credit_note.py`, `reject_credit_note.py`, `reverse_credit_note.py` y `process_credit_note.py`; los rechazos se traducen a `InvalidOperation` (o `ValueError` en la reversión, como antes).
- **`DevolutionPolicy`:** métodos `items_decision`, `invoice_decision`, `confirmation_client_decision` y `status_decision`. Integrada en `devolution_register.py` con el mismo orden de validaciones y cortes tempranos.
- **`InvoiceRoundingPolicy`:** encapsula `_round_up_whole_unit` y `_round_down_whole_unit`; `normalize_invoice_discounts` la usa para subtotales, descuentos de línea y descuento global. Se conservaron los parámetros `round_up` y los algoritmos de prorrateo/cantidades sin cambios.
- **Wiki:** sección de políticas en `wiki/modules/credit_notes.md`, nueva ficha `wiki/modules/devolutions.md`, enlace desde `wiki/modules/INDEX.md` y ejemplos actualizados en `wiki/conventions.md` §4.1.
- **Tests:** nuevos `test_policy_decision.py`, `test_credit_note_decision_policy.py`, `test_devolution_decision_policy.py` y `test_invoice_rounding_policy.py` con tablas de decisión y modelos reales.

### Revisión
- Revisor independiente: **APROBADO CON MENORES**. Se agregaron casos de precedencia entre reglas, se usó la constante real `SALE_CLIENT_ID` en los tests, se eliminó la propiedad muerta `enabled` de `InvoiceRoundingPolicy` y se precisaron las fichas de notas de crédito y devoluciones.

### Verificación
- `ruff check` sobre las policies, registros de notas de crédito/devoluciones/invoice_register y tests nuevos: limpio.
- `ty check`: limpio.
- `pytest -q`: `402 passed` (único warning preexistente de `pytest-asyncio` sobre `asyncio_default_fixture_loop_scope`).

## Fecha: 2026-11-27 (Ventas de un Producto)
### Objetivo
Extender la consulta de facturas por producto para alimentar la pantalla **“Ventas de un Producto”** con filtros de fecha, cliente y usuario, resumen de totales y exclusión de facturas anuladas.

### Resumen Técnico
- **Colección `Invoices`:** `fetch_all_invoices_by_product` agrega `status: {"$ne": "cancelled"}` cuando no se envía estado; nueva `fetch_product_sales_summary` con `$unwind`, `$match` de `saleItems.product.id` y `$group` (`invoiceCount` vía `$addToSet`, `totalQuantity`, `totalBonQuantity`, `total`).
- **Modelo `ProductSalesSummary`:** nuevo modelo Pydantic camelCase exportado desde `repos/v1/invoices/__init__.py`.
- **Endpoint:** `GET /api/v1/invoices/byProduct/{product_id}/totals` en datasource, repositorio, controller y router, reutilizando `InvoiceFilterParams`.
- **Test:** `test/test_invoices_by_product.py` valida filtros, exclusión de anuladas, pipeline de agregación, respuesta en ceros y paginación por cursor.
- **Correcciones de auditoría:** `InvoiceFilterParams` incorpora `cursorDate`/`cursorId`; `fetch_all_invoices_by_product` ordena por `(createdAt, id)` descendente y aplica `$or` para cursor; índice compuesto `branchId + createdAt + id`; pruebas de cursor.
- **Verificación:** `ruff check`, `ty check` y suite completa (`192 passed`).
- **Sin sincronización a `lite`:** cambio pendiente de sincronización explícita por decisión del usuario.

## Fecha: 2026-11-27 (Tipado de tests)
### Objetivo
Eliminar los 35 diagnósticos de `ty check` en `test/` sin excluir los tests del chequeo de tipos.

### Resumen Técnico
- **Nuevo helper `test/mock_helpers.py`:** `fake(Tipo, **atributos)` envuelve `SimpleNamespace` con `typing.cast` para crear dobles de prueba tipados.
- **Tests refactorizados:** `test_app_settings_invoice_display.py`, `test_credit_note_vs_devolution.py` y `test_devolution_credit_audit_fixes.py` usan `fake(...)` en los 31 mocks que no eran asignables a sus tipos nominales.
- **Narrowing:** `test_credit_note_policy.py` valida `approvedBy` y `test_devolution_credit_audit_fixes.py` valida `await_args` antes de accederlos.
- **Test desactualizado corregido:** `test_user_roles.py` ahora compara el conjunto completo de 13 submódulos comerciales (incluye `approveInvoiceCancellation` y `approveReceiptCancellation`) en vez de un conteo fijo de 11.
- **Verificación:** `ty check` y `ruff check` limpios en el código de aplicación; 48 pruebas de los archivos afectados y suite completa (`172 passed`) en verde.

## Fecha: 2026-11-27
### Objetivo
Documentar las reglas de negocio de conversión de órdenes/cotizaciones a factura con turnos (`useShifts`, `chargeConvertedOrdersToShift`, `requireShiftForConvertedOrders`).

### Resumen Técnico
- **Wiki:** nueva sección **"Reglas de negocio: conversión de órdenes/cotizaciones a factura con turnos"** en `wiki/modules/app_settings.md` y resumen en `wiki/modules/INDEX.md`.
- **Reglas documentadas:** `useShifts` solo no carga al turno; `chargeConvertedOrdersToShift` habilita la carga; `requireShiftForConvertedOrders` exige turno abierto y bloquea la conversión con HTTP 400 si falta.
- **Sin cambios de código:** solo documentación.

## Fecha: 2026-11-26
### Objetivo
Implementar **Solicitudes de Anulación de Factura** (`invoice_cancellation_requests`), integración con **Turnos** (sección *"Facturas Anuladas"*) y permiso granular `approveInvoiceCancellation`.

### Resumen Técnico
- **Nuevo módulo `invoice_cancellation_requests`:** colección `InvoiceCancellationRequests` (índice único parcial `ux_pending_cancellation_per_invoice`), modelos, `FilterParams`, datasource, repositorio, core atómico (`validate_invoice_cancellable`, `create_cancellation_request`, `approve_cancellation_request`, `reject_cancellation_request`, `cancel_cancellation_request`) y router `/api/v1/invoice-cancellation-requests`.
- **Reglas de negocio:** facturas de contado reingresan stock (`quantity + bonQuantity`) + Kárdex (`invoice_cancellation`); facturas a crédito sin abonos (`status == "open"`, `amountPaid == 0`) reingresan stock y revierten saldo en `ClientFinanceEngine`; bloquea facturas con abonos, devoluciones/NC activas o turno cerrado.
- **Roles:** agregado `CommercialSubModules.APPROVE_INVOICE_CANCELLATION = "approveInvoiceCancellation"` en `role_manager.py` (por defecto en `Supervisor` y `Admin` vía `all`; control aplicado en frontend).
- **Turnos y consultas:** agregados 8 campos `cancelledInvoice*` en `ShiftTotals`/`BaseShift`/`ShiftArqueoTotals` sin doble resta en `expectedCash`; corregido `fetch_pending_to_paid_invoices` y excluidas facturas `cancelled` por defecto en totales y ventas por producto.
- **Verificación:** `ruff check`, `ty check` y `pytest test/test_invoice_cancellation_requests.py test/test_shifts.py` (`22 passed`).

## Fecha: 2026-11-26 (Parte 2)
### Objetivo
Agregar banderas `useInvoiceCancellations` y `useReceiptCancellations` (`false` por defecto) en `AppSettings` e implementar **Solicitudes de Anulación de Recibos** (`receipt_cancellation_requests`).

### Resumen Técnico
- **`AppSettings` y Roles:** agregados `useInvoiceCancellations: bool = False`, `useReceiptCancellations: bool = False` en `app_setting_model.py`; y `CommercialSubModules.APPROVE_RECEIPT_CANCELLATION = "approveReceiptCancellation"` en `role_manager.py` (asignado por defecto a `Supervisor` y `Admin` vía `all`).
- **Nuevo módulo `receipt_cancellation_requests`:** colección `ReceiptCancellationRequests` (índice único parcial `ux_pending_cancellation_per_receipt`), modelos, `FilterParams`, datasource, repository, core atómico (`validate_receipt_cancellable`, `create_receipt_cancellation_request`, `approve_receipt_cancellation_request`, `reject_receipt_cancellation_request`, `cancel_receipt_cancellation_request`) y router `/api/v1/receipt-cancellation-requests`.
- **Reglas de negocio de recibos:** permite anular recibos aunque hayan dejado la factura en estado `paid` (restando `amountApplied` en la factura), revierte devoluciones/NC aplicadas y restaura la deuda del cliente siempre que el turno siga `open`.
- **Turnos:** agregados `cancelledReceiptTotal` y `cancelledReceiptCount` en `ShiftTotals`/`BaseShift`/`ShiftArqueoTotals`.
- **Verificación:** `ruff check`, `ty check` y `pytest test/test_receipt_cancellation_requests.py test/test_invoice_cancellation_requests.py test/test_shifts.py` (`29 passed`).

## Fecha: 2026-02-02
### Objetivo
Optimización de `app\core\transfer_manager\transfer_manager.py` y `app\core\transfer_manager\process_out_transfer.py`.

### Mejoras Implementadas
1.  **Consolidación de Items**: Agrupación por `productId` para validar stock total y reducir redundancia en operaciones de base de datos.
2.  **Integridad de Costos**: Actualización automática del campo `cost` en los items del traslado usando el `averageCost` de la sucursal de origen.
3.  **Kardex Accuracy**: Mejora en el cálculo del `resultStock` para transacciones de salida con items duplicados en un mismo documento.
4.  **Clean Code**: Eliminación de código muerto (comentado) y simplificación del manejo de excepciones en el Manager.

### Estado
Finalizado y verificado mediante análisis estático.

## Fecha: 2026-02-27
### Objetivo
Code Review del endpoint `/product-sales` en `invoices_router.py`.

### Resumen de Revisión
1.  **Flujo Verificado**: Se trazó la ejecución desde el Router -> Controller -> Repo -> DataSource -> InvoicesCollection (MongoDB).
2.  **Consulta DB**: Se analizó el pipeline de agregación en `fetch_all_product_sales`. Utiliza `$match`, `$unwind`, `$group` y `$sort`.
3.  **Hallazgos**: 
    *   Uso correcto de índices en el `$match`.
    *   Manejo de dinero y cantidades mediante `int`.
    *   Se identificó que los parámetros `offset` y `limit` no se están aplicando en la agregación de ventas por producto (potencial de mejora en escalabilidad).

## Fecha: 2026-03-21
### Objetivo
Análisis profundo y optimización de los nuevos totales en `daily_report_maker.py`, la orquestación en `ReportManager` y Notificaciones de Telegram.

### Resumen de Revisión
1. **Reportes Diarios y Cajas**: Se revisó la recolección de métricas transaccionales (facturas y recibos) asegurando que todas las sucursales, incluso con cero ventas, queden mapeadas.
2. **Cálculo de Deuda (Owed)**: Se identificó teóricamente que sumar la cartera viva (`totalOwed`) de los días con `__add__` genera "datos fantasma". Se validó el "Snapshot en Vivo" usando una nueva consulta `get_pending_invoice_totals_by_branch`.
3. **App Notifier (Telegram)**: Se refactorizó la alerta ejecutiva, desglosando limpiamente "Ingresos a Caja (Contado + Abonos)" y utilizando el término inequívoco "Nuevas Cuentas por Cobrar".

## Fecha: 2026-03-22
### Objetivo
Revisión profunda del flujo del endpoint `/initial-balance` en `app\api\v1\clients\clients_router.py`.

### Resumen de Revisión
1. **Flujo Verificado**: Desde Router -> Controller -> Repository -> `process_create_client.py` -> `client_financial_movement.py`.
2. **Hallazgos**:
   - Validación robusta en el controller con `client.hasMovements` para evadir saldos iniciales dobles.
   - Atomicidad garantizada vía transacción de sesión en MongoDB.
   - Generación controlada de factura de saldo inicial sin afectación de inventario (usando etiqueta `INITIAL_BALANCE`).
   - El movimiento se registra adecuadamente como `debit` (cargo) en la cuenta del cliente para mantener coherencia financiera.

## Fecha: 2026-04-24
### Objetivo
Estandarización de reglas para Agentes AI y creación de `AGENTS.md`.

### Resumen de Sesión
1. **Manual para IAs**: Se generó el archivo `AGENTS.md` que centraliza la arquitectura (Onion), convenciones de nombrado (`camelCase` para campos de modelos) y tipos de datos (fechas y dinero como `int`).
2. **Consistencia de Tooling**: Se documentó el flujo obligatorio de uso de `onion-cli` para la creación de nuevos módulos, asegurando que cualquier agente mantenga la integridad estructural del proyecto.
3. **Protocolo de Contexto**: Se reafirmó el uso de `GEMINI.md` para el historial de sesiones y `AGENTS.md` como guía técnica permanente.

## Fecha: 2026-05-10
### Objetivo
Migración de endpoints de historiales de entradas de `entry_histories` hacia `entry_docs` para centralización.

### Resumen de Sesión
1. **Migración Controlada**: Se copiaron las funciones de consulta de historiales (con información de proveedores) desde `entry_histories` hacia las capas Datasource, Repository, Controller y Router de `entry_docs`.
2. **Uso de Kwargs**: Se implementó el uso de `**kwargs` para el endpoint paginado, facilitando el traspaso limpio de todos los query params (incluyendo `startDate`, `endDate`, `supplierId`) hacia la colección de MongoDB sin ensuciar las firmas.
3. **Prevención de Conflictos**: Los nuevos endpoints se expusieron bajo el prefijo `/history` dentro de `/entry-docs` para evitar colisiones. Se conservó el módulo `entry_histories` intacto para permitir una transición segura y retrocompatible desde el frontend.

## Fecha: 2026-05-10 (Parte 2)
### Objetivo
Migración de endpoints de historiales de salidas (`exit_histories`) hacia `exit_docs`.

### Resumen de Sesión
1. **Migración Exit Docs**: Se replicó el patrón para las salidas, moviendo las consultas de `exit_histories` hacia `exit_docs`.

## Fecha: 2026-05-14
### Objetivo
Implementación de endpoint de streaming para productos (`get_all_products_in_branch_streamed`).

### Resumen de Sesión
1. **Endpoint de Streaming**: Se implementó el flujo completo para el endpoint de obtención de productos mediante Server-Sent Events / NDJSON, permitiendo manejar grandes volúmenes de datos.
2. **Capas Actualizadas**:
    - **Router (`products_router.py`)**: Se corrigió el error del parámetro `query` faltante y se devolvió una instancia correcta de `StreamingResponse` con `media_type="application/x-ndjson"`.
    - **Controller (`products_controller.py`)**: Se implementó un generador asíncrono que retorna los objetos `ProductInDbInBranch` serializados como cadenas JSON.
    - **Repository y DataSource**: Se propagó el generador asíncrono respetando las validaciones del modelo Pydantic.
    - **Collection (`products_collection.py`)**: Se implementó la iteración sobre el cursor de la agregación de MongoDB (`async for document in cursor: yield document`), excluyendo los filtros de paginación limit/offset para volcar todo el inventario de la sucursal de manera eficiente.

## Fecha: 2026-05-14 (Parte 2)
### Objetivo
Creación de endpoint de exportación de lista de precios en Excel.

### Resumen de Sesión
1.  **Nuevo Módulo Exports**: Se crearon `exports_router.py` and `exports_controller.py` bajo `app/api/v1/exports/` para centralizar descargas de archivos.
2.  **Endpoint `/exports/price-list`**: Se implementó un endpoint `GET` que genera una lista de precios en formato `.xlsx`.
3.  **Consumo de Stream**: El controlador consume eficientemente el método `get_all_product_in_branch_streamed` (creado en la sesión anterior) para evitar cargar todo el inventario en memoria.
4.  **PriceListService**: Se agregó `PriceListService` y sus dataclasses (`PriceListRow`, `PriceListSheet`) en `excel_service.py` para abstraer la creación del Excel usando `openpyxl`. Los montos de dinero se dividen entre 100 para convertirlos de centavos a decimales.
5.  **Retorno**: El endpoint utiliza `FileResponse` de FastAPI para entregar el archivo directamente al cliente.

## Fecha: 2026-05-16
### Objetivo
Extracción de la capa de negocio (`repos`, `core`, `tools`, `services/mongo`) a un paquete Python instalable (`kardex-business`) en monorepo local.

### Resumen de Implementación
1. **Creación del Paquete**: Se creó `packages/kardex-business/` con `pyproject.toml` propio y namespace `kardex.business.*`.
2. **Archivos Movidos**: ~151 archivos de `repos/v1/`, 20+ módulos de `core/`, 9 herramientas de `tools/`, 33 colecciones de `services/mongo_collections/v1/` y `mongo_service.py`/`mongo_indexes.py` fueron copiados al paquete.
3. **Importaciones Actualizadas**: Todos los imports internos en el paquete se actualizaron de `repos.`, `core.`, `tools.`, `services.` a `kardex.business.repos.`, etc.
4. **Shims de Retrocompatibilidad**: Se crearon shims en `app/repos/__init__.py`, `app/tools/__init__.py` (con `sys.modules` redirect) y `app/core/__init__.py` (imports locales) para que los imports antiguos sigan funcionando durante la migración gradual.
5. **Servicios No-Mongo**: `excel_service.py`, `ml_service.py`, `telgram_service.py` se quedan en `app/services/` junto con sus dependencias (openpyxl, onnxruntime, httpx). `MongoService` y `create_indexes` se re-exportan desde el paquete vía `app/services/__init__.py`.
6. **Dependencias del Paquete**: `fastapi`, `motor`, `pydantic`, `pytz`, `argon2-cffi`, `pyjwt`.
7. **Dependencia Local**: `kardex-business` se agregó como dependencia path editable en `pyproject.toml`.
8. **Fix de Circularidad**: Se resolvió dependencia circular entre `clients_repository` ↔ `core.client.process_create_client` usando lazy imports (vía `from __future__ import annotations` e imports dentro de métodos).
9. **Verificación**: La app FastAPI se importa correctamente con 187 rutas, 34 repositorios, y todas las capas de `core`, `tools` y `services`.

### Estado
Completado y verificado. Los shims permiten migración gradual de imports de `repos.v1.*` → `kardex.business.repos.v1.*` (y аналогично para core, tools, services).

## Fecha: 2026-05-17
### Objetivo
Code Review y validación de la refactorización del módulo de control de stock y kardex `product_ledger` en `kardex-business`.

### Resumen de Revisión
1. **Estructura y Atomicidad**: Se verificó la excelente separación de responsabilidades y el flujo atómico basado en sesiones de MongoDB con reintentos transaccionales para conflictos concurrentes (código 112).
2. **Refactorización de Excepciones (Éxito)**: El usuario resolvió de forma magistral el bug de desalineación de `InsufficientBalanceError` centralizando las excepciones en `packages/kardex-business/src/kardex/tools/kardex_exceptions.py`.
3. **Desacoplamiento de FastAPI**: Se eliminó la dependencia de `fastapi.HTTPException` dentro del paquete de negocio `kardex-business`. Las excepciones se propagan de manera nativa y son mapeadas limpiamente a nivel global mediante Exception Handlers en `app/regis_exception_handlers.py`. Esto respeta perfectamente la Onion Architecture.
4. **Oportunidad Detectada**: Alinear la excepción de sucursal no encontrada en el flujo de entradas (`process_entry_doc.py`) usando la nueva excepción `BranchNotFound` para total consistencia.

## Fecha: 2026-05-20
### Objetivo
Estandarización de todas las Collection classes y Datasources al patrón `BaseMongoCollection` + `get_instance()`.

### Resumen de Implementación
1. **`BaseMongoCollection`**: Se corrigió el import de `from services` a `from kardex.services`.
2. **33 Collection classes**: Se refactorizaron para extender `BaseMongoCollection` en lugar de implementar su propio singleton via `__new__()`. Se eliminaron `_instance`, `__new__()`, y `__init__()` con `MongoService` de cada una. Se normalizó `self.__collection` → `self._collection`.
3. **33 Datasource classes**: Se cambió `CollectionName()` por `CollectionName.get_instance()` para usar el singleton correctamente.
4. **Auditoría Completa de Instanciaciones**: Se revisó todo el codebase y se eliminaron las referencias legacy a constructores directos `Collection()` en:
   - [process_create_product.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/lite/core/product_register/process_create_product.py)
   - [etag_tool.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/tools/etag_tool.py)
   - [mongo_indexes.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/services/mongo_indexes.py)
5. **Verificación**: `ty` typecheck pasó exitosamente a nivel global, certificando la validez del tipado estático del nuevo patrón Singleton.

## Fecha: 2026-05-21
### Objetivo
Actualizar `AGENTS.md` con la guía de uso completa y detallada de la herramienta `onion` CLI.

### Resumen de Implementación
1. **Guía Expandida**: Se reemplazó la sección simplificada "Onion CLI — Entity Generation" en `AGENTS.md` con una especificación detallada de la CLI Onion.
2. **Documentación Multitecnológica**: Se incluyeron todos los comandos de la CLI para FastAPI (Python) y Flutter/Dart (cubits, models, data sources, etc.), convenciones de nombres (singular), parámetros de directorios de salida (`--output-dir`), estructuras de directorios generadas y workflows típicos.

## Fecha: 2026-05-22
### Objetivo
Creación e integración del módulo de gastos (`expense`) en la arquitectura Onion (FastAPI + paquete de negocio `kardex-business`).

### Resumen de Implementación
1. **Generación con Onion CLI**: Se generó la estructura base usando la CLI con variables de entorno UTF-8 para Windows.
2. **Reubicación al Paquete de Negocio**: Se movió la capa de negocio (repositorios, modelos, datasource, colección de MongoDB) al paquete `kardex-business` de acuerdo a la arquitectura, manteniendo el enrutador y controlador en el servidor FastAPI (`app/`).
3. **Refinamiento de Requisitos**:
   - **`docNumber` único**: Se configuró un índice único en MongoDB sobre `docNumber`. Si no se especifica en la creación, se autogenera una secuencia con el contador incremental `"expenseNumber"`.
   - **Consistencia de Fechas**: Se integró `dateId` en `BaseExpense` y `UpdateExpense` para que sea provisto directamente desde el frontend en formato `"YYYY-MM-DD"`, removiendo la generación en el servidor.
   - **Dinero en Centavos**: Todos los campos financieros (`amount`) se almacenaron como enteros (`int`).
   - **Filtros Avanzados y Paginación**: Se creó `ExpensesFilterParams` en un nuevo subpaquete `common/filter_params/` que hereda de `HistoryParams` para soportar búsquedas complejas (rango de fechas de creación `createdAt`, rangos de montos, categoría, sucursal, etc.) y paginación (`limit`, `offset`) retornando un `ListResponse`.
   - **Índices en MongoDB**: Se indexó el campo `createdAt` en la colección `Expenses` para soportar consultas de rango ("mayor que" y "menor que") de forma eficiente.
4. **Verificación**: Las comprobaciones estáticas con `ruff` y el typechecking completo de `ty` pasaron con éxito de forma global.

## Fecha: 2026-05-22 (Parte 2)
### Objetivo
Creación de la clase `KardexConfig` en memoria para habilitar saldos negativos en existencias durante facturación.

### Resumen de Implementación
1. **Configuración en Memoria**: Creación de la clase `KardexConfig` estructurada como un Singleton en `packages/kardex-business/src/kardex/kardex_config.py`.
2. **Propiedad `letInvoiceWithNegative`**: Atributo booleano que permite omitir el error `InsufficientBalanceError` en salidas cuyo subtipo es `"invoice"` (facturas).
3. **Core Integración**: Modificación de `InventoryBatchTransformer.prepare_exit` para evaluar `KardexConfig().letInvoiceWithNegative` al validar límites de stock.
4. **Verificación**: Comprobaciones estáticas (`ruff` y `ty`) exitosas y validación dinámica de escenarios `True` y `False` mediante script en `scratch/test_negative_stock.py`.

## Fecha: 2026-05-22 (Parte 3)
### Objetivo
Persistencia de stock negativo a nivel de Base de Datos (MongoDB) al facturar.

### Resumen de Implementación
1. **Parámetro `allow_negative` en Colección**: Se añadió el parámetro opcional `allow_negative` a los métodos de sustracción `substract_product_account_data` y `bulk_substract_product_account_data` de [product_accounts_collection.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/services/mongo_collections/v1/product_accounts_collection.py).
2. **Evadir Filtro Restrictivo**: Si `allow_negative` es `True`, se omiten las cláusulas restrictivas de stock de MongoDB (ej. `$expr` que exige stock disponible >= qty), logrando que la operación `$inc` de decremento decremente a valores negativos sin arrojar `OperationFailure`.
3. **Propagación en Core**: Se modificó `execute_exit` en [inventory_engine.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/core/inventory/inventory_engine.py) para aceptar y propagar este parámetro.
4. **Acoplamiento con Facturación**: Se actualizó [process_invoice.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/core/invoice_register/process_invoice.py) para pasar `allow_negative=KardexConfig().letInvoiceWithNegative` a `InventoryEngine.execute_exit`.
5. **Verificación**: Comprobación estática (`ruff` y `ty`) y script de integración con DB `scratch/test_db_negative_stock.py`.

## Fecha: 2026-05-22 (Parte 4)
### Objetivo
Agregar la variable de configuración `followTransaction` a `KardexConfig`.

### Resumen de Implementación
1. **Propiedad `followTransaction`**: Se agregó a [kardex_config.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/kardex_config.py) la variable de clase `followTransaction: bool = True` por defecto, permitiendo que la lógica del negocio pueda acceder y conmutar el comportamiento del rastreo de transacciones del Kardex.
2. **Verificación**: Se ejecutó `ty check` de forma global con éxito rotundo.

## Fecha: 2026-05-23
### Objetivo
Implementación de endpoint `/byProduct/{product_id}` para obtener facturas asociadas a un producto.

### Resumen de Implementación
1. **Colección (`invoices_collection.py`)**: Implementado `fetch_all_invoices_by_product` utilizando `build_query` y aplicando la condición `{"saleItems.product.id": product_id}` sobre el índice de MongoDB existente `IndexModel([("saleItems.product.id", 1)])`.
2. **DataSource (`invoices_datasource.py`)**: Añadido método de delegación `get_all_invoices_by_product` a nivel de DataSource de facturas.
3. **Repository (`invoices_repository.py`)**: Añadido `get_all_invoices_by_product` que invoca al DataSource y valida/serializa los resultados usando `InvoiceInDb.model_validate`.
4. **Controller (`invoices_controller.py`)**: Añadido `get_invoices_by_product` que serializa los query parameters `InvoiceQueryParams` y encapsula el listado en un objeto `ListResponse`.
5. **Router (`invoices_router.py`)**: Registrado el endpoint `GET /byProduct/{product_id}` utilizando `Depends(InvoiceQueryParams)` para permitir el filtrado avanzado compatible con las búsquedas generales de facturas.
6. **Verificación**: Ejecutado type-checking estático global (`ty check`) con éxito rotundo.

## Fecha: 2026-05-23 (Parte 2)
### Objetivo
Implementación de lógica y endpoint de abonos (`add_to_amount_paid`) para Gastos (`Expenses`).

### Resumen de Implementación
1. **Modelos (`expense_model.py`)**: Se agregó `amountPaid: int = 0` a `BaseExpense` y `amountPaid: int | None = None` a `UpdateExpense`. También se creó la clase `AddToAmountRequest` para tipar las peticiones de abono con los campos `expenseId` y `amountPaid`.
2. **Exportación de Tipos (`__init__.py`)**: Se exportó `AddToAmountRequest` en el barrel de `expenses` para que esté disponible en la capa de la API de FastAPI.
3. **Colección (`expenses_collection.py`)**: Se implementó el método `add_to_amount_paid` mediante un pipeline de agregación atómico que acumula el pago usando `$add` y `$ifNull`, actualizando el estado a `"paid"` si se cubre el total (`amount`), o `"partiallyPaid"` en caso contrario, además de guardar la fecha `paidAt` al completarse el pago.
4. **Capas de Negocio**: Se añadieron las llamadas delegadas correspondientes en `ExpensesDataSource` y `ExpensesRepository`.
5. **FastAPI (Controller y Router)**: Se creó el método en `ExpensesController` y se expuso el endpoint `POST /add-to-amount-paid` en `expenses_router.py`.
6. **Optimización de Índices (Colección)**: Se actualizó `create_indexes` en `expenses_collection.py` para crear los índices en lote mediante una lista de `IndexModel`, añadiendo un índice único sobre `id` y optimizando el ordenamiento en `createdAt` a `-1` (descendente).
7. **Verificación**: Se ejecutó exitosamente un script de prueba de integración `test_expense_payment.py` y se pasaron los chequeos de tipos estáticos globales (`ty check`).

## Fecha: 2026-05-24
### Objetivo
Comparación y evaluación de viabilidad de la rama `lite` frente a `main`.

### Resumen de Revisión
1. **Diferencias Clave**: La rama `lite` hereda todo el historial de `main`, pero deshabilita activamente múltiples rutas de FastAPI (`entry_docs`, `exit_docs`, `expenses`, `suppliers`, `product_stats`, `product_transactions`, `imports`) y elimina servicios no esenciales como Machine Learning (`ml_service.py` y `product_classifier.py`).
2. **Duplicidad y Mantenimiento**: Mantener una rama Git divergente a largo plazo solo para deshabilitar módulos genera una alta carga de mantenimiento, obligando a continuos merges manuales para resolver conflictos.
3. **Recomendación**: Se sugiere eliminar la rama `lite` y controlar la activación de módulos mediante variables de entorno (ej. `LITE_MODE=true`) o flags de configuración en `onion-config.toml`.

## Fecha: 2026-05-25
### Objetivo
Bloqueo de ajuste directo de existencias en el repositorio de cuentas cuando `followTransaction` está activo.

### Resumen de Implementación
1. **Nueva Excepción**: Creación de `DirectStockAdjustmentBlocked` en `kardex_exceptions.py` y exportación en `tools/__init__.py`.
2. **Validación en Repositorio**: Se modificaron `update_product_account_stock_and_cost`, `add_product_account_stock` y `substract_product_account_stock` en `ProductAccountsRepository` para que lancen `DirectStockAdjustmentBlocked` si `KardexConfig().followTransaction` es `True`.
3. **Mapeo Global HTTP**: Se registró la excepción en `app/regis_exception_handlers.py` con el manejador `handle_forbidden` para devolver un código HTTP `403 Forbidden` al cliente.
4. **Imports limpios**: Se reestructuraron todos los imports de la unificación para ubicarse en la parte superior de cada archivo.

## Fecha: 2026-05-31
### Objetivo
Creación e integración del CRUD de Categorías de Gastos (`Expense Categories`) en la arquitectura Onion (FastAPI + paquete de negocio `kardex-business`).

### Resumen de Implementación
1. **Generación con Onion CLI**: Generación de la estructura base del módulo usando `onion crud-mongo expense-category --version 1` bajo entornos UTF-8 para Windows.
2. **Reubicación de Negocio**: Traslado de la capa de negocio (repositorios, modelos, datasource y colección MongoDB) al paquete `kardex-business`. Se eliminaron los duplicados redundantes generados localmente por la CLI en `app/services/`.
3. **Registro e Indexación**: Registro de `ExpenseCategoriesCollection` en el barrel de colecciones e inicialización automática de sus índices únicos en `mongo_indexes.py`.
4. **Estandarización de Tipos**: Ajuste de los modelos Pydantic a camelCase (`createdAt`, `updatedAt`) y fechas en entero (`int` Unix Timestamp). Se configuró el controlador y enrutador de FastAPI para retornar `ListResponse` en la obtención masiva.
5. **Verificación**: Validación estática con `ruff` y `ty check` exitosa a nivel global, y ejecución de pruebas de integración dinámicas directas a MongoDB pasando de forma exitosa.

## Fecha: 2026-06-04
### Objetivo
Migración de los parámetros de consulta (query/filter params) definidos en la capa API (`app/`) hacia el paquete de negocio `kardex-business` para tipado estático y desacoplamiento.

### Resumen de Implementación
1. **Modelos Centralizados**: Creación de las clases de filter params en `packages/kardex-business/src/kardex/repos/v1/common/filter_params/` (e.g. `ClientFilterParams`, `ProductFilterParams`, `InvoiceFilterParams`, `ProductTransactionFilterParams`, `ExecutiveSummaryFilterParams`, `ReceiptFilterParams`, etc.) heredando de una clase base común `BaseFilterParams`.
2. **Tipado de Repositorios**: Actualización de todos los métodos de búsqueda en los repositorios de `kardex-business` para que reciban la correspondiente instancia tipada de filter params, encargándose de desempaquetar las propiedades mediante `**params.model_dump(...)` al llamar a la capa DataSource, garantizando que DataSources y colecciones mantengan sus firmas de `**kwargs`.
3. **Inyección en Controladores y Routers**: Modificación de los controladores y routers de FastAPI en `app/` para inyectar estos filter params mediante `Depends(...)`, logrando deserializar directamente desde la URL.
4. **Remoción de Legacy**: Eliminación definitiva de todos los archivos obsoletos `query_params.py` and `transaction_query_params.py` de la capa API.
5. **Verificación**: Comprobación estática global y tipado exitosos mediante `ruff check` y `ty check` (todos los chequeos aprobados).
6. **Resolución de Importación Circular**: Se detectó una dependencia circular al cargar el barrel `filter_params` debido a la importación de tipos (como `TransactionType`, `DevolutionStatus`, `InvoiceStatus`, `OrderStatus`, `PaymentMethod`) desde los modelos de repositorios. Al ser tipos `Literal` puros (alias de strings), se redefinieron localmente en cada archivo de filter_params, eliminando cualquier importación externa de la capa de repositorios y convirtiendo a `common/filter_params` en un paquete hoja sin dependencias circulares. La importación de inicio del servidor con `import app.main` funciona perfectamente ahora.

## Fecha: 2026-06-06
### Objetivo
Explicación de flujo del endpoint `search_product_in_branch` e implementación del nuevo endpoint por lote de IDs en la sucursal.

### Resumen de Revisión e Implementación
1. **Flujo de Capas**: Se revisaron todas las capas que componen el endpoint `GET /branch/{branch_id}/search/{text_query}`.
2. **Implementación de Consulta por lote de IDs (`GET_PRODUCTS_BY_IDS`)**:
### Resumen de Sesión
1. **Migración Exit Docs**: Se replicó el patrón para las salidas, moviendo las consultas de `exit_histories` hacia `exit_docs`.

## Fecha: 2026-05-14
### Objetivo
Implementación de endpoint de streaming para productos (`get_all_products_in_branch_streamed`).

### Resumen de Sesión
1. **Endpoint de Streaming**: Se implementó el flujo completo para el endpoint de obtención de productos mediante Server-Sent Events / NDJSON, permitiendo manejar grandes volúmenes de datos.
2. **Capas Actualizadas**:
    - **Router (`products_router.py`)**: Se corrigió el error del parámetro `query` faltante y se devolvió una instancia correcta de `StreamingResponse` con `media_type="application/x-ndjson"`.
    - **Controller (`products_controller.py`)**: Se implementó un generador asíncrono que retorna los objetos `ProductInDbInBranch` serializados como cadenas JSON.
    - **Repository y DataSource**: Se propagó el generador asíncrono respetando las validaciones del modelo Pydantic.
    - **Collection (`products_collection.py`)**: Se implementó la iteración sobre el cursor de la agregación de MongoDB (`async for document in cursor: yield document`), excluyendo los filtros de paginación limit/offset para volcar todo el inventario de la sucursal de manera eficiente.

## Fecha: 2026-05-14 (Parte 2)
### Objetivo
Creación de endpoint de exportación de lista de precios en Excel.

### Resumen de Sesión
1.  **Nuevo Módulo Exports**: Se crearon `exports_router.py` and `exports_controller.py` bajo `app/api/v1/exports/` para centralizar descargas de archivos.
2.  **Endpoint `/exports/price-list`**: Se implementó un endpoint `GET` que genera una lista de precios en formato `.xlsx`.
3.  **Consumo de Stream**: El controlador consume eficientemente el método `get_all_product_in_branch_streamed` (creado en la sesión anterior) para evitar cargar todo el inventario en memoria.
4.  **PriceListService**: Se agregó `PriceListService` y sus dataclasses (`PriceListRow`, `PriceListSheet`) en `excel_service.py` para abstraer la creación del Excel usando `openpyxl`. Los montos de dinero se dividen entre 100 para convertirlos de centavos a decimales.
5.  **Retorno**: El endpoint utiliza `FileResponse` de FastAPI para entregar el archivo directamente al cliente.

## Fecha: 2026-05-16
### Objetivo
Extracción de la capa de negocio (`repos`, `core`, `tools`, `services/mongo`) a un paquete Python instalable (`kardex-business`) en monorepo local.

### Resumen de Implementación
1. **Creación del Paquete**: Se creó `packages/kardex-business/` con `pyproject.toml` propio y namespace `kardex.business.*`.
2. **Archivos Movidos**: ~151 archivos de `repos/v1/`, 20+ módulos de `core/`, 9 herramientas de `tools/`, 33 colecciones de `services/mongo_collections/v1/` y `mongo_service.py`/`mongo_indexes.py` fueron copiados al paquete.
3. **Importaciones Actualizadas**: Todos los imports internos en el paquete se actualizaron de `repos.`, `core.`, `tools.`, `services.` a `kardex.business.repos.`, etc.
4. **Shims de Retrocompatibilidad**: Se crearon shims en `app/repos/__init__.py`, `app/tools/__init__.py` (con `sys.modules` redirect) y `app/core/__init__.py` (imports locales) para que los imports antiguos sigan funcionando durante la migración gradual.
5. **Servicios No-Mongo**: `excel_service.py`, `ml_service.py`, `telgram_service.py` se quedan en `app/services/` junto con sus dependencias (openpyxl, onnxruntime, httpx). `MongoService` y `create_indexes` se re-exportan desde el paquete vía `app/services/__init__.py`.
6. **Dependencias del Paquete**: `fastapi`, `motor`, `pydantic`, `pytz`, `argon2-cffi`, `pyjwt`.
7. **Dependencia Local**: `kardex-business` se agregó como dependencia path editable en `pyproject.toml`.
8. **Fix de Circularidad**: Se resolvió dependencia circular entre `clients_repository` ↔ `core.client.process_create_client` usando lazy imports (vía `from __future__ import annotations` e imports dentro de métodos).
9. **Verificación**: La app FastAPI se importa correctamente con 187 rutas, 34 repositorios, y todas las capas de `core`, `tools` y `services`.

### Estado
Completado y verificado. Los shims permiten migración gradual de imports de `repos.v1.*` → `kardex.business.repos.v1.*` (y аналогично para core, tools, servicios).

## Fecha: 2026-05-17
### Objetivo
Code Review y validación de la refactorización del módulo de control de stock y kardex `product_ledger` en `kardex-business`.

### Resumen de Revisión
1. **Estructura y Atomicidad**: Se verificó la excelente separación de responsabilidades y el flujo atómico basado en sesiones de MongoDB con reintentos transaccionales para conflictos concurrentes (código 112).
2. **Refactorización de Excepciones (Éxito)**: El usuario resolvió de forma magistral el bug de desalineación de `InsufficientBalanceError` centralizando las excepciones en `packages/kardex-business/src/kardex/tools/kardex_exceptions.py`.
3. **Desacoplamiento de FastAPI**: Se eliminó la dependencia de `fastapi.HTTPException` dentro del paquete de negocio `kardex-business`. Las excepciones se propagan de manera nativa y son mapeadas limpiamente a nivel global mediante Exception Handlers en `app/regis_exception_handlers.py`. Esto respeta perfectamente la Onion Architecture.
4. **Oportunidad Detectada**: Alinear la excepción de sucursal no encontrada en el flujo de entradas (`process_entry_doc.py`) usando la nueva excepción `BranchNotFound` para total consistencia.

## Fecha: 2026-05-20
### Objetivo
Estandarización de todas las Collection classes y Datasources al patrón `BaseMongoCollection` + `get_instance()`.

### Resumen de Implementación
1. **`BaseMongoCollection`**: Se corrigió el import de `from services` a `from kardex.services`.
2. **33 Collection classes**: Se refactorizaron para extender `BaseMongoCollection` en lugar de implementar su propio singleton via `__new__()`. Se eliminaron `_instance`, `__new__()`, y `__init__()` con `MongoService` de cada una. Se normalizó `self.__collection` → `self._collection`.
3. **33 Datasource classes**: Se cambió `CollectionName()` por `CollectionName.get_instance()` para usar el singleton correctamente.
4. **Auditoría Completa de Instanciaciones**: Se revisó todo el codebase y se eliminaron las referencias legacy a constructores directos `Collection()` en:
   - [process_create_product.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/lite/core/product_register/process_create_product.py)
   - [etag_tool.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/tools/etag_tool.py)
   - [mongo_indexes.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/services/mongo_indexes.py)
5. **Verificación**: `ty` typecheck pasó exitosamente a nivel global, certificando la validez del tipado estático del nuevo patrón Singleton.

## Fecha: 2026-05-21
### Objetivo
Actualizar `AGENTS.md` con la guía de uso completa y detallada de la herramienta `onion` CLI.

### Resumen de Implementación
1. **Guía Expandida**: Se reemplazó la sección simplificada "Onion CLI — Entity Generation" en `AGENTS.md` con una especificación detallada de la CLI Onion.
2. **Documentación Multitecnológica**: Se incluyeron todos los comandos de la CLI para FastAPI (Python) y Flutter/Dart (cubits, models, data sources, etc.), convenciones de nombres (singular), parámetros de directorios de salida (`--output-dir`), estructuras de directorios generadas y workflows típicos.

## Fecha: 2026-05-22
### Objetivo
Creación e integración del módulo de gastos (`expense`) en la arquitectura Onion (FastAPI + paquete de negocio `kardex-business`).

### Resumen de Implementación
1. **Generación con Onion CLI**: Se generó la estructura base usando la CLI con variables de entorno UTF-8 para Windows.
2. **Reubicación al Paquete de Negocio**: Se movió la capa de negocio (repositorios, modelos, datasource, colección de MongoDB) al paquete `kardex-business` de acuerdo a la arquitectura, manteniendo el enrutador y controlador en el servidor FastAPI (`app/`).
3. **Refinamiento de Requisitos**:
   - **`docNumber` único**: Se configuró un índice único en MongoDB sobre `docNumber`. Si no se especifica en la creación, se autogenera una secuencia con el contador incremental `"expenseNumber"`.
   - **Consistencia de Fechas**: Se integró `dateId` en `BaseExpense` y `UpdateExpense` para que sea provisto directamente desde el frontend en formato `"YYYY-MM-DD"`, removiendo la generación en el servidor.
   - **Dinero en Centavos**: Todos los campos financieros (`amount`) se almacenaron como enteros (`int`).
   - **Filtros Avanzados y Paginación**: Se creó `ExpensesFilterParams` en un nuevo subpaquete `common/filter_params/` que hereda de `HistoryParams` para soportar búsquedas complejas (rango de fechas de creación `createdAt`, rangos de montos, categoría, sucursal, etc.) y paginación (`limit`, `offset`) retornando un `ListResponse`.
   - **Índices en MongoDB**: Se indexó el campo `createdAt` en la colección `Expenses` para soportar consultas de rango ("mayor que" y "menor que") de forma eficiente.
4. **Verificación**: Las comprobaciones estáticas con `ruff` y el typechecking completo de `ty` pasaron con éxito de forma global.

## Fecha: 2026-05-22 (Parte 2)
### Objetivo
Creación de la clase `KardexConfig` en memoria para habilitar saldos negativos en existencias durante facturación.

### Resumen de Implementación
1. **Configuración en Memoria**: Creación de la clase `KardexConfig` estructurada como un Singleton en `packages/kardex-business/src/kardex/kardex_config.py`.
2. **Propiedad `letInvoiceWithNegative`**: Atributo booleano que permite omitir el error `InsufficientBalanceError` en salidas cuyo subtipo es `"invoice"` (facturas).
3. **Core Integración**: Modificación de `InventoryBatchTransformer.prepare_exit` para evaluar `KardexConfig().letInvoiceWithNegative` al validar límites de stock.
4. **Verificación**: Comprobaciones estáticas (`ruff` y `ty`) exitosas y validación dinámica de escenarios `True` y `False` mediante script en `scratch/test_negative_stock.py`.

## Fecha: 2026-05-22 (Parte 3)
### Objetivo
Persistencia de stock negativo a nivel de Base de Datos (MongoDB) al facturar.

### Resumen de Implementación
1. **Parámetro `allow_negative` en Colección**: Se añadió el parámetro opcional `allow_negative` a los métodos de sustracción `substract_product_account_data` y `bulk_substract_product_account_data` de [product_accounts_collection.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/services/mongo_collections/v1/product_accounts_collection.py).
2. **Evadir Filtro Restrictivo**: Si `allow_negative` es `True`, se omiten las cláusulas restrictivas de stock de MongoDB (ej. `$expr` que exige stock disponible >= qty), logrando que la operación `$inc` de decremento decremente a valores negativos sin arrojar `OperationFailure`.
3. **Propagación en Core**: Se modificó `execute_exit` en [inventory_engine.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/core/inventory/inventory_engine.py) para aceptar y propagar este parámetro.
4. **Acoplamiento con Facturación**: Se actualizó [process_invoice.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/core/invoice_register/process_invoice.py) para pasar `allow_negative=KardexConfig().letInvoiceWithNegative` a `InventoryEngine.execute_exit`.
5. **Verificación**: Comprobación estática (`ruff` y `ty`) y script de integración con DB `scratch/test_db_negative_stock.py`.

## Fecha: 2026-05-22 (Parte 4)
### Objetivo
Agregar la variable de configuración `followTransaction` a `KardexConfig`.

### Resumen de Implementación
1. **Propiedad `followTransaction`**: Se agregó a [kardex_config.py](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/kardex_config.py) la variable de clase `followTransaction: bool = True` por defecto, permitiendo que la lógica del negocio pueda acceder y conmutar el comportamiento del rastreo de transacciones del Kardex.
2. **Verificación**: Se ejecutó `ty check` de forma global con éxito rotundo.

## Fecha: 2026-05-23
### Objetivo
Implementación de endpoint `/byProduct/{product_id}` para obtener facturas asociadas a un producto.

### Resumen de Implementación
1. **Colección (`invoices_collection.py`)**: Implementado `fetch_all_invoices_by_product` utilizando `build_query` y aplicando la condición `{"saleItems.product.id": product_id}` sobre el índice de MongoDB existente `IndexModel([("saleItems.product.id", 1)])`.
2. **DataSource (`invoices_datasource.py`)**: Añadido método de delegación `get_all_invoices_by_product` a nivel de DataSource de facturas.
3. **Repository (`invoices_repository.py`)**: Añadido `get_all_invoices_by_product` que invoca al DataSource y valida/serializa los resultados usando `InvoiceInDb.model_validate`.
4. **Controller (`invoices_controller.py`)**: Añadido `get_invoices_by_product` que serializa los query parameters `InvoiceQueryParams` y encapsula el listado en un objeto `ListResponse`.
5. **Router (`invoices_router.py`)**: Registrado el endpoint `GET /byProduct/{product_id}` utilizando `Depends(InvoiceQueryParams)` para permitir el filtrado avanzado compatible con las búsquedas generales de facturas.
6. **Verificación**: Ejecutado type-checking estático global (`ty check`) con éxito rotundo.

## Fecha: 2026-05-23 (Parte 2)
### Objetivo
Implementación de lógica y endpoint de abonos (`add_to_amount_paid`) para Gastos (`Expenses`).

### Resumen de Implementación
1. **Modelos (`expense_model.py`)**: Se agregó `amountPaid: int = 0` a `BaseExpense` y `amountPaid: int | None = None` a `UpdateExpense`. También se creó la clase `AddToAmountRequest` para tipar las peticiones de abono con los campos `expenseId` y `amountPaid`.
2. **Exportación de Tipos (`__init__.py`)**: Se exportó `AddToAmountRequest` en el barrel de `expenses` para que esté disponible en la capa de la API de FastAPI.
3. **Colección (`expenses_collection.py`)**: Se implementó el método `add_to_amount_paid` mediante un pipeline de agregación atómico que acumula el pago usando `$add` y `$ifNull`, actualizando el estado a `"paid"` si se cubre el total (`amount`), o `"partiallyPaid"` en caso contrario, además de guardar la fecha `paidAt` al completarse el pago.
4. **Capas de Negocio**: Se añadieron las llamadas delegadas correspondientes en `ExpensesDataSource` y `ExpensesRepository`.
5. **FastAPI (Controller y Router)**: Se creó el método en `ExpensesController` y se expuso el endpoint `POST /add-to-amount-paid` en `expenses_router.py`.
6. **Optimización de Índices (Colección)**: Se actualizó `create_indexes` en `expenses_collection.py` para crear los índices en lote mediante una lista de `IndexModel`, añadiendo un índice único sobre `id` y optimizando el ordenamiento en `createdAt` a `-1` (descendente).
7. **Verificación**: Se ejecutó exitosamente un script de prueba de integración `test_expense_payment.py` y se pasaron los chequeos de tipos estáticos globales (`ty check`).

## Fecha: 2026-05-24
### Objetivo
Comparación y evaluación de viabilidad de la rama `lite` frente a `main`.

### Resumen de Revisión
1. **Diferencias Clave**: La rama `lite` hereda todo el historial de `main`, pero deshabilita activamente múltiples rutas de FastAPI (`entry_docs`, `exit_docs`, `expenses`, `suppliers`, `product_stats`, `product_transactions`, `imports`) y elimina servicios no esenciales como Machine Learning (`ml_service.py` y `product_classifier.py`).
2. **Duplicidad y Mantenimiento**: Mantener una rama Git divergente a largo plazo solo para deshabilitar módulos genera una alta carga de mantenimiento, obligando a continuos merges manuales para resolver conflictos.
3. **Recomendación**: Se sugiere eliminar la rama `lite` y controlar la activación de módulos mediante variables de entorno (ej. `LITE_MODE=true`) o flags de configuración en `onion-config.toml`.

## Fecha: 2026-05-25
### Objetivo
Bloqueo de ajuste directo de existencias en el repositorio de cuentas cuando `followTransaction` está activo.

### Resumen de Implementación
1. **Nueva Excepción**: Creación de `DirectStockAdjustmentBlocked` en `kardex_exceptions.py` y exportación en `tools/__init__.py`.
2. **Validación en Repositorio**: Se modificaron `update_product_account_stock_and_cost`, `add_product_account_stock` y `substract_product_account_stock` en `ProductAccountsRepository` para que lancen `DirectStockAdjustmentBlocked` si `KardexConfig().followTransaction` es `True`.
3. **Mapeo Global HTTP**: Se registró la excepción en `app/regis_exception_handlers.py` con el manejador `handle_forbidden` para devolver un código HTTP `403 Forbidden` al cliente.
4. **Imports limpios**: Se reestructuraron todos los imports de la unificación para ubicarse en la parte superior de cada archivo.

## Fecha: 2026-05-31
### Objetivo
Creación e integración del CRUD de Categorías de Gastos (`Expense Categories`) en la arquitectura Onion (FastAPI + paquete de negocio `kardex-business`).

### Resumen de Implementación
1. **Generación con Onion CLI**: Generación de la estructura base del módulo usando `onion crud-mongo expense-category --version 1` bajo entornos UTF-8 para Windows.
2. **Reubicación de Negocio**: Traslado de la capa de negocio (repositorios, modelos, datasource y colección MongoDB) al paquete `kardex-business`. Se eliminaron los duplicados redundantes generados localmente por la CLI en `app/services/`.
3. **Registro e Indexación**: Registro de `ExpenseCategoriesCollection` en el barrel de colecciones e inicialización automática de sus índices únicos en `mongo_indexes.py`.
4. **Estandarización de Tipos**: Ajuste de los modelos Pydantic a camelCase (`createdAt`, `updatedAt`) y fechas en entero (`int` Unix Timestamp). Se configuró el controlador y enrutador de FastAPI para retornar `ListResponse` en la obtención masiva.
5. **Verificación**: Validación estática con `ruff` y `ty check` exitosa a nivel global, y ejecución de pruebas de integración dinámicas directas a MongoDB pasando de forma exitosa.

## Fecha: 2026-06-04
### Objetivo
Migración de los parámetros de consulta (query/filter params) definidos en la capa API (`app/`) hacia el paquete de negocio `kardex-business` para tipado estático y desacoplamiento.

### Resumen de Implementación
1. **Modelos Centralizados**: Creación de las clases de filter params en `packages/kardex-business/src/kardex/repos/v1/common/filter_params/` (e.g. `ClientFilterParams`, `ProductFilterParams`, `InvoiceFilterParams`, `ProductTransactionFilterParams`, `ExecutiveSummaryFilterParams`, `ReceiptFilterParams`, etc.) heredando de una clase base común `BaseFilterParams`.
2. **Tipado de Repositorios**: Actualización de todos los métodos de búsqueda en los repositorios de `kardex-business` para que reciban la correspondiente instancia tipada de filter params, encargándose de desempaquetar las propiedades mediante `**params.model_dump(...)` al llamar a la capa DataSource, garantizando que DataSources y colecciones mantengan sus firmas de `**kwargs`.
3. **Inyección en Controladores y Routers**: Modificación de los controladores y routers de FastAPI en `app/` para inyectar estos filter params mediante `Depends(...)`, logrando deserializar directamente desde la URL.
4. **Remoción de Legacy**: Eliminación definitiva de todos los archivos obsoletos `query_params.py` and `transaction_query_params.py` de la capa API.
5. **Verificación**: Comprobación estática global y tipado exitosos mediante `ruff check` y `ty check` (todos los chequeos aprobados).
6. **Resolución de Importación Circular**: Se detectó una dependencia circular al cargar el barrel `filter_params` debido a la importación de tipos (como `TransactionType`, `DevolutionStatus`, `InvoiceStatus`, `OrderStatus`, `PaymentMethod`) desde los modelos de repositorios. Al ser tipos `Literal` puros (alias de strings), se redefinieron localmente en cada archivo de filter_params, eliminando cualquier importación externa de la capa de repositorios y convirtiendo a `common/filter_params` en un paquete hoja sin dependencias circulares. La importación de inicio del servidor con `import app.main` funciona perfectamente ahora.

## Fecha: 2026-06-06
### Objetivo
Explicación de flujo del endpoint `search_product_in_branch` e implementación del nuevo endpoint por lote de IDs en la sucursal.

### Resumen de Revisión e Implementación
1. **Flujo de Capas**: Se revisaron todas las capas que componen el endpoint `GET /branch/{branch_id}/search/{text_query}`.
2. **Implementación de Consulta por lote de IDs (`GET_PRODUCTS_BY_IDS`)**:
   - **Modelo (`product_model.py`)**: Se creó y exportó la clase request `GetProductsInBranchRequest` que encapsula `productIds: list[str]`.
   - **Router (`products_router.py`)**: Se registró el endpoint `POST /branch/{branch_id}/by-ids` que recibe la lista de IDs en el body.
   - **Controller (`products_controller.py`)**: Se agregó `get_products_in_branch_by_ids` que llama al repositorio y retorna los elementos mapeados en un `ListResponse`.
   - **Repository (`products_repository.py`)**: Invoca la fuente de datos y valida cada diccionario resultante con `ProductInDbInBranch.model_validate`.
   - **DataSource (`products_datasource.py`)**: Delega la búsqueda hacia la colección.
   - **Collection (`products_collection.py`)**: Se implementó `fetch_products_in_branch_by_ids` ejecutando una agregación con `$match` usando `{"id": {"$in": product_ids}, "isDeleted": False}` y haciendo `$lookup` con `$unwind` de `ProductAccounts` y `ProductSaleProfiles` para la sucursal especificada.
3. **Verificación**: Tipado y consistencia estática aprobados por `ty check`.

## Fecha: 2026-06-07
### Objetivo
Code Review y optimización del flujo transaccional de categorías de gastos (`expense_categories`).

### Resumen de Revisión y Optimización
1. **Detección de Bug**: Se identificó un bug donde al renombrar una categoría de gastos, los gastos existentes no se actualizaban debido a que se buscaba por el nombre nuevo en lugar del anterior.
2. **Implementación Transaccional**:
   - Se modificó la colección de categorías para soportar lectura con sesión de MongoDB (`session`).
   - Se actualizó el DataSource para consultar el `old_name` en la base de datos antes de aplicar el cambio.
   - Se añadió un condicional para actualizar la colección de gastos (`Expenses`) únicamente si el nombre sufrió una modificación real (`old_name != new_name`).
3. **Verificación**: Todo el tipado estático pasó de forma exitosa mediante `ty check`.

## Fecha: 2026-06-07 (Parte 2)
### Objetivo
Integración de gastos registrados y pagados (`expensesTotal` y `expensesPaid`) únicamente en los Resúmenes Ejecutivos (semanales, mensuales y anuales) y notificaciones de Telegram.

### Resumen de Implementación
1. **Modelos Modificados**: Se agregaron los campos opcionales `expensesTotal` y `expensesPaid` (inicializados en `0`) en `BaseExecutiveSummary` de `executive_summary_model.py`.
2. **Consulta por Agregación**: Se implementó el método `get_expenses_summary_in_range` en `ExpensesCollection` de `expenses_collection.py` que calcula:
   - `expensesTotal` como la suma de `amount` de todos los gastos activos y no eliminados del rango del periodo.
   - `expensesPaid` como la suma de `amount` únicamente de los gastos que tienen `status == "paid"`.
3. **Poblado en Schedulers**: Se modificó `daily_report_maker.py` (`WeeklyReportMaker`, `MonthlyReportMaker`, `YearlyReportMaker`) para invocar el resumen de gastos a través de `ReportManager` y poblar el objeto `CreateExecutiveSummary`.
4. **Notificaciones de Telegram**: Se modificó `app_notifier.py` (`notify_executive_report`) para desglosar la sección `💸 EGRESOS POR GASTOS 💸` detallando Gastos Totales, Pagados y el saldo Pendiente (Por Pagar).
5. **Verificación**: Se creó y ejecutó con éxito un script de integración `scratch/test_report_expenses.py`, validando el correcto funcionamiento con MongoDB y los cálculos del periodo. Las pruebas estáticas con `ty check` y `ruff` pasaron exitosamente.
6. **Migración de Roles y Permisos**: Se implementó la lógica en `update_default_roles` dentro de `create_default_roles.py` para iterar de manera incremental sobre los roles existentes en MongoDB y añadirles cualquier permiso nuevo del código (como `"expenses"`) sin sobreescribir configuraciones personalizadas preexistentes.
7. **Categorías de Gastos Predeterminadas**: Se creó el archivo `create_default_expense_categories.py` en `default_values` e integración en el flujo de inicialización de FastAPI (`services_initializer.py`) para registrar de forma idempotente las categorías de gastos más comunes (como Electricidad, Agua, Impuestos, Renta, etc.), además de 9 categorías sugeridas adicionales para dar robustez corporativa al sistema.

## Fecha: 2026-06-08
### Objetivo
Creación de la guía unificada de arquitectura y estilo Onion Fullstack.

### Resumen de Sesión
1. **Creación de Guía**: Se generó el archivo `ONION_FULLSTACK_STYLE_GUIDE.md` en la raíz del repositorio.
2. **Consolidación de Estándares**:
   - Backend: flujo de capas, transaccionalidad atómica y manejo desacoplado de excepciones de negocio.
   - Frontend: separación de Cubits de lectura y escritura, enfoque estándar de sincronización y enfoque reactivo con `ReactiveRepository`.
   - Onion CLI: documentación de comandos clave y pasos manuales indispensables de ajuste.

## Fecha: 2026-06-12
### Objetivo
Explicación detallada de la migración del driver de base de datos a PyMongo Async (`AsyncMongoClient`) y el manejo de transacciones.

### Resumen de Sesión
1. **Investigación de Deprecación**: Se validó el estado de deprecación de `Motor` (EOL en mayo de 2026) en favor del nuevo soporte asíncrono nativo introducido oficialmente en `pymongo` (GA desde v4.13).
2. **Comparativa de Transacciones**:
   - Se analizó la sintaxis clásica de transacciones basada en el Driver Motor frente a la nueva API asíncrona de `pymongo`.
   - Se evaluó el uso de la API de Callback (`with_transaction`) que provee lógica robusta de reintento automático para errores de tipo `TransientTransactionError`.
   - Se introdujo el concepto de `AsyncClientSession.bind()` (incorporado en `pymongo>=4.17.0`, la versión actual del proyecto), el cual elimina la necesidad de pasar explícitamente el parámetro `session=session` a cada operación CRUD individual dentro de un bloque de código.

## Fecha: 2026-06-12 (Parte 2)
### Objetivo
Creación e integración de la excepción `MongoMigrationException`, su aplicación en la migración asíncrona de MongoDB y unificación de transacciones.

### Resumen de Sesión
1. **Definición de Excepción**: Se añadió `MongoMigrationException` heredando de `KardexException` en `kardex_exceptions.py` y se exportó en el barrel file de herramientas de negocio.
2. **Control de Errores en Upserts (`find_one_and_update`)**:
   - Se identificó que con la migración, los métodos `find_one_and_update` que retornan documentos tras realizar un upsert o una modificación atómica crítica (`ReturnDocument.AFTER`) podían devolver de forma imprevista `None` según el tipado estático del driver.
   - Se inyectó control con `MongoMigrationException` en los métodos de `AccountBalancesCollection`, `ClientsCollection`, `CountersCollection` y `ProductAccountsCollection`. Si el resultado de la operación es `None`, se lanza la excepción, garantizando firmas de retorno estrictas `dict[str, Any]` (sin el tipo opcional `| None`).
3. **Corrección de Await en Agregaciones**: Se restauraron y agregaron los keywords `await` faltantes en las llamadas a `collection.aggregate` dentro de `ProductAccountsCollection` (`get_product_account_with_product_data`, `get_all_product_accounts_with_product` y `get_total_current_stock`), solucionando los errores de tipo `CoroutineType` en el typechecker.
4. **Unificación de Transacciones**:
   - Se refactorizaron todas las transacciones del proyecto para seguir el patrón correcto del driver PyMongo Async en todo el codebase:
     ```python
     async with mongo_client.start_session() as session:
         async with await session.start_transaction():
     ```
     en lugar de colocar el `await` en el `start_session()`.
   - Se aplicó esta corrección en 18 módulos del core y del negocio, así como en los scripts del playground.
5. **Verificación de Tipado Estático y Runtime (¡Éxito Total!)**:
   - Se resolvió una discrepancia en el script `auto_code.py` agregando una aserción para asegurar que `current_counter` no sea `None`.
   - Tras corregir los bloques de transacciones, se ejecutó `ty check` de forma global obteniendo un **"All checks passed!"** rotundo, eliminando por completo todas las advertencias/diagnósticos remanentes. El sistema de tipos está 100% limpio y validado tanto estática como dinámicamente.

## Fecha: 2026-06-20
### Objetivo
Optimización de relevancia y ordenamiento de mayor a menor coincidencia en las consultas de búsqueda de productos de MongoDB (`ProductsCollection`).

### Resumen de Sesión
1. **Análisis Comparativo**: Se identificó que las búsquedas de productos no utilizaban la lógica de sanitización ni priorizaban las coincidencias por prefijo en nombre y código como se hacía en clientes con `positionBoost` y `finalScore`.
2. **Implementación de Position Boost**:
   - Se modificaron `search_product_by_text`, `searchProductWithAccount` y `searchProductInBranch` en `ProductsCollection` para usar un pipeline de agregación.
   - Se añadió sanitización de la query mediante `re.escape(text_query)`.
   - Se inyectaron boosts de relevancia (`nameBoost` y `codeBoost` con valor `100` si coinciden al inicio con el regex `^`).
3. **Búsqueda por Código de Barras Parcial**: Se introdujo una condición `$or` en el `$match` inicial de los buscadores para evaluar la consulta tanto en la búsqueda de texto `$text` tradicional de MongoDB como en el prefijo del campo `code` vía regex. Esto solventa la limitación de MongoDB donde consultas parciales de códigos no devolvían ningún resultado.
4. **Optimización en Sucursales**: Se trasladaron las etapas `$sort` por `finalScore` y `$limit` al final del pipeline de agregación en `searchProductInBranch`, evitando la pérdida silente de resultados provocada por el `$unwind` de registros no existentes en la sucursal sobre un conjunto limitado previamente.
5. **Verificación Estática y Dinámica**:
   - Se validó el correcto funcionamiento y ordenamiento mediante el script de integración `scratch/test_product_search_boost.py`.
   - Se corrieron los chequeos de calidad estáticos (`ruff check` y `ty check`) para el archivo modificado, superando todos los análisis sin advertencias ni errores.

## Fecha: 2026-06-27
### Objetivo
Code Review de la variable de entorno `LET_NEGATIVE` y el comportamiento de `letInvoiceWithNegative`.

### Resumen de Revisión
1. **Prioridad de `LET_NEGATIVE`**: Se verificó en `app/app_lifespan.py` que si la variable de entorno `LET_NEGATIVE` existe (no es `None`), su valor booleano (`true`/`false`) tiene la última palabra y sobrescribe el valor configurado automáticamente por `is_lite`.
2. **Comportamiento de `letInvoiceWithNegative`**: Se rastreó su uso a través de `inventory_batch_transformer.py` y `process_invoice.py` (para facturas directas y facturas anónimas). Cuando está habilitado, permite omitir la excepción `InsufficientBalanceError` en memoria durante salidas de tipo `"invoice"` y pasa `allow_negative=True` a `InventoryEngine.execute_exit`, lo que a su vez previene la restricción de stock disponible en MongoDB en `bulk_substract_product_account_data`.

## Fecha: 2026-07-04
### Objetivo
Discusión y análisis de diseño lógico para el manejo de variaciones de productos y presentaciones múltiples.

### Resumen de Discusión
1. **Alternativa A (Productos Hijos Independientes)**:
   - Se evaluó el uso de un campo opcional `variation: ProductVariation | None` en [BaseProduct](file:///c:/Users/sytru/Developer/Projects/kardex_app/kardex-server/packages/kardex-business/src/kardex/repos/v1/products/models/product_model.py#L7-L17) que apunta a un `parentId` y define un `conversionFactor`.
   - Se acordó que el stock físico residirá exclusivamente en el Padre para evitar redundancia y desincronización de datos.
   - Las agregaciones de MongoDB calcularán dinámicamente el stock y el costo promedio de las variaciones en tiempo de consulta.
   - El motor de inventario interceptará transacciones sobre productos hijos y redirigirá la afectación de stock físico al documento del padre en base al factor de conversión.
2. **Alternativa B (Arreglo de Presentaciones en el Padre)**:
   - Se analizó la viabilidad de agregar un arreglo de presentaciones directamente al producto padre. 
   - Aunque simplificaría el motor de inventario, se descartó debido a que añade alta complejidad a la UI (selección de presentación al vender) y a la asignación de perfiles de precios independientes por sucursal (`ProductSaleProfiles`).
3. **Estado**: Discusión teórica completada. Decisión en espera de definición final por el usuario debido a la gran escala de impacto en el sistema.

## Fecha: 2026-07-21
### Objetivo
Auditoría exhaustiva de código buscando posibles bugs, condiciones de carrera, errores de cálculo en costos o stock, inconsistencias en transacciones de MongoDB y casos borde en todo el core de inventario (`packages/kardex-business/src/kardex/core`).

### Resumen de Revisión
1. **Detección de Bugs Críticos**:
   - **`prepare_exit` / Kardex Result Stock**: Para documentos de salida con ítems duplicados del mismo producto, `new_tx.resultStock` muta el objeto en memoria en pasos intermedios irreales y genera transacciones redundantes no consolidadas.
   - **Devoluciones de Clientes (`process_devolution.py`)**: `process_devolution` promete acreditar la cuenta del cliente en la documentación/comentarios pero NO invoca `ClientFinanceEngine.process_movement`, dejando la deuda del cliente intacta tras una devolución. Además, no inicializa `ProductSaleProfile` si el producto devuelto no tenía cuenta en la sucursal.
   - **Despacho de Pedidos Facturados (`process_invoice.py`)**: Cuando `is_order_fulfillment=True`, se usa `bulk_dispatch_promise_stock` que exige estrictamente `promiseStock >= qty`, fallando si hay desajuste previo aun si `letInvoiceWithNegative=True`. No usa el motor unificado `InventoryEngine.execute_exit`.
   - **Cancelación de Pedidos (`cancel_order.py`)**: `bulk_substract_from_promise_stock` recibe tuplas sin consolidar. Si un producto aparece en 2 ítems del pedido, el segundo `UpdateOne` falla al exigir `promiseStock >= qty` individual tras la primera resta parcial.
   - **Mapeo y Enmascaramiento de Excepciones**: En varios managers (`ProductLedgerManager`, `AdjustLedgerManager`, `InvoiceRegister`) se capturan las excepciones de negocio (`InsufficientBalanceError`) para relanzar copias genéricas sin los atributos de contexto (`product_id`, `product_name`), o se capturan todos los `OperationFailure` reintentando errores ajenos a conflictos de escritura (código 112).
   - **Bloqueo Global de Mutex**: `AdjustLedgerManager` y `InvoiceRegister` usan `asyncio.Lock()` globales en memoria que bloquean operaciones concurrentes entre distintas sucursales y lanzan `asyncio.TimeoutError` sin capturar.

## Fecha: 2026-08-04
### Objetivo
Eliminación de la dependencia `onnxruntime` del backend `kardex-server` y reubicación del modelo `product_classifier.onnx` a la carpeta `ml_pending/` en la raíz del proyecto para su futura integración en Flutter.

### Resumen de Implementación
1. **Carpeta `ml_pending/`**: Se creó e integró la carpeta directamente en la raíz contenedora del monorepo (`kardex_app/ml_pending/`), compartida por `kardex-server` y `kardex_app_front`, conteniendo el modelo `product_classifier.onnx` junto a un `README.md` explicativo con las pautas para su posterior integración On-Device ML en Flutter. Se eliminó la carpeta `app/assets/` del servidor.
2. **Dependencias del Servidor**: Se eliminó `"onnxruntime>=1.26.0"` de `pyproject.toml` y se ejecutó `uv sync`, desinstalando con éxito `onnxruntime`, `numpy`, `protobuf` y `flatbuffers`, reduciendo significativamente el tamaño del proyecto y el uso de memoria RAM en **Railway**.
3. **Limpieza de Servicios**: Se eliminó `app/services/ml_service.py` y la subcarpeta `app/core/ml/`. Se removieron las importaciones e inicializaciones de `ProductClassifierService` y `ProductClassifier` en `app/services/__init__.py`, `app/core/services_initializer.py` y `app/core/__init__.py`.
4. **Endpoint de Estadísticas**: Se actualizó `estimate_product_stats` en `product_stats_controller.py` para calcular el procesamiento de estadísticas de transacciones y asignar un nivel de estimación por defecto `0` (que mapea a la etiqueta `"-"`), manteniendo la compatibilidad con clientes existentes sin arrojar errores `501`.
5. **Verificación Estática**: Se ejecutaron con éxito las verificaciones pre-commit requeridas (`ruff check` y `ty check`), pasando todos los chequeos sin errores ni advertencias.

## Fecha: 2026-08-16
### Objetivo
Soporte de filtro por rango de fechas en el listado paginado de órdenes/cotizaciones para el nuevo módulo frontend "Buscador de Cotizaciones/Órdenes".

### Resumen de Implementación
1. **Cambio mínimo en `orders_collection.py`**: En `fetch_paginated_orders` se capturan ahora los parámetros `startDate`/`endDate` del `**kwargs` y, si ambos están presentes, se agrega al query de MongoDB el filtro `query["createdAt"] = {"$gte": start_date, "$lte": end_date}`. Se replicó el mismo patrón que ya usaba `fetch_products_in_orders`.
2. **Sin cambios en capas superiores**: El repositorio, controller, datasource y filtros (`OrderFilterParams`) ya propagaban `startDate`/`endDate` de forma natural; la colección era la única capa que los ignoraba.
3. **Verificación Estática**: `ruff check` y `ty check` pasaron sin errores.

## Fecha: 2026-11-08
### Objetivo
Endurecimiento de los endpoints de importaciones CSV y soporte del contrato de sucursal para el nuevo módulo frontend de importaciones.

### Resumen de Implementación
1. **Router de importaciones**: Se agregó `Depends(auth_middleware)` a las cuatro rutas y una dependencia compartida `get_branch_id` que acepta los headers `X-Branch` y `branch-id`. Se añadió el modelo `ImportResponse` con `status`, `message` e `importedCount`.
2. **Parser CSV robusto**: `imports_controller.py` ahora valida extensión, tamaño máximo (10 MB), codificación UTF-8 con BOM, delimitador `,` o `;`, columnas obligatorias, montos decimales a centavos, cantidades enteras, booleanos y `tags` (lista JSON o valores separados por `;`). Los errores devuelven `400` con número de fila y campo.
3. **Inventario inicial**: Se valida que no exista previamente el documento de inventario inicial por sucursal y se cambió el `id` del documento de `0000` a `0000-{branchId}` para evitar colisiones entre sucursales.
4. **ProductImport**: Se agregó un validador de `tags` que tolera cadenas vacías, listas JSON y valores separados por `;`. También se agregó soporte para el cuarto precio (`price4`), aplicado en `salePrice4` durante la importación.
5. **Verificación**: `ruff check`, `ty check`, importación de `app.main` y pruebas del parser con BOM, `;`, campos vacíos y columnas faltantes pasaron correctamente.

## Fecha: 2026-11-08
### Objetivo
Agregar la moneda global configurable al módulo `app_settings`.

### Resumen de Implementación
1. **Modelo de configuración**: Se agregó `currency` a `BaseAppSetting` con tipo `Literal["NIO", "USD", "HNL", "GTQ", "CRC", "COP", "MXN", "EUR"]` y valor por defecto `"NIO"`. `UpdateAppSetting` acepta el campo como opcional para PATCH parcial.
2. **Retrocompatibilidad**: Los documentos existentes de MongoDB sin el campo se validan con `NIO` por defecto, sin requerir migración.
3. **Documentación**: Se actualizó `wiki/modules/app_settings.md` con el nuevo campo y su propósito visual.
4. **Verificación**: `ruff check` y `ty check` pasaron sin errores.

## Fecha: 2026-11-08
### Objetivo
Agregar la moneda secundaria informativa y su tasa de cambio al módulo `app_settings`.

### Resumen de Implementación
1. **Modelo de configuración**: Se agregó `secondaryCurrency` con tipo `CurrencyCode` y valor por defecto `"USD"`, y `exchangeRate` como `float` con valor por defecto `0.0` y validación `ge=0`. `UpdateAppSetting` acepta ambos como opcionales para PATCH parcial.
2. **Retrocompatibilidad**: Los documentos existentes sin estos campos se validan automáticamente con `USD` y `0.0`, sin migración.
3. **Alcance informativo**: La tasa representa cuántas unidades de `currency` equivalen a 1 unidad de `secondaryCurrency`. No se usa para convertir montos ni modificar precios, tickets o reportes.
4. **Documentación**: Se actualizó `wiki/modules/app_settings.md` con ambos campos.
5. **Verificación**: `ruff check`, `ty check` e importación de `app.main` sin errores.

## Fecha: 2026-11-08
### Objetivo
Habilitar la visualización del total de facturas en la moneda secundaria.

### Resumen de Implementación
1. **Modelo de configuración**: Se agregó `showInvoiceTotalInSecondaryCurrency` como `bool` con valor por defecto `False`. `UpdateAppSetting` lo acepta como opcional para PATCH parcial.
2. **Retrocompatibilidad**: Los documentos existentes sin el campo se validan automáticamente con `False`, sin migración.
3. **Alcance**: El campo solo habilita la línea informativa en el visor, ticket térmico y PDF A4 de facturas. No altera montos, pagos, cuentas por cobrar ni inventario.
4. **Documentación**: Se actualizó `wiki/modules/app_settings.md` con el nuevo campo.
5. **Verificación**: `ruff check`, `ty check` e importación de `app.main` sin errores.

## Fecha: 2026-11-08
### Objetivo
Estandarizar la numeración de facturas generadas por saldos iniciales usando `CounterManager`.

### Resumen de Implementación
1. **Alta de cliente con saldo**: `process_create_client_with_balance` ahora obtiene el folio con `CounterManager().next_invoice_number(session)`, en lugar de reutilizar el número de cliente.
2. **Saldo inicial individual**: `create_initial_balance` usa el contador de facturas en lugar del `id` del cliente para el `docNumber`.
3. **Saldo inicial masivo**: `_execute_multiple_initial_balance` dejó de generar folios largos con timestamp y número aleatorio; ahora usa `next_invoice_number(session)` dentro de la misma transacción.
4. **Integridad del movimiento**: El `document_id` del movimiento financiero ahora coincide con el `id` UUID real de la factura creada (antes apuntaba al folio temporal en el flujo masivo).
5. **Verificación**: `ruff check` y `ty check` pasaron sin errores.

## Escalas de Unidades con Fracciones Comerciales (Noviembre 2026)
### Objetivo
Reemplazar las escalas por defecto basadas en gramo/mililitro/centímetro por micro-escalas comerciales con `scaleType`.

### Resumen de Implementación
1. **Modelo**: `BaseUnitScale.scaleType` (`weight`, `volume`, `length`, `pack`, `fractionPack`, `custom`), también en `CreateUnitScale`, `UpdateUnitScale` y `UnitScaleInDb`. Los documentos viejos se leen como `custom`.
2. **Semillas**: `Libra`, `Litro` y `Metro` con base cuarto; `fractionPack` para Caja x10/x12/x20/x24/x30/x50/x60/x100 y Docena. `pack` y `time` no se siembran por ahora.
3. **Limpieza**: se eliminan las semillas viejas solo si coinciden nombre y unidad base (`Peso`/`Gramo`, `Volumen`/`Mililitro`, `Longitud`/`Centímetro`, `Tiempo`/`Segundo`), para no borrar escalas personalizadas.
4. **Documentación**: `wiki/modules/unit_scales.md` actualizado con `fractionPack`, `pack`, reglas de fracción y precios.
5. **Verificación**: `ruff check` y `ty check` pasaron sin errores; se confirmaron 12 escalas semilla con sus factores e índices.

## Decisiones P0 de Unidades, Notas de Crédito y Devoluciones (Noviembre 2026)
- Se cerró el alcance **P0 = C3 + C7**. Las **bonificaciones** quedan diferidas por decisión de negocio (la app aún no las muestra/explota visualmente) y las **devoluciones directas** quedan deprecadas, reemplazadas por notas de crédito.
- **C3 (backend):** solo notas de crédito; líneas identificadas por `invoiceItemIndex`; tope acumulado por línea/factura; devolución parcial permitida; rechazo de cantidades no múltiplas del `conversionFactor`; `floor` en cantidad y dinero; el backend recalcula `amount` desde las líneas; `idempotencyKey`; sin lock por factura (riesgo residual aceptado).
- **C7 (contrato frontend):** la unidad libre guarda el texto visible completo; `validator` desde el controlador; sincronización al guardar; el placeholder `Unidad Base` no se persiste; confirmación única.
- **P1** (cantidades/display/búsqueda rápida/transferencias) quedó implementado en la fase posterior (ver entrada siguiente); la revalidación de stock al cobrar no se cambió. **P2** (semillas, PATCH null, precio 0, etiquetas, N=2/4, `showButtons`) queda pendiente.
- **Producción:** la maneja el usuario; no se agrega migración ni guard de producción.
- Sesión de solo documentación: no se modificó código ni tests.

## P1 de Unidades: Metadata, Display, Búsqueda Rápida y Transferencias (Noviembre 2026)
### Objetivo
Documentar la implementación P1 de cantidades, presentación, búsqueda rápida y borradores de transferencia, con foco en el contrato backend.

### Resumen de Implementación
1. **Metadata backend:** `SaleItem` acepta `selectedUnitName`, `standardUnitName` y `standardUnitFactor`; `EntryItem`, `ExitItem` y `TransferItem` aceptan `standardUnitName`/`standardUnitFactor` (y `TransferItem` también `selectedUnitName`). Todos son opcionales y retrocompatibles; no requieren migración.
2. **Display:** la regla de presentación vive en el frontend (`UnitDisplayFormatter`): la unidad superior solo se usa si la cantidad base es divisible por su factor; si no, se muestra en la unidad estándar (ej. `1.5 Quintal → 150 Libra`). El backend sigue guardando cantidades y dinero como `int`.
3. **Búsqueda rápida (frontend-only):** no inserta ítems con cantidad base `0`; con stock `0` y `restrictStock` no inserta; sin `restrictStock` permite cantidad positiva y el backend decide.
4. **Borradores de transferencia (frontend-only):** `v3` guarda `baseUnitName`, `standardUnitName`, `standardUnitFactor`, `selectedUnitIndex`, `conversionFactor` y `selectedUnitName` por fila. `v2` reconvierte cantidad/costo con el factor guardado; `v1` o base cambiada infiere `defaultUnitIndex`, marca `needsUnitReview` y permite continuar con advertencia.
5. **Stock:** la política no cambió; el backend sigue decidiendo con `LET_NEGATIVE`/LITE.
6. **Verificación:** `ruff check` y `ty check` OK; `pytest` **14/14**; `git diff --check` OK. En frontend, `flutter analyze` limpio y `flutter test` **83/83**.

### Limitaciones Residuales
- Las tablas/list views de inventario y transferencia (frontend) guardan cantidad display `int`; no admiten fracciones en unidad estándar.
- Con `defaultUnitIndex = 0`, la regla considera “superiores” a todas las unidades extra; revisar en escalas personalizadas.
- Los documentos viejos sin metadata conservan el fallback decimal en la unidad seleccionada.
- No se ejecutó hot reload ni prueba manual de UI.
- **No hay commit.**

## Renombres de Fracciones y Contrato de Costos (Noviembre 2026)
### Objetivo
Alinear las semillas de unidades con los nombres `1/4 ...`/`1/2 ...` y documentar la presentación de costos base vs unidad seleccionada.

### Resumen
1. **Semillas:** `create_default_unit_scales.py` usa `1/4 Libra`, `1/4 Litro`, `1/4 Metro`, `1/4 Caja xN (M u)`, `1/2 Caja xN (M u)`, `1/4 Docena (3 u)` y `1/2 Docena (6 u)`.
2. **Sin cambios de contrato:** factores, `defaultUnitIndex`, cantidades (`int`) y dinero (`int`) no cambian.
3. **Base de datos:** si ya existen escalas con los nombres viejos, `create_unit_scale_if_absent` no las renombra; hay que recrearlas o migrarlas. Con BD vacía, el reinicio crea los nombres nuevos.
4. **Presentación:** el frontend muestra la fila base primero en la comparación de costos (`UnitCostComparison`) y ya no muestra el factor crudo en las etiquetas de unidad.
5. **Verificación:** `ruff check` y `ty check` OK; `pytest` **14/14**; sin commit.


## Fecha: 2026-11-10
### Objetivo
Agregar la imagen corporativa global (`companyLogoUrl`) a `AppSettings` para uso estético en el frontend.

### Resumen
1. **Modelo:** `BaseAppSetting` y `UpdateAppSetting` incluyen `companyLogoUrl: str | None = None`; los documentos existentes son retrocompatibles sin migración.
2. **Persistencia:** el PATCH parcial existente guarda la URL y refresca la caché de `AppSettingsTool`; no se modificaron repositorios, datasources ni controladores.
3. **Frontend:** `AppSettingsScreen` sube JPG/PNG con `ImageUploader` y guarda la URL al instante; el home, el Panel Administrativo y el selector multi-sucursal consumen el logo mediante `CompanyLogo`.
4. **Verificación:** `ruff check` y `ty check` OK; `flutter analyze` limpio y test de serialización aprobado.
5. **No hay commit.**

## Fecha: 2026-11-10 (Parte 2)
### Objetivo
Agregar totales y desglose por tipo de gasto (`expenses`) al endpoint `GET /api/v1/reports/total-results-by-date-range`, de forma retrocompatible.

### Resumen de Implementación
1. **Modelos:** `ExpenseTypeTotal` y `ExpenseTotals` en `repos/v1/expenses/models/expense_totals_model.py`, exportados desde el paquete de gastos.
2. **Agregado Mongo:** `ExpensesCollection.get_expenses_totals_in_range` filtra por `date` (no `createdAt`), `branchId`, `isDeleted=False`, `isActive=True` y opcionalmente `createdBy.id`; agrupa por `type` con `total`, `paid` (solo `status == "paid"` sobre `amount`) y `count`, y calcula `pending = total - paid`.
3. **Capas:** datasource y repository delegan/validan el resultado como `ExpenseTotals`; el controller lo inyecta en `TotalsResult` con manejo de errores no fatal (`logger.exception` + `expenses=None`).
4. **Índice:** se agregó `IndexModel([("branchId", 1), ("date", -1)])` a `ExpensesCollection.create_indexes()` sin eliminar los existentes.
5. **Verificación:** `ruff check` y `ty check` OK; sin cambios en el router de reportes, `/expenses` ni `get_expenses_summary_in_range`. No hay commit.

## Fecha: 2026-11-10 (Parte 3)
### Objetivo
Implementar el backend de `AdjustmentRequest`: solicitudes de conteo fisico con flujo de aprobacion y aplicacion atomica de ajustes de inventario.

### Resumen de Implementacion
1. **Generacion CLI:** `onion repo-mongo adjustment_request --version 1 --output-dir packages/kardex-business/src/kardex` y `onion router adjustment_request --version 1 --output-dir app`; se elimino el `kardex/config/onion-config.toml` generado y se registro `AdjustmentRequests` en `app/config/onion-config.toml`.
2. **Modelos:** `BaseAdjustmentRequest`, `CreateAdjustmentRequest`, `UpdateAdjustmentRequest`, `AdjustmentRequestInDb`, `AdjustmentRequestItem`, `CreateAdjustmentRequestItem`, `ApproveAdjustmentRequest` y `CancelAdjustmentRequest` con timestamps Unix ms, `isDeleted` y estado `pending|approved|cancelled`.
3. **Snapshot de inventario:** create/update recalculan `systemStock`, `difference`, `subtotal`, `entryTotal` y `exitTotal` desde `ProductAccounts`; nunca confian en valores del cliente.
4. **Aprobacion:** `AdjustmentRequestManager.approve` valida estado pendiente, autoria distinta al aprobador y ejecuta `process_adjustment_request` en una sola transaccion Mongo con mutex compartido y reintentos para el codigo 112. Genera `AdjustExit` y/o `AdjustEntry` segun el signo de la diferencia almacenada.
5. **Inmutabilidad y cancelacion:** update/delete/cancel solo operan sobre solicitudes pendientes; cancelar no altera stock.
6. **API:** router `/adjustment-requests` con CRUD, `approve` y `cancel`; listado con `ListResponse(count, data)` y notificaciones Telegram por cada documento generado.
7. **Verificacion:** `ruff check` y `ty check` OK; pruebas de humo de repositorio y manager con dobles en memoria. No hay commit.

## Fecha: 2026-11-10 (Parte 4)
### Objetivo
Refactorizar `process_adjustment_request` al patron Pipeline-Steps, con contexto compartido, pasos independientes y resultado final tipado.

### Resumen de Implementacion
1. **Base generica:** `pipeline/base.py` define `PipelineStep`, `Pipeline`, `PipelineResult` y `should_execute` para omitir pasos sin trabajo.
2. **Contexto:** `AdjustmentRequestContext` concentra request, aprobador, sesion, sucursal, items separados, cuentas, lotes, documentos y resultado final.
3. **Steps:** se separaron validacion, split de items, carga de sucursal/productos/cuentas, preparacion/ejecucion/persistencia de salida, preparacion/ejecucion/persistencia de entrada, aprobacion y construccion del resultado.
4. **Orquestador:** `process_adjustment_request.py` quedo reducido a abrir la transaccion Mongo, ejecutar el pipeline y devolver `context.result.request`; la transaccion y el control de concurrencia siguen fuera de los steps.
5. **Inyeccion:** cada step recibe colecciones/repositorios por constructor; el builder arma el pipeline con los singletons del proyecto.
6. **Tests:** `test/test_adjustment_request_pipeline.py` cubre orden/skip del pipeline, split de items, validaciones de estado/autoaprobacion y construccion del resultado.
7. **Verificacion:** `ruff check`, `ty check` y `pytest` OK. No hay cambios de API, manager, frontend ni comportamiento funcional. No hay commit.

## Fecha: 2026-11-11
### Objetivo
Restringir la aprobación de `AdjustmentRequest` a los roles `Supervisor` y `Admin`, permitiendo la autoaprobación únicamente al rol `Admin`.

### Resumen de Implementacion
1. **Manager:** `AdjustmentRequestManager` recibe `UsersRepository`, resuelve el aprobador por `approvedBy.id`, rechaza usuarios inexistentes/inactivos (`APPROVER_NOT_FOUND`) y valida el rol (`APPROVAL_REQUIRES_SUPERVISOR_OR_ADMIN`).
2. **Autoaprobación:** se mantiene `SELF_APPROVAL_NOT_ALLOWED` para Supervisores y Operadores; el rol `Admin` puede aprobar su propia solicitud.
3. **Pipeline:** `AdjustmentRequestContext` incorpora `approver_role`; `ValidateRequestStep` aplica la misma regla dentro de la transacción.
4. **Creación:** sin cambios; las solicitudes creadas por un Admin siguen guardándose como `pending` hasta su aprobación explícita.
5. **Tests:** se actualizó `test/test_adjustment_request_pipeline.py` con casos de Operador, Supervisor y Admin (10 pruebas).
6. **Verificación:** `ruff check`, `ty check` y `pytest test/test_adjustment_request_pipeline.py` OK. No hay commit.

## Fecha: 2026-11-11 (Parte 2)
### Objetivo
Guardar como snapshot la imagen del producto en cada ítem de `AdjustmentRequest` para mostrarla en el formulario y detalle del frontend.

### Resumen de Implementacion
1. **Modelo:** `AdjustmentRequestItem` agrega `image: str = ""`; los documentos históricos sin el campo se validan con cadena vacía.
2. **Repositorio:** `_build_items` indexa los productos consultados por ID y asigna `image=product.image` al construir cada ítem, sin confiar en el payload del cliente.
3. **Compatibilidad:** el campo es aditivo; creación, edición, aprobación y cancelación conservan el comportamiento actual.
4. **Tests:** `test/test_adjustment_request_item_image.py` cubre serialización y compatibilidad con documentos antiguos.
5. **Verificación:** `ruff check`, `ty check` y `pytest` OK. No hay migraciones de Mongo ni cambios de API obligatorios.

## Fecha: 2026-11-14
### Objetivo
Implementar en `kardex-server` (rama `main`) el backend de la funcionalidad opcional de **Turnos y Caja**: apertura/cierre/arqueo de turnos por cajero y movimientos manuales de efectivo, con vinculacion aditiva de `shiftId` en facturas, recibos, devoluciones, notas de credito y gastos.

### Resumen de Implementacion
1. **Scaffolding Onion:** `onion repo-mongo shift shift-cash-movement` en `packages/kardex-business` y `onion router` en `app/`. Se elimino el `kardex/config/onion-config.toml` espurio, se registraron `Shifts` y `ShiftCashMovements` en `app/config/onion-config.toml` y se exportaron las colecciones en `mongo_collections/v1/__init__.py`. `mongo_service.py` y `base_mongo_collection.py` quedaron intactos.
2. **Modelos y filtros:** `ShiftInDb`, `ShiftPreview` (sin `closedAt`/`closedBy`), `CreateShift`, `CloseShiftRequest`, `UpdateShift`, `ShiftCashMovementInDb`; filtros `ShiftFilterParams` y `ShiftCashMovementFilterParams`. Dinero en `int`, campos `camelCase`, `amount > 0`, `countedCash >= 0`.
3. **Excepciones:** `ActiveShiftAlreadyExistsError` (409), `ShiftNotFound` (404), `CashMovementNotFound` (404) y `ShiftNotOpen` (400) en `kardex_exceptions.py`, registradas en `app/regis_exception_handlers.py`.
4. **Indices:** `Shifts` (`id` y `docNumber` unicos, `(openedBy.id, status)` unico parcial `ux_open_shift_per_user`, `(branchId, status, openedAt -1)`) y `ShiftCashMovements` (`id`, `docNumber` unicos, `shiftId`, `(branchId, createdAt -1)`). Se agrego `IndexModel([("shiftId", 1)])` no unico a `Invoices`, `Receipts`, `Devolutions`, `CreditNotes` y `Expenses`. Todo se ejecuta desde `mongo_indexes.create_indexes()` y no depende de `CURRENT_INDEX_VERSION`.
5. **Atomicidad:** `open_shift` genera `docNumber` antes del insert y traduce `DuplicateKeyError` (11000) a 409. `process_cash_movement` y `delete_cash_movement` usan `start_session()` + `start_transaction()`; `ExpensesRepository.create_expense`/`delete_expense_by_id` aceptan `session` opcional (retrocompatible).
6. **Consolidado:** agregaciones Mongo por turno (`` + ``) y funcion pura `compute_shift_totals` en `core/shift_register/shift_totals.py`. `expectedCash = initialCash + facturas cash + recibos cash + entradas - devoluciones confirmadas - salidas`. Devoluciones solo `confirmed`; notas de credito `approved`/`confirmed`/`applied` solo informativo; recibos con `isDeleted != True`.
7. **HTTP:** 7 endpoints en `/shifts` y 4 en `/shift-cash-movements`, ambos routers con `dependencies=[Depends(auth_middleware)]`, controllers delgados y `ListResponse[T]` en listados. `DELETE` de movimientos solo con turno `open` y borrado logico del movimiento y del gasto vinculado.
8. **Bandera:** `AppSettings.useShifts` (`false` por defecto) en `BaseAppSetting` y `UpdateAppSetting`; con `false` el comportamiento actual no cambia y `shiftId` queda `null`.
9. **Verificacion:** `ruff check` OK; `ty check` OK sobre `app` y el paquete; `pytest test/test_shifts.py` (8 pruebas) OK. Quedan 9 diagnosticos preexistentes de `ty` en `test/test_credit_note_policy.py` y `test/test_credit_note_vs_devolution.py`, ajenos a esta feature y sin modificar. No hay commit.

## Fecha: 2026-11-15
### Objetivo
Agregar el endpoint composite de arqueo de turno (`GET /api/v1/composite/shift-arqueo/{shift_id}`) para que el frontend obtenga turno, consolidado, movimientos y documentos en una sola llamada, sin cambiar el cierre ni la logica contable.

### Resumen de Implementacion
1. **Funciones puras:** `shift_totals.py` suma `totals_from_shift_document`, `is_document_counted` (con constantes de estados/colecciones) y `resolve_totals_source`.
2. **Armado:** `core/shift_register/shift_arqueo.py` expone `build_shift_arqueo`; turno `open` recalcula en vivo, turno `closed` devuelve el consolidado persistido (`stored`). Usa `asyncio.gather` para totales + 5 listados y consulta `limit + 1` para calcular `truncated`.
3. **Modelos:** `ShiftArqueoDocument`, `ShiftArqueoTotals`, `ShiftArqueoMeta` y `ShiftArqueoResponse` en `repos/v1/shifts/models/shift_arqueo_model.py` (exportados desde `repos.v1.shifts`).
4. **Colecciones:** `fetch_documents_by_shift` con ``, ` createdAt`, `` y proyeccion minima en invoices, receipts, devolutions y credit_notes. Movimientos reutilizan el repositorio existente.
5. **HTTP:** endpoint aditivo en `composite_router` con `includeDocuments` y `documentsLimit` (1..1000); controller delega en `build_shift_arqueo`.
6. **Docs y tests:** ficha en `wiki/modules/composite.md` y 4 pruebas puras nuevas en `test/test_shifts.py` (roundtrip de totales, defaults, reglas counted y live/stored). `ruff`, `ty` y `pytest` (57 pruebas) OK. No hay commit.

## Fecha: 2026-11-17
### Objetivo
Cerrar hallazgos de integridad de la feature de productos no inventariables y servicios (`productType`).

### Resumen de Implementacion
1. **Anulacion de notas de credito:** `reverse_credit_note` resuelve el tipo de cada item y solo resta stock a `item`; servicios y no inventariables ya no quedan con existencias negativas al anular una NC de devolucion.
2. **Transiciones de tipo:** `item -> nonInventory/service` se bloquea si existe `currentStock` distinto de 0 o `promiseStock > 0` en cualquier sucursal; se elimino el asentamiento de cierre y el borrado silencioso de existencias. `nonInventory/service -> item` reinicia costos con `reset_product_accounts_stock_and_cost_with_session` y regresa el producto al catalogo global sin aprovisionar cuentas en otras sucursales.
3. **Sucursal inmutable:** `UpdateProduct.branchId` solo se honra en la conversion `item -> nonInventory/service`; en cualquier otra actualizacion se descarta y el producto conserva la sucursal donde fue creado. La sucursal de un servicio o no inventariable no puede moverse (el middleware `multi_tenant_middleware` no esta cableado, por eso la conversion sigue recibiendo la sucursal en el body).
4. **Guard de inventario:** `ensure_inventory_products` rechaza IDs inexistentes (`PRODUCT_NOT_FOUND`) e ignora productos con `isDeleted`; `fetch_product_types_map` tambien ignora borrados. Se agrego el guard a `process_incoming_transfer` y `legacy_incoming_tranfer`.
5. **Validaciones:** `UpdateProductAccount`, `AddToProductAccount` y `SubstractToProductAccount` usan `Field(ge=0)`; `process_create_product_with_data` valida la sucursal con `resolve_required_branch_id` antes de crear cuentas o perfiles.
6. **Tests:** `test/test_product_types.py` cubre transiciones, inmutabilidad de sucursal, anulacion de NC, guard de productos inexistentes/borrados, rangos negativos y traslado entrante con servicios (20 pruebas). Suite completa: 83 passed.
7. **Verificacion:** `ruff check` OK; `ty check` solo reporta los 9 diagnosticos preexistentes de `test/test_credit_note_policy.py` y `test/test_credit_note_vs_devolution.py`. Sin commit.

---

## Fecha: 2026-11-24
### Objetivo
Soporte de `priceUnitFactor` y migración de escalas continuas (`Libra`, `Litro`, `Metro`) de cuartos (`1/4`) a centésimas (`0.01`, `priceUnitFactor = 100`) con 100% retrocompatibilidad, más correcciones derivadas de la revisión de código.

### Cambios Implementados
1. **Modelos Pydantic:** Agregado `priceUnitFactor: int = Field(default=1, ge=1)` en `BaseUnitScale`/`UpdateUnitScale`, `BaseProduct`/`UpdateProduct`, `InventoryProduct`, `SaleItem`, `EntryItem`, `ExitItem`, `TransferItem` y `CreateAdjustmentRequestItem`.
2. **Semillas (`create_default_unit_scales.py`):** Reemplazadas las escalas continuas de `1/4` por `0.01 Libra`, `0.01 Litro` y `0.01 Metro` (`conversionFactor = 100`, `priceUnitFactor = 100`) con limpieza automática de los pares `1/4` en `OLD_DEFAULT_SCALES`.
3. **Cálculos y consultas:**
   - `calculate_line_amount` con aritmética entera half-up (alineada con Dart `.round()`).
   - `fetch_product_types_and_price_factors_map` en una sola consulta a `Products` para facturas y pedidos.
   - `ensure_inventory_products` retorna `{productId: priceUnitFactor}` para fijar el factor server-side en entradas, salidas, ajustes y traslados sin queries extra.
   - Corregido fallback de `hold_sales_repository.py`, `orders_controller.py`, `adjustment_requests_repository.py`, `bi/repository.py` y `product_accounts_collection.py` (`get_total_current_stock` con `$floor(... + 0.5)`).
4. **Guard de inmutabilidad (`product_type_lifecycle.py`):** Bloquea el cambio de `priceUnitFactor` si hay stock, promesa o transacciones, excepto durante la transición `item -> service/nonInventory` (que ya valida stock 0).
5. **Tests:** `test/test_price_unit_factor.py` + verificación con `ruff check`, `ty check` y `pytest`.

---

## Fecha: 2026-11-27
### Objetivo
Eliminar la restricción que obligaba a usar Notas de Crédito para devoluciones de facturas a crédito, permitiendo devoluciones directas en facturas a crédito sin abonos (`amountPaid == 0` y `status == "open"`) y manteniendo el comportamiento habitual en contado, sin afectar el efectivo de turnos/reportes y validando el tope acumulado entre Devoluciones y Notas de Crédito.

### Resumen de Implementación
1. **Modelo (`devolution_model.py`):** Agregado `originalInvoicePaymentType: str | None = None` en `BaseDevolution` y `UpdateDevolution`.
2. **Validación en creación y confirmación (`devolution_register.py`, `devolutions_controller.py`, `process_devolution.py`):**
   - `DevolutionRegister.create_devolution` valida la factura y fija `originalInvoicePaymentType = invoice.paymentType`.
   - En facturas `credit`, se permiten devoluciones siempre que `amountPaid == 0` y `status == "open"`; se rechazan con `InvalidOperation` si tienen abonos o están pagadas (`partiallyPaid` / `paid`). Facturas de contado continúan permitiéndose sin restricciones de pago.
3. **Cruce acumulado (`process_credit_note.py` y `devolution_register.py`):** Agregado `sum_previously_returned_from_devolutions` (con soporte `invoiceItemIndex` y fallback determinista legacy) sumado en `_recalculate_devolution_items` y en `_validate_returned_quantities`.
4. **Turnos, Reporte Diario y Cobranza Compuesta (`devolutions_collection.py`, `shift_totals.py`, `shift_arqueo.py`, `composite_controller.py`):**
   - `get_totals_by_status_by_shift` y `fetch_confirmed_devolutions_total` filtran `originalInvoicePaymentType != "credit"`.
   - `is_document_counted` y `_to_arqueo_document` exponen `paymentMethod = originalInvoicePaymentType` y marcan `counted = False` en devoluciones de crédito.
   - `CompositeController.get_client_pending_invoices` filtra devoluciones vinculadas a las facturas pendientes.
5. **Verificación:** `ruff check`, `ty check` y `pytest test/test_credit_note_vs_devolution.py test/test_credit_note_policy.py test/test_shifts.py` (`45 passed`) e `import main` OK.
6. **Correcciones de Auditoría (`C1`, `C4`, `A1–A4`):**
   - **A1 (`process_devolution.py`):** Reingreso de `abs(item.quantity + item.bonQuantity)` al confirmar devoluciones (clientes y anónimas).
   - **C1 / A3 (`process_receipt.py`, `devolutions_collection.py`, `credit_notes_collection.py`):** Validación transaccional estricta de `appliedDevolutions` (existencia, sin duplicados, `status == "confirmed"`, `clientId`, `originalInvoicePaymentType in ("credit", None)`, `0 < amountApplied <= total`) y rechazo de facturas con devoluciones `open`.
   - **A4 (`reverse_receipt.py`):** Corregido `status="available"` → `status="confirmed"` al revertir recibos.
   - **C1 / C4 (`composite_controller.py`):** `get_client_pending_invoices` consulta devoluciones sin restringir por `branchId` activo y suma solo `confirmed` en `summary.totalDevolutions`.
   - **A2 (`report_manager.py`, `daily_report_maker.py`, `reports_controller.py`):** `totalReceiptCash` usa `totalReceipts` (efectivo real) en lugar de `totalAppliedInvoices`.
   - **Verificación ampliada:** `ruff check`, `ty check` y `pytest` (`69 passed` incluyendo `test_devolution_credit_audit_fixes.py`).

---

## Fecha: 2026-11-27
### Objetivo
Agregar la opción global `allowCancellationsOutsideShift` para permitir crear y aprobar solicitudes de anulación de facturas y recibos pertenecientes a turnos ya cerrados, sin relajar las demás validaciones de anulación.

### Resumen de Implementación
1. **AppSettings (`app_setting_model.py`):** `allowCancellationsOutsideShift: bool = False` en `BaseAppSetting` y `bool | None = None` en `UpdateAppSetting`.
2. **Validadores (`validate_invoice_cancellable.py`, `validate_receipt_cancellable.py`):** al detectar un turno cerrado se consulta `AppSettingsTool`; si la bandera está activa no se lanza `InvalidOperation`. El resto de reglas (estado, abonos, devoluciones, notas de crédito y facturas aplicadas) permanece intacto.
3. **Alcance:** aplica a la creación y a la aprobación de solicitudes. Los arqueos de turnos cerrados conservan sus totales almacenados.
4. **Tests:** nuevos casos con turno cerrado y bandera activa; los rechazos existentes se mockean con la bandera en `False`.
5. **Documentación:** `wiki/modules/app_settings.md` actualizado con el campo y la regla de negocio.
6. **Verificación:** `ruff check` OK; `pytest` de anulaciones 17/17. La suite completa queda en 156 passed y 1 fallo preexistente en `test_user_roles.py` (el catálogo comercial espera 11 submodules y hoy hay 13). `ty check` solo reporta diagnósticos preexistentes en archivos de test.

---

## Fecha: 2026-11-27 — Correcciones de auditoría
### Objetivo
Aplicar las correcciones aprobadas tras la revisión de la opción `allowCancellationsOutsideShift`.

### Resumen de Implementación
1. **C1 (aprobado):** nuevo `require_settings_access` en `app_middleware` (autenticación + módulo `settings`/rol Admin). Se aplica a `POST`, listado, consulta por id, `PATCH` y `DELETE` de `/app-settings`; `GET /app-settings/current` queda público para el arranque de la app. El frontend protege `/settings` con sesión + `Modules.settings`.
2. **M4 (aprobado):** tests de creación y aprobación con turno cerrado/bandera activa para facturas y recibos, más casos negativos con devoluciones activas y facturas anuladas.
3. **B1 (aprobado):** se restauró la aserción de `useReceiptCancellations` junto a la nueva bandera; el widget test del switch quedó en el frontend.
4. **B3 (aprobado):** documentación y subtítulo del switch advierten sobre reportes vivos y reembolso de efectivo.
5. **M2:** se resolvió en el frontend con PATCH parcial de solo campos modificados.
6. **Verificación:** `ruff check` OK; `pytest` de anulaciones y accesos de settings 27/27; `flutter analyze` sin issues y widget test del switch aprobado.
7. **N2 (aprobado):** `wiki/modules/INDEX.md` actualizado con el guard `JWT + settings` y la excepción pública de `GET /app-settings/current`.
8. **Deuda pendiente por decisión del usuario:** N1 (redirect web en `AuthInitial/AuthLoading`), N3 (cobertura del widget test), N4 (creación de recibo con turno cerrado), N5 (tests de integración de rutas) y N6 (semántica Admin/root backend vs frontend).

---

## Fecha: 2026-11-27 — Redondeo hacia arriba en facturas
### Objetivo
Agregar la opción global `roundUpInvoiceTotals` (`False` por defecto) para redondear hacia arriba los subtotales de línea y ajustar los descuentos hacia abajo, dejando el total de la factura en unidades enteras.

### Resumen de Implementación
1. **AppSettings (`app_setting_model.py`):** `roundUpInvoiceTotals: bool = False` en `BaseAppSetting` y `bool | None = None` en `UpdateAppSetting`.
2. **Normalización (`process_invoice.py`):** `normalize_invoice_discounts(..., round_up=False)` redondea el subtotal de cada línea hacia arriba y los descuentos de línea/global hacia abajo; el total queda entero y se mantiene `subtotal - descuentos = total`. No se agrega un campo de redondeo.
3. **Registro de facturas (`invoice_register.py`):** `InvoiceRegister` lee `AppSettingsTool` y pasa `round_up` a `process_invoice`/`process_anon_invoice`. Aplica a facturas directas, anónimas y conversiones; no a órdenes ni cotizaciones.
4. **Tests:** `test_invoice_discounts.py` agrega casos de subtotal redondeado, descuentos de línea/global redondeados hacia abajo y default `False`.
5. **Documentación:** `wiki/modules/app_settings.md` actualizado con el campo y la sección de redondeo.
6. **Correcciones de auditoría aprobadas (M2):** `process_anon_invoice` ahora normaliza después de `_prepare_and_execute_invoice_inventory`, garantizando que `priceUnitFactor` ya esté resuelto al calcular subtotales y redondeos.
7. **Deuda pendiente:** B1/B2/B3 y cobertura adicional documentadas en `../deuda_tecnica_pendiente.md`.
8. **Verificación:** `ruff check` OK; `pytest` de descuentos y anulaciones aprobado; `ty check` filtrado a archivos modificados sin diagnósticos.

---

## Fecha: 2026-11-27 — Validación de pagos en recibos
### Objetivo
Rechazar recibos con pagos incoherentes (método, moneda, monto recibido o cambio) antes de persistirlos, para proteger el arqueo y el comprobante impreso.

### Resumen de Implementación
1. **Nueva validación (`core/receipt_register/validate_receipt_payment.py`):** rechaza total negativo y montos aplicados negativos; exige referencia bancaria para tarjeta/transferencia; si hay `paymentDetail`, exige efectivo, total mayor que cero, moneda primaria o secundaria habilitada, tasa configurada válida, monto recibido convertido mayor o igual al total y cambio exacto. La conversión usa redondeo mitad hacia arriba para coincidir con Dart.
2. **Integración (`process_receipt.py`):** la validación se ejecuta antes de abrir la transacción. `AppSettingsTool` solo se consulta cuando hay `paymentDetail`, manteniendo la compatibilidad con recibos legacy y con tests que no inicializan Mongo.
3. **Compatibilidad:** los recibos en efectivo sin `paymentDetail` siguen permitidos; los pagos con tarjeta/transferencia sin referencia ahora se rechazan; la moneda secundaria requiere `allowSecondaryCurrencyPayment` y una tasa válida.
4. **Tests:** nuevo `test/test_receipt_payment_validation.py` con 16 casos (efectivo primario/secundario, moneda secundaria deshabilitada, tasa inválida, tarjeta/transferencia, cambio incorrecto, moneda inválida, total cero, montos negativos y recibos legacy).
5. **Verificación:** `ruff check` y `ty check` filtrados sin issues; `pytest -q` **188 passed**.
6. **Sin commit.** La sincronización `main` → `lite` queda pendiente para el lote final por decisión del usuario.

---

## Fecha: 2026-11-27 — Lote 1: Policy Object para AppSettings y pagos de recibos
### Objetivo
Extraer reglas de configuración y de validación de pagos de recibos a objetos de política puros, sin IO ni dependencias HTTP, preservando exactamente el comportamiento y los mensajes existentes.

### Resumen de Implementación
1. **Nuevo paquete `core/policies/`:** `AppSettingsPolicy` interpreta `AppSettingInDb | None` sin consultar Mongo ni usar `AppSettingsTool`; expone `converted_order_shift_policy`, `round_up_invoice_totals` y `allows_cancellations_outside_shift`. Con `settings=None` aplica defaults conservadores (`NEVER`, `False`, `False`).
2. **`ConvertedOrderShiftPolicy(str, Enum)`:** valores `NEVER`, `OPTIONAL`, `REQUIRED`; propiedades `links_to_shift` (OPTIONAL/REQUIRED) y `requires_open_shift` (solo REQUIRED). Centraliza la tabla de verdad de `useShifts` / `chargeConvertedOrdersToShift` / `requireShiftForConvertedOrders`.
3. **`ReceiptPaymentPolicy` (`core/receipt_register/receipt_payment_policy.py`):** `evaluate(receipt)` devuelve `ReceiptPaymentDecision(allowed, reason)` replicando el orden y los mensajes de `validate_receipt_payment` (total y montos negativos, referencia bancaria, `paymentDetail` solo en efectivo, settings ausente, monedas permitidas, moneda secundaria habilitada y tasa válida, monto recibido con redondeo mitad hacia arriba y cambio exacto). `_round_half_up` queda como helper privado.
4. **Integraciones:** `OrdersController` usa `converted_order_shift_policy` y conserva el HTTP 400 cuando falta `shiftId`; `InvoiceRegister` usa `round_up_invoice_totals`; `process_receipt` evalúa la policy y solo consulta settings cuando hay `paymentDetail`. `validate_receipt_payment` queda como wrapper delgado que lanza `InvalidOperation`.
5. **Tests:** `test/test_app_settings_policy.py` cubre las 8 combinaciones de turnos, las propiedades derivadas, redondeo, anulaciones fuera de turno y `settings=None`. `test/test_receipt_payment_policy.py` cubre la API de decisión para los casos permitidos y cada motivo de rechazo, incluido el redondeo mitad hacia arriba.
6. **Verificación:** `ruff check` OK; `ty check` OK; `pytest` dirigido a policies, validación de recibos y cancelaciones **80 passed**; suite completa **234 passed**. Sin levantar servicios ni tocar Mongo.
7. **Correcciones post-revisión:**
   - `AppSettingInDb` y `CreateReceipt` se importan solo bajo `TYPE_CHECKING` con `from __future__ import annotations`, evitando cargar módulos Mongo al importar las policies.
   - `allows_cancellations_outside_shift` ahora lo consumen `validate_invoice_cancellable` y `validate_receipt_cancellable`; se eliminó la lectura directa de la bandera.
   - `ReceiptPaymentDecision.__post_init__` exige `reason` no vacío cuando `allowed=False`; los consumidores usan `cast(str, decision.reason)` y se eliminó el fallback redundante.
   - Tests extra: referencia bancaria solo-espacios, wrapper con `settings=None` + `paymentDetail`, y decisión denegada con `None`, `""` y `"   "`.
   - Wiki actualizada: `wiki/modules/app_settings.md` sección 7 y `wiki/conventions.md` sección 4.1; se aclara que la policy lanza `InvalidOperation` y el mapeo HTTP vive en `app/regis_exception_handlers.py`.
8. **Sin commit.** Cambios locales en la rama `main`.

---

## Fecha: 2026-11-27 — Lote 2: Policy Object para anulación de facturas y recibos
### Objetivo
Extraer las reglas de anulación de facturas y recibos a policies puras, reutilizando `CancellationDecision` como contrato común y preservando exactamente el orden de validaciones, las consultas async, los cortes tempranos y los mensajes existentes.

### Resumen de Implementación
1. **`core/policies/cancellation_decision.py`:** nuevo `CancellationDecision(allowed, reason)`; un rechazo exige `reason` no vacío (`ValueError` en caso contrario). El barrel `core/policies/__init__.py` lo exporta, pero no reexporta las policies de anulación para evitar ciclos.
2. **`InvoiceCancellationPolicy` (`core/invoice_cancellation_register/invoice_cancellation_policy.py`):** etapas `header_decision` (anulada, borrador, crédito con abonos/pagada), `shift_decision` (turno `open` o ausente permitido; cerrado solo con `allowCancellationsOutsideShift`), `devolutions_decision` y `credit_notes_decision`. Las constantes `ACTIVE_DEVOLUTION_STATUSES` y `ACTIVE_CREDIT_NOTE_STATUSES` se movieron aquí.
3. **`ReceiptCancellationPolicy` (`core/receipt_cancellation_register/receipt_cancellation_policy.py`):** `header_decision` (recibo eliminado, devoluciones/notas aplicadas), `shift_decision` y `applied_invoice_decision` (factura inexistente o en `cancelled`/`draft`).
4. **Orquestadores:** `validate_invoice_cancellable` y `validate_receipt_cancellable` conservan las mismas consultas y su orden; solo consultan `AppSettingsTool` cuando el turno existe y no está `open`, y traducen la primera decisión denegada a `InvalidOperation` mediante `_ensure_allowed`. Se mantienen los imports `ShiftsCollection`, `DevolutionsCollection`, `CreditNotesCollection`, `InvoicesCollection` y `AppSettingsTool` en sus módulos para los parches de los tests existentes.
5. **Tests:** nuevos `test/test_invoice_cancellation_policy.py` y `test/test_receipt_cancellation_policy.py` con tablas de decisión sin base de datos: estados de cabecera, turnos abiertos/cerrados/ausentes, devoluciones y notas en cada estado activo e inerte, facturas aplicadas y la invariante de `CancellationDecision`.
6. **Documentación:** `wiki/conventions.md` sección 4.1 y `wiki/modules/app_settings.md` secciones 5 y 7 actualizadas con las nuevas policies y el contrato de decisión.
7. **Revisión:** revisor independiente **APROBADO CON MENORES**. Se agregaron casos de crédito parcial y efectivo con abonos, tests de regresión para turno sin `status`, aserciones de `session`/`client_id=None`, aserción estricta de `reason` en decisiones permitidas y precisión en la wiki sobre las etapas de recibos.
8. **Verificación:** `ruff check` sin errores en los archivos del lote; `ty check` OK; `pytest` dirigido **76 passed**; suite completa **288 passed**. Sin levantar servicios ni tocar Mongo. Se detectaron 3 errores E402 preexistentes en `test/test_user_roles.py`, ajenos a este lote.
9. **Sin commit.** Cambios locales en la rama `main`.
