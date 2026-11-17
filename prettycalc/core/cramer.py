"""Regla de Cramer para sistemas cuadrados con determinante distinto de cero.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
x_i = det(A_i(b)) / det(A), donde A_i(b) sustituye la columna i por b.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Tuple

from prettycalc.core.determinants import (
    determinant_triangulation,
    record_determinant_working,
    require_square_matrix,
)
from prettycalc.core.matrix_inversion import SingularMatrixError
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar, subscript


@dataclass(frozen=True)
class CramerResult:
    """Solución por cocientes de determinantes y las matrices columna reemplazadas."""

    solution: List[Fraction]
    det_A: Fraction
    column_determinants: List[Tuple[int, Matrix, Fraction]]
    is_applicable: bool
    failure_reason: Optional[str] = None
    #: det(A), cada A_i(b) con su determinante desarrollado y cada cociente x_i.
    tracer: StepTracer = field(default_factory=StepTracer, compare=False)


def replace_column(A: Matrix, column_index: int, values: List[Fraction]) -> Matrix:
    """Devuelve una copia de A con la columna `column_index` sustituida por `values`."""
    if column_index < 0 or column_index >= A.cols:
        raise IndexError(
            f"La columna {column_index + 1} no existe en una matriz de {A.cols} columnas."
        )
    if len(values) != A.rows:
        raise DimensionMismatchError(
            "No se puede reemplazar la columna: "
            f"A tiene {A.rows} filas y el vector tiene {len(values)} componentes.",
            left_shape=A.shape,
            right_shape=(len(values),),
            operation="reemplazar columna",
        )
    data = A.to_list()
    for row_index, value in enumerate(values):
        data[row_index][column_index] = value
    return Matrix(data)


def _shown(value: Fraction) -> str:
    """Un negativo va entre paréntesis en un cociente: 6 / (−2)."""
    text = format_scalar(value)
    return f"({text})" if value < 0 else text


def solve_cramer(A: Matrix, b: Vector) -> CramerResult:
    """Resuelve A x = b por la Regla de Cramer.

    Raises:
        NonSquareMatrixError: Si A.rows != A.cols.
        DimensionMismatchError: Si A.rows != dim(b).
        SingularMatrixError: Si det(A) = 0 (Cramer no aplica).
    """
    order = require_square_matrix(A, "aplicar la Regla de Cramer")
    if b.dimension != order:
        raise DimensionMismatchError(
            "La Regla de Cramer exige un sistema n×n: "
            f"A es {order}×{order} y b ∈ ℝ^{b.dimension}. Se exige dim(b) = n.",
            left_shape=A.shape,
            right_shape=(b.dimension,),
            operation="Regla de Cramer",
        )

    determinant = determinant_triangulation(A).value
    if determinant == Fraction(0, 1):
        raise SingularMatrixError(
            "La Regla de Cramer no aplica porque det(A) = 0. "
            "La matriz de coeficientes es singular: el sistema puede ser "
            "inconsistente o indeterminado. Gauss-Jordan clasifica cuál de los dos es."
        )

    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            "Matriz de coeficientes A. Cramer: xᵢ = det(Aᵢ(b)) / det(A), donde Aᵢ(b) es A con "
            "la columna i reemplazada por b. Primero det(A), que no debe ser cero."
        ),
        latex_title=r"x_i = \frac{\det(A_i(b))}{\det(A)}",
    )
    record_determinant_working(tracer, A, r"\det(A)", "det(A)")

    column_determinants: List[Tuple[int, Matrix, Fraction]] = []
    solution: List[Fraction] = []
    for column_index in range(order):
        i = column_index + 1
        column = tuple((row, column_index) for row in range(order))
        replaced = replace_column(A, column_index, b.components)
        column_det = record_determinant_working(
            tracer,
            replaced,
            rf"\det(A_{{{i}}}(b))",
            f"det(A{subscript(i)}(b))",
            intro=f"A{subscript(i)}(b): la columna {i} de A se reemplaza por b (resaltada). ",
            highlight_cells=column,
        )
        value = column_det / determinant
        tracer.record_step(
            replaced,
            latex_formula=rf"x_{{{i}}} = \frac{{{format_scalar(column_det, mode='latex')}}}{{{format_scalar(determinant, mode='latex')}}} = {format_scalar(value, mode='latex')}",
            heuristic_text=(
                f"x{subscript(i)} = det(A{subscript(i)}(b)) / det(A) = "
                f"{_shown(column_det)} / {_shown(determinant)} = {format_scalar(value)}."
            ),
            highlight_cells=column,
        )
        column_determinants.append((column_index, replaced, column_det))
        solution.append(value)
    return CramerResult(
        solution=solution,
        det_A=determinant,
        column_determinants=column_determinants,
        is_applicable=True,
        failure_reason=None,
        tracer=tracer,
    )


def format_cramer_component(index: int, column_det: Fraction, det_a: Fraction, value: Fraction) -> str:
    """Texto x_i = det(A_i(b)) / det(A) = fracción simplificada."""
    position = index + 1
    return (
        f"x{position} = det(A{position}(b)) / det(A) = "
        f"{format_scalar(column_det)} / {format_scalar(det_a)} = {format_scalar(value)}"
    )


# Reexportación explícita para que los llamadores no importen la excepción desde otro módulo.
__all__ = [
    "CramerResult",
    "format_cramer_component",
    "replace_column",
    "solve_cramer",
]
