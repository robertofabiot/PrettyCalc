"""Álgebra matricial: suma, resta, escala, producto y transpuesta.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.
Aritmética exacta con fractions.Fraction. Sin NumPy, SciPy ni math.
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
    """Producto por escalar: recibe A y k, devuelve C con C_ij = k · A_ij."""
    k = parse_scalar(scalar)
    C = Matrix.zeros(A.rows, A.cols)
    for i in range(A.rows):
        for j in range(A.cols):
            C.set(i, j, k * A.get(i, j))
    return C


def matrix_transpose(A: Matrix) -> Matrix:
    """Transpuesta: si A es m×n, devuelve Aᵀ de n×m con (Aᵀ)_ji = A_ij.

    No modifica A. El intercambio de índices es la definición, no un pivoteo.
    """
    transposed = Matrix.zeros(A.cols, A.rows)
    for row_index in range(A.rows):
        for col_index in range(A.cols):
            transposed.set(col_index, row_index, A.get(row_index, col_index))
    return transposed


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


def _format_cell_formula(
    row_index: int,
    col_index: int,
    term_texts: List[str],
    total: Fraction,
) -> str:
    """Texto de la sumatoria de la celda C_ij para el inspector."""
    total_text = format_scalar(total, mode="fraction")
    sum_body = " + ".join(term_texts) if term_texts else "0"
    return (
        f"C_{row_index + 1},{col_index + 1} = Σ_k A_{row_index + 1}k · B_k{col_index + 1} "
        f"= {sum_body} = {total_text}"
    )


def _cell_product(A: Matrix, B: Matrix, row_index: int, col_index: int) -> MultiplicationStepDetail:
    """Producto punto de la fila row_index de A con la columna col_index de B."""
    accum = Fraction(0, 1)
    products: List[Tuple[Fraction, Fraction, Fraction]] = []
    term_texts: List[str] = []
    for shared in range(A.cols):
        left = A.get(row_index, shared)
        right = B.get(shared, col_index)
        prod = left * right
        accum += prod
        products.append((left, right, prod))
        left_text = format_scalar(left, mode="fraction")
        right_text = format_scalar(right, mode="fraction")
        term_texts.append(f"({left_text})·({right_text})")
    return MultiplicationStepDetail(
        row=row_index,
        col=col_index,
        products=products,
        total=accum,
        formula=_format_cell_formula(row_index, col_index, term_texts, accum),
    )


def matrix_multiply(A: Matrix, B: Matrix) -> Matrix:
    """Producto C = A · B. Exige columnas de A = filas de B y devuelve C."""
    result, _ = matrix_multiply_with_details(A, B)
    return result


def matrix_multiply_with_details(
    A: Matrix,
    B: Matrix,
) -> Tuple[Matrix, List[MultiplicationStepDetail]]:
    """Producto A · B y una ficha por cada C_ij. Devuelve (C, detalles)."""
    _require_conformable(A, B)
    result = Matrix.zeros(A.rows, B.cols)
    details: List[MultiplicationStepDetail] = []
    for row_index in range(A.rows):
        for col_index in range(B.cols):
            detail = _cell_product(A, B, row_index, col_index)
            result.set(row_index, col_index, detail.total)
            details.append(detail)
    return result, details
