# Módulo de Servicios Compuestos / Composite Router (`app/api/v1/composite`)

El módulo **Composite** implementa el patrón de arquitectura **API Composition / Aggregator (BFF - Backend for Frontend)**. Su propósito es consolidar múltiples fuentes de datos y modelos del sistema en respuestas compuestas y precalculadas en una única petición HTTP, optimizando la latencia de red y evitando múltiples viajes de ida y vuelta (*roundtrips*) desde el cliente Flutter.

---

## 1. Justificación Arquitectónica

Antes de la existencia de este router, pantallas con flujos multidominio (como **Facturas por cobrar al cliente / Cobranzas**) disparaban 3 consultas HTTP simultáneas:
1. `GET /api/v1/invoices/pending/{client_id}`
2. `GET /api/v1/devolutions/all/active?client_id=...&branch_id=...`
3. `GET /api/v1/credit-notes/?client_id=...&status=confirmed`

Con el patrón **Composite**, el servidor resuelve las 3 consultas internamente contra MongoDB en paralelo (`asyncio.gather`) con latencia casi nula, computa el balance canónico del cliente y entrega una única respuesta estructurada.

```mermaid
flowchart TD
    Flutter["Frontend (Flutter / Web / Mobile)"] -->|1 HTTP Request| CompositeRouter["/api/v1/composite/client-pending-invoices"]
    CompositeRouter --> Controller["CompositeController"]
    Controller --> InvoicesRepo["InvoicesRepository (Facturas pendientes)"]
    Controller --> DevolutionsRepo["DevolutionsRepository (Devoluciones activas)"]
    Controller --> CreditNotesRepo["CreditNotesRepository (Notas de crédito confirmadas)"]
    InvoicesRepo --> MongoDB[(MongoDB)]
    DevolutionsRepo --> MongoDB
    CreditNotesRepo --> MongoDB
```

---

## 2. Endpoints Disponibles

### `GET /api/v1/composite/client-pending-invoices`

Obtiene todas las facturas pendientes de cobro, devoluciones activas a favor y notas de crédito confirmadas disponibles de un cliente para una sucursal, junto con el resumen consolidado de totales.

- **Seguridad:** Requiere autenticación Bearer JWT (`auth_middleware`).
- **Query Parameters:**
  - `clientId` (o `client_id`, `str`, requerido): Identificador del cliente.
  - `branchId` (o `branch_id`, `str`, requerido): Identificador de la sucursal actual.

#### Respuesta JSON (`ClientPendingInvoicesCompositeResponse`):
```json
{
  "invoices": [
    {
      "id": "inv_123",
      "docNumber": "000452",
      "total": 50000,
      "amountPaid": 10000,
      "totalRemaining": 40000,
      ...
    }
  ],
  "devolutions": [
    {
      "id": "dev_789",
      "docNumber": "DEV-0012",
      "total": 5000,
      "status": "confirmed",
      ...
    }
  ],
  "creditNotes": [
    {
      "id": "cn_456",
      "docNumber": "NC-0008",
      "type": "amount",
      "amount": 10000,
      "status": "confirmed",
      ...
    }
  ],
  "summary": {
    "totalInvoices": 40000,
    "totalDevolutions": 5000,
    "totalCreditNotes": 10000,
    "netTotalPayable": 25000
  }
}
```

---

### `GET /api/v1/composite/shift-arqueo/{shift_id}`

Arqueo completo de un turno en **una sola llamada** (evita 6 roundtrips: turno + consolidado + movimientos + facturas + recibos + devoluciones + notas de crédito). Agregado puramente de lectura: no cierra el turno ni modifica nada.

- **Seguridad:** `auth_middleware` a nivel de `composite_router`.
- **Query Parameters:**
  - `includeDocuments` (`bool`, default `true`): si es `false` no ejecuta los 5 listados; devuelve listas vacías y `meta.truncated = null`.
  - `documentsLimit` (`int`, `ge=1`, `le=1000`, default `500`): tamaño máximo por listado.

#### Respuesta JSON (`ShiftArqueoResponse`):
```json
{
  "shift": { "id": "shift_1", "status": "open", "initialCash": 100000, "...": "ShiftInDb" },
  "totals": {
    "invoiceCashTotal": 50000,
    "expectedCash": 173000,
    "grandTotal": 127000,
    "...": "24 campos de ShiftTotals"
  },
  "cashMovements": [
    { "id": "mv_1", "shiftId": "shift_1", "type": "in", "amount": 5000, "...": "ShiftCashMovementInDb" }
  ],
  "invoices": [
    {
      "id": "inv_1",
      "docNumber": "000452",
      "amount": 50000,
      "paymentMethod": "cash",
      "status": "paid",
      "type": null,
      "clientName": "Cliente",
      "createdAt": 1731456000000,
      "referenceDocNumber": null,
      "counted": true
    }
  ],
  "receipts": [],
  "devolutions": [],
  "creditNotes": [],
  "meta": { "totalsSource": "live", "documentsLimit": 500, "truncated": false }
}
```

#### Reglas de negocio

- **`totalsSource`:** turno `open` → recalcula con `aggregate_shift_totals()` (`"live"`). Turno `closed` → usa el consolidado **persistido** en el documento (`totals_from_shift_document`) y devuelve `"stored"`, para que el arqueo coincida con el ticket impreso y no cambie con el tiempo.
- **`counted`:** mismas reglas que el consolidado. Facturas: `status != "cancelled"` (las canceladas se listan con `counted: false`). Recibos y movimientos: siempre `true` (los `isDeleted` se excluyen en la query). Devoluciones: solo `status == "confirmed"`. Notas de crédito: `status in ("approved", "confirmed", "applied")`.
- **Queries:** facturas `{"shiftId": id}` (incluye canceladas); recibos `{"shiftId": id, "isDeleted": {"$ne": true}}`; devoluciones y notas de crédito `{"shiftId": id}`; movimientos `{"shiftId": id, "isDeleted": {"$ne": true}}`.
- **Orden:** `createdAt` ascendente en los 5 listados (los movimientos se invierten tras leer los más recientes).
- **`truncated`:** cada consulta pide `limit + 1`; si alguna colección o los movimientos exceden `limit`, se recorta a `limit` y `truncated` pasa a `true`. Con `includeDocuments=false` vale `null`, que significa "documentos no solicitados" (no "lista completa").
- El consolidado lo calcula `kardex/core/shift_register/shift_totals.py`; el armado vive en `kardex/core/shift_register/shift_arqueo.py` y **no** altera `close_shift`.

---

## 3. Modelos Pydantic (`composite_models.py`)

- **`PendingCheckoutSummary`:**
  - `totalInvoices` (`int` en centavos): Sumatoria de `totalRemaining` de todas las facturas pendientes.
  - `totalDevolutions` (`int` en centavos): Sumatoria de devoluciones activas aplicables.
  - `totalCreditNotes` (`int` en centavos): Sumatoria de notas de crédito confirmadas disponibles.
  - `netTotalPayable` (`int` en centavos): Balance neto a pagar `max(0, totalInvoices - totalDevolutions - totalCreditNotes)`.
- **`ClientPendingInvoicesCompositeResponse`:**
  - `invoices: list[InvoiceInDb]`
  - `devolutions: list[DevolutionInDb]`
  - `creditNotes: list[CreditNoteInDb]`
  - `summary: PendingCheckoutSummary`

> Los modelos de `shift-arqueo` viven en `kardex/repos/v1/shifts/models/shift_arqueo_model.py` (`ShiftArqueoDocument`, `ShiftArqueoTotals`, `ShiftArqueoMeta`, `ShiftArqueoResponse`) porque reutilizan `ShiftInDb` y `ShiftCashMovementInDb`; se exportan desde `kardex.repos.v1.shifts`. Se dejaron fuera de `composite_models.py` para no crear dependencias del paquete de dominio hacia la capa web.

---

## 4. Guía para Futuros Desarrolladores / Agentes

Al incorporar nuevas pantallas o flujos en el frontend que requieran combinar datos de 2 o más entidades en un solo tiempo de carga (ej. estado de cuenta integral, cierre combinado de turno, o liquidaciones de caja):
1. **Evitar** disparar múltiples peticiones HTTP encadenadas en el cliente.
2. **Extender** `app/api/v1/composite/` agregando el endpoint agregado correspondiente.
3. Mantener siempre la convención de tipos (`camelCase` en atributos, montos enteros en centavos y timestamps Unix en milisegundos).
