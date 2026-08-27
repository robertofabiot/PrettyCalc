"""Sistema de trazabilidad de pasos intermedios (StepTracer) para PrettyCalc.

Captura cada mutación, pivote, fórmula formal LaTeX y texto heurístico.
100% Python estándar (sin dependencias externas).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Iterator
from prettycalc.core.types import Matrix


@dataclass(frozen=True)
class CalculationStep:
    """Representa un estado discreto en la secuencia de resolución de un algoritmo.

    Attributes:
        step_number: Número secuencial del paso (0 para el estado inicial).
        matrix: Copia snapshot de la matriz en este paso.
        pivot_pos: Coordenadas (fila, columna) del pivote activo, o None si no aplica.
        latex_formula: Notación matemática formal de la operación elemental aplicada.
        heuristic_text: Texto descriptivo en lenguaje natural de la transformación.
        split_col: Índice de columna para trazar la partición aumentada [A | b].
        actor_row: Fila de referencia (pivote) que no muta en esta operación.
        affected_rows: Filas que sí cambian en esta operación.
    """
    step_number: int
    matrix: Matrix
    pivot_pos: Optional[Tuple[int, int]]
    latex_formula: str
    heuristic_text: str
    split_col: Optional[int] = None
    actor_row: Optional[int] = None
    affected_rows: Tuple[int, ...] = ()

    def to_latex_display(self) -> str:
        """Retorna el código LaTeX completo de la matriz en este paso."""
        return self.matrix.to_latex(split_col=self.split_col)


class StepTracer:
    """Trazador y recolector secuencial de pasos de cálculo."""

    def __init__(self, split_col: Optional[int] = None):
        """Inicializa un trazador vacío.

        Args:
            split_col: Índice de columna para la partición aumentada por defecto.
        """
        self._steps: List[CalculationStep] = []
        self._split_col: Optional[int] = split_col

    def record_initial(
        self,
        matrix: Matrix,
        description: str = "Matriz aumentada inicial del sistema",
        latex_title: str = "\\text{Sistema Inicial } [A \\mid b]",
    ) -> CalculationStep:
        """Registra el paso 0 correspondiente al estado inicial."""
        self.clear()
        step = CalculationStep(
            step_number=0,
            matrix=matrix.copy(),
            pivot_pos=None,
            latex_formula=latex_title,
            heuristic_text=description,
            split_col=self._split_col,
        )
        self._steps.append(step)
        return step

    def record_step(
        self,
        matrix: Matrix,
        latex_formula: str,
        heuristic_text: str,
        pivot_pos: Optional[Tuple[int, int]] = None,
        split_col: Optional[int] = None,
        actor_row: Optional[int] = None,
        affected_rows: Optional[Tuple[int, ...]] = None,
    ) -> CalculationStep:
        """Registra una nueva transformación elemental."""
        effective_split = split_col if split_col is not None else self._split_col
        step_number = len(self._steps)
        step = CalculationStep(
            step_number=step_number,
            matrix=matrix.copy(),
            pivot_pos=pivot_pos,
            latex_formula=latex_formula,
            heuristic_text=heuristic_text,
            split_col=effective_split,
            actor_row=actor_row,
            affected_rows=affected_rows or (),
        )
        self._steps.append(step)
        return step

    def get_steps(self) -> List[CalculationStep]:
        """Retorna la lista inmutable/copia de pasos registrados."""
        return list(self._steps)

    def clear(self) -> None:
        """Limpia los pasos registrados."""
        self._steps.clear()

    @property
    def total_steps(self) -> int:
        """Cantidad total de pasos registrados."""
        return len(self._steps)

    def __len__(self) -> int:
        return len(self._steps)

    def __getitem__(self, index: int) -> CalculationStep:
        return self._steps[index]

    def __iter__(self) -> Iterator[CalculationStep]:
        return iter(self._steps)
