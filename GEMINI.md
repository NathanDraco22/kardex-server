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
