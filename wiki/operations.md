# Operación y Entorno (`kardex-server`)

Cómo instalar, ejecutar, configurar y verificar el backend.

---

## 1. Requisitos

- Python `>=3.12` (la imagen Docker usa `3.13`).
- [`uv`](https://docs.astral.sh/uv/) instalado.
- MongoDB accesible (local o remoto).

---

## 2. Instalación

```powershell
cd kardex-server
uv sync
```

`uv sync` instala el proyecto y el paquete local editable `packages/kardex-business`.

---

## 3. Ejecución local

Los imports del proyecto son absolutos (`from api.v1.router import router_v1`), por lo que el proceso debe ejecutarse **desde `app/`** o con `app/` en `PYTHONPATH`.

### Opción A — desde `app/` (recomendada)

```powershell
cd kardex-server/app
uv run fastapi dev --port 8000
```

Equivale a la configuración de `.vscode/launch.json` (`fastapi dev --port 8000`).

### Opción B — desde la raíz

```powershell
cd kardex-server
$env:PYTHONPATH = "app"
uv run uvicorn main:app --reload --port 8000
```

### Opción C — Docker

```powershell
docker build -t kardex-server .
docker run --env-file .env -p 8080:8080 kardex-server
```

El contenedor trabaja en `/home/server/app` y ejecuta
`fastapi run --host 0.0.0.0 --port 8080`.

---

## 4. Variables de entorno

| Variable | Default | Uso |
| :--- | :--- | :--- |
| `MONGO_URL` | `mongodb://localhost:27017` | Cadena de conexión al cluster multi-tenant. |
| `MODE` | *(sin default)* | `DEV` (desarrollo) o `PROD` (oculta OpenAPI). |
| `LITE_MODE` | `false` | Activa reglas de la edición Lite. |
| `LET_NEGATIVE` | *(sin default)* | Sobrescribe `KardexConfig.letInvoiceWithNegative`. |
| `JWT_SECRET` | `secretApp` | Firma de tokens. **Cámbialo en producción.** |
| `INDEXES_VERSION` | *(vacío)* | Override de emergencia de `CURRENT_INDEX_VERSION` para forzar un re-apply de índices. |
| `APP_VERSION` | `1.0.0` | Se guarda en `Meta.appVersion`. |
| `TELEGRAM_BOT_TOKEN` | *(sin default)* | Integración de notificaciones Telegram. |
| `TELEGRAM_CHAT_ID` | `""` | Chat destino de notificaciones. |

> `DB_NAME` **ya no se usa en runtime**. La base de datos se resuelve por el header de tenant (`X-Servin`); sin header, la petición responde 400 y cualquier acceso a Mongo sin contexto lanza `TenantContextMissingError`. La herramienta legacy `tools/migrate_branch_images.py` sigue aceptando `--db-name`.

> Los defaults de `JWT_SECRET` y `MONGO_URL` son de desarrollo. Nunca los uses tal cual en producción.

---

## 5. Documentación interactiva

| Ruta | Descripción |
| :--- | :--- |
| `/sdoc` | Scalar UI (recomendada). |
| `/scalar` | Scalar UI con proxy. |
| `/openapi.json` | Esquema OpenAPI. Se desactiva si `MODE=PROD`. |

La app se registra como **“Ledger Server”** en `app/main.py`.

---

## 6. Modos de ejecución

### `MODE=DEV`

- OpenAPI disponible.
- Recomendado para desarrollo local.

### `MODE=PROD`

- OpenAPI deshabilitado.
- El tenant sigue siendo obligatorio en ambos modos: no hay fallback a `DB_NAME`.

### `LITE_MODE=true`

Ajusta `KardexConfig` al arrancar (`app/app_lifespan.py`):

| Bandera | `main` | `lite` |
| :--- | :--- | :--- |
| `letInvoiceWithNegative` | `false` | `true` |
| `followTransaction` | `true` | `false` |
| `createFullProductProfile` | `false` | `true` |

`LET_NEGATIVE` tiene prioridad sobre `LITE_MODE` para `letInvoiceWithNegative`.

---

## 7. Arranque, aprovisionamiento e índices

`app/app_lifespan.py` solo aplica las banderas de Lite y ejecuta `MongoService().init_client()`. **No** crea índices ni datos semilla: cada tenant se aprovisiona por separado.

### Aprovisionar un tenant nuevo

`POST /api/v1/core-settings` (super token Ed25519, con `X-Servin: <nickname>`) ejecuta, dentro del request:

1. `CoreSettings` en la base del tenant (nickname normalizado).
2. `provision_tenant`: cliente/venta contado, sucursal, roles, usuario `root`, propietario (idempotente por `username`), categorías de gasto, escalas, app settings e integración.
3. `Meta` inicial (`isProvisioned: false`, `indexesVersion: 0`).
4. Los índices se crean en `BackgroundTasks` (`finalize_tenant_indexes`) y cierran `Meta` con `isProvisioned: true` e `indexesVersion: CURRENT_INDEX_VERSION`.

Un reintento del `POST` repara un aprovisionamiento incompleto: las semillas son `*_if_absent` y el propietario se busca por `username`.

### Aplicar migraciones a los tenants existentes

```powershell
# Revisar sin escribir
$env:PYTHONPATH = "app"; .venv\Scripts\python.exe tools\migrate_tenants.py --dry-run

# Aplicar índices y datos a todos los tenants
$env:PYTHONPATH = "app"; .venv\Scripts\python.exe tools\migrate_tenants.py

# Solo un tenant
$env:PYTHONPATH = "app"; .venv\Scripts\python.exe tools\migrate_tenants.py --indexes --tenant tienda-a
```

El runner enumera `list_database_names()`, descarta `admin/local/config`, exige `Meta.kind == "kardex-tenant"` y aplica:

| `Meta.indexesVersion` vs objetivo | Acción |
| :--- | :--- |
| igual | omite |
| menor | crea índices y actualiza `Meta` |
| mayor | `WARN` "servidor más viejo que los datos"; no toca |

También ejecuta el backfill de `Products.altCode` (antes `set_new_values` en el arranque).

> `CURRENT_INDEX_VERSION` se sube en el mismo PR que cambia una definición de índice. `INDEXES_VERSION` es solo un override de emergencia.

### Scheduler

El scheduler de procesos y los reportes programados fueron eliminados. `DailySummaries` y `ExecutiveSummaries` quedan en solo lectura; no hay notificaciones de las 7am.

---

## 8. Tests

```powershell
cd kardex-server
uv run pytest test/
```

- `test/__init__.py` agrega `app/` al `sys.path`, por eso debe ejecutarse desde la raíz del server.
- `test/test_demo.py` está vacío (0 bytes); no lo tomes como suite de referencia.
- Las pruebas de integración multi-tenant (`test_multi_tenant_isolation.py`, `test_provision_tenant.py`, `test_migrate_tenants.py`) se **omiten** si no hay un MongoDB alcanzable en `MONGO_URL`.

---

## 9. Verificación pre-commit

```powershell
# Lint
$env:PYTHONPATH = "app;$env:PYTHONPATH"; .venv\Scripts\ruff.exe check packages/kardex-business/src/kardex/ app/

# Tipos
$env:PYTHONPATH = "app;$env:PYTHONPATH"; .venv\Scripts\ty.exe check
```

Ambos deben pasar. No se considera terminada una tarea con errores de `ruff` o `ty`.

---

## 10. Problemas comunes

| Síntoma | Causa probable | Solución |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'api'` | Se ejecutó desde la raíz sin `PYTHONPATH`. | `cd app` o `$env:PYTHONPATH = "app"`. |
| `ModuleNotFoundError: No module named 'kardex'` | El paquete editable no está instalado. | `uv sync`. |
| `400 Missing required tenant header` | La llamada no envía `X-Servin`. | Envía `X-Servin: <nickname>` (el front y el Service Manager ya lo hacen). |
| `500 No tenant in context` | Script/tarea de fondo que tocó Mongo sin contexto. | Usa `run_with_tenant_context` o `Collection.get_instance(nickname)`. |
| `403 Tenant mismatch` | Token de un tenant con header de otro. | Envía el header del tenant del token. |
| `ETag` vacío en el primer request | El tenant no estaba en caché y falta `ensure_loaded()`. | El middleware lo carga; verifica que se use `router_v1`. |
| OpenAPI devuelve 404 | `MODE=PROD`. | Cambia el modo en desarrollo. |
| Los tests no encuentran `app` | Se ejecutaron fuera de la raíz del server. | `cd kardex-server` y `uv run pytest test/`. |
| Cambios en `onion-config.toml` sin efecto | Es un registro, no configuración runtime. | Asegúrate de declarar `collection_name` en la clase. |

---

## 11. Checklist al terminar una tarea

- [ ] `uv sync` sin cambios inesperados en `uv.lock`.
- [ ] `ruff check` limpio.
- [ ] `ty check` limpio.
- [ ] `pytest` pasa (o se documenta por qué no aplica).
- [ ] La app arranca localmente.
- [ ] Cambio registrado en `GEMINI.md` según `AGENTS.md`.
