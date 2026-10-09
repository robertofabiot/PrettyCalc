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
    matrix_multiply_with_details,
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
    C: Optional[Matrix] = None,
) -> List[PropertyCheck]:
    """Reúne las propiedades estructurales de A y las identidades algebraicas y de la transpuesta."""
    checks = structural_checks(A) + transpose_identity_checks(A, B, scalar)
    if B is not None and C is not None:
        checks.extend(matrix_algebraic_identity_checks(A, B, C))
    return checks


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


@dataclass(frozen=True)
class MatrixDistributiveResult:
    """Resultado formal de la comprobación de la propiedad distributiva de matrices:

    Izquierda: A · (B + C) = A·B + A·C
    Derecha:   (A + B) · C = A·C + B·C
    """

    A: Matrix
    B: Matrix
    C: Matrix
    is_left: bool
    intermediate_sum: Matrix
    lhs_result: Matrix
    first_product: Matrix
    second_product: Matrix
    rhs_result: Matrix
    is_equal: bool
    verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]
    lhs_steps: List[str]
    rhs_steps: List[str]


@dataclass(frozen=True)
class MatrixAssociativeResult:
    """Resultado formal de la comprobación de la propiedad asociativa de matrices:

        A · (B · C) = (A · B) · C
    """

    A: Matrix
    B: Matrix
    C: Matrix
    intermediate_bc: Matrix
    lhs_result: Matrix
    intermediate_ab: Matrix
    rhs_result: Matrix
    is_equal: bool
    verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]
    lhs_steps: List[str]
    rhs_steps: List[str]


def verify_matrix_distributive_left(
    A: Matrix,
    B: Matrix,
    C: Matrix,
) -> MatrixDistributiveResult:
    """Verifica y desglosa paso a paso la propiedad distributiva por la izquierda:

        A · (B + C) = A·B + A·C

    Condiciones de conformabilidad:
        1. B.shape == C.shape (B y C deben ser del mismo tamaño n × p).
        2. A.cols == B.rows (el número de columnas de A debe coincidir con las filas de B).

    Raises:
        DimensionMismatchError: Si las dimensiones no son compatibles.
    """
    if B.shape != C.shape:
        raise DimensionMismatchError(
            f"Las matrices B y C tienen dimensiones incompatibles para la suma (B + C): "
            f"B es {B.rows}×{B.cols} y C es {C.rows}×{C.cols}. "
            "La suma matricial exige que ambas matrices tengan exactamente la misma dimensión n×p.",
            left_shape=B.shape,
            right_shape=C.shape,
            operation="suma matricial B + C (propiedad distributiva)",
        )

    if A.cols != B.rows:
        raise DimensionMismatchError(
            f"Dimensiones incompatibles para el producto A · (B + C): "
            f"A es {A.rows}×{A.cols} pero B y C son de tamaño {B.rows}×{B.cols}. "
            f"El producto exige que el número de columnas de A ({A.cols}) coincida con "
            f"el número de filas de B y C ({B.rows}).",
            left_shape=A.shape,
            right_shape=B.shape,
            operation="propiedad distributiva A(B + C) = AB + AC",
        )

    # 1. LHS: A · (B + C)
    B_plus_C = matrix_add(B, C)
    lhs_result, lhs_details = matrix_multiply_with_details(A, B_plus_C)

    lhs_steps = [
        f"1. Suma intermedia (B + C) de tamaño {B.rows}×{B.cols}:",
        *[
            f"   (B + C)_{i + 1},{j + 1} = {format_scalar(B.get(i, j))} + {format_scalar(C.get(i, j))} = {format_scalar(B_plus_C.get(i, j))}"
            for i in range(B.rows)
            for j in range(B.cols)
        ],
        f"2. Producto matriz-matriz A · (B + C) de tamaño {A.rows}×{B.cols}:",
        *[f"   {d.formula}" for d in lhs_details],
    ]

    # 2. RHS: A·B + A·C
    AB, ab_details = matrix_multiply_with_details(A, B)
    AC, ac_details = matrix_multiply_with_details(A, C)
    rhs_result = matrix_add(AB, AC)

    rhs_steps = [
        f"1. Producto A · B de tamaño {A.rows}×{B.cols}:",
        *[f"   {d.formula}" for d in ab_details],
        f"2. Producto A · C de tamaño {A.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in ac_details],
        f"3. Suma final (A·B) + (A·C) de tamaño {A.rows}×{B.cols}:",
        *[
            f"   (AB + AC)_{i + 1},{j + 1} = {format_scalar(AB.get(i, j))} + {format_scalar(AC.get(i, j))} = {format_scalar(rhs_result.get(i, j))}"
            for i in range(A.rows)
            for j in range(B.cols)
        ],
    ]

    # 3. Comprobación celda a celda
    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    all_equal = True
    for i in range(A.rows):
        for j in range(B.cols):
            v_lhs = lhs_result.get(i, j)
            v_rhs = rhs_result.get(i, j)
            eq = v_lhs == v_rhs
            all_equal = all_equal and eq
            checklist.append((f"Celda ({i + 1},{j + 1})", v_lhs, v_rhs, eq))

    return MatrixDistributiveResult(
        A=A,
        B=B,
        C=C,
        is_left=True,
        intermediate_sum=B_plus_C,
        lhs_result=lhs_result,
        first_product=AB,
        second_product=AC,
        rhs_result=rhs_result,
        is_equal=all_equal,
        verification_checklist=checklist,
        lhs_steps=lhs_steps,
        rhs_steps=rhs_steps,
    )


def verify_matrix_distributive_right(
    A: Matrix,
    B: Matrix,
    C: Matrix,
) -> MatrixDistributiveResult:
    """Verifica y desglosa paso a paso la propiedad distributiva por la derecha:

        (A + B) · C = A·C + B·C

    Condiciones de conformabilidad:
        1. A.shape == B.shape (A y B deben ser del mismo tamaño m × n).
        2. A.cols == C.rows (el número de columnas de A y B debe coincidir con las filas de C).

    Raises:
        DimensionMismatchError: Si las dimensiones no son compatibles.
    """
    if A.shape != B.shape:
        raise DimensionMismatchError(
            f"Las matrices A y B tienen dimensiones incompatibles para la suma (A + B): "
            f"A es {A.rows}×{A.cols} y B es {B.rows}×{B.cols}. "
            "La suma matricial exige que ambas matrices tengan exactamente la misma dimensión m×n.",
            left_shape=A.shape,
            right_shape=B.shape,
            operation="suma matricial A + B (propiedad distributiva)",
        )

    if A.cols != C.rows:
        raise DimensionMismatchError(
            f"Dimensiones incompatibles para el producto (A + B) · C: "
            f"A y B son de tamaño {A.rows}×{A.cols} pero C es {C.rows}×{C.cols}. "
            f"El producto exige que las columnas de A y B ({A.cols}) coincidan con "
            f"las filas de C ({C.rows}).",
            left_shape=A.shape,
            right_shape=C.shape,
            operation="propiedad distributiva (A + B)C = AC + BC",
        )

    # 1. LHS: (A + B) · C
    A_plus_B = matrix_add(A, B)
    lhs_result, lhs_details = matrix_multiply_with_details(A_plus_B, C)

    lhs_steps = [
        f"1. Suma intermedia (A + B) de tamaño {A.rows}×{A.cols}:",
        *[
            f"   (A + B)_{i + 1},{j + 1} = {format_scalar(A.get(i, j))} + {format_scalar(B.get(i, j))} = {format_scalar(A_plus_B.get(i, j))}"
            for i in range(A.rows)
            for j in range(A.cols)
        ],
        f"2. Producto matriz-matriz (A + B) · C de tamaño {A.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in lhs_details],
    ]

    # 2. RHS: A·C + B·C
    AC, ac_details = matrix_multiply_with_details(A, C)
    BC, bc_details = matrix_multiply_with_details(B, C)
    rhs_result = matrix_add(AC, BC)

    rhs_steps = [
        f"1. Producto A · C de tamaño {A.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in ac_details],
        f"2. Producto B · C de tamaño {B.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in bc_details],
        f"3. Suma final (A·C) + (B·C) de tamaño {A.rows}×{C.cols}:",
        *[
            f"   (AC + BC)_{i + 1},{j + 1} = {format_scalar(AC.get(i, j))} + {format_scalar(BC.get(i, j))} = {format_scalar(rhs_result.get(i, j))}"
            for i in range(A.rows)
            for j in range(C.cols)
        ],
    ]

    # 3. Comprobación celda a celda
    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    all_equal = True
    for i in range(A.rows):
        for j in range(C.cols):
            v_lhs = lhs_result.get(i, j)
            v_rhs = rhs_result.get(i, j)
            eq = v_lhs == v_rhs
            all_equal = all_equal and eq
            checklist.append((f"Celda ({i + 1},{j + 1})", v_lhs, v_rhs, eq))

    return MatrixDistributiveResult(
        A=A,
        B=B,
        C=C,
        is_left=False,
        intermediate_sum=A_plus_B,
        lhs_result=lhs_result,
        first_product=AC,
        second_product=BC,
        rhs_result=rhs_result,
        is_equal=all_equal,
        verification_checklist=checklist,
        lhs_steps=lhs_steps,
        rhs_steps=rhs_steps,
    )


def verify_matrix_associative(
    A: Matrix,
    B: Matrix,
    C: Matrix,
) -> MatrixAssociativeResult:
    """Verifica y desglosa paso a paso la propiedad asociativa:

        A · (B · C) = (A · B) · C

    Condiciones de conformabilidad:
        1. A.cols == B.rows
        2. B.cols == C.rows

    Raises:
        DimensionMismatchError: Si las dimensiones no son compatibles para el producto sucesivo.
    """
    if A.cols != B.rows:
        raise DimensionMismatchError(
            f"Dimensiones incompatibles para A · B: columnas de A ({A.cols}) ≠ filas de B ({B.rows}).",
            left_shape=A.shape,
            right_shape=B.shape,
            operation="producto A · B (propiedad asociativa)",
        )

    if B.cols != C.rows:
        raise DimensionMismatchError(
            f"Dimensiones incompatibles para B · C: columnas de B ({B.cols}) ≠ filas de C ({C.rows}).",
            left_shape=B.shape,
            right_shape=C.shape,
            operation="producto B · C (propiedad asociativa)",
        )

    # 1. LHS: A · (B · C)
    BC, bc_details = matrix_multiply_with_details(B, C)
    lhs_result, lhs_details = matrix_multiply_with_details(A, BC)

    lhs_steps = [
        f"1. Producto intermedio (B · C) de tamaño {B.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in bc_details],
        f"2. Producto final A · (B · C) de tamaño {A.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in lhs_details],
    ]

    # 2. RHS: (A · B) · C
    AB, ab_details = matrix_multiply_with_details(A, B)
    rhs_result, rhs_details = matrix_multiply_with_details(AB, C)

    rhs_steps = [
        f"1. Producto intermedio (A · B) de tamaño {A.rows}×{B.cols}:",
        *[f"   {d.formula}" for d in ab_details],
        f"2. Producto final (A · B) · C de tamaño {A.rows}×{C.cols}:",
        *[f"   {d.formula}" for d in rhs_details],
    ]

    # 3. Comprobación celda a celda
    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    all_equal = True
    for i in range(A.rows):
        for j in range(C.cols):
            v_lhs = lhs_result.get(i, j)
            v_rhs = rhs_result.get(i, j)
            eq = v_lhs == v_rhs
            all_equal = all_equal and eq
            checklist.append((f"Celda ({i + 1},{j + 1})", v_lhs, v_rhs, eq))

    return MatrixAssociativeResult(
        A=A,
        B=B,
        C=C,
        intermediate_bc=BC,
        lhs_result=lhs_result,
        intermediate_ab=AB,
        rhs_result=rhs_result,
        is_equal=all_equal,
        verification_checklist=checklist,
        lhs_steps=lhs_steps,
        rhs_steps=rhs_steps,
    )


def _distributive_left_check(A: Matrix, B: Optional[Matrix], C: Optional[Matrix]) -> PropertyCheck:
    """Verifica A · (B + C) = A·B + A·C si B y C son conformables."""
    name = "A · (B + C) = A·B + A·C"
    if B is None or C is None:
        return PropertyCheck(name, "no_aplica", "No se proporcionaron las matrices B y C.")
    if B.shape != C.shape or A.cols != B.rows:
        return PropertyCheck(
            name,
            "no_aplica",
            f"No aplica: A es {A.rows}×{A.cols}, B es {B.rows}×{B.cols} y C es {C.rows}×{C.cols}.",
        )
    res = verify_matrix_distributive_left(A, B, C)
    return _mark_bool(
        name,
        res.is_equal,
        "La multiplicación matricial distribuye por la izquierda respecto a la suma.",
        "La igualdad no se cumple.",
    )


def _distributive_right_check(A: Matrix, B: Optional[Matrix], C: Optional[Matrix]) -> PropertyCheck:
    """Verifica (A + B) · C = A·C + B·C si A, B y C son conformables."""
    name = "(A + B) · C = A·C + B·C"
    if B is None or C is None:
        return PropertyCheck(name, "no_aplica", "No se proporcionaron las matrices B y C.")
    if A.shape != B.shape or A.cols != C.rows:
        return PropertyCheck(
            name,
            "no_aplica",
            f"No aplica: A es {A.rows}×{A.cols}, B es {B.rows}×{B.cols} y C es {C.rows}×{C.cols}.",
        )
    res = verify_matrix_distributive_right(A, B, C)
    return _mark_bool(
        name,
        res.is_equal,
        "La multiplicación matricial distribuye por la derecha respecto a la suma.",
        "La igualdad no se cumple.",
    )


def _associative_check(A: Matrix, B: Optional[Matrix], C: Optional[Matrix]) -> PropertyCheck:
    """Verifica A · (B · C) = (A · B) · C si el producto sucesivo es conformable."""
    name = "A · (B · C) = (A · B) · C"
    if B is None or C is None:
        return PropertyCheck(name, "no_aplica", "No se proporcionaron las matrices B y C.")
    if A.cols != B.rows or B.cols != C.rows:
        return PropertyCheck(
            name,
            "no_aplica",
            f"No aplica: A es {A.rows}×{A.cols}, B es {B.rows}×{B.cols} y C es {C.rows}×{C.cols}.",
        )
    res = verify_matrix_associative(A, B, C)
    return _mark_bool(
        name,
        res.is_equal,
        "El producto de matrices cumple la propiedad asociativa.",
        "La igualdad no se cumple.",
    )


def matrix_algebraic_identity_checks(
    A: Matrix,
    B: Optional[Matrix] = None,
    C: Optional[Matrix] = None,
) -> List[PropertyCheck]:
    """Comprueba las identidades algebraicas clásicas entre A, B y C."""
    checks: List[PropertyCheck] = []
    if B is None or C is None:
        return checks
    checks.append(_distributive_left_check(A, B, C))
    checks.append(_distributive_right_check(A, B, C))
    checks.append(_associative_check(A, B, C))
    return checks
