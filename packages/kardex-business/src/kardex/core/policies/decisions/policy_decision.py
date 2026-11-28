from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Resultado de evaluar una regla de dominio."""

    allowed: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.allowed and not (self.reason or "").strip():
            raise ValueError("Una decisión rechazada requiere un motivo.")
