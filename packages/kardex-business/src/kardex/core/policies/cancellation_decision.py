from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CancellationDecision:
    """Resultado de evaluar si una entidad puede anularse."""

    allowed: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.allowed and not (self.reason or "").strip():
            raise ValueError(
                "Una decisión de cancelación rechazada requiere un motivo."
            )
