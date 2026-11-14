# Documentación del Módulo: Notas de Crédito (`credit_notes`)

El módulo **Notas de Crédito (`CreditNote`)** representa la evolución y sustitución progresiva de las devoluciones tradicionales en `kardex-server`. Provee un mecanismo formal, trazable y contable para gestionar retornos de productos o concesión de saldos a favor para clientes, integrándose de forma atómica con el inventario físico (Kárdex), cuentas por cobrar y emisión de recibos de pago.

---

## 1. Arquitectura del Módulo (Onion Pattern)

Siguiendo el estándar de arquitectura limpia del servidor:

```text
kardex-server/
├── app/
│   └── api/v1/credit_notes/
│       ├── credit_notes_router.py       # Endpoints REST (FastAPI con auth_middleware)
│       └── credit_notes_controller.py   # Controlador y empaquetado ListResponse
└── packages/kardex-business/src/kardex/
    ├── repos/v1/credit_notes/
    │   ├── models/credit_note_model.py  # Modelos Pydantic v2 (camelCase)
    │   ├── data/credit_notes_datasource.py # DataSource hacia MongoDB
    │   └── credit_notes_repository.py   # Repositorio de negocio
    ├── services/mongo_collections/v1/
    │   └── credit_notes_collection.py   # Colección MongoDB (CreditNotes)
    ├── repos/v1/common/filter_params/
    │   └── credit_note_filter_params.py # Parámetros de consulta y paginación
    └── core/credit_note_register/
        ├── credit_note_register.py      # Validaciones previas de negocio
        └── process_credit_note.py       # Transacción atómica en MongoDB
```

---

## 2. Modalidades Operativas (`CreditNoteType`)

La nota de crédito soporta dos tipos de operación:

1. **Por Devolución (`CreditNoteType.devolution`)**:
   - Vinculada obligatoriamente a una factura original mediante `originalInvoiceId` y `originalInvoiceDocNumber`.
   - Especifica la lista de productos retornados (`returnedItems: list[SaleItem]`).
   - **Efecto en Inventario:** Incrementa automáticamente el stock disponible en la sucursal emisora y genera un movimiento formal en el Kárdex (`ProductTransaction` con `subtype="credit_note"` y `type="entry"`).
   - **Estado Inicial:** Nace en estado `confirmed`. Si la factura de origen fue a crédito, el monto queda disponible como saldo a favor para aplicarse en el siguiente pago/recibo del cliente.

2. **Por Monto (`CreditNoteType.amount`)**:
   - Asociada directamente a un cliente registrado (`clientId` y `clientInfo`).
   - Requiere un motivo detallado obligatorio (`description`).
   - No afecta inventario físico ni genera movimientos de Kárdex.
   - Nace en estado `confirmed` para amortizar deudas del cliente en el módulo de cobranza.

---

## 3. Estados de la Nota de Crédito (`CreditNoteStatus`)

```mermaid
stateDiagram-v2
    [*] --> emitted: Emisión (devolution / amount) [Stock NO se toca]
    emitted --> approved: Aprobación Formal [Reingreso a Stock si es devolución]
    emitted --> rejected: Rechazo [Registra motivo]
    approved --> applied: Aplicada en Recibo (appliedCreditNotes)
    approved --> cancelled: Anulación / Cancelación [Revierte Stock si fue devolución]
    applied --> approved: Reversión de Recibo (reverse_receipt)
```

- **`emitted`**: Estado inicial al crear la nota. No afecta el inventario físico ni descuenta saldo de la factura.
- **`approved`**: Nota formalmente aprobada. Si es devolución, reingresa el stock físico a `Products` y crea `ProductTransaction`. Descuenta de la factura asociada y queda habilitada para aplicarse en recibos. (Equivalente semántico al legacy `confirmed`).
- **`rejected`**: Nota desestimada con motivo explícito (`rejectionReason`). No afecta inventario ni facturas.
- **`applied`**: Aplicada en un recibo oficial de pago (`appliedReceiptId`), reduciendo la deuda del cliente con `ClientTransaction` (`subtype="credit_note"`).
- **`cancelled`**: Anulada, revirtiendo sus efectos contables y de inventario si ya estaba aprobada.
- **`open`**: Estado opcional para borradores.

---

## 4. Modelos de Dominio (`credit_note_model.py`)

Todos los campos utilizan nomenclatura **`camelCase`** para interoperabilidad con MongoDB y Flutter:

```python
class CreditNoteType(str, Enum):
    devolution = "devolution"
    amount = "amount"

class CreditNoteStatus(str, Enum):
    emitted = "emitted"
    open = "open"
    approved = "approved"
    confirmed = "confirmed"
    rejected = "rejected"
    cancelled = "cancelled"
    applied = "applied"

class BaseCreditNote(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    type: CreditNoteType
    docNumber: str = ""
    originalInvoiceId: str = ""
    originalInvoiceDocNumber: str = ""
    returnedItems: list[SaleItem] = []
    amount: int                                  # Monto monetario en centavos
    description: str = ""
    status: CreditNoteStatus = CreditNoteStatus.emitted
    createdBy: UserInfo
    approvedBy: UserInfo | None = None
    approvedAt: int | None = None
    rejectedBy: UserInfo | None = None
    rejectedAt: int | None = None
    rejectionReason: str | None = None
    appliedReceiptId: str | None = None
    appliedReceiptDocNumber: str | None = None
    appliedAt: int | None = None

class CreateCreditNote(BaseCreditNote):
    pass

class ApproveCreditNote(BaseModel):
    approvedBy: UserInfo

class RejectCreditNote(BaseModel):
    rejectedBy: UserInfo
    reason: str = ""
```

class UpdateCreditNote(BaseModel):
    status: CreditNoteStatus | None = None
    appliedReceiptId: str | None = None
    appliedReceiptDocNumber: str | None = None
    appliedAt: int | None = None

class CreditNoteInDb(BaseCreditNote):
    id: str                                      # UUID v4
    createdAt: int                               # Timestamp en milisegundos
    updatedAt: int | None = None
```

---

## 5. Proceso Atómico Core (`process_credit_note.py`)

La emisión de notas de crédito se ejecuta dentro de una sesión transaccional de MongoDB (`client.start_session()`):

1. **Generación de Folio Consecutivo:** Obtiene el siguiente folio único por sucursal mediante `CounterManager.next_credit_note_number()`.
2. **Reingreso de Inventario (Devolución):**
   - Para cada producto en `returnedItems`, incrementa su stock físico (`stock += qty`) en la colección `Products`.
   - Inserta un registro en `ProductTransactions` con `subtype="credit_note"`, tipo `entry`, referenciando el folio de la nota.
3. **Persistencia de la Nota:** Inserta el documento en `CreditNotes` en estado `confirmed`.

---

## 6. Integración con el Módulo de Recibos (`process_receipt.py`)

Cuando un cliente con compras a crédito realiza un pago o abono:

1. El payload de `CreateReceipt` incluye `appliedCreditNotes: list[AppliedCreditNote]`.
2. `process_receipt.py` valida la existencia y estado `confirmed` de cada nota de crédito.
3. Suma el monto de las notas de crédito al total de fondos aplicados a las facturas pendientes (`total_funds = cash + devolutions + credit_notes`).
4. Amortiza las facturas pendientes reduciendo `amountPaid` y `totalRemaining`.
5. Por cada nota de crédito aplicada:
   - Modifica el estado de la nota a `applied`, registrando `appliedReceiptId`, `appliedReceiptDocNumber` y `appliedAt`.
   - Emite una transacción de cliente (`ClientTransactionInDb`) con `subtype="credit_note"`, debitando el saldo pendiente del cliente.
6. **Reversión (`reverse_receipt.py`):** Si un recibo es revertido/anulado, las notas de crédito aplicadas retornan a su estado `confirmed`, y la deuda del cliente se restablece atómicamente.

---

## 7. Reversión y Eliminación Atómica (`reverse_credit_note.py`)

Si una nota de crédito fue emitida por error o cancelada antes de ser aplicada en un recibo oficial:

1. **Restricción de Estado:** Solo se permite eliminar notas con estado diferente a `applied` (`open`, `confirmed` o `cancelled`). Si la nota ya fue aplicada, la operación es rechazada con un error HTTP 400 impidiendo inconsistencias contables en recibos emitidos.
2. **Reversión de Inventario (Devolución):**
   - Para notas de tipo `devolution`, se inicia una sesión atómica de MongoDB (`client.start_session()`).
   - Se deduce el stock físico en `Products` correspondiente a cada `returnedItem` (`stock -= qty`), revirtiendo el reingreso previo.
   - Se eliminan de `ProductTransactions` todos los movimientos asociados al documento (`documentId == credit_note.id` o `documentDocNumber == credit_note.docNumber`).
3. **Eliminación del Registro:** Se elimina permanentemente el documento de la colección `CreditNotes`.
4. **Notas por Monto:** Para notas de tipo `amount`, la reversión no afecta inventario y simplemente elimina el saldo a favor pendiente del registro.

---

## 8. Permisos y Seguridad (`role_manager.py`)

Se agregaron los siguientes permisos dentro del módulo comercial:

- `CREATE_CREDIT_NOTE`: Autoriza la emisión de notas de crédito por devolución o monto.
- `CREDIT_NOTE_HISTORY`: Autoriza la consulta del historial maestro y auditoría de notas de crédito.

> [!IMPORTANT]
> **Pendiente y Roadmap Futuro de Aprobación:**
> Actualmente, cualquier usuario autenticado en el sistema puede **aprobar** o **rechazar** una nota de crédito emitida. Queda registrado como pendiente técnico incorporar un permiso granular específico (e.g., `APPROVE_CREDIT_NOTE`) para limitar la aprobación a perfiles con rol de Administrador o Supervisor.

---

## 9. Catálogo de Endpoints REST (`/api/v1/credit-notes`)

Todos los endpoints requieren autenticación mediante JWT (`auth_middleware`):

| Método | Endpoint | Descripción | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/credit-notes` | Emite una nueva nota de crédito en estado `emitted` (sin tocar stock) | `CreditNoteInDb` |
| `POST` | `/api/v1/credit-notes/{id}/approve` | Aprueba la nota (reingresa stock a Kárdex si es devolución) | `CreditNoteInDb` |
| `POST` | `/api/v1/credit-notes/{id}/reject` | Rechaza la nota indicando motivo de rechazo | `CreditNoteInDb` |
| `GET` | `/api/v1/credit-notes` | Lista paginada con filtros (`status`, `type`, fechas, cliente) | `ListResponse[CreditNoteInDb]` |
| `GET` | `/api/v1/credit-notes/all/active` | Consulta notas activas (`emitted`, `approved`, `confirmed`, `open`) | `ListResponse[CreditNoteInDb]` |
| `GET` | `/api/v1/credit-notes/client/{client_id}` | Notas de crédito asociadas a un cliente específico | `ListResponse[CreditNoteInDb]` |
| `GET` | `/api/v1/credit-notes/invoice/{invoice_id}` | Notas vinculadas a una factura en particular | `ListResponse[CreditNoteInDb]` |
| `GET` | `/api/v1/credit-notes/doc/{doc_number}` | Búsqueda por folio consecutivo | `CreditNoteInDb` |
| `GET` | `/api/v1/credit-notes/{id}` | Búsqueda por identificador UUID | `CreditNoteInDb` |
| `DELETE` | `/api/v1/credit-notes/{id}` | Elimina la nota y revierte stock solo si estaba aprobada | `CreditNoteInDb` |
