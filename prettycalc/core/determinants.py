"""Determinantes exactos: fórmula 2×2, Sarrus, triangulación y cofactores de Laplace.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Aritmética exacta con fractions.Fraction. Sin NumPy, SciPy ni SymPy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import List, Optional, Tuple

from prettycalc.core.matrix_inversion import NonSquareMatrixError, SingularMatrixError
from prettycalc.core.matrix_ops import matrix_multiply, matrix_scale, matrix_transpose
from prettycalc.core.operations import (
    add_row_multiple,
    get_add_multiple_metadata,
    get_swap_metadata,
    swap_rows,
)
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import Matrix, format_scalar, parse_scalar


class DeterminantMethod(Enum):
    """Método pedagógico con el que se evalúa det(A)."""

    DIRECT_2X2 = "Fórmula directa 2×2"
    SARRUS_3X3 = "Regla de Sarrus (3×3)"
    TRIANGULATION = "Triangulación Gaussiana (n×n)"
    LAPLACE_ROW = "Desarrollo por Cofactores (Fila)"
    LAPLACE_COL = "Desarrollo por Cofactores (Columna)"


@dataclass(frozen=True)
class DeterminantResult:
    """Valor exacto de det(A) y el desglose del método elegido."""

    value: Fraction
    matrix: Matrix
    method: DeterminantMethod
    step_descriptions: List[str]
    tracer: StepTracer
    triangular_matrix: Optional[Matrix] = None
    row_swaps_count: int = 0
    is_singular: bool = False


def require_square_matrix(A: Matrix, operation: str) -> int:
    """Exige una matriz n×n y devuelve n.

    Raises:
        NonSquareMatrixError: Si A.rows != A.cols.
    """
    if A.rows != A.cols:
        raise NonSquareMatrixError(
            f"No se puede {operation}: la matriz es {A.rows}×{A.cols}. "
            "Esta operación solo está definida para matrices cuadradas (n×n)."
        )
    return A.rows


def singularity_diagnosis(value: Fraction, order: int) -> str:
    """Texto de rango e invertibilidad a partir de det(A)."""
    shown = format_scalar(value, mode="fraction")
    if value != Fraction(0, 1):
        return (
            f"det(A) = {shown} ≠ 0. A es no singular: rango(A) = {order}, "
            "las filas y columnas son linealmente independientes y existe A⁻¹."
        )
    return (
        f"det(A) = 0. A es singular: rango(A) < {order}, "
        "las filas y columnas son linealmente dependientes y no existe A⁻¹."
    )


def _pack(
    *,
    value: Fraction,
    original: Matrix,
    method: DeterminantMethod,
    steps: List[str],
    tracer: StepTracer,
    triangular: Optional[Matrix] = None,
    swaps: int = 0,
) -> DeterminantResult:
    return DeterminantResult(
        value=value,
        matrix=original.copy(),
        method=method,
        step_descriptions=list(steps),
        tracer=tracer,
        triangular_matrix=None if triangular is None else triangular.copy(),
        row_swaps_count=swaps,
        is_singular=value == Fraction(0, 1),
    )


def _record(
    tracer: StepTracer,
    matrix: Matrix,
    latex_formula: str,
    heuristic_text: str,
    steps: List[str],
    pivot_pos: Optional[tuple[int, int]] = None,
    actor_row: Optional[int] = None,
    affected_rows: Optional[tuple[int, ...]] = None,
    highlight_cells: Optional[tuple[tuple[int, int], ...]] = None,
    alert_rows: Optional[tuple[int, ...]] = None,
) -> None:
    steps.append(heuristic_text)
    tracer.record_step(
        matrix=matrix,
        latex_formula=latex_formula,
        heuristic_text=heuristic_text,
        pivot_pos=pivot_pos,
        actor_row=actor_row,
        affected_rows=affected_rows,
        highlight_cells=highlight_cells,
        alert_rows=alert_rows,
    )


def delete_row_and_column(A: Matrix, drop_row: int, drop_col: int) -> Matrix:
    """Submatriz que se obtiene al borrar la fila drop_row y la columna drop_col.

    Raises:
        ValueError: Si A es 1×1, porque el menor sería la matriz vacía.
        IndexError: Si la fila o la columna no existen.
    """
    if A.rows <= 1 or A.cols <= 1:
        raise ValueError(
            "El menor de una matriz 1×1 es el determinante de la matriz vacía, "
            "que por convención vale 1 y no se representa como matriz."
        )
    if drop_row < 0 or drop_row >= A.rows or drop_col < 0 or drop_col >= A.cols:
        raise IndexError(
            f"No existe la entrada ({drop_row + 1}, {drop_col + 1}) en una matriz "
            f"{A.rows}×{A.cols}."
        )
    data: List[List[Fraction]] = []
    for row_index in range(A.rows):
        if row_index == drop_row:
            continue
        data.append(
            [
                A.get(row_index, col_index)
                for col_index in range(A.cols)
                if col_index != drop_col
            ]
        )
    return Matrix(data)


def minor_determinant(A: Matrix, row_index: int, col_index: int) -> Fraction:
    """M_ij = det(A_ij). En 1×1 el menor vacío vale 1 por convención."""
    order = require_square_matrix(A, "calcular un menor")
    if row_index < 0 or row_index >= order or col_index < 0 or col_index >= order:
        raise IndexError(
            f"No existe el menor M_{row_index + 1}{col_index + 1} en una matriz {order}×{order}."
        )
    if order == 1:
        return Fraction(1, 1)
    return determinant_triangulation(delete_row_and_column(A, row_index, col_index)).value


def determinant_2x2(A: Matrix) -> DeterminantResult:
    """det(A) = ad − bc para una matriz 2×2.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
        ValueError: Si A no es exactamente 2×2.
    """
    order = require_square_matrix(A, "usar la fórmula directa 2×2")
    if order != 2:
        raise ValueError(
            "La fórmula directa det(A) = ad − bc solo aplica a matrices 2×2. "
            f"A es {order}×{order}."
        )
    a_entry = A.get(0, 0)
    b_entry = A.get(0, 1)
    c_entry = A.get(1, 0)
    d_entry = A.get(1, 1)
    product_ad = a_entry * d_entry
    product_bc = b_entry * c_entry
    value = product_ad - product_bc
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description="Matriz 2×2. El determinante es el producto de la diagonal principal menos el de la secundaria.",
        latex_title=r"\det(A) = ad - bc",
    )
    steps: List[str] = []
    text = (
        f"det(A) = ({format_scalar(a_entry)})·({format_scalar(d_entry)}) "
        f"− ({format_scalar(b_entry)})·({format_scalar(c_entry)}) "
        f"= {format_scalar(product_ad)} − {format_scalar(product_bc)} "
        f"= {format_scalar(value)}."
    )
    _record(tracer, A, r"\det(A) = ad - bc", text, steps)
    _record(tracer, A, r"\det(A)", singularity_diagnosis(value, order), steps)
    return _pack(
        value=value,
        original=A,
        method=DeterminantMethod.DIRECT_2X2,
        steps=steps,
        tracer=tracer,
    )


def determinant_sarrus_3x3(A: Matrix) -> DeterminantResult:
    """Regla de Sarrus: suma de las diagonales principales menos las secundarias.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
        ValueError: Si A no es exactamente 3×3.
    """
    order = require_square_matrix(A, "usar la regla de Sarrus")
    if order != 3:
        raise ValueError(
            "La regla de Sarrus solo está definida para matrices 3×3. "
            f"A es {order}×{order}."
        )
    entries = [[A.get(row_index, col_index) for col_index in range(3)] for row_index in range(3)]
    principal = (
        entries[0][0] * entries[1][1] * entries[2][2],
        entries[0][1] * entries[1][2] * entries[2][0],
        entries[0][2] * entries[1][0] * entries[2][1],
    )
    secondary = (
        entries[0][2] * entries[1][1] * entries[2][0],
        entries[0][0] * entries[1][2] * entries[2][1],
        entries[0][1] * entries[1][0] * entries[2][2],
    )
    principal_sum = principal[0] + principal[1] + principal[2]
    secondary_sum = secondary[0] + secondary[1] + secondary[2]
    value = principal_sum - secondary_sum
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description="Matriz 3×3. Sarrus suma las tres diagonales principales y resta las tres secundarias.",
        latex_title=r"\det(A)\text{ por Sarrus}",
    )
    steps: List[str] = []
    principal_text = " + ".join(format_scalar(term) for term in principal)
    secondary_text = " + ".join(format_scalar(term) for term in secondary)
    _record(
        tracer,
        A,
        r"\det(A) = (d_1 + d_2 + d_3) - (s_1 + s_2 + s_3)",
        (
            f"Diagonales principales: {principal_text} = {format_scalar(principal_sum)}. "
            f"Diagonales secundarias: {secondary_text} = {format_scalar(secondary_sum)}. "
            f"det(A) = {format_scalar(principal_sum)} − {format_scalar(secondary_sum)} "
            f"= {format_scalar(value)}."
        ),
        steps,
    )
    _record(tracer, A, r"\det(A)", singularity_diagnosis(value, order), steps)
    return _pack(
        value=value,
        original=A,
        method=DeterminantMethod.SARRUS_3X3,
        steps=steps,
        tracer=tracer,
    )


def determinant_triangulation(A: Matrix) -> DeterminantResult:
    """det(A) = (−1)^k ∏ u_ii tras triangular por filas, sin escalar pivotes.

    Un intercambio de filas aporta un factor −1. Sumar un múltiplo de una fila
    a otra no cambia el determinante. Si una columna no tiene pivote, det(A) = 0.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    order = require_square_matrix(A, "triangularizar el determinante")
    working = A.copy()
    tracer = StepTracer()
    tracer.record_initial(
        working,
        description=(
            "Matriz cuadrada inicial. Se triangulariza solo con intercambios y "
            "combinaciones de filas: no se escalan los pivotes, para que el "
            "determinante quede en el signo por el producto de la diagonal."
        ),
        latex_title=r"\det(A)\text{ por triangulación}",
    )
    steps: List[str] = []
    sign = Fraction(1, 1)
    swaps = 0

    for col_index in range(order):
        pivot_row = None
        for row_index in range(col_index, order):
            if working.get(row_index, col_index) != Fraction(0, 1):
                pivot_row = row_index
                break
        if pivot_row is None:
            text = (
                f"La columna {col_index + 1} no tiene pivote desde la diagonal hacia abajo. "
                "La forma triangular tiene un cero en la diagonal, así que det(A) = 0."
            )
            _record(
                tracer,
                working,
                r"\det(A) = 0",
                text,
                steps,
                pivot_pos=(col_index, col_index),
                highlight_cells=tuple((i, i) for i in range(order)),
            )
            return _pack(
                value=Fraction(0, 1),
                original=A,
                method=DeterminantMethod.TRIANGULATION,
                steps=steps,
                tracer=tracer,
                triangular=working,
                swaps=swaps,
            )
        if pivot_row != col_index:
            working = swap_rows(working, col_index, pivot_row)
            sign *= Fraction(-1, 1)
            swaps += 1
            latex, heuristic = get_swap_metadata(col_index, pivot_row)
            _record(
                tracer,
                working,
                latex,
                heuristic + " Intercambiar dos filas multiplica el determinante por −1.",
                steps,
                pivot_pos=(col_index, col_index),
                actor_row=col_index,
                affected_rows=(col_index, pivot_row),
            )
        pivot_value = working.get(col_index, col_index)
        for row_index in range(col_index + 1, order):
            below = working.get(row_index, col_index)
            if below == Fraction(0, 1):
                continue
            factor = -(below / pivot_value)
            working = add_row_multiple(working, row_index, col_index, factor)
            latex, heuristic = get_add_multiple_metadata(row_index, col_index, factor)
            _record(
                tracer,
                working,
                latex,
                heuristic + " Sumar un múltiplo de una fila a otra no cambia el determinante.",
                steps,
                pivot_pos=(col_index, col_index),
                actor_row=col_index,
                affected_rows=(row_index,),
            )

    diagonal = Fraction(1, 1)
    diagonal_terms: List[str] = []
    for index in range(order):
        entry = working.get(index, index)
        diagonal *= entry
        diagonal_terms.append(format_scalar(entry))
    value = sign * diagonal
    sign_text = format_scalar(sign, mode="fraction")
    product_text = " · ".join(diagonal_terms) if diagonal_terms else "1"
    text = (
        f"Matriz triangular superior. det(A) = ({sign_text}) · ({product_text}) "
        f"= {format_scalar(value)}. Intercambios de fila: {swaps}."
    )
    factors = "".join(
        f"({format_scalar(working.get(index, index))})" for index in range(order)
    )
    _record(
        tracer,
        working,
        (
            rf"\det(A) = (-1)^{{{swaps}}} \prod u_{{ii}} = "
            rf"({format_scalar(sign)}) \cdot {factors} = {format_scalar(value)}"
        ),
        text,
        steps,
        highlight_cells=tuple((index, index) for index in range(order)),
    )
    return _pack(
        value=value,
        original=A,
        method=DeterminantMethod.TRIANGULATION,
        steps=steps,
        tracer=tracer,
        triangular=working,
        swaps=swaps,
    )


def determinant_laplace_expansion(
    A: Matrix,
    *,
    along: str = "row",
    index: int = 0,
) -> DeterminantResult:
    """Desarrollo de Laplace por una fila o una columna (índice 0-based).

    det(A) = Σ a_ij C_ij, con C_ij = (−1)^(i+j) det(A_ij).
    Cada menor se evalúa por triangulación.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
        ValueError: Si `along` no es "row" ni "col".
        IndexError: Si `index` no pertenece a la fila o columna pedida.
    """
    order = require_square_matrix(A, "desarrollar por cofactores")
    if along not in ("row", "col"):
        raise ValueError(
            f"El desarrollo de Laplace pide una fila o una columna; se recibió '{along}'."
        )
    if index < 0 or index >= order:
        axis_name = "fila" if along == "row" else "columna"
        raise IndexError(
            f"La {axis_name} {index + 1} no existe en una matriz {order}×{order}."
        )
    method = DeterminantMethod.LAPLACE_ROW if along == "row" else DeterminantMethod.LAPLACE_COL
    axis_name = "fila" if along == "row" else "columna"
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            f"Desarrollo por cofactores a lo largo de la {axis_name} {index + 1}. "
            "Cada término es la entrada por su cofactor (−1)^(i+j) M_ij."
        ),
        latex_title=rf"\det(A) = \sum a_{{ij}} C_{{ij}}\ \text{{({axis_name} {index + 1})}}",
    )
    steps: List[str] = []
    total = Fraction(0, 1)
    for offset in range(order):
        if along == "row":
            row_index, col_index = index, offset
        else:
            row_index, col_index = offset, index
        entry = A.get(row_index, col_index)
        sign = Fraction(1, 1) if (row_index + col_index) % 2 == 0 else Fraction(-1, 1)
        if order == 1:
            minor_value = Fraction(1, 1)
            shown = A
            minor_note = "el menor vacío vale 1 por convención"
        else:
            shown = delete_row_and_column(A, row_index, col_index)
            minor_value = determinant_triangulation(shown).value
            minor_note = f"det(menor) = {format_scalar(minor_value)}"
        cofactor = sign * minor_value
        term = entry * cofactor
        total += term
        _record(
            tracer,
            shown,
            rf"a_{{{row_index + 1}{col_index + 1}}} C_{{{row_index + 1}{col_index + 1}}}",
            (
                f"Entrada a_{row_index + 1}{col_index + 1} = {format_scalar(entry)}. "
                f"Signo (−1)^({row_index + 1}+{col_index + 1}) = {format_scalar(sign)}; "
                f"{minor_note}. Cofactor = {format_scalar(cofactor)}. "
                f"Aporte = {format_scalar(term)}."
            ),
            steps,
        )
    _record(
        tracer,
        A,
        r"\det(A)",
        (
            f"Suma de los aportes por la {axis_name} {index + 1}: "
            f"det(A) = {format_scalar(total)}. {singularity_diagnosis(total, order)}"
        ),
        steps,
    )
    return _pack(
        value=total,
        original=A,
        method=method,
        steps=steps,
        tracer=tracer,
    )


def matrix_determinant(
    A: Matrix,
    method: DeterminantMethod = DeterminantMethod.TRIANGULATION,
    expansion_index: int = 0,
) -> DeterminantResult:
    """Calcula det(A) con el método indicado.

    `expansion_index` es el índice 0-based de la fila o columna del desarrollo
    de Laplace. Los otros métodos lo ignoran.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
        ValueError: Si el método no corresponde al orden de A.
        IndexError: Si el índice de Laplace está fuera de rango.
    """
    if method is DeterminantMethod.DIRECT_2X2:
        return determinant_2x2(A)
    if method is DeterminantMethod.SARRUS_3X3:
        return determinant_sarrus_3x3(A)
    if method is DeterminantMethod.TRIANGULATION:
        return determinant_triangulation(A)
    if method is DeterminantMethod.LAPLACE_ROW:
        return determinant_laplace_expansion(A, along="row", index=expansion_index)
    if method is DeterminantMethod.LAPLACE_COL:
        return determinant_laplace_expansion(A, along="col", index=expansion_index)
    raise ValueError(f"Método de determinante no reconocido: {method!r}.")


@dataclass(frozen=True)
class DeterminantPropertiesResult:
    """Contraste de det(AB), det(Aᵀ), det(A⁻¹) y det(kA)."""

    A: Matrix
    B: Optional[Matrix]
    k: Optional[Fraction]
    det_A: Fraction
    det_B: Optional[Fraction]
    det_AB: Optional[Fraction]
    det_transpose: Fraction
    det_scaled: Optional[Fraction]
    is_multiplicative_valid: Optional[bool]
    is_transpose_valid: bool
    is_scaling_valid: Optional[bool]
    tracer: StepTracer
    det_inverse: Optional[Fraction] = None
    inverse_reciprocal: Optional[Fraction] = None
    is_inverse_valid: Optional[bool] = None


def _same_square_order(A: Matrix, B: Matrix, operation: str) -> int:
    order = require_square_matrix(A, operation)
    require_square_matrix(B, operation)
    if A.shape != B.shape:
        from prettycalc.core.types import DimensionMismatchError

        raise DimensionMismatchError(
            f"No se puede {operation}: A es {A.rows}×{A.cols} y B es {B.rows}×{B.cols}. "
            "Las dos matrices deben ser cuadradas del mismo orden.",
            left_shape=A.shape,
            right_shape=B.shape,
            operation=operation,
        )
    return order


def verify_determinant_multiplicative(
    A: Matrix,
    B: Matrix,
) -> Tuple[Fraction, Fraction, Fraction, bool, StepTracer]:
    """Verifica det(AB) = det(A) · det(B) con StepTracer."""
    _same_square_order(A, B, "comprobar det(AB) = det(A) det(B)")
    det_a = matrix_determinant(A).value
    det_b = matrix_determinant(B).value
    product = matrix_multiply(A, B)
    det_ab = matrix_determinant(product).value
    expected = det_a * det_b
    holds = det_ab == expected
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=f"det(A) = {format_scalar(det_a)}.",
        latex_title=r"\det(A)",
    )
    tracer.record_step(
        B,
        latex_formula=r"\det(B)",
        heuristic_text=f"det(B) = {format_scalar(det_b)}.",
    )
    tracer.record_step(
        product,
        latex_formula=r"\det(AB) = \det(A)\det(B)",
        heuristic_text=(
            f"det(AB) = {format_scalar(det_ab)} y det(A)·det(B) = {format_scalar(expected)}. "
            + ("La igualdad se cumple." if holds else "La igualdad no se cumple.")
        ),
    )
    return det_a, det_b, det_ab, holds, tracer


def verify_determinant_transpose(A: Matrix) -> Tuple[Fraction, Fraction, bool, StepTracer]:
    """Verifica det(Aᵀ) = det(A)."""
    require_square_matrix(A, "comprobar det(Aᵀ) = det(A)")
    det_a = matrix_determinant(A).value
    transposed = matrix_transpose(A)
    det_transpose = matrix_determinant(transposed).value
    holds = det_transpose == det_a
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=f"det(A) = {format_scalar(det_a)}.",
        latex_title=r"\det(A)",
    )
    tracer.record_step(
        transposed,
        latex_formula=r"\det(A^{T}) = \det(A)",
        heuristic_text=(
            f"det(Aᵀ) = {format_scalar(det_transpose)}. "
            + ("Coincide con det(A)." if holds else "No coincide con det(A).")
        ),
    )
    return det_a, det_transpose, holds, tracer


def verify_determinant_inverse(A: Matrix) -> Tuple[Fraction, Fraction, bool, StepTracer]:
    """Verifica det(A⁻¹) = 1/det(A) cuando A es no singular.

    Raises:
        SingularMatrixError: Si det(A) = 0.
        NonSquareMatrixError: Si A no es cuadrada.
    """
    require_square_matrix(A, "comprobar det(A⁻¹) = 1/det(A)")
    det_a = matrix_determinant(A).value
    if det_a == 0:
        raise SingularMatrixError(
            "No se puede comprobar det(A⁻¹) = 1/det(A): det(A) = 0 y A no es invertible."
        )
    from prettycalc.core.matrix_inversion import matrix_inverse

    inverse = matrix_inverse(A).inverse
    det_inverse = matrix_determinant(inverse).value
    reciprocal = Fraction(1, 1) / det_a
    holds = det_inverse == reciprocal
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=f"det(A) = {format_scalar(det_a)} ≠ 0, así que existe A⁻¹.",
        latex_title=r"\det(A^{-1}) = 1/\det(A)",
    )
    tracer.record_step(
        inverse,
        latex_formula=r"\det(A^{-1}) = \frac{1}{\det(A)}",
        heuristic_text=(
            f"det(A⁻¹) = {format_scalar(det_inverse)} y 1/det(A) = {format_scalar(reciprocal)}. "
            + ("La igualdad se cumple." if holds else "La igualdad no se cumple.")
        ),
    )
    return det_a, det_inverse, holds, tracer


def verify_determinant_scalar_scaling(
    A: Matrix,
    k: Fraction,
) -> Tuple[Fraction, Fraction, bool, StepTracer]:
    """Verifica det(kA) = kⁿ det(A). Devuelve (det(kA), kⁿ det(A), ¿iguales?, traza)."""
    order = require_square_matrix(A, "comprobar det(kA) = kⁿ det(A)")
    scalar = parse_scalar(k)
    det_a = matrix_determinant(A).value
    scaled = matrix_scale(A, scalar)
    det_scaled = matrix_determinant(scaled).value
    expected = (scalar ** order) * det_a
    holds = det_scaled == expected
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=f"det(A) = {format_scalar(det_a)} y el orden es n = {order}.",
        latex_title=r"\det(kA) = k^{n}\det(A)",
    )
    tracer.record_step(
        scaled,
        latex_formula=rf"\det\left({format_scalar(scalar, mode='latex')} A\right) = {format_scalar(scalar, mode='latex')}^{{{order}}}\det(A)",
        heuristic_text=(
            f"det(kA) = {format_scalar(det_scaled)} y kⁿ det(A) = {format_scalar(expected)}. "
            + ("La igualdad se cumple." if holds else "La igualdad no se cumple.")
        ),
    )
    return det_scaled, expected, holds, tracer


def verify_determinant_properties(
    A: Matrix,
    B: Optional[Matrix] = None,
    k: Optional[Fraction] = None,
) -> DeterminantPropertiesResult:
    """Contrasta las propiedades multiplicativas, de transpuesta, inversa y escala."""
    det_a, det_transpose, transpose_ok, transpose_tracer = verify_determinant_transpose(A)
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description="Comprobación de las propiedades del determinante.",
        latex_title=r"\det",
    )
    for step in transpose_tracer.get_steps():
        if step.step_number == 0:
            continue
        tracer.record_step(
            step.matrix,
            latex_formula=step.latex_formula,
            heuristic_text=step.heuristic_text,
            pivot_pos=step.pivot_pos,
        )

    det_b: Optional[Fraction] = None
    det_ab: Optional[Fraction] = None
    multiplicative_ok: Optional[bool] = None
    if B is not None:
        det_a, det_b, det_ab, multiplicative_ok, product_tracer = verify_determinant_multiplicative(A, B)
        for step in product_tracer.get_steps():
            tracer.record_step(
                step.matrix,
                latex_formula=step.latex_formula,
                heuristic_text=step.heuristic_text,
                pivot_pos=step.pivot_pos,
            )

    det_inverse: Optional[Fraction] = None
    reciprocal: Optional[Fraction] = None
    inverse_ok: Optional[bool] = None
    try:
        _, det_inverse, inverse_ok, inverse_tracer = verify_determinant_inverse(A)
    except SingularMatrixError as exc:
        tracer.record_step(
            A,
            latex_formula=r"\det(A) = 0",
            heuristic_text=str(exc),
        )
    else:
        reciprocal = Fraction(1, 1) / det_a
        for step in inverse_tracer.get_steps():
            if step.step_number == 0:
                continue
            tracer.record_step(
                step.matrix,
                latex_formula=step.latex_formula,
                heuristic_text=step.heuristic_text,
                pivot_pos=step.pivot_pos,
            )

    det_scaled: Optional[Fraction] = None
    scaling_ok: Optional[bool] = None
    scalar: Optional[Fraction] = None
    if k is not None:
        scalar = parse_scalar(k)
        det_scaled, _expected, scaling_ok, scale_tracer = verify_determinant_scalar_scaling(A, scalar)
        for step in scale_tracer.get_steps():
            if step.step_number == 0:
                continue
            tracer.record_step(
                step.matrix,
                latex_formula=step.latex_formula,
                heuristic_text=step.heuristic_text,
                pivot_pos=step.pivot_pos,
            )

    return DeterminantPropertiesResult(
        A=A.copy(),
        B=None if B is None else B.copy(),
        k=scalar,
        det_A=det_a,
        det_B=det_b,
        det_AB=det_ab,
        det_transpose=det_transpose,
        det_scaled=det_scaled,
        is_multiplicative_valid=multiplicative_ok,
        is_transpose_valid=transpose_ok,
        is_scaling_valid=scaling_ok,
        tracer=tracer,
        det_inverse=det_inverse,
        inverse_reciprocal=reciprocal,
        is_inverse_valid=inverse_ok,
    )
