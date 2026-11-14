# Convenciones de Código y Datos (`kardex-server`)

Reglas que se aplican a **todo cambio** en el backend. Si una tarea requiere romper una de estas reglas, debe justificarse explícitamente.

---

## 1. Nombrado

| Elemento | Convención | Ejemplo |
| :--- | :--- | :--- |
| Archivos y carpetas | `snake_case` | `credit_notes_controller.py` |
| Clases | `PascalCase` | `CreditNotesRepository` |
| Funciones y variables | `snake_case` | `process_credit_note` |
| Entidades de dominio | **singular** | `product`, no `products` |
| Campos Pydantic | **`camelCase`** | `productId`, `branchId`, `createdAt` |
| Colecciones Mongo | `PascalCase` descriptivo | `Products`, `CreditNotes` |
| Endpoints | `kebab-case` | `/credit-notes`, `/adjustment-requests` |

La regla de `camelCase` en modelos es **no negociable**: es el contrato con Flutter y con los documentos de MongoDB.

---

## 2. Tipos de datos

| Dato | Tipo | Regla |
| :--- | :--- | :--- |
| Fechas | `int` | Timestamp Unix en **milisegundos** |
| Dinero | `int` | **Centavos** (nunca `float`) |
| Cantidades / stock | `int` | Unidades base de la escala del producto |
| Identificadores | `str` | UUID generado con `UuidTool` o id alfanumérico |
| Booleanos | `bool` | Sin conversiones ambiguas |

```python
# Correcto
createdAt: int          # 1731456000000
total: int              # 150050 = $1,500.50

# Incorrecto
createdAt: datetime
total: float
```

---

## 3. Modelos Pydantic

Cada entidad sigue el patrón de cuatro clases:

```python
class BaseProduct(BaseModel): ...      # Campos comunes
class CreateProduct(BaseProduct): ...  # Body de POST
class UpdateProduct(BaseModel): ...    # Body de PATCH (todo opcional)
class ProductInDb(BaseProduct): ...    # Respuesta (incluye id/created_at/updated_at)
```

Reglas:

- Valida en el modelo, no a mano en el controller.
- `Update*` debe permitir campos opcionales (`str | None = None`).
- No expongas modelos internos de Mongo directamente; usa `*InDb`.
- Usa `Field(...)` para límites, descripciones y alias cuando aplique.

---

## 4. Repositorios

- Singleton con `get_instance()` y constructor que acepta el datasource (inyección).
- Toda regla de negocio de una entidad vive aquí o en `core/`, nunca en el router.
- Los repos devuelven modelos de dominio, no diccionarios crudos.

```python
class ProductsRepository:
    _instance: "ProductsRepository | None" = None

    def __init__(self, data_source: ProductsDataSource) -> None:
        self.data_source = data_source

    @classmethod
    def get_instance(cls) -> "ProductsRepository":
        if cls._instance is None:
            cls._instance = cls(ProductsDataSource())
        return cls._instance
```

---

## 5. Excepciones

- Las excepciones de negocio heredan de `KardexException` (`kardex/tools/kardex_exceptions.py`).
- **Nunca** lances `HTTPException` desde `packages/kardex-business`.
- El mapeo a códigos HTTP vive en `app/regis_exception_handlers.py`.
- Usa excepciones específicas (`InsufficientBalanceError`, `BranchNotFound`, etc.) en lugar de `Exception` genérica.

---

## 6. Colecciones MongoDB

1. Cada colección tiene su clase en `services/mongo_collections/v1/<entidad>_collection.py`.
2. Declara `collection_name` en la clase.
3. Registra el nombre en `app/config/onion-config.toml`.
4. No hardcodees nombres de colección en datasources ni procesos: usa la clase.

```python
class ProductsCollection(BaseMongoCollection):
    collection_name = "Products"

    async def fetch_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        ...
```

> ⚠️ Inconsistencia conocida: `expiration_logs_collection.py` declara `collection_name = "ExpirationLog"`, mientras `onion-config.toml` registra `ExpirationLogs`. Verifica antes de consultar esa colección directamente.

---

## 7. Filtros y paginación

- Los filtros de listado viven en `kardex/repos/v1/common/filter_params/`.
- Cada módulo filtrable tiene su `<entidad>_filter_params.py`.
- Extiende `BaseFilterParams` cuando aplique.
- No inventes query params sueltos en el router: agrupa en el modelo de filtros.

```python
@router.get("")
async def get_all_products(query_params: ProductFilterParams = Depends()) -> ListResponse[ProductInDb]:
    ...
```

---

## 8. Respuestas

- Los listados usan `ListResponse[T]` de `app/responses/v1/list_response.py`.
- Las respuestas de un módulo con estructura propia pueden tener su `responses.py` local (ej. `invoices/responses.py`).
- Mantén `camelCase` también en los modelos de respuesta.

---

## 9. Dependencias

- Gestión con `uv`: `uv add <paquete>` / `uv remove <paquete>`.
- El paquete `kardex-business` **no** puede depender de FastAPI.
- No edites `uv.lock` a mano.

---

## 10. Tests

- Ubicación: `test/` en la raíz del server.
- Framework: `pytest` + `pytest-asyncio`.
- `test/__init__.py` agrega `app/` al `sys.path`; ejecuta desde la raíz del server.
- Prioriza tests de reglas de negocio (procesos de `core/`) sobre tests de endpoints.
- `test/test_demo.py` está vacío: no lo uses como referencia.

```powershell
uv run pytest test/
```

---

## 11. Verificación pre-commit (obligatoria)

```powershell
# Lint
$env:PYTHONPATH = "app;$env:PYTHONPATH"; .venv\Scripts\ruff.exe check packages/kardex-business/src/kardex/ app/

# Tipos
$env:PYTHONPATH = "app;$env:PYTHONPATH"; .venv\Scripts\ty.exe check
```

Ambos deben pasar antes de dar una tarea por terminada. Si `ty` marca un falso positivo, documéntalo; no lo silencies sin justificación.

---

## 12. Checklist rápida

- [ ] ¿La lógica está en la capa correcta?
- [ ] ¿Los campos nuevos son `camelCase`?
- [ ] ¿El dinero es `int` en centavos?
- [ ] ¿Las fechas son `int` en ms?
- [ ] ¿El repo es singleton con `get_instance()`?
- [ ] ¿La excepción hereda de `KardexException`?
- [ ] ¿La colección está registrada en `onion-config.toml`?
- [ ] ¿El router declara `auth_middleware`?
- [ ] ¿Pasan `ruff` y `ty`?
