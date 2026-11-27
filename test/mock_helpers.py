from types import SimpleNamespace
from typing import Any, TypeVar, cast

T = TypeVar("T")


def fake(_cls: type[T], /, **attributes: Any) -> T:
    """Crea un doble de prueba tipado como `_cls` con los atributos dados."""
    return cast(T, SimpleNamespace(**attributes))
