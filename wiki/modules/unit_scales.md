# Documentación del Módulo: Escalas de Unidades (`unit_scales`)

El módulo **Escalas de Unidades (`UnitScale`)** proporciona plantillas reutilizables de conversión de unidades de medida en `kardex-server`. Una escala define una **unidad base** (la fracción mínima que se vende) y una lista de **unidades extra** con factores enteros respecto a esa base.

La decisión central de esta versión:

> **La unidad base es la fracción comercial mínima que el negocio vende. El `scaleType` de la escala define si la base es un cuarto (peso/volumen/longitud), media/cuarto de empaque (`fractionPack`) o la unidad (`pack`).**

Esto permite que el factor comercial sea `2` o `4` en los casos comunes, en lugar de `454`, `1000`, `12`, `24` o `30`, y reduce el problema de redondeo de precios (`C1`) sin cambiar los tipos `int` de stock y dinero.

---

## 1. Arquitectura del Módulo (Onion Pattern)

```text
kardex-server/
├── app/
│   └── api/v1/unit_scales/
│       ├── unit_scales_router.py       # Endpoints REST (FastAPI)
│       └── unit_scales_controller.py   # Orquestación y ListResponse
└── packages/kardex-business/src/kardex/
    ├── repos/v1/unit_scales/
    │   ├── models/unit_scale_model.py  # Modelos Pydantic v2 (camelCase)
    │   ├── data/unit_scales_datasource.py # Interacción con MongoDB
    │   └── unit_scales_repository.py   # Lógica y singleton de negocio
    ├── services/mongo_collections/v1/
    │   └── unit_scales_collection.py   # Colección MongoDB (UnitScales)
    └── core/default_values/
        └── create_default_unit_scales.py # Semillas iniciales
```

---

## 2. Modelo de Dominio (`unit_scale_model.py`)

Todos los campos usan **`camelCase`**:

```python
ScaleType = Literal[
    "weight",
    "volume",
    "length",
    "pack",
    "fractionPack",
    "custom",
]

class BaseUnitScale(BaseModel):
    name: str
    scaleType: ScaleType = "custom"
    baseUnit: str                       # unidad base (factor 1)
    units: list[ExtraUnit] = []         # unidades extra con factores
    defaultUnitIndex: int = 0           # 0 = baseUnit, 1..N = unidades extras
    wholesaleUnitIndex: int = 0         # 0 = usar default

class CreateUnitScale(BaseUnitScale):
    pass

class UpdateUnitScale(BaseModel):
    name: str | None = None
    scaleType: ScaleType | None = None
    baseUnit: str | None = None
    units: list[ExtraUnit] | None = None
    defaultUnitIndex: int | None = None
    wholesaleUnitIndex: int | None = None

class UnitScaleInDb(BaseUnitScale):
    id: str
    createdAt: int
    updatedAt: int | None = None
```

- Los documentos viejos que no tengan `scaleType` se leen como `custom`.
- `scaleType` vive **solo en la escala**; el producto guarda su copia de `unitName`, `extraUnits`, `defaultUnitIndex` y `wholesaleUnitIndex`.

---

## 3. Tipos de escala (`scaleType`)

| `scaleType` | Base | ¿Venta por unidad? | Uso |
| :--- | :--- | :---: | :--- |
| `weight` | `1/4 Libra` | No | Peso continuo |
| `volume` | `1/4 Litro` (250 ml) | No | Volumen continuo |
| `length` | `1/4 Metro` (25 cm) | No | Longitud continua |
| `pack` | `Unidad` (1) | **Sí** | Empaque con venta por unidad |
| `fractionPack` | Media/cuarto de empaque | No | Empaque fraccionado |
| `custom` | La que defina el usuario | Según factores | Casos especiales |

`time` no se incluye por ahora porque el negocio vende productos, no servicios. Queda pendiente para el futuro.

---

## 4. Escalas por Defecto (`default_values`)

Al inicializar los servicios (`services_initializer.py`), `create_default_unit_scales()` siembra las siguientes escalas.

### 4.1. Continuas

| Escala | `scaleType` | Base | Extras | Default | Mayorista |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Libra** | `weight` | `1/4 Libra` | `Libra` ×4, `Arroba (25 lb)` ×100, `Quintal (100 lb)` ×400 | Libra | Arroba/Quintal |
| **Litro** | `volume` | `1/4 Litro` | `Litro` ×4, `Bidón 5 L` ×20, `Bidón 20 L` ×80 | Litro | Bidón 20 L |
| **Metro** | `length` | `1/4 Metro` | `Metro` ×4, `Rollo 50 m` ×200, `Rollo 100 m` ×400 | Metro | Rollo 100 m |

### 4.2. `fractionPack`

Para un empaque de `N` unidades:

- `N % 4 == 0` → base cuarto de empaque (factor `4` al empaque).
- `N % 4 != 0` y `N % 2 == 0` → base media parte del empaque (factor `2`).
- `N` impar → no hay fracción exacta; se usa empaque completo o `pack`.

| Preset | Base | Extras | Default |
| :--- | :--- | :--- | :--- |
| **Caja x10** | `1/2 Caja x10 (5 u)` | `Caja x10 (10 u)` ×2 | Caja x10 |
| **Caja x12** | `1/4 Caja x12 (3 u)` | `1/2 Caja x12 (6 u)` ×2; `Caja x12 (12 u)` ×4 | Caja x12 |
| **Caja x20** | `1/4 Caja x20 (5 u)` | `1/2 Caja x20 (10 u)` ×2; `Caja x20 (20 u)` ×4 | Caja x20 |
| **Caja x24** | `1/4 Caja x24 (6 u)` | `1/2 Caja x24 (12 u)` ×2; `Caja x24 (24 u)` ×4 | Caja x24 |
| **Caja x30** | `1/2 Caja x30 (15 u)` | `Caja x30 (30 u)` ×2 | Caja x30 |
| **Caja x50** | `1/2 Caja x50 (25 u)` | `Caja x50 (50 u)` ×2 | Caja x50 |
| **Caja x60** | `1/4 Caja x60 (15 u)` | `1/2 Caja x60 (30 u)` ×2; `Caja x60 (60 u)` ×4 | Caja x60 |
| **Caja x100** | `1/4 Caja x100 (25 u)` | `1/2 Caja x100 (50 u)` ×2; `Caja x100 (100 u)` ×4 | Caja x100 |
| **Docena** | `1/4 Docena (3 u)` | `1/2 Docena (6 u)` ×2; `Docena (12 u)` ×4 | Docena |

`Caja x12` y `Docena` son numéricamente equivalentes. Se puede sembrar una sola o ambas con nombres distintos.

### 4.3. `pack`

`pack` no se siembra por defecto; es una opción avanzada para productos que se venden por unidad suelta. Su base es `Unidad` y sus extras son `1/2 Caja xN` (factor `N/2`) y `Caja xN` (factor `N`). Permite vender 1 unidad, media caja o caja completa.

---

## 5. Limpieza de escalas viejas

Las escalas anteriores (`Peso` con gramos, `Volumen` con mililitros, `Longitud` con centímetros y `Tiempo`) se eliminan de `create_default_unit_scales.py` y se limpian de la base de datos de desarrollo:

- No hay productos en producción usando esas escalas.
- `create_unit_scale_if_absent` solo inserta; no actualiza ni borra documentos existentes. Por eso el arranque debe eliminar explícitamente los nombres viejos antes de sembrar los nuevos.
- Los nombres nuevos (`Libra`, `Litro`, `Metro`, `Caja xN - Fracción`, `Docena - Fracción`) no colisionan con los viejos.
- **Renombre `1/4`/`1/2`:** si la BD ya contiene las escalas por defecto con bases `Cuarto de ...` o extras `Media ...`, `create_unit_scale_if_absent` no las actualiza porque solo inserta. Hay que eliminarlas/recrearlas o ejecutar una migración. Con la BD vacía, el arranque crea directamente `1/4 Libra`, `1/4 Litro`, `1/4 Metro`, `1/4 Caja xN`, `1/2 Caja xN`, `1/4 Docena` y `1/2 Docena`.
- Si en el futuro hay producción, esta limpieza debe convertirse en una migración versionada, no en un borrado indiscriminado.
- En el alcance P0 actual no se agrega migración ni guard de producción; la operación de producción la maneja el usuario.

---

## 6. Endpoints REST (`/api/v1/unit-scales`)

Sin cambios de rutas. El campo `scaleType` viaja en el payload:

| Método | Endpoint | Descripción | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/unit-scales` | Crea una escala | `UnitScaleInDb` |
| `GET` | `/api/v1/unit-scales` | Lista escalas | `ListResponse[UnitScaleInDb]` |
| `GET` | `/api/v1/unit-scales/{id}` | Obtiene una escala | `UnitScaleInDb` |
| `PATCH` | `/api/v1/unit-scales/{id}` | Actualiza parcialmente | `UnitScaleInDb` |
| `DELETE` | `/api/v1/unit-scales/{id}` | Elimina una escala | `UnitScaleInDb` |

Todos requieren `auth_middleware`.

---

## 7. Colección MongoDB (`UnitScales`)

- Nombre: `UnitScales`.
- `create_unit_scale_if_absent(name, unit_scale)` sigue insertando de forma idempotente.
- Se agrega un método de limpieza que solo borra una semilla vieja si coinciden
  nombre **y** unidad base, para no eliminar escalas personalizadas con el mismo
  nombre:
  ```python
  async def delete_unit_scales_by_name_and_base_unit(
      self,
      old_scales: list[tuple[str, str]],
  ) -> None:
      ...
  ```
  Ejemplo de pares viejos: `("Peso", "Gramo")`, `("Volumen", "Mililitro")`,
  `("Longitud", "Centímetro")`, `("Tiempo", "Segundo")`.
- Los documentos nuevos incluyen `scaleType`; los viejos se interpretan como `custom`.

---

## 8. Integridad contable e integración con el frontend

> [!IMPORTANT]
> **El Kárdex y el dinero siguen siendo `int`:**
> `currentStock`, `promiseStock`, `SaleItem.quantity`, `ProductTransaction.quantity` y todos los totales monetarios siguen siendo enteros. La unidad base es la fracción mínima y el frontend convierte la cantidad comercial a base antes de enviar.

Reglas de integración:

1. **Cantidad base:** `baseQuantity = round(displayQuantity * conversionFactor)`.
2. **Precio base:** `basePrice = round(commercialPriceCents / conversionFactor)`.
3. **Paso del `QuantityField`:** `1 / conversionFactor` de la unidad seleccionada (una unidad base).
4. **Precios:** con factor `2`/`4`, los precios en córdobas enteros son exactos; `.50`/`.25`/`.99` pueden redondear. `C1` queda mitigado, no eliminado.
5. **Escalas viejas:** el frontend ya no mantiene una lista estándar duplicada; consume las escalas del backend.
6. **Unidad libre (C7):** el frontend envía `unitName` como el texto visible completo del controlador, sincronizado al guardar. El placeholder `Unidad Base` no se persiste. El backend no valida contra un catálogo; guarda el texto recibido.
7. **Notas de crédito (C3):** el backend valida montos y cantidades contra la factura y las notas previas, recalcula `amount` desde las líneas y exige `idempotencyKey`; no hay lock por factura (riesgo residual aceptado).

---

## 9. Pendientes

- **`time`:** escala de servicios (segundo, minuto, hora, día) para el futuro.
- **Migración de producción:** si algún día existen productos con escalas viejas, la limpieza debe ser versionada y auditable.
- **Etiquetas de unidad en reportes/CSV:** usar la unidad comercial por defecto; no exportar cantidades base sin unidad.
- **Cambio de base con stock (H9):** bloquear o advertir; la escala es una plantilla y no convierte stock existente.
- **Edición/borrado de escalas en uso (M10/M11):** los productos existentes conservan su copia; advertir en la UI.
- **C1 en `pack` y escalas personalizadas:** el redondeo sigue existiendo; no prometer cero error.
- **P1 (noviembre 2026):** ver la sección 10 para la regla base/estándar/superior, la metadata de línea, la búsqueda rápida y los borradores `v3`, incluidas sus limitaciones residuales.

### Pendiente: bonificaciones en devoluciones y notas de crédito

**En espera.** La app aún no muestra ni explota visualmente las bonificaciones (`bonQuantity`). No se modifica el flujo actual. Cuando se active la UI, se debe definir si son retornables y aplicar simetría de stock/costo:

- Si son retornables: `process_devolution.py` y `process_credit_note.py` reingresan `abs(quantity + bonQuantity)` y el costo de devolución usa `cost * (quantity + bonQuantity)`.
- Si no son retornables: forzar `bonQuantity: 0` en los ítems devueltos y no mostrarla en el documento.

### Devoluciones directas (deprecadas)

Las devoluciones directas no se tocan en esta fase: se consideran **deprecadas** y serán reemplazadas por **notas de crédito**, que son el flujo objetivo.

### Producción

La operación de producción la maneja el usuario. No se agrega migración ni guard de producción en este alcance.

---

## 10. Reglas P1 de cantidades, display y borradores (noviembre 2026)

> **Alcance backend:** el stock, las cantidades base y el dinero siguen siendo `int`. El backend **no calcula el display**; acepta y persiste la metadata opcional de unidad para que el frontend pueda presentar la cantidad en la unidad correcta. El working tree sigue **sin commit**.

### 10.1. Base, estándar y superior

| Nivel | Contrato | `int` |
| :--- | :--- | :---: |
| **Base** | Fracción comercial mínima; factor `1` | Sí; es la unidad indivisible |
| **Estándar** | Unidad comercial principal (`defaultUnitIndex`) | La cantidad base sigue siendo `int`; el display puede ser fraccionario |
| **Superior** | Unidad extra con factor mayor al estándar | Solo se muestra entera |

La regla de presentación es del frontend: la unidad superior solo se usa si `baseQuantity % factorDeLaUnidadSeleccionada == 0`; si no, se muestra en la unidad estándar. El backend no impone esta regla ni convierte cantidades.

### 10.2. Metadata de línea aceptada y persistida

Los modelos de documento aceptan campos opcionales para que el frontend resuelva el display:

| Modelo backend | Campos nuevos |
| :--- | :--- |
| `SaleItem` | `selectedUnitName`, `standardUnitName`, `standardUnitFactor` |
| `EntryItem` | `standardUnitName`, `standardUnitFactor` |
| `ExitItem` | `standardUnitName`, `standardUnitFactor` |
| `TransferItem` | `selectedUnitName`, `standardUnitName`, `standardUnitFactor` |

- Todos son opcionales (`str | None` / `int | None`).
- `standardUnitFactor` es el factor de la unidad estándar respecto a la base (`Libra = 4`, `Caja x30 = 30` en `pack`).
- Los documentos viejos sin estos campos siguen siendo válidos; el frontend usa un fallback decimal en la unidad seleccionada.
- El backend no valida que `standardUnitFactor` coincida con la escala del producto; esa consistencia la garantiza el frontend al construir la línea.
- `AdjustExitItem` es un modelo de frontend; el backend no tiene un campo equivalente en este alcance.

### 10.3. Cambio de unidad y display

- **Cambio exacto:** el frontend convierte `baseQuantity / factorNuevo`. Si la unidad nueva es estándar o base, admite fracciones; si es superior, exige un entero exacto.
- **Cambio no exacto a unidad superior:** reinicia la cantidad a `0`; no se redondea a una fracción de unidad superior.
- **Display superior:** solo si la cantidad base es divisible por el factor; si no, se muestra en la unidad estándar (ej. `1.5 Quintal → 150 Libra`).
- **Documentos viejos:** sin metadata, el display conserva el fallback decimal en la unidad seleccionada.
- El backend recibe siempre `quantity`/`baseQuantity` como `int`; no cambia el contrato de stock ni de kardex.

### 10.4. Búsqueda rápida: base `0`

La búsqueda rápida es **frontend-only**. Su regla P1 es no insertar ítems cuando la cantidad base resultante es `0`:

- `0.1 × 4 = 0.4 → round = 0`: no se inserta.
- Stock `0` con `restrictStock`: no se inserta.
- Sin `restrictStock`: se permite una cantidad positiva y el backend decide.

**La política de stock del backend no cambió:** `LET_NEGATIVE`/LITE sigue siendo la autoridad final. No se agregó revalidación al cobrar ni agrupación de líneas duplicadas.

### 10.5. Borradores de transferencia `v3`

El borrador es **frontend-only** (Hive), pero su contrato viaja al backend al crear la transferencia:

- `v3` guarda por fila `selectedUnitIndex`, `conversionFactor`, `selectedUnitName`, `baseUnitName`, `standardUnitName` y `standardUnitFactor`.
- `quantity` y `unitaryCost` son **comerciales** (unidad seleccionada); la cantidad base se reconstruye como `savedQuantity × savedFactor`.
- El costo comercial se recalcula como `averageCost × factorSeleccionado` cuando hay costo promedio.
- `v2` reconvierte con el factor guardado; si la unidad ya no existe, cae a base.
- `v1` o base cambiada: infiere `defaultUnitIndex`, marca `needsUnitReview` y permite continuar con advertencia.
- Al enviar la transferencia, `TransferItem` conserva `conversionFactor` y la metadata de unidad; el backend sigue recibiendo cantidades y costos `int`.

### 10.6. Verificación y limitaciones residuales

- **Verificación:** `ruff check` y `ty check` OK; `pytest` **14/14**; `git diff --check` OK. En frontend, `flutter analyze` limpio y `flutter test` **83/83**.
- **Sin hot reload ni prueba manual de UI.**
- **Tablas/list views `int` (frontend):** inventario y transferencia no admiten fracciones en unidad estándar; límite estructural para un bloque futuro.
- **`defaultUnitIndex = 0`:** si la unidad estándar es la base, la regla considera “superiores” a todas las unidades extra; revisar en escalas personalizadas.
- **Documentos viejos:** sin metadata no se puede reconstruir la unidad estándar; el display queda en la unidad seleccionada.
- **Sin migración:** los campos nuevos son opcionales y retrocompatibles; no se requiere migración de MongoDB.
- **Commit:** no se realizó.
