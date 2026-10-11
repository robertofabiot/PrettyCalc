"""Regla de Cramer para sistemas cuadrados con determinante distinto de cero.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
x_i = det(A_i(b)) / det(A), donde A_i(b) sustituye la columna i por b.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Tuple

from prettycalc.core.determinants import determinant_triangulation, require_square_matrix
from prettycalc.core.matrix_inversion import SingularMatrixError
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar


@dataclass(frozen=True)
class CramerResult:
    """Solución por cocientes de determinantes y las matrices columna reemplazadas."""

    solution: List[Fraction]
    det_A: Fraction
    column_determinants: List[Tuple[int, Matrix, Fraction]]
    is_applicable: bool
    failure_reason: Optional[str] = None


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

    column_determinants: List[Tuple[int, Matrix, Fraction]] = []
    solution: List[Fraction] = []
    for column_index in range(order):
        replaced = replace_column(A, column_index, b.components)
        column_det = determinant_triangulation(replaced).value
        column_determinants.append((column_index, replaced, column_det))
        solution.append(column_det / determinant)
    return CramerResult(
        solution=solution,
        det_A=determinant,
        column_determinants=column_determinants,
        is_applicable=True,
        failure_reason=None,
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
