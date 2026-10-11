"""Matriz de menores, cofactores, adjunta e inversa analítica.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
A⁻¹ = (1 / det A) · adj(A), con adj(A) = Cᵀ y C_ij = (−1)^(i+j) M_ij.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

from prettycalc.core.determinants import (
    determinant_triangulation,
    minor_determinant,
    require_square_matrix,
)
from prettycalc.core.matrix_ops import matrix_scale, matrix_transpose
from prettycalc.core.types import Matrix


@dataclass(frozen=True)
class AdjugateResult:
    """Menores, cofactores, adjunta y, si det(A) ≠ 0, la inversa analítica."""

    minors_matrix: Matrix
    cofactors_matrix: Matrix
    adjugate_matrix: Matrix
    inverse_via_adjugate: Optional[Matrix]
    det_A: Fraction


def _cofactors_from_minors(minors: Matrix) -> Matrix:
    """Aplica el tablero de signos (−1)^(i+j) a la matriz de menores."""
    signed = Matrix.zeros(minors.rows, minors.cols)
    for row_index in range(minors.rows):
        for col_index in range(minors.cols):
            sign = Fraction(1, 1) if (row_index + col_index) % 2 == 0 else Fraction(-1, 1)
            signed.set(row_index, col_index, sign * minors.get(row_index, col_index))
    return signed


def minors_matrix(A: Matrix) -> Matrix:
    """Matriz M con M_ij = det(A_ij). En 1×1, M_11 = 1.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    order = require_square_matrix(A, "formar la matriz de menores")
    minors = Matrix.zeros(order, order)
    for row_index in range(order):
        for col_index in range(order):
            minors.set(row_index, col_index, minor_determinant(A, row_index, col_index))
    return minors


def cofactor_matrix(A: Matrix) -> Matrix:
    """Matriz de cofactores C_ij = (−1)^(i+j) M_ij.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    return _cofactors_from_minors(minors_matrix(A))


def adjugate_matrix(A: Matrix) -> Matrix:
    """adj(A) = Cᵀ, la transpuesta de la matriz de cofactores.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    return matrix_transpose(cofactor_matrix(A))


def calculate_adjugate_and_inverse(A: Matrix) -> AdjugateResult:
    """Calcula menores, cofactores, adjunta y A⁻¹ = (1/det A) adj(A).

    Si det(A) = 0, `inverse_via_adjugate` es None: la adjunta sigue definida.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    require_square_matrix(A, "calcular la adjunta")
    minors = minors_matrix(A)
    cofactors = _cofactors_from_minors(minors)
    adjugate = matrix_transpose(cofactors)
    determinant = determinant_triangulation(A).value
    inverse: Optional[Matrix]
    if determinant == Fraction(0, 1):
        inverse = None
    else:
        inverse = matrix_scale(adjugate, Fraction(1, 1) / determinant)
    return AdjugateResult(
        minors_matrix=minors,
        cofactors_matrix=cofactors,
        adjugate_matrix=adjugate,
        inverse_via_adjugate=inverse,
        det_A=determinant,
    )
