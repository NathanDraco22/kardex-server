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
| `MONGO_URL` | `mongodb://localhost:27017` | Cadena de conexión a MongoDB. |
| `DB_NAME` | `LedgerDB` | Base de datos usada por `MongoService`. |
| `MODE` | *(sin default)* | `DEV` no arranca el scheduler; `PROD` oculta OpenAPI. |
| `LITE_MODE` | `false` | Activa reglas de la edición Lite. |
| `LET_NEGATIVE` | *(sin default)* | Sobrescribe `KardexConfig.letInvoiceWithNegative`. |
| `JWT_SECRET` | `secretApp` | Firma de tokens. **Cámbialo en producción.** |
| `TELEGRAM_BOT_TOKEN` | *(sin default)* | Integración de notificaciones Telegram. |
| `TELEGRAM_CHAT_ID` | `""` | Chat destino de notificaciones. |

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

- **No** arranca el scheduler (`app/core/scheduler/app_scheduler.py`).
- OpenAPI disponible.
- Recomendado para desarrollo local.

### `MODE=PROD`

- OpenAPI deshabilitado.
- No hay comportamiento especial adicional en `main.py`.

### `LITE_MODE=true`

Ajusta `KardexConfig` al arrancar (`app/app_lifespan.py`):

| Bandera | `main` | `lite` |
| :--- | :--- | :--- |
| `letInvoiceWithNegative` | `false` | `true` |
| `followTransaction` | `true` | `false` |
| `createFullProductProfile` | `false` | `true` |

`LET_NEGATIVE` tiene prioridad sobre `LITE_MODE` para `letInvoiceWithNegative`.

---

## 7. Inicialización y scheduler

Al arrancar, `app/app_lifespan.py` ejecuta `app/core/services_initializer.py`, que crea/actualiza:

- Roles por defecto (`create_default_roles`).
- Categorías de gasto (`create_default_expense_categories`).
- Escalas de unidades (`create_default_unit_scales`).
- ETags (`set_default_etags`).
- Integración por defecto (`create_default_integration`).
- App settings (`create_default_app_settings`).
- Usuario root (`create_root_user`).
- Cachés de sucursales, usuarios inactivos y app settings.

El scheduler solo arranca si `MODE != "DEV"`.

---

## 8. Tests

```powershell
cd kardex-server
uv run pytest test/
```

- `test/__init__.py` agrega `app/` al `sys.path`, por eso debe ejecutarse desde la raíz del server.
- `test/test_demo.py` está vacío (0 bytes); no lo tomes como suite de referencia.

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
| No se ejecutan recordatorios/reportes | `MODE=DEV`. | Usa otro modo o invoca la tarea manualmente. |
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
