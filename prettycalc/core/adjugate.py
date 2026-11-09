"""Matriz de menores, cofactores, adjunta e inversa analítica.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
A⁻¹ = (1 / det A) · adj(A), con adj(A) = Cᵀ y C_ij = (−1)^(i+j) M_ij.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from prettycalc.core.determinants import (
    delete_row_and_column,
    minor_determinant,
    record_determinant_working,
    require_square_matrix,
)
from prettycalc.core.matrix_ops import matrix_scale, matrix_transpose
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import Matrix, format_scalar, subscript


@dataclass(frozen=True)
class AdjugateResult:
    """Menores, cofactores, adjunta y, si det(A) ≠ 0, la inversa analítica."""

    minors_matrix: Matrix
    cofactors_matrix: Matrix
    adjugate_matrix: Matrix
    inverse_via_adjugate: Optional[Matrix]
    det_A: Fraction
    #: Procedimiento completo: cada menor con su cuenta, signos, transpuesta e inversa.
    tracer: StepTracer = field(default_factory=StepTracer, compare=False)


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
    order = require_square_matrix(A, "calcular la adjunta")
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            "Matriz adjunta en cuatro etapas: cada menor Mᵢⱼ, la matriz de cofactores "
            "Cᵢⱼ = (−1)^(i+j)·Mᵢⱼ, su transpuesta adj(A) = Cᵀ y, si det(A) ≠ 0, "
            "A⁻¹ = (1/det A)·adj(A)."
        ),
        latex_title=r"\text{adj}(A) = C^{T}",
    )

    # Etapa 1: cada menor, con su cuenta completa.
    minors = Matrix.zeros(order, order)
    for row_index in range(order):
        for col_index in range(order):
            i, j = row_index + 1, col_index + 1
            if order == 1:
                value = Fraction(1, 1)
                tracer.record_step(
                    A,
                    latex_formula=r"M_{11} = 1",
                    heuristic_text="En una matriz 1×1 el menor es vacío y vale 1 por convención.",
                )
            else:
                value = record_determinant_working(
                    tracer,
                    delete_row_and_column(A, row_index, col_index),
                    rf"M_{{{i}{j}}}",
                    f"M{subscript(i, j)}",
                    intro=f"Menor {row_index * order + j} de {order * order}: se tachan la fila {i} y la columna {j}. ",
                )
            minors.set(row_index, col_index, value)
    tracer.record_step(
        minors,
        latex_formula=r"M = (M_{ij})",
        heuristic_text="Matriz de menores: cada posición guarda el menor Mᵢⱼ calculado arriba.",
    )

    # Etapa 2: tablero de signos.
    cofactors = _cofactors_from_minors(minors)
    flipped = tuple(
        (r, c) for r in range(order) for c in range(order) if (r + c) % 2 == 1
    )
    tracer.record_step(
        cofactors,
        latex_formula=r"C_{ij} = (-1)^{i+j} M_{ij}",
        heuristic_text=(
            "Matriz de cofactores: el tablero de signos (−1)^(i+j) cambia el signo de las "
            "posiciones resaltadas (i + j impar) y deja igual las demás."
        ),
        highlight_cells=flipped,
    )

    # Etapa 3: transpuesta.
    adjugate = matrix_transpose(cofactors)
    tracer.record_step(
        adjugate,
        latex_formula=r"\text{adj}(A) = C^{T}",
        heuristic_text="Adjunta: se transpone C; la fila i de C pasa a ser la columna i de adj(A).",
    )

    # Etapa 4: det(A) por la primera fila (reutiliza los cofactores) e inversa.
    determinant = sum(
        (A.get(0, col) * cofactors.get(0, col) for col in range(order)), Fraction(0, 1)
    )
    terms = " + ".join(
        f"({format_scalar(A.get(0, col))})({format_scalar(cofactors.get(0, col))})"
        for col in range(order)
    )
    tracer.record_step(
        A,
        latex_formula=rf"\det(A) = \sum_j a_{{1j}} C_{{1j}} = {format_scalar(determinant, mode='latex')}",
        heuristic_text=(
            f"det(A) por la fila 1 con los cofactores ya calculados: {terms} "
            f"= {format_scalar(determinant)}."
        ),
        highlight_cells=tuple((0, col) for col in range(order)),
    )
    inverse: Optional[Matrix]
    if determinant == Fraction(0, 1):
        inverse = None
        tracer.record_step(
            adjugate,
            latex_formula=r"\det(A) = 0",
            heuristic_text="det(A) = 0: la adjunta existe, pero A no es invertible y no hay A⁻¹.",
        )
    else:
        factor = Fraction(1, 1) / determinant
        inverse = matrix_scale(adjugate, factor)
        tracer.record_step(
            inverse,
            latex_formula=rf"A^{{-1}} = \frac{{1}}{{{format_scalar(determinant, mode='latex')}}}\,\text{{adj}}(A)",
            heuristic_text=(
                f"A⁻¹ = (1/det A)·adj(A): cada entrada de adj(A) se multiplica por "
                f"1/{format_scalar(determinant)} = {format_scalar(factor)}."
            ),
        )
    return AdjugateResult(
        minors_matrix=minors,
        cofactors_matrix=cofactors,
        adjugate_matrix=adjugate,
        inverse_via_adjugate=inverse,
        det_A=determinant,
        tracer=tracer,
    )
