import os
from collections import OrderedDict
from typing import Any, TypeVar

V = TypeVar("V")

DEFAULT_MAX_TENANT_CACHE_SIZE = 256


def _resolve_default_maxsize() -> int:
    raw = os.getenv("MAX_TENANT_CACHE_SIZE", str(DEFAULT_MAX_TENANT_CACHE_SIZE))
    try:
        parsed = int(raw)
        return max(1, parsed)
    except ValueError:
        return DEFAULT_MAX_TENANT_CACHE_SIZE


class BoundedTenantCache(OrderedDict[str, V]):
    """Diccionario LRU acotado por tenant.

    Hereda de ``OrderedDict`` (subclase de ``dict``) para mantener
    compatibilidad con ``.clear()``, ``in``, ``.get()`` y ``.setdefault()``
    sin crecer indefinidamente ante headers ``X-Servin`` arbitrarios.
    """

    def __init__(self, maxsize: int | None = None) -> None:
        super().__init__()
        self.maxsize = (
            max(1, maxsize) if maxsize is not None else _resolve_default_maxsize()
        )

    def __setitem__(self, key: str, value: V) -> None:
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        while len(self) > self.maxsize:
            self.popitem(last=False)

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        if key in self:
            self.move_to_end(key)
            return super().__getitem__(key)
        return default

    def setdefault(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        if key in self:
            self.move_to_end(key)
            return super().__getitem__(key)
        self[key] = default
        return default
