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
## Fecha: 2026-03-30
### Objetivo
Resumen general y entendimiento de la arquitectura y alcance del proyecto Kardex App.

### Entendimiento del Proyecto Kardex App

**1. Propósito General**
Es un sistema integral administrativo y punto de venta (ERP/POS multistore), diseñado para gestionar inventarios, ventas, finanzas y clientes a través de múltiples sucursales de manera sincronizada y robusta.

**2. Arquitectura de Software**
El proyecto opera con una arquitectura Cliente-Servidor separada:
*   **Backend (Python/FastAPI):** Se encarga de la lógica de negocio sólida. Implementa un patrón de capas (Routers -> Controllers -> Repositories -> DataSources). Utiliza MongoDB como base de datos aplicando pipelines de agregación avanzados y transacciones de multi-documentos para asegurar la consistencia en el registro de movimientos financieros e inventario (ACID).
*   **Frontend (Flutter):** Aplicación estructurada por módulos bajo el patrón BLoC (Cubit) para el manejo de estados (`View -> Cubit -> DataSource -> Models`). Administra la interfaz de usuario, navegación, visualización de datos (tablas, gráficos) y documentos (como diálogos de recibos, facturas).

**3. Dominios y Módulos Clave**
*   **Gestión de Inventario (Kardex):** Seguimiento detallado del stock y costos de productos. Soporta operaciones avanzadas como traslados (Transfers) entre sucursales optimizando los agrupamientos, preservando el costo promedio.
*   **Ventas y Facturación (Invoices / Receipts):** Generación de facturas de venta, procesamiento de cobros de deudas a clientes (Receipts) y control de devoluciones. Todos con sus correspondientes impresiones o vistas de interfaz (`invoice_viewer`, `receipt_writer`).
*   **Gestión de Clientes y Crédito:** Control de historial financiero, cuentas por cobrar, deudas activas e inicialización de saldos (`Initial Balance`) con registros atómicos tipo cargo/abono.
*   **Reportes y Resúmenes Diarios:** Generadores de resúmenes de efectivo, facturación, cuentas por cobrar y snapshot diario (`ReportManager` y `daily_report_maker.py`), con integraciones de notificaciones ejecutivas mediante bots (ej. Telegram).

**4. Reglas de Negocio Estrictas**
El sistema previene la duplicidad de saldos, obliga a realizar transacciones financieras con operaciones inmutables en la base de datos, y enfatiza en el "Clean Code" validando los estados del inventario previo al movimiento. Hay una clara directiva de cuidar el "Live Snapshot" de las deudas en vez de una sola sumatoria histórica.
