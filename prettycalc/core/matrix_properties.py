"""Propiedades estructurales de una matriz y comprobaciones de la transpuesta.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.
Clasifica tipo, nulidad, forma y simetría, y verifica las identidades de Aᵀ
sin mutar las matrices de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, List, Literal, Optional, Sequence

from prettycalc.core.matrix_ops import (
    matrix_add,
    matrix_multiply,
    matrix_scale,
    matrix_transpose,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, format_scalar, parse_scalar

PropertyStatus = Literal["cumple", "no_cumple", "no_aplica", "dato"]


@dataclass(frozen=True)
class PropertyCheck:
    """Nombre, estado (cumple, no cumple, no aplica o dato) y frase de detalle."""

    name: str
    status: PropertyStatus
    detail: str


def describe_matrix_kind(A: Matrix) -> str:
    """Devuelve el tipo estructural de A: cuadrada, rectangular, fila o columna."""
    rows, cols = A.rows, A.cols
    if rows == 1 and cols == 1:
        return "cuadrada 1×1 (también vector fila y vector columna)"
    if rows == 1:
        return f"vector fila (1×{cols})"
    if cols == 1:
        return f"vector columna ({rows}×1)"
    if rows == cols:
        return f"cuadrada ({rows}×{rows})"
    return f"rectangular ({rows}×{cols})"


def is_zero_matrix(A: Matrix) -> bool:
    """True si toda entrada de A es cero."""
    zero = Fraction(0, 1)
    for row_index in range(A.rows):
        for col_index in range(A.cols):
            if A.get(row_index, col_index) != zero:
                return False
    return True


def is_diagonal(A: Matrix) -> bool:
    """True si A es cuadrada y a_ij = 0 para todo i distinto de j."""
    if A.rows != A.cols:
        return False
    for row_index in range(A.rows):
        for col_index in range(A.cols):
            if row_index != col_index and A.get(row_index, col_index) != 0:
                return False
    return True


def is_scalar_matrix(A: Matrix) -> bool:
    """True si A = k I: es diagonal y la diagonal es constante."""
    if not is_diagonal(A):
        return False
    pivot = A.get(0, 0)
    for index in range(1, A.rows):
        if A.get(index, index) != pivot:
            return False
    return True


def is_upper_triangular(A: Matrix) -> bool:
    """True si A es cuadrada y a_ij = 0 siempre que i > j."""
    if A.rows != A.cols:
        return False
    for row_index in range(A.rows):
        for col_index in range(row_index):
            if A.get(row_index, col_index) != 0:
                return False
    return True


def is_lower_triangular(A: Matrix) -> bool:
    """True si A es cuadrada y a_ij = 0 siempre que i < j."""
    if A.rows != A.cols:
        return False
    for row_index in range(A.rows):
        for col_index in range(row_index + 1, A.cols):
            if A.get(row_index, col_index) != 0:
                return False
    return True


def is_identity(A: Matrix) -> bool:
    """True si A es cuadrada y coincide con I_n."""
    if A.rows != A.cols:
        return False
    return A == Matrix.identity(A.rows)


def is_symmetric(A: Matrix) -> bool:
    """True si A es cuadrada y A = Aᵀ."""
    if A.rows != A.cols:
        return False
    return matrix_transpose(A) == A


def is_skew_symmetric(A: Matrix) -> bool:
    """True si A es cuadrada y Aᵀ = −A."""
    if A.rows != A.cols:
        return False
    return matrix_transpose(A) == matrix_scale(A, -1)


def matrix_trace(A: Matrix) -> Fraction:
    """Suma de la diagonal. Recibe A cuadrada y devuelve tr(A).

    Raises:
        DimensionMismatchError: Si A no es n×n.
    """
    if A.rows != A.cols:
        raise DimensionMismatchError(
            f"La traza solo está definida para matrices cuadradas; A es {A.rows}×{A.cols}.",
            left_shape=A.shape,
            operation="traza",
        )
    total = Fraction(0, 1)
    for index in range(A.rows):
        total += A.get(index, index)
    return total


def structural_checks(A: Matrix) -> List[PropertyCheck]:
    """Lista el tipo de A y, si es cuadrada, las propiedades clásicas y la traza."""
    checks = [
        PropertyCheck("Tipo", "dato", describe_matrix_kind(A)),
        _mark_bool(
            "Matriz nula",
            is_zero_matrix(A),
            "Todas las entradas son 0.",
            "Hay al menos una entrada distinta de 0.",
        ),
    ]
    checks.extend(_square_property_checks(A))
    return checks


def transpose_identity_checks(
    A: Matrix,
    B: Optional[Matrix] = None,
    scalar: Any = None,
) -> List[PropertyCheck]:
    """Comprueba (Aᵀ)ᵀ = A y, cuando hay datos, (A+B)ᵀ, (kA)ᵀ y (AB)ᵀ."""
    return [
        _double_transpose_check(A),
        _sum_transpose_check(A, B),
        _scalar_transpose_check(A, scalar),
        _product_transpose_check(A, B),
    ]


def analyze_matrix(
    A: Matrix,
    B: Optional[Matrix] = None,
    scalar: Any = None,
) -> List[PropertyCheck]:
    """Reúne las propiedades estructurales de A y las identidades de la transpuesta."""
    return structural_checks(A) + transpose_identity_checks(A, B, scalar)


def format_property_lines(checks: Sequence[PropertyCheck]) -> List[str]:
    """Convierte cada chequeo en una línea con marca ✓, ✗, — o ·."""
    marks = {"cumple": "✓", "no_cumple": "✗", "no_aplica": "—", "dato": "·"}
    return [f"{marks[check.status]}  {check.name}: {check.detail}" for check in checks]


def _mark_bool(name: str, holds: bool, when_true: str, when_false: str) -> PropertyCheck:
    """Arma un chequeo binario: cumple si holds, si no no_cumple."""
    status: PropertyStatus = "cumple" if holds else "no_cumple"
    return PropertyCheck(name, status, when_true if holds else when_false)


def _if_square(
    A: Matrix,
    name: str,
    holds: bool,
    when_true: str,
    when_false: str,
) -> PropertyCheck:
    """Aplica un predicado solo a matrices n×n; en otro caso marca no aplica."""
    if A.rows != A.cols:
        return PropertyCheck(name, "no_aplica", "No aplica: la matriz no es cuadrada.")
    return _mark_bool(name, holds, when_true, when_false)


def _square_property_checks(A: Matrix) -> List[PropertyCheck]:
    """Propiedades que el curso define únicamente para matrices cuadradas."""
    return [
        _if_square(A, "Matriz identidad", is_identity(A), "A = I_n.", "A ≠ I_n."),
        _if_square(
            A, "Matriz diagonal", is_diagonal(A),
            "a_ij = 0 para i ≠ j.", "Hay entradas fuera de la diagonal.",
        ),
        _if_square(
            A, "Matriz escalar", is_scalar_matrix(A),
            "La diagonal es constante y el resto es nulo.", "No es de la forma k·I.",
        ),
        _if_square(
            A, "Triangular superior", is_upper_triangular(A),
            "Ceros estrictamente bajo la diagonal.", "Hay un a_ij ≠ 0 con i > j.",
        ),
        _if_square(
            A, "Triangular inferior", is_lower_triangular(A),
            "Ceros estrictamente sobre la diagonal.", "Hay un a_ij ≠ 0 con i < j.",
        ),
        _if_square(A, "Simétrica", is_symmetric(A), "A = Aᵀ.", "A ≠ Aᵀ."),
        _if_square(A, "Antisimétrica", is_skew_symmetric(A), "Aᵀ = −A.", "Aᵀ ≠ −A."),
        _trace_check(A),
    ]


def _trace_check(A: Matrix) -> PropertyCheck:
    """Informa tr(A) si A es cuadrada."""
    if A.rows != A.cols:
        return PropertyCheck("Traza", "no_aplica", "No aplica: tr(A) exige una matriz cuadrada.")
    return PropertyCheck("Traza", "dato", f"tr(A) = {format_scalar(matrix_trace(A))}.")


def _double_transpose_check(A: Matrix) -> PropertyCheck:
    """Verifica (Aᵀ)ᵀ = A comparando la matriz recuperada con la original."""
    recovered = matrix_transpose(matrix_transpose(A))
    return _mark_bool(
        "(Aᵀ)ᵀ = A",
        recovered == A,
        "La transpuesta de la transpuesta recupera A.",
        "La doble transpuesta no coincide con A.",
    )


def _sum_transpose_check(A: Matrix, B: Optional[Matrix]) -> PropertyCheck:
    """Verifica (A+B)ᵀ = Aᵀ+Bᵀ cuando A y B tienen la misma dimensión."""
    name = "(A + B)ᵀ = Aᵀ + Bᵀ"
    if B is None:
        return PropertyCheck(name, "no_aplica", "No se proporcionó la matriz B.")
    if A.shape != B.shape:
        return PropertyCheck(
            name,
            "no_aplica",
            f"No aplica: A es {A.rows}×{A.cols} y B es {B.rows}×{B.cols}.",
        )
    left = matrix_transpose(matrix_add(A, B))
    right = matrix_add(matrix_transpose(A), matrix_transpose(B))
    return _mark_bool(name, left == right, "La transpuesta reparte la suma.", "La igualdad no se cumple.")


def _scalar_transpose_check(A: Matrix, scalar: Any) -> PropertyCheck:
    """Verifica (k·A)ᵀ = k·Aᵀ para el escalar concreto recibido."""
    name = "(k · A)ᵀ = k · Aᵀ"
    if scalar is None:
        return PropertyCheck(name, "no_aplica", "No se proporcionó el escalar k.")
    k = parse_scalar(scalar)
    left = matrix_transpose(matrix_scale(A, k))
    right = matrix_scale(matrix_transpose(A), k)
    shown = format_scalar(k)
    return _mark_bool(name, left == right, f"Se cumple para k = {shown}.", f"Falla para k = {shown}.")


def _product_transpose_check(A: Matrix, B: Optional[Matrix]) -> PropertyCheck:
    """Verifica (A·B)ᵀ = Bᵀ·Aᵀ si el producto es conformable."""
    name = "(A · B)ᵀ = Bᵀ · Aᵀ"
    if B is None:
        return PropertyCheck(name, "no_aplica", "No se proporcionó la matriz B.")
    # El orden se invierte: transponer un producto no es conmutar los factores.
    if A.cols != B.rows:
        return PropertyCheck(
            name,
            "no_aplica",
            f"No aplica: columnas de A ({A.cols}) ≠ filas de B ({B.rows}).",
        )
    left = matrix_transpose(matrix_multiply(A, B))
    right = matrix_multiply(matrix_transpose(B), matrix_transpose(A))
    return _mark_bool(
        name,
        left == right,
        "El producto invierte el orden al transponer.",
        "La igualdad no se cumple.",
    )
