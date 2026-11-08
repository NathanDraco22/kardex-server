# Documentación del Módulo: Escalas de Unidades (`unit_scales`)

El módulo **Escalas de Unidades (`UnitScale`)** proporciona plantillas reutilizables de conversión de unidades de medida (como Peso, Volumen, Longitud, Tiempo y escalas personalizadas) en `kardex-server`. Centraliza las reglas de equivalencia para que los productos no tengan que reconfigurar manualmente sus unidades extras y factores de conversión en cada registro.

---

## 1. Arquitectura del Módulo (Onion Pattern)

Siguiendo el estándar de arquitectura limpia del servidor:

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
        └── create_default_unit_scales.py # Semillas iniciales (Peso, Volumen, Longitud, Tiempo)
```

---

## 2. Modelo de Dominio (`unit_scale_model.py`)

Todos los campos utilizan nomenclatura **`camelCase`**:

```python
class BaseUnitScale(BaseModel):
    name: str                           # Nombre de la escala (ej. "Peso")
    baseUnit: str                       # Unidad base mínima (factor 1, ej. "Gramo")
    units: list[ExtraUnit] = []         # Unidades hijas con factores de conversión
    defaultUnitIndex: int = 0           # 0 = baseUnit, 1..N = unidades extras
    wholesaleUnitIndex: int = 0         # 0 = no definida / fallback a base

class CreateUnitScale(BaseUnitScale):
    pass

class UpdateUnitScale(BaseModel):
    name: str | None = None
    baseUnit: str | None = None
    units: list[ExtraUnit] | None = None
    defaultUnitIndex: int | None = None
    wholesaleUnitIndex: int | None = None

class UnitScaleInDb(BaseUnitScale):
    id: str                             # UUID v4
    createdAt: int                      # Timestamp en milisegundos
    updatedAt: int | None = None        # Timestamp en milisegundos
```

---

## 3. Escalas por Defecto (`default_values`)

Al inicializar los servicios (`services_initializer.py`), se ejecuta `create_default_unit_scales()`, insertando de forma idempotente (`create_unit_scale_if_absent`) las siguientes 4 escalas:

| Escala | Unidad Base | Unidades Extras y Factores Multiplicadores |
| :--- | :--- | :--- |
| **Peso** | `Gramo` | `Onza` (x28), `Libra` (x454), `Kilogramo` (x1000), `Quintal` (x45400) |
| **Volumen** | `Mililitro` | `Litro` (x1000), `Galón` (x3785) |
| **Longitud** | `Centímetro` | `Metro` (x100), `Yarda` (x91) |
| **Tiempo** | `Segundo` | `Minuto` (x60), `Hora` (x3600), `Día` (x86400) |

---

## 4. Endpoints REST (`/api/v1/unit-scales`)

Todos los endpoints requieren autenticación mediante `auth_middleware`:

| Método | Endpoint | Descripción | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/unit-scales` | Crea una nueva escala | `UnitScaleInDb` |
| `GET` | `/api/v1/unit-scales` | Lista todas las escalas ordenadas alfabéticamente | `ListResponse[UnitScaleInDb]` |
| `GET` | `/api/v1/unit-scales/{id}` | Obtiene una escala por su identificador | `UnitScaleInDb` |
| `PATCH` | `/api/v1/unit-scales/{id}` | Actualiza parcialmente una escala | `UnitScaleInDb` |
| `DELETE` | `/api/v1/unit-scales/{id}` | Elimina una escala del sistema | `UnitScaleInDb` |

---

## 5. Colección MongoDB (`UnitScales`)

Registrada en `app/config/onion-config.toml`:
- Nombre de la colección: `UnitScales`
- Método especial para inicialización:
  ```python
  async def create_unit_scale_if_absent(self, name: str, unit_scale: dict) -> None:
      await self._collection.update_one(
          {"name": name},
          {"$setOnInsert": unit_scale},
          upsert=True,
      )
  ```
