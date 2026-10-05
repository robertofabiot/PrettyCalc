"""Operaciones y propiedades del producto matriz-vector A · x.

Implementa la fundamentación algebraica de las propiedades del producto
matriz-vector según el teorema canónico de álgebra lineal:
    1. Propiedad Distributiva: A(u + v) = A·u + A·v
    2. Propiedad de Homogeneidad / Multiplicación por Escalar: A(c·u) = c·(A·u)

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
Prohibido NumPy, SciPy y álgebra lineal de `math`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, List, Sequence, Tuple

from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    Vector,
    format_scalar,
    parse_scalar,
)
from prettycalc.core.vector_ops import vector_add, vector_scale


def _require_vector_conformability(
    A: Matrix,
    x: Vector,
    vector_name: str = "x",
    operation: str = "producto matriz-vector A · x",
) -> None:
    """Valida que el número de columnas de A coincida con la dimensión del vector x."""
    if A.cols != x.dimension:
        raise DimensionMismatchError(
            f"No se puede calcular {operation}: la matriz A es de tamaño {A.rows}×{A.cols} "
            f"pero el vector {vector_name} vive en ℝ^{x.dimension}. "
            f"El producto exige que el número de columnas de A ({A.cols}) coincida con la "
            f"dimensión de {vector_name} (dim({vector_name}) = {A.cols}).",
            left_shape=A.shape,
            right_shape=(x.dimension,),
            operation=operation,
        )


def matrix_vector_multiply(A: Matrix, x: Vector) -> Vector:
    """Calcula el producto matriz-vector y = A · x en aritmética exacta.

    Para A ∈ M_{m×n} y x ∈ ℝⁿ, el resultado es un vector y ∈ ℝᵐ donde:
        y_i = (A · x)_i = Σ_{j=1}^n A_{i,j} · x_j

    Raises:
        DimensionMismatchError: Si A.cols ≠ dim(x).
    """
    _require_vector_conformability(A, x, vector_name="x", operation="producto matriz-vector A · x")
    m = A.rows
    n = A.cols
    result_components: List[Fraction] = []

    for i in range(m):
        accum = Fraction(0, 1)
        for j in range(n):
            accum += A.get(i, j) * x[j]
        result_components.append(accum)

    return Vector(result_components)


def matrix_vector_multiply_with_details(
    A: Matrix,
    x: Vector,
    vector_name: str = "x",
) -> Tuple[Vector, List[str]]:
    """Calcula A · x y retorna el vector resultante junto al desglose pedagógico por fila."""
    _require_vector_conformability(A, x, vector_name=vector_name, operation="producto matriz-vector A · x")
    m = A.rows
    n = A.cols
    result_components: List[Fraction] = []
    step_descriptions: List[str] = []

    for i in range(m):
        accum = Fraction(0, 1)
        terms: List[str] = []
        for j in range(n):
            a_val = A.get(i, j)
            x_val = x[j]
            prod = a_val * x_val
            accum += prod
            terms.append(f"({format_scalar(a_val)})·({format_scalar(x_val)})")
        result_components.append(accum)
        terms_joined = " + ".join(terms) if terms else "0"
        step_descriptions.append(
            f"Fila {i + 1}: {terms_joined} = {format_scalar(accum)}"
        )

    return Vector(result_components), step_descriptions


@dataclass(frozen=True)
class DistributivePropertyResult:
    """Resultado formal de la comprobación de la propiedad distributiva:

        A · (u + v) = A · u + A · v

    Attributes:
        A: Matriz de coeficientes m×n.
        u: Vector u en ℝⁿ.
        v: Vector v en ℝⁿ.
        u_plus_v: Vector suma u + v en ℝⁿ.
        lhs_result: Vector resultante del lado izquierdo A · (u + v) en ℝᵐ.
        Au: Vector resultante A · u en ℝᵐ.
        Av: Vector resultante A · v en ℝᵐ.
        rhs_result: Vector resultante del lado derecho (A · u) + (A · v) en ℝᵐ.
        is_equal: True si ambos lados coinciden componente a componente.
        verification_checklist: Lista de tuplas (etiqueta, valor_LHS, valor_RHS, coincide).
        lhs_steps: Detalle paso a paso del lado izquierdo.
        rhs_steps: Detalle paso a paso del lado derecho.
    """

    A: Matrix
    u: Vector
    v: Vector
    u_plus_v: Vector
    lhs_result: Vector
    Au: Vector
    Av: Vector
    rhs_result: Vector
    is_equal: bool
    verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]
    lhs_steps: List[str]
    rhs_steps: List[str]


def verify_distributive_property(
    A: Matrix,
    u: Vector,
    v: Vector,
) -> DistributivePropertyResult:
    """Verifica y desglosa rigurosamente la propiedad distributiva A(u + v) = A·u + A·v.

    Condiciones de conformabilidad:
        1. dim(u) = dim(v) (ambos vectores deben pertenecer al mismo ℝⁿ).
        2. A.cols = dim(u) (el número de columnas de A debe ser n).

    Raises:
        DimensionMismatchError: Si dim(u) ≠ dim(v) o si A.cols ≠ dim(u).
    """
    if u.dimension != v.dimension:
        raise DimensionMismatchError(
            f"Los vectores u y v tienen dimensiones distintas: dim(u) = {u.dimension} "
            f"y dim(v) = {v.dimension}. La suma (u + v) exige que ambos vectores pertenezcan "
            f"al mismo espacio ℝⁿ.",
            left_shape=(u.dimension,),
            right_shape=(v.dimension,),
            operation="suma vectorial u + v (propiedad distributiva)",
        )

    if A.cols != u.dimension:
        raise DimensionMismatchError(
            f"Dimensiones incompatibles para la propiedad distributiva: la matriz A es "
            f"{A.rows}×{A.cols} pero los vectores viven en ℝ^{u.dimension}. "
            f"Se requiere que el número de columnas de A coincida con la dimensión de u y v (n = {A.cols}).",
            left_shape=A.shape,
            right_shape=(u.dimension,),
            operation="propiedad distributiva A(u + v) = Au + Av",
        )

    # 1. Lado Izquierdo (LHS): A · (u + v)
    u_plus_v = vector_add(u, v)
    lhs_result, lhs_prod_details = matrix_vector_multiply_with_details(A, u_plus_v, vector_name="(u + v)")

    lhs_steps = [
        "1. Suma intermedia (u + v) en ℝⁿ:",
        *[f"   (u + v)_{i + 1} = {format_scalar(u[i])} + {format_scalar(v[i])} = {format_scalar(u_plus_v[i])}" for i in range(u.dimension)],
        "2. Producto matriz-vector A · (u + v) en ℝᵐ:",
        *[f"   {step}" for step in lhs_prod_details],
    ]

    # 2. Lado Derecho (RHS): A·u + A·v
    Au, au_details = matrix_vector_multiply_with_details(A, u, vector_name="u")
    Av, av_details = matrix_vector_multiply_with_details(A, v, vector_name="v")
    rhs_result = vector_add(Au, Av)

    rhs_steps = [
        "1. Producto A · u en ℝᵐ:",
        *[f"   {step}" for step in au_details],
        "2. Producto A · v en ℝᵐ:",
        *[f"   {step}" for step in av_details],
        "3. Suma final (A·u) + (A·v) en ℝᵐ:",
        *[f"   Componente {i + 1}: {format_scalar(Au[i])} + {format_scalar(Av[i])} = {format_scalar(rhs_result[i])}" for i in range(A.rows)],
    ]

    # 3. Comprobación componente a componente
    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    all_equal = True
    for i in range(A.rows):
        val_lhs = lhs_result[i]
        val_rhs = rhs_result[i]
        matches = val_lhs == val_rhs
        all_equal = all_equal and matches
        checklist.append((f"Componente {i + 1}", val_lhs, val_rhs, matches))

    return DistributivePropertyResult(
        A=A,
        u=u,
        v=v,
        u_plus_v=u_plus_v,
        lhs_result=lhs_result,
        Au=Au,
        Av=Av,
        rhs_result=rhs_result,
        is_equal=all_equal,
        verification_checklist=checklist,
        lhs_steps=lhs_steps,
        rhs_steps=rhs_steps,
    )


@dataclass(frozen=True)
class HomogeneityPropertyResult:
    """Resultado formal de la comprobación de la propiedad de homogeneidad:

        A · (c · u) = c · (A · u)

    Attributes:
        A: Matriz de coeficientes m×n.
        u: Vector u en ℝⁿ.
        c: Escalar racional c.
        cu: Vector escalado c · u en ℝⁿ.
        lhs_result: Vector resultante del lado izquierdo A · (c · u) en ℝᵐ.
        Au: Vector resultante A · u en ℝᵐ.
        rhs_result: Vector resultante del lado derecho c · (A · u) en ℝᵐ.
        is_equal: True si ambos lados coinciden componente a componente.
        verification_checklist: Lista de tuplas (etiqueta, valor_LHS, valor_RHS, coincide).
        lhs_steps: Detalle paso a paso del lado izquierdo.
        rhs_steps: Detalle paso a paso del lado derecho.
    """

    A: Matrix
    u: Vector
    c: Fraction
    cu: Vector
    lhs_result: Vector
    Au: Vector
    rhs_result: Vector
    is_equal: bool
    verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]
    lhs_steps: List[str]
    rhs_steps: List[str]


def verify_homogeneity_property(
    A: Matrix,
    u: Vector,
    scalar: Any,
) -> HomogeneityPropertyResult:
    """Verifica y desglosa rigurosamente la propiedad de homogeneidad A(c·u) = c·(A·u).

    Condiciones de conformabilidad:
        1. A.cols = dim(u) (el número de columnas de A debe coincidir con la dimensión de u).
        2. scalar debe ser convertible a Fraction exacta mediante `parse_scalar`.

    Raises:
        DimensionMismatchError: Si A.cols ≠ dim(u).
        ValueError / TypeError: Si el escalar no es válido.
    """
    _require_vector_conformability(
        A,
        u,
        vector_name="u",
        operation="propiedad de homogeneidad A(c·u) = c(Au)",
    )

    c = parse_scalar(scalar)

    # 1. Lado Izquierdo (LHS): A · (c · u)
    cu = vector_scale(u, c)
    lhs_result, lhs_details = matrix_vector_multiply_with_details(A, cu, vector_name="(c·u)")

    lhs_steps = [
        f"1. Escalado intermedio (c · u) en ℝⁿ con c = {format_scalar(c)}:",
        *[f"   (c · u)_{i + 1} = ({format_scalar(c)}) · ({format_scalar(u[i])}) = {format_scalar(cu[i])}" for i in range(u.dimension)],
        "2. Producto matriz-vector A · (c · u) en ℝᵐ:",
        *[f"   {step}" for step in lhs_details],
    ]

    # 2. Lado Derecho (RHS): c · (A · u)
    Au, au_details = matrix_vector_multiply_with_details(A, u, vector_name="u")
    rhs_result = vector_scale(Au, c)

    rhs_steps = [
        "1. Producto intermedio A · u en ℝᵐ:",
        *[f"   {step}" for step in au_details],
        f"2. Escalado final c · (A · u) en ℝᵐ con c = {format_scalar(c)}:",
        *[f"   Componente {i + 1}: ({format_scalar(c)}) · ({format_scalar(Au[i])}) = {format_scalar(rhs_result[i])}" for i in range(A.rows)],
    ]

    # 3. Comprobación componente a componente
    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    all_equal = True
    for i in range(A.rows):
        val_lhs = lhs_result[i]
        val_rhs = rhs_result[i]
        matches = val_lhs == val_rhs
        all_equal = all_equal and matches
        checklist.append((f"Componente {i + 1}", val_lhs, val_rhs, matches))

    return HomogeneityPropertyResult(
        A=A,
        u=u,
        c=c,
        cu=cu,
        lhs_result=lhs_result,
        Au=Au,
        rhs_result=rhs_result,
        is_equal=all_equal,
        verification_checklist=checklist,
        lhs_steps=lhs_steps,
        rhs_steps=rhs_steps,
    )
