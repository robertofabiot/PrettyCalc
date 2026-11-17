"""Álgebra matricial: suma, resta, escala, producto y transpuesta.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.
Aritmética exacta con fractions.Fraction. Sin NumPy, SciPy ni math.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, List, Tuple

from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    format_scalar,
    parse_scalar,
    subscript,
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
            "Se requiere A m×n y B n×p para obtener la matriz producto C = AB de tamaño m×p.",
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
    """Desglose pedagógico de una celda C_ij = (AB)_ij = Σ_k A_ik · B_kj.

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
        f"C_{row_index + 1},{col_index + 1} = (AB)_{row_index + 1},{col_index + 1} "
        f"= Σ_k A_{row_index + 1}k · B_k{col_index + 1} "
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
    """Producto C = AB = A · B. Exige columnas de A = filas de B y devuelve C."""
    result, _ = matrix_multiply_with_details(A, B)
    return result


def matrix_multiply_with_details(
    A: Matrix,
    B: Matrix,
) -> Tuple[Matrix, List[MultiplicationStepDetail]]:
    """Producto A · B (C = AB) y desglose por celda C_ij = (AB)_ij. Devuelve (C, detalles)."""
    _require_conformable(A, B)
    result = Matrix.zeros(A.rows, B.cols)
    details: List[MultiplicationStepDetail] = []
    for row_index in range(A.rows):
        for col_index in range(B.cols):
            detail = _cell_product(A, B, row_index, col_index)
            result.set(row_index, col_index, detail.total)
            details.append(detail)
    return result, details


# ---------------------------------------------------------------------------
# Procedimientos paso a paso (carrusel)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatrixOperationResult:
    """Resultado de una operación matricial con su procedimiento."""

    matrix: Matrix
    tracer: StepTracer


def _p(value: Fraction) -> str:
    return f"({format_scalar(value)})"


def _row_cells(row_index: int, cols: int) -> Tuple[Tuple[int, int], ...]:
    return tuple((row_index, col) for col in range(cols))


def trace_matrix_sum(A: Matrix, B: Matrix, *, subtract: bool = False) -> MatrixOperationResult:
    """A + B (o A − B) con un paso por fila: cᵢⱼ = aᵢⱼ ± bᵢⱼ.

    Raises:
        DimensionMismatchError: Si A y B no tienen el mismo tamaño.
    """
    result = matrix_sub(A, B) if subtract else matrix_add(A, B)
    shown = "−" if subtract else "+"
    symbol = "-" if subtract else "+"
    name = "resta" if subtract else "suma"
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            f"Primer operando A ({A.rows}×{A.cols}). La {name} se hace entrada a entrada: "
            f"cᵢⱼ = aᵢⱼ {shown} bᵢⱼ, por eso A y B deben tener el mismo tamaño."
        ),
        latex_title=rf"C = A {symbol} B",
    )
    tracer.record_step(
        B,
        latex_formula=r"B",
        heuristic_text=f"Segundo operando B ({B.rows}×{B.cols}).",
    )
    for row in range(A.rows):
        pieces = ", ".join(
            f"{_p(A.get(row, col))} {shown} {_p(B.get(row, col))} = {format_scalar(result.get(row, col))}"
            for col in range(A.cols)
        )
        tracer.record_step(
            result,
            latex_formula=rf"c_{{{row + 1}j}} = a_{{{row + 1}j}} {symbol} b_{{{row + 1}j}}",
            heuristic_text=f"Fila {row + 1} de C: {pieces}.",
            affected_rows=(row,),
            highlight_cells=_row_cells(row, A.cols),
        )
    return MatrixOperationResult(matrix=result, tracer=tracer)


def trace_matrix_scale(A: Matrix, scalar: Any) -> MatrixOperationResult:
    """k · A con un paso por fila: (kA)ᵢⱼ = k · aᵢⱼ."""
    k = parse_scalar(scalar)
    result = matrix_scale(A, k)
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=f"Se multiplica cada entrada de A por k = {format_scalar(k)}: (kA)ᵢⱼ = k · aᵢⱼ.",
        latex_title=rf"(kA)_{{ij}} = k\,a_{{ij}},\quad k = {format_scalar(k, mode='latex')}",
    )
    for row in range(A.rows):
        pieces = ", ".join(
            f"{_p(k)}·{_p(A.get(row, col))} = {format_scalar(result.get(row, col))}"
            for col in range(A.cols)
        )
        tracer.record_step(
            result,
            latex_formula=rf"(kA)_{{{row + 1}j}} = k\,a_{{{row + 1}j}}",
            heuristic_text=f"Fila {row + 1}: {pieces}.",
            affected_rows=(row,),
            highlight_cells=_row_cells(row, A.cols),
        )
    return MatrixOperationResult(matrix=result, tracer=tracer)


def trace_matrix_product(A: Matrix, B: Matrix) -> MatrixOperationResult:
    """A · B con un paso por entrada: cᵢⱼ = Σₖ aᵢₖ bₖⱼ (fila i de A por columna j de B).

    Raises:
        DimensionMismatchError: Si las columnas de A no coinciden con las filas de B.
    """
    result, details = matrix_multiply_with_details(A, B)
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            f"A es {A.rows}×{A.cols} y B es {B.rows}×{B.cols}: como A tiene {A.cols} columnas y B "
            f"{B.rows} filas, C = AB existe y es {A.rows}×{B.cols}. Cada entrada cᵢⱼ es la fila i "
            "de A por la columna j de B."
        ),
        latex_title=r"c_{ij} = \sum_k a_{ik}\,b_{kj}",
    )
    tracer.record_step(B, latex_formula=r"B", heuristic_text=f"Segundo factor B ({B.rows}×{B.cols}).")
    for detail in details:
        i, j = detail.row + 1, detail.col + 1
        products = " + ".join(f"{_p(left)}{_p(right)}" for left, right, _prod in detail.products)
        partials = " + ".join(_p(prod) for _left, _right, prod in detail.products)
        tracer.record_step(
            result,
            latex_formula=rf"c_{{{i}{j}}} = \sum_k a_{{{i}k}}\,b_{{k{j}}} = {format_scalar(detail.total, mode='latex')}",
            heuristic_text=(
                f"c{subscript(i, j)} = fila {i} de A · columna {j} de B = {products} "
                f"= {partials} = {format_scalar(detail.total)}."
            ),
            highlight_cells=((detail.row, detail.col),),
        )
    return MatrixOperationResult(matrix=result, tracer=tracer)


def trace_matrix_transpose(A: Matrix) -> MatrixOperationResult:
    """Aᵀ con un paso por fila: la fila i de A pasa a ser la columna i de Aᵀ."""
    result = matrix_transpose(A)
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            f"A es {A.rows}×{A.cols}, así que Aᵀ es {A.cols}×{A.rows}: (Aᵀ)ᵢⱼ = aⱼᵢ, "
            "las filas de A se escriben como columnas."
        ),
        latex_title=r"(A^{T})_{ij} = a_{ji}",
    )
    for row in range(A.rows):
        values = ", ".join(format_scalar(A.get(row, col)) for col in range(A.cols))
        tracer.record_step(
            result,
            latex_formula=rf"\text{{fila }} {row + 1} \text{{ de }} A \to \text{{columna }} {row + 1} \text{{ de }} A^{{T}}",
            heuristic_text=f"La fila {row + 1} de A, ({values}), pasa a ser la columna {row + 1} de Aᵀ.",
            highlight_cells=tuple((col, row) for col in range(A.cols)),
        )
    return MatrixOperationResult(matrix=result, tracer=tracer)


# Interfaz unificada del álgebra matricial: la inversa vive en matrix_inversion
# y se reexporta aquí para que suma, producto, transpuesta e inversa compartan módulo.
from prettycalc.core.matrix_inversion import (  # noqa: E402
    MatrixInverseResult,
    NonSquareMatrixError,
    SingularMatrixError,
    matrix_inverse,
    solve_system_via_inverse,
    solve_via_inverse,
)
