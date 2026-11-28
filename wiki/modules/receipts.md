# Documentación del Módulo: Recibos (`receipts`)

El módulo **Recibos (`Receipt`)** registra el cobro de facturas combinando pago monetario, devoluciones confirmadas y notas de crédito aprobadas. Cada recibo genera movimientos de cliente independientes por cada fondo aplicado y actualiza el saldo pendiente de las facturas.

---

## 1. Arquitectura del Módulo (Onion Pattern)

```text
kardex-server/
├── app/api/v1/receipts/
│   ├── receipts_router.py                 # Endpoints REST (JWT)
│   └── receipts_controller.py             # Controlador
└── packages/kardex-business/src/kardex/
    ├── repos/v1/receipts/
    │   ├── models/receipt_model.py        # Modelos Pydantic (camelCase)
    │   ├── data/receipts_datasource.py    # DataSource hacia MongoDB
    │   └── receipts_repository.py         # Repositorio de negocio
    ├── services/mongo_collections/v1/
    │   └── receipts_collection.py         # Colección Receipts
    ├── core/receipt_register/
    │   ├── receipt_register.py            # Validación de sucursal, cliente y turno
    │   ├── process_receipt.py             # Transacción atómica de registro
    │   └── reverse_receipt.py             # Reversión al eliminar un recibo
    └── core/policies/receipts/
        ├── receipt_payment_policy.py      # Coherencia del pago y del detalle en efectivo
        ├── receipt_application_policy.py  # Reglas puras de aplicación de fondos
        └── receipt_cancellation_policy.py # Reglas puras de anulación de recibos
```

---

## 2. Flujo de Aplicación (`process_receipt`)

1. `ReceiptRegister` valida que la sucursal y el cliente existan, y el turno si viene informado.
2. Se evalúa `ReceiptPaymentPolicy` (montos negativos, referencia bancaria, moneda y cambio).
3. Dentro de una transacción de MongoDB se calculan `total_funds` (pago + devoluciones + notas de crédito) y `total_applied` (facturas).
4. Se genera el `docNumber` con `CounterManager` si falta.
5. `ReceiptApplicationPolicy` valida la cuadratura de fondos, cada nota de crédito, cada devolución y cada factura, en ese orden.
6. Se inserta el recibo, se suma `amountApplied` a cada factura y se registran las transacciones de cliente: devoluciones (`subtype="devolution"`), notas de crédito (`subtype="credit_note"`) y pago monetario (`subtype="receipt"`).

Las validaciones de `ReceiptApplicationPolicy` se traducen a `InvalidOperation(reason)` mediante el helper privado `_ensure_allowed`; `ReceiptPaymentPolicy` conserva su traducción directa y las escrituras y movimientos financieros no contienen reglas de decisión.

---

## 3. Capa de Políticas (Policy Object)

`ReceiptApplicationPolicy` vive en `core/policies/receipts/receipt_application_policy.py` y es pura: sin FastAPI, Mongo, `AppSettingsTool`, `session` ni IO. Recibe modelos de dominio o documentos ya resueltos por el orquestador.

| Método de `ReceiptApplicationPolicy` | Regla evaluada | Motivo de rechazo |
| :--- | :--- | :--- |
| `funds_decision(*, total_funds, total_applied)` | Los fondos igualan exactamente lo aplicado a facturas. | `"Discrepancy Error: Total Funds (...) does not match Total Applied to Invoices (...)."` |
| `credit_note_duplicate_decision(credit_note_id, seen_ids)` | La nota de crédito no se repite en el recibo. | `"Nota de crédito duplicada en el recibo: ...."` |
| `applied_credit_note_decision(applied, credit_note, *, client_id)` | La nota existe, está `approved`/`confirmed`, pertenece al cliente y el monto aplicado es válido. | `"Nota de crédito ... no encontrada."`, `"La nota de crédito #... no está aprobada (estado: ...)."`, `"La nota de crédito #... pertenece a otro cliente."`, `"El monto aplicado (...) de la nota de crédito #... es inválido (total: ...)."` |
| `devolution_duplicate_decision(devolution_id, seen_ids)` | La devolución no se repite en el recibo. | `"Devolución duplicada en el recibo: ...."` |
| `applied_devolution_decision(applied, devolution, *, client_id)` | La devolución existe, está `confirmed`, pertenece al cliente, proviene de factura a crédito y el monto aplicado es válido. | `"Devolución ... no encontrada."`, `"La devolución #... no está confirmada (estado: ...)."`, `"La devolución #... pertenece a otro cliente."`, `"La devolución #... proviene de una factura de contado y no puede aplicarse en recibos."`, `"El monto aplicado (...) de la devolución #... es inválido (total: ...)."` |
| `applied_invoice_decision(applied, invoice, *, has_open_devolution=False)` | La factura existe, no tiene devoluciones abiertas y el pago no supera el saldo pendiente (`total - amountPaid`). | `"Invoice ... not found"`, `"La factura #... tiene una devolución pendiente de confirmar."`, `"Overpayment Error: Payment of ... exceeds pending balance of ... for Invoice ..."` |

La validación de coherencia del pago (efectivo, moneda secundaria, referencia bancaria) permanece en `ReceiptPaymentPolicy`, ubicada en `core/policies/receipts/receipt_payment_policy.py`; la anulación de recibos vive en `core/policies/receipts/receipt_cancellation_policy.py`.

---

## 4. Endpoints REST (`/api/v1/receipts`)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/v1/receipts` | Registra un recibo y aplica sus fondos. |
| `GET` | `/api/v1/receipts` | Lista recibos con filtros y paginación. |
| `GET` | `/api/v1/receipts/invoice/{invoice_id}` | Recibos asociados a una factura. |
| `GET` | `/api/v1/receipts/totals` | Totales de recibos según filtros. |
| `GET` | `/api/v1/receipts/totals/byPaymentMethod` | Totales agrupados por método de pago. |
| `GET` | `/api/v1/receipts/history` | Historial de recibos por cliente. |
| `GET` | `/api/v1/receipts/doc/{doc_number}` | Busca un recibo por folio. |
| `GET` | `/api/v1/receipts/{receipt_id}` | Busca un recibo por identificador. |
| `PATCH` | `/api/v1/receipts/{receipt_id}` | Actualiza un recibo. |
| `DELETE` | `/api/v1/receipts/{receipt_id}` | Elimina un recibo y revierte sus efectos. |
