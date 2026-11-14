# Índice de Módulos del API (`wiki/modules/INDEX.md`)

Catálogo completo de los **48 módulos** montados en `app/api/v1/router.py`. Sirve para que un agente pase de una tarea de negocio al router, repositorio y colección correctos sin explorar el árbol a ciegas.

> **Cómo usar:** usa este documento cuando ya sepas el dominio (ventas, inventario, catálogos, finanzas, configuración) y necesites los archivos exactos. El detalle profundo solo existe hoy para 4 módulos; el resto se documenta aquí a nivel de mapa.
>
> Lectura previa: [`../INDEX.md`](../INDEX.md) (contexto general y estructura), [`../architecture.md`](../architecture.md) (capas y flujos) y [`../conventions.md`](../conventions.md) (reglas de código).

---

## Leyenda

| Símbolo | Significado |
| :--- | :--- |
| **JWT** | `dependencies=[Depends(auth_middleware)]` en el `APIRouter` |
| **API Key** | `dependencies=[Depends(api_key_middleware)]` |
| **Super** | `validate_super_token` (endpoints administrativos globales) |
| **⚠** | Sin guard declarado a nivel de router; verifica endpoint por endpoint |
| **—** | No aplica / el módulo reutiliza repos de otros módulos |

Rutas: todas cuelgan de `/api/v1`. La columna *Repo* es relativa a
`packages/kardex-business/src/kardex/repos/v1/`; *Proceso* a
`packages/kardex-business/src/kardex/core/`; *Colección* es el `collection_name`
real de `services/mongo_collections/v1/`.

---

## 1. Ventas y Cobranza (10 módulos)

| Módulo | Prefix | Repo | Colección | Proceso | Guard | Doc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoices` | `/invoices` | `invoices` | `Invoices` | `invoice_register` | JWT | — |
| `orders` | `/orders` | `orders` | `Orders` | `order_register` | JWT | — |
| `hold_sales` | `/hold-sales` | `hold_sales` | `HoldSales` | — | JWT | — |
| `receipts` | `/receipts` | `receipts` | `Receipts` | `receipt_register` | JWT | — |
| `devolutions` | `/devolutions` | `devolutions` | `Devolutions` | `devolution_register` | JWT | — |
| `credit_notes` | `/credit-notes` | `credit_notes` | `CreditNotes` | `credit_note_register` | JWT | [credit_notes.md](./credit_notes.md) |
| `invoice_devolutions` | `/invoice-devolutions` | — (`invoices` + `devolutions`) | `Invoices` / `Devolutions` | — | JWT | — |
| `composite` | `/composite` | — (`invoices` + `devolutions` + `credit_notes`) | — (agrega) | — | JWT | [composite.md](./composite.md) |
| `product_prices` | `/product-prices` | `product_prices` | `ProductPrices` | — | ⚠ | — |
| `product_sale_profiles` | `/product-sale-profiles` | `product_sale_profiles` | `ProductSaleProfiles` | — | JWT | — |

**Endpoints clave**

- `POST /invoices`, `GET /invoices`, `GET /invoices/{id}`, `GET /invoices/pending/{client_id}`.
- `POST /orders`, `POST /orders/make-invoice/{order_id}`, `PATCH /orders/cancel/{order_id}`.
- `POST /receipts`, `GET /receipts/totals`, `GET /receipts/history`, `PATCH /receipts/{id}`.
- `POST /credit-notes`, `POST /credit-notes/{id}/approve`, `POST /credit-notes/{id}/reject`, `GET /credit-notes/all/active`.
- `POST /devolutions`, `PATCH /devolutions/confirm/{id}`, `PATCH /devolutions/cancel/{id}`, `GET /devolutions/all/active`.
- `GET /composite/client-pending-invoices` (`clientId` + `branchId`).

**Notas de dominio**

- `credit_notes` sustituye progresivamente a `devolutions`; ambos conviven y `composite` consolida los tres saldos.
- `hold_sales` persiste ventas en espera por sucursal, no es un carrito local.

---

## 2. Inventario y Kárdex (14 módulos)

| Módulo | Prefix | Repo | Colección | Proceso | Guard | Doc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `products` | `/products` | `products` | `Products` | `product_register` / `lite/core/product_register` | ⚠ | — |
| `inventories` | `/inventories` | `inventories` | `ProductAccounts` | `inventory` | JWT | — |
| `entry_docs` | `/entry-docs` | `entry_docs` | `EntryDocs` | `product_ledger` | JWT | — |
| `entry_histories` | `/entry-histories` | `entry_histories` | `EntryDocs` | — | JWT | — |
| `exit_docs` | `/exit-docs` | `exit_docs` | `ExitDocs` | `product_ledger` | JWT | — |
| `exit_histories` | `/exit-histories` | `exit_histories` | `ExitDocs` | — | JWT | — |
| `adjust_entries` | `/adjust-entries` | `adjust_entries` | `AdjustEntries` | `adjust_ledger` | JWT | — |
| `adjust_exits` | `/adjust-exits` | `adjust_exits` | `AdjustExits` | `adjust_ledger` | JWT | — |
| `adjustment_requests` | `/adjustment-requests` | `adjustment_requests` | `AdjustmentRequests` (+ `ProductAccounts`) | `adjustment_requests` | JWT | — |
| `transfers` | `/transfers` | `transfers` | `Transfers` | `transfer_manager` | JWT | — |
| `expiration_logs` | `/expiration-logs` | `expiration_logs` | `ExpirationLog` | — | JWT | — |
| `product_accounts` | `/product-accounts` | `product_accounts` | `ProductAccounts` | — | ⚠ | — |
| `product_transactions` | `/product-transactions` | `product_transactions` | `ProductTransactions` | — | ⚠ | — |
| `product_stats` | `/product-stats` | `product_stats` | `ProductStats` | — | ⚠ | — |

**Endpoints clave**

- `POST /entry-docs` (formal) y `POST /entry-docs/direct` (sin kárdex); ídem `exit-docs`.
- `POST /entry-docs` genera logs de vencimiento cuando el ítem trae `expirationDate`.
- `GET /products/branch/{branch_id}`, `GET /products/branch/{branch_id}/search/{texto}`, `PATCH /products/{id}`.
- `GET /inventories?branchId=...`, `POST /inventories/reset-stock`.
- `POST /adjustment-requests`, `POST /adjustment-requests/{id}/approve`, `POST /adjustment-requests/{id}/cancel`.
- `POST /transfers`, `POST /transfers/{id}/receive`, `POST /transfers/{id}/cancel`.
- `GET /expiration-logs/near/{branch_id}/list`.
- `PATCH /product-accounts/products/{product_id}/branches/{branch_id}` (+ `/add`, `/substract`).

**Notas de dominio**

- **Doble flujo de inventario:** `product_ledger` (con `ProductTransaction` formal) vs. `*_direct` (movimiento atómico de alto rendimiento).
- El stock real vive en `ProductAccounts` por sucursal; `Products` es el maestro global.
- `inventory_engine.py` concentra la aritmética de existencias y validaciones de negocio.
- `adjustment_requests` usa un pipeline de pasos (`pipeline/steps/`) y al aprobar crea el documento de entrada/salida por ajuste.
- **Ojo:** `ExpirationLog` (clase) vs. `ExpirationLogs` (registro en `onion-config.toml`); verifica el nombre antes de consultar Mongo directamente.

---

## 3. Catálogos (8 módulos)

| Módulo | Prefix | Repo | Colección | Proceso | Guard | Doc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `product_categories` | `/product-categories` | `product_categories` | `ProductCategories` | — | ⚠ | — |
| `units` | `/units` | `units` | `Units` | — | JWT | — |
| `unit_scales` | `/unit-scales` | `unit_scales` | `UnitScales` | `default_values` (semilla) | JWT | [unit_scales.md](./unit_scales.md) |
| `clients` | `/clients` | `clients` | `Clients` | `client` | JWT | — |
| `client_groups` | `/client-groups` | `client_groups` | `ClientGroups` | — | JWT | — |
| `client_transactions` | `/client-transactions` | `client_transactions` | `ClientTransactions` | — (`finance` se usa desde facturas/clientes) | JWT | — |
| `suppliers` | `/suppliers` | `suppliers` | `Suppliers` | — | JWT | — |
| `branches` | `/branches` | `branches` | `Branches` | `default_values` | JWT | — |

**Endpoints clave**

- `POST /clients`, `GET /clients/balance`, `GET /clients/search/{texto}`, `POST /clients/initial-balance`.
- `GET /client-transactions`, `GET /client-transactions/{id}`.
- `POST /suppliers`, `GET /suppliers/search/{texto}`.
- `POST /branches`, `PATCH /branches/{id}` (incluye `isCommerce`).
- `POST /unit-scales`, `PATCH /unit-scales/{id}`.
- `GET /units`, `POST /product-categories`.

**Notas de dominio**

- `branches.isCommerce` decide si la sucursal vende (comercio) o solo almacena.
- Los límites de crédito del cliente se validan en facturación, no en el catálogo.
- `unit_scales` define la unidad base y factores enteros; es la fuente de verdad para conversiones de despacho.

---

## 4. Finanzas, Reportes y BI (8 módulos)

| Módulo | Prefix | Repo | Colección | Proceso | Guard | Doc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `expenses` | `/expenses` | `expenses` | `Expenses` | — | ⚠ | — |
| `expense_categories` | `/expense-categories` | `expense_categories` | `ExpenseCategories` (+ `Expenses`) | — | ⚠ | — |
| `daily_summaries` | `/daily-summaries` | `daily_summaries` | `DailySummaries` | `report_manager` | JWT | — |
| `executive_summaries` | `/executive-summaries` | `executive_summaries` | `ExecutiveSummaries` | `report_manager` | JWT | — |
| `reports` | `/reports` | — (agrega) | — | `report_manager` | ⚠ | — |
| `exports` | `/exports` | `products` | — (Excel) | — | ⚠ | — |
| `bi` | `/bi` | `bi` | — (agrega) | — | **API Key** | — |
| `admin_panels` | `/admin-panels` | — (`invoices`) | — (agrega) | — | JWT | — |

**Endpoints clave**

- `GET /expenses`, `POST /expenses`, `POST /expenses/add-to-amount-paid`, `DELETE /expenses/{id}`.
- `GET /reports/general-report`, `GET /reports/total-results-by-date-range`.
- `GET /daily-summaries`, `POST /executive-summaries`.
- `GET /exports/price-list` (descarga Excel/CSV vía `app/services/excel_service.py`).
- `GET /bi/invoices`, `/bi/invoice-items`, `/bi/cash-flow`, `/bi/inventory`, `/bi/customers`.
- `GET /admin-panels/...` (gráficas de los últimos 7 días).

**Notas de dominio**

- `reports`, `exports`, `bi` y `admin_panels` son **agregadores de solo lectura**: no tienen colección propia.
- `bi` está pensado para Power BI y se autentica con API Key, no con JWT.
- El reporte de gastos usa `createdAt` como fecha de registro; `date` es la fecha del documento.

---

## 5. Configuración, Seguridad e Importaciones (8 módulos)

| Módulo | Prefix | Repo | Colección | Proceso | Guard | Doc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `auths` | `/auths` | `users` (vía core) | `Users` | `security` | ⚠ (login público) | — |
| `users` | `/users` | `users` | `Users` | `security` | JWT | — |
| `user_roles` | `/user-roles` | `user_roles` | `UserRoles` | `role_manager` | ⚠ | — |
| `api_keys` | `/api-keys` | `api_keys` | `ApiKeys` | — | JWT | — |
| `app_settings` | `/app-settings` | `app_settings` | `AppSettings` | `default_values` | ⚠ | [app_settings.md](./app_settings.md) |
| `core_settings` | `/core-settings` | `core_settings` | `CoreSettings` | — | **Super** | — |
| `integrations` | `/integrations` | `integrations` | `Integrations` | — | ⚠ | — |
| `imports` | `/imports` | — (escribe en otros repos) | `Products` / `Clients` / `Suppliers` / `ProductAccounts` | `imports` | JWT | — |

**Endpoints clave**

- `POST /auths/login`, `POST /auths/refresh-token`, `POST /auths/change-password`, `GET /auths/servin-status`.
- `POST /users`, `GET /users/active?branchId=...`, `PATCH /users/{id}`.
- `POST /user-roles`, `PATCH /user-roles/{id}`.
- `POST /api-keys`, `PATCH /api-keys/{id}/toggle`, `DELETE /api-keys/{id}`.
- `GET /app-settings/current`, `PATCH /app-settings/{id}`.
- `POST /imports/preview?type=...`, `POST /imports/init-inventory`, `/imports/inventory`, `/imports/clients`, `/imports/suppliers`.
- `POST /integrations/telegram/test`.

**Notas de dominio**

- `GET /app-settings/current` es la lectura canónica de parámetros globales; se cachea en `AppSettingsTool`.
- `auths/login` debe ser público por diseño; no lo "arregles" agregando JWT al router.
- Las importaciones de inventario usan la sucursal virtual `0000-<branchId>` para el inventario inicial.
- `core_settings` exige super-token: es configuración de plataforma, no de negocio.

---

## 6. Módulos sin documentación dedicada

Solo estos 4 tienen documento propio en `wiki/modules/`:

- [`app_settings.md`](./app_settings.md)
- [`unit_scales.md`](./unit_scales.md)
- [`credit_notes.md`](./credit_notes.md)
- [`composite.md`](./composite.md)

Los otros **44** se cubren por ahora con este índice. Prioridad sugerida para futuras fichas (por impacto y complejidad):

| Prioridad | Módulos | Motivo |
| :--- | :--- | :--- |
| Alta | `invoices`, `receipts`, `adjustment_requests`, `transfers`, `imports` | Flujos atómicos, estados y efectos en stock/dinero. |
| Media | `entry_docs`, `exit_docs`, `products`, `orders`, `devolutions` | Núcleo operativo diario. |
| Media | `expenses`, `clients`, `client_transactions` | Impacto contable y de cartera. |
| Baja | `units`, `product_categories`, `api_keys`, `reports`, `bi` | CRUD o agregadores simples. |

---

## 7. Reglas de consistencia al crear un módulo nuevo

1. Genera el esqueleto con `onion crud <entidad> --version 1` (o `crud-mongo` si necesita colección).
2. Registra el router en `app/api/v1/router.py` con su prefijo.
3. Declara `collection_name` en `services/mongo_collections/v1/<entidad>_collection.py` y añádelo a `app/config/onion-config.toml`.
4. Añade el `APIRouter(..., dependencies=[Depends(auth_middleware)])` **desde el inicio**.
5. Crea el `filter_params` en `repos/v1/common/filter_params/` si el listado es paginado/filtrable.
6. Reutiliza `ListResponse[T]` para listados.
7. Documenta el módulo en `wiki/modules/` y enlázalo en este índice.
