"""Operaciones algebraicas fundamentales entre vectores de ℝⁿ.

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
Prohibido NumPy, SciPy y álgebra lineal de `math`.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from prettycalc.core.types import (
    DimensionMismatchError,
    Vector,
    parse_scalar,
)


def _require_same_dimension(u: Vector, v: Vector, operation: str) -> None:
    """Valida que u y v vivan en el mismo ℝⁿ."""
    if u.dimension != v.dimension:
        raise DimensionMismatchError(
            f"No se puede {operation}: dim(u) = {u.dimension} ≠ dim(v) = {v.dimension}. "
            "La suma, resta y el producto punto exigen vectores de la misma dimensión n.",
            left_shape=(u.dimension,),
            right_shape=(v.dimension,),
            operation=operation,
        )


def vector_add(u: Vector, v: Vector) -> Vector:
    """Suma elemento a elemento: (u + v)_i = u_i + v_i.

    Raises:
        DimensionMismatchError: Si dim(u) ≠ dim(v).
    """
    _require_same_dimension(u, v, "sumar vectores")
    return Vector([u[i] + v[i] for i in range(u.dimension)])


def vector_sub(u: Vector, v: Vector) -> Vector:
    """Resta elemento a elemento: (u − v)_i = u_i − v_i.

    Raises:
        DimensionMismatchError: Si dim(u) ≠ dim(v).
    """
    _require_same_dimension(u, v, "restar vectores")
    return Vector([u[i] - v[i] for i in range(u.dimension)])


def vector_scale(v: Vector, scalar: Any) -> Vector:
    """Multiplicación por escalar exacto: (k · v)_i = k · v_i."""
    k = parse_scalar(scalar)
    return Vector([k * v[i] for i in range(v.dimension)])


def vector_dot(u: Vector, v: Vector) -> Fraction:
    """Producto punto euclídeo: u · v = Σ u_i · v_i.

    Raises:
        DimensionMismatchError: Si dim(u) ≠ dim(v).
    """
    _require_same_dimension(u, v, "calcular el producto punto")
    accum = Fraction(0, 1)
    for i in range(u.dimension):
        accum += u[i] * v[i]
    return accum
