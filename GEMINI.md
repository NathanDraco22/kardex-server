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
2. **Mapeo Explícito**: Se corrigió un potencial bug de la migración de `entry_docs` donde los parámetros `camelCase` (`supplierId`, `clientId`) generaban error al enviarse como `**kwargs` a Mongo que esperaba `snake_case`. Se implementó un mapeo explícito en ambos controladores (`entry_docs` y `exit_docs`) garantizando compatibilidad.
