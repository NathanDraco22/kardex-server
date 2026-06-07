# Contexto de Conversación - Code Review Transfer Optimization

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
