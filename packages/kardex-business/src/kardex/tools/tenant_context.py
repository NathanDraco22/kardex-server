"""Utilidades del contexto multi-tenant.

Centraliza el identificador de tenant (nickname):

- ``normalize_nickname``: ``.strip().lower()`` en una sola capa. MongoDB es
  *case-sensitive* con los nombres de base de datos, asi que el nickname debe
  normalizarse de forma identica en el middleware, el core-settings, el
  aprovisionamiento, ``Meta`` y los runners.
- ``is_valid_tenant_nickname``: patron y lista negra compartidos por el
  middleware de tenant y el aprovisionamiento.
- ``run_with_tenant_context``: helper para tareas de fondo. Una
  ``BackgroundTask`` no debe confiar en que el contexto del request siga vivo.
"""

import re
from typing import Any, Awaitable, Callable, TypeVar

from kardex.kardex_config import KardexContext, kardexCtx

TENANT_NICKNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,48}$")

RESERVED_TENANT_NICKNAMES = frozenset(
    {"admin", "local", "config", "kardexcontrol"}
)

T = TypeVar("T")


def normalize_nickname(nickname: str | None) -> str:
    """Normaliza un nickname de tenant. Cadena vacia si viene ``None``."""

    return (nickname or "").strip().lower()


def is_valid_tenant_nickname(nickname: str) -> bool:
    """Valida el patron y la lista negra de nombres de base de datos."""

    if not nickname:
        return False

    if not TENANT_NICKNAME_PATTERN.match(nickname):
        return False

    return nickname not in RESERVED_TENANT_NICKNAMES


async def run_with_tenant_context(
    nickname: str,
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Ejecuta ``fn`` fijando explicitamente el tenant.

    Se usa en las ``BackgroundTasks`` que tocan MongoDB: el ``finally`` de una
    dependencia con ``yield`` ocurre despues de las tareas de fondo en FastAPI
    0.136+, pero no queremos depender de ese detalle interno (cambio entre
    versiones y configurable con ``Depends(scope=...)``).
    """

    token = kardexCtx.set(KardexContext(businessNickname=normalize_nickname(nickname)))
    try:
        return await fn(*args, **kwargs)
    finally:
        kardexCtx.reset(token)
