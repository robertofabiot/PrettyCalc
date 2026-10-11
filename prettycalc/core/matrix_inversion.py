"""Inversión de matrices por Gauss-Jordan sobre [A | I_n] y resolución x = A^{-1} b.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Aritmética exacta con fractions.Fraction. Sin NumPy, SciPy ni SymPy.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Optional, Tuple

from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


class SingularMatrixError(ValueError):
    """Excepción al intentar invertir una matriz de rango deficiente (det(A) = 0)."""

    def __init__(self, message: str, tracer: Optional[StepTracer] = None) -> None:
        super().__init__(message)
        self.tracer = tracer


class NonSquareMatrixError(ValueError):
    """Excepción cuando se solicita la inversa de una matriz rectangular m ≠ n."""


@dataclass(frozen=True)
class MatrixInverseResult:
    """Resultado de invertir A mediante [A | I_n] ~ [I_n | A^{-1}]."""

    inverse: Matrix
    original: Matrix
    tracer: StepTracer
    is_invertible: bool
    identity_check_passed: bool


def _require_square(A: Matrix) -> int:
    """Exige A cuadrada y devuelve el orden n."""
    if A.rows != A.cols:
        raise NonSquareMatrixError(
            "La inversa solo está definida para matrices cuadradas (n×n). "
            f"A es {A.rows}×{A.cols}."
        )
    return A.rows


def _left_block_is_identity(reduced: Matrix, order: int) -> bool:
    """True si las primeras n columnas de la reducida son I_n."""
    for row_index in range(order):
        for col_index in range(order):
            expected = Fraction(1, 1) if row_index == col_index else Fraction(0, 1)
            if reduced.get(row_index, col_index) != expected:
                return False
    return True


def _zero_rows_in_left_block(reduced: Matrix, order: int) -> list[int]:
    """Filas 1-based del bloque izquierdo que quedaron en ceros."""
    zero_rows: list[int] = []
    for row_index in range(order):
        if all(reduced.get(row_index, col_index) == Fraction(0, 1) for col_index in range(order)):
            zero_rows.append(row_index + 1)
    return zero_rows


def _extract_right_block(reduced: Matrix, order: int) -> Matrix:
    """Extrae A^{-1} de las columnas n .. 2n-1 de [I_n | A^{-1}]."""
    data = [
        [reduced.get(row_index, order + col_index) for col_index in range(order)]
        for row_index in range(order)
    ]
    return Matrix(data)


def _identity_product_holds(original: Matrix, inverse: Matrix) -> bool:
    """Comprueba A · A^{-1} = I_n y A^{-1} · A = I_n."""
    from prettycalc.core.matrix_ops import matrix_multiply

    identity = Matrix.identity(original.rows)
    return (
        matrix_multiply(original, inverse) == identity
        and matrix_multiply(inverse, original) == identity
    )


def matrix_inverse(A: Matrix) -> MatrixInverseResult:
    """Invierte A calculando la RREF sobre [A | I_n].

    Raises:
        NonSquareMatrixError: Si A.rows != A.cols.
        SingularMatrixError: Si rango(A) < n (aparece una fila de ceros en el bloque izquierdo).
    """
    order = _require_square(A)
    augmented = A.augment(Matrix.identity(order))
    reduced, tracer = gauss_jordan_elimination(
        augmented,
        split_col=order,
        initial_description=(
            "Matriz super-aumentada inicial [A | I_n]. "
            "La inversa existe si y solo si esta matriz se reduce a [I_n | A^{-1}]."
        ),
        initial_latex=r"\text{Inicio } [A \mid I_n]",
    )
    if not _left_block_is_identity(reduced, order):
        zero_rows = _zero_rows_in_left_block(reduced, order)
        if len(zero_rows) == 1:
            rows_text = f"la fila {zero_rows[0]} quedó en ceros"
        elif len(zero_rows) > 1:
            listed = ", ".join(str(row) for row in zero_rows[:-1]) + f" y {zero_rows[-1]}"
            rows_text = f"las filas {listed} quedaron en ceros"
        else:
            rows_text = "alguna fila del bloque izquierdo quedó en ceros"
        raise SingularMatrixError(
            "La matriz es singular y no es invertible. "
            f"En la reducción de [A | I_n] el bloque izquierdo no llegó a I_{order}: "
            f"{rows_text}, así que rango(A) < {order}. "
            "Por el Teorema de la Matriz Invertible, det(A) = 0 y no existe A^{-1}.",
            tracer=tracer,
        )

    inverse = _extract_right_block(reduced, order)
    identity_ok = _identity_product_holds(A, inverse)
    if identity_ok:
        closing = "Se comprueba A · A^{-1} = I_n y A^{-1} · A = I_n."
    else:
        closing = "La comprobación A · A^{-1} = I_n no se cumplió."
    tracer.record_step(
        matrix=reduced,
        latex_formula=r"[I_n \mid A^{-1}]",
        heuristic_text=(
            "El bloque izquierdo es I_n y el bloque derecho es A^{-1}. " + closing
        ),
        split_col=order,
    )
    return MatrixInverseResult(
        inverse=inverse,
        original=A.copy(),
        tracer=tracer,
        is_invertible=True,
        identity_check_passed=identity_ok,
    )


def solve_via_inverse(A: Matrix, b: Vector) -> Tuple[Vector, MatrixInverseResult]:
    """Resuelve A x = b calculando x = A^{-1} · b para A invertible.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
        DimensionMismatchError: Si dim(b) ≠ n.
        SingularMatrixError: Si A no es invertible.
    """
    order = _require_square(A)
    if b.dimension != order:
        raise DimensionMismatchError(
            "No se puede resolver A x = b mediante x = A^{-1} b: "
            f"A es {order}×{order} y b ∈ ℝ^{b.dimension}. Se exige dim(b) = n.",
            left_shape=A.shape,
            right_shape=(b.dimension,),
            operation="resolver mediante inversa",
        )

    from prettycalc.core.matrix_vector_ops import matrix_vector_multiply

    result = matrix_inverse(A)
    solution = matrix_vector_multiply(result.inverse, b)
    return solution, result


solve_system_via_inverse = solve_via_inverse
