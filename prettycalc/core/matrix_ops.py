"""Álgebra matricial básica: suma, resta, escala y producto con bucles anidados.

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
Prohibido NumPy, SciPy y álgebra lineal de `math`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, List, Tuple

from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    format_scalar,
    parse_scalar,
)


def _require_same_shape(A: Matrix, B: Matrix, operation: str) -> None:
    """Valida A.shape == B.shape para suma y resta."""
    if A.shape != B.shape:
        raise DimensionMismatchError(
            f"No se puede {operation}: A es {A.rows}×{A.cols} y B es {B.rows}×{B.cols}. "
            "La suma y la resta exigen matrices de idénticas dimensiones m×n.",
            left_shape=A.shape,
            right_shape=B.shape,
            operation=operation,
        )


def _require_conformable(A: Matrix, B: Matrix) -> None:
    """Valida A.cols == B.rows para el producto A · B."""
    if A.cols != B.rows:
        raise DimensionMismatchError(
            f"No se puede multiplicar: columnas de A ({A.cols}) ≠ filas de B ({B.rows}). "
            f"El producto A_{{{A.rows}×{A.cols}}} · B_{{{B.rows}×{B.cols}}} no es conformable. "
            "Se requiere A m×n y B n×p para obtener C m×p.",
            left_shape=A.shape,
            right_shape=B.shape,
            operation="multiplicar matrices",
        )


def matrix_add(A: Matrix, B: Matrix) -> Matrix:
    """Suma elemento a elemento: C_ij = A_ij + B_ij.

    Raises:
        DimensionMismatchError: Si A.shape ≠ B.shape.
    """
    _require_same_shape(A, B, "sumar matrices")
    C = Matrix.zeros(A.rows, A.cols)
    for i in range(A.rows):
        for j in range(A.cols):
            C.set(i, j, A.get(i, j) + B.get(i, j))
    return C


def matrix_sub(A: Matrix, B: Matrix) -> Matrix:
    """Resta elemento a elemento: C_ij = A_ij − B_ij.

    Raises:
        DimensionMismatchError: Si A.shape ≠ B.shape.
    """
    _require_same_shape(A, B, "restar matrices")
    C = Matrix.zeros(A.rows, A.cols)
    for i in range(A.rows):
        for j in range(A.cols):
            C.set(i, j, A.get(i, j) - B.get(i, j))
    return C


def matrix_scale(A: Matrix, scalar: Any) -> Matrix:
    """Producto por escalar: C_ij = k · A_ij."""
    k = parse_scalar(scalar)
    C = Matrix.zeros(A.rows, A.cols)
    for i in range(A.rows):
        for j in range(A.cols):
            C.set(i, j, k * A.get(i, j))
    return C


@dataclass(frozen=True)
class MultiplicationStepDetail:
    """Desglose pedagógico de una celda C_ij = Σ_k A_ik · B_kj.

    Attributes:
        row: Índice i (0-based) de la fila en A y en C.
        col: Índice j (0-based) de la columna en B y en C.
        products: Triplets (A_ik, B_kj, A_ik·B_kj) para cada k.
        total: Suma exacta de los productos parciales.
        formula: Texto de la sumatoria para el inspector y el informe.
    """

    row: int
    col: int
    products: List[Tuple[Fraction, Fraction, Fraction]]
    total: Fraction
    formula: str


def matrix_multiply(A: Matrix, B: Matrix) -> Matrix:
    """Producto matricial C = A · B mediante tres bucles anidados.

    Condición de conformabilidad: A.cols == B.rows.
    Cada celda se calcula como producto punto de la fila i de A con la
    columna j de B:

        C[i][j] = sum(A[i][k] * B[k][j] for k in range(n))

    Raises:
        DimensionMismatchError: Si las matrices no son conformables.
    """
    result, _ = matrix_multiply_with_details(A, B)
    return result


def matrix_multiply_with_details(
    A: Matrix,
    B: Matrix,
) -> Tuple[Matrix, List[MultiplicationStepDetail]]:
    """Producto A · B junto al desglose de cada celda para el inspector.

    Algoritmo en Python estándar (tres bucles anidados, aritmética exacta):

        C = Matrix.zeros(m, p)
        for i in range(m):
            for j in range(p):
                accum = Fraction(0, 1)
                for k in range(n):
                    accum += A.get(i, k) * B.get(k, j)
                C.set(i, j, accum)

    Returns:
        (C, detalles) donde `detalles` tiene una entrada por cada C_ij.
    """
    _require_conformable(A, B)

    m, n = A.rows, A.cols
    p = B.cols
    C = Matrix.zeros(m, p)
    details: List[MultiplicationStepDetail] = []

    for i in range(m):
        for j in range(p):
            accum = Fraction(0, 1)
            products: List[Tuple[Fraction, Fraction, Fraction]] = []
            term_texts: List[str] = []
            for k in range(n):
                a_ik = A.get(i, k)
                b_kj = B.get(k, j)
                prod = a_ik * b_kj
                accum += prod
                products.append((a_ik, b_kj, prod))
                a_str = format_scalar(a_ik, mode="fraction")
                b_str = format_scalar(b_kj, mode="fraction")
                term_texts.append(f"({a_str})·({b_str})")

            C.set(i, j, accum)
            total_str = format_scalar(accum, mode="fraction")
            sum_body = " + ".join(term_texts) if term_texts else "0"
            formula = (
                f"C_{i + 1},{j + 1} = Σ_k A_{i + 1}k · B_k{j + 1} "
                f"= {sum_body} = {total_str}"
            )
            details.append(
                MultiplicationStepDetail(
                    row=i,
                    col=j,
                    products=products,
                    total=accum,
                    formula=formula,
                )
            )

    return C, details
