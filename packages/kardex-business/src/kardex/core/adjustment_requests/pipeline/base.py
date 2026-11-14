from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

TContext = TypeVar("TContext")


class PipelineStep(ABC, Generic[TContext]):
    """Paso independiente de un pipeline.

    Cada paso lee y escribe únicamente el contexto que recibe. No conoce a los
    demás pasos ni abre transacciones; el orquestador es quien define el orden
    y el límite transaccional.
    """

    @property
    def name(self) -> str:
        return type(self).__name__

    def should_execute(self, context: TContext) -> bool:
        """Permite omitir el paso cuando el contexto no tiene trabajo para él."""
        return True

    @abstractmethod
    async def execute(self, context: TContext) -> None:
        raise NotImplementedError


@dataclass
class PipelineResult(Generic[TContext]):
    context: TContext
    executed_steps: list[str]
    skipped_steps: list[str]


class Pipeline(Generic[TContext]):
    """Ejecuta una secuencia de pasos sobre un contexto compartido."""

    def __init__(self, steps: Sequence[PipelineStep[TContext]]):
        self.steps = list(steps)

    async def run(self, context: TContext) -> PipelineResult[TContext]:
        executed_steps: list[str] = []
        skipped_steps: list[str] = []

        for step in self.steps:
            if not step.should_execute(context):
                skipped_steps.append(step.name)
                continue

            await step.execute(context)
            executed_steps.append(step.name)

        return PipelineResult(
            context=context,
            executed_steps=executed_steps,
            skipped_steps=skipped_steps,
        )
