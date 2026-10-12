"""Operaciones algebraicas fundamentales entre vectores de ℝⁿ.

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
Prohibido NumPy, SciPy y álgebra lineal de `math`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Tuple

from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    Vector,
    format_scalar,
    parse_scalar,
)


_SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _space(n: int) -> str:
    """ℝⁿ con el exponente volado: ℝ³, ℝ¹⁰."""
    return "ℝ" + str(n).translate(_SUPERSCRIPTS)


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


def _square_free_parts(value: int) -> Tuple[int, int]:
    """Parte value = cuadrado² · libre, con libre sin factores cuadrados."""
    if value < 0:
        raise ValueError("No se descompone un entero negativo en factores cuadrados.")
    if value == 0:
        return 0, 1
    square = 1
    free = 1
    rest = value
    factor = 2
    while factor * factor <= rest:
        count = 0
        while rest % factor == 0:
            rest //= factor
            count += 1
        if count:
            square *= factor ** (count // 2)
            if count % 2 == 1:
                free *= factor
        factor = 3 if factor == 2 else factor + 2
    if rest > 1:
        free *= rest
    return square, free


def vector_norm_squared(v: Vector) -> Fraction:
    """Calcula el valor exacto racional de ||v||² = Σ v_i² = v · v."""
    return vector_dot(v, v)


def vector_norm_exact(v: Vector) -> Tuple[Fraction, int, int]:
    """Devuelve (coeficiente, radicando, denominador) con ||v|| = coef · √(rad_num / rad_den).

    El radicando queda libre de factores cuadrados y, tras racionalizar,
    el denominador del radical es 1: ||v|| = coef · √rad_num.
    """
    squared = vector_norm_squared(v)
    if squared == 0:
        return Fraction(0, 1), 1, 1
    if squared < 0:
        raise ValueError("La suma de cuadrados de un vector real no puede ser negativa.")
    radical_square, radical_free = _square_free_parts(squared.numerator * squared.denominator)
    coefficient = Fraction(radical_square, squared.denominator)
    return coefficient, radical_free, 1


def vector_distance_squared(u: Vector, v: Vector) -> Fraction:
    """Calcula ||u − v||² en aritmética exacta.

    Raises:
        DimensionMismatchError: Si u y v no viven en el mismo ℝⁿ.
    """
    return vector_norm_squared(vector_sub(u, v))


def vector_distance_exact(u: Vector, v: Vector) -> Tuple[Fraction, int, int]:
    """Forma radical exacta de d(u, v) = ||u − v||."""
    return vector_norm_exact(vector_sub(u, v))


def vector_outer_product(u: Vector, v: Vector) -> Matrix:
    """Calcula el producto exterior u · vᵀ, de tamaño m × n, con M_ij = u_i · v_j."""
    data = [
        [u[row_index] * v[col_index] for col_index in range(v.dimension)]
        for row_index in range(u.dimension)
    ]
    return Matrix(data)


def format_exact_sqrt(
    coefficient: Fraction,
    radical_numerator: int,
    radical_denominator: int = 1,
) -> str:
    """Texto pedagógico de coef · √(rad_num / rad_den), por ejemplo 5 o (1/2)√2."""
    if coefficient == 0 or radical_numerator == 0:
        return "0"
    coefficient_text = format_scalar(coefficient)
    if radical_numerator == radical_denominator:
        return coefficient_text
    if radical_denominator == 1:
        radical = f"√{radical_numerator}"
    else:
        radical = f"√({radical_numerator}/{radical_denominator})"
    if coefficient == 1:
        return radical
    if coefficient == -1:
        return f"−{radical}"
    if coefficient.denominator == 1:
        return f"{coefficient_text}{radical}"
    return f"({coefficient_text}){radical}"


def format_exact_sqrt_latex(
    coefficient: Fraction,
    radical_numerator: int,
    radical_denominator: int = 1,
) -> str:
    """LaTeX de la misma forma radical exacta."""
    if coefficient == 0 or radical_numerator == 0:
        return "0"
    coefficient_latex = format_scalar(coefficient, mode="latex")
    if radical_numerator == radical_denominator:
        return coefficient_latex
    if radical_denominator == 1:
        radical = f"\\sqrt{{{radical_numerator}}}"
    else:
        body = format_scalar(Fraction(radical_numerator, radical_denominator), mode="latex")
        radical = f"\\sqrt{{{body}}}"
    if coefficient == 1:
        return radical
    if coefficient == -1:
        return f"-{radical}"
    return f"{coefficient_latex}{radical}"


@dataclass(frozen=True)
class VectorMetricResult:
    """Norma o distancia: cuadrado racional, radical simplificado y traza."""

    squared: Fraction
    coefficient: Fraction
    radical_numerator: int
    radical_denominator: int
    display: str
    latex: str
    tracer: StepTracer


@dataclass(frozen=True)
class OuterProductResult:
    """Matriz diádica u vᵀ y el registro de su construcción."""

    matrix: Matrix
    tracer: StepTracer


def _metric_result(squared: Fraction, coefficient: Fraction, radical_numerator: int, radical_denominator: int, tracer: StepTracer) -> VectorMetricResult:
    return VectorMetricResult(
        squared=squared,
        coefficient=coefficient,
        radical_numerator=radical_numerator,
        radical_denominator=radical_denominator,
        display=format_exact_sqrt(coefficient, radical_numerator, radical_denominator),
        latex=format_exact_sqrt_latex(coefficient, radical_numerator, radical_denominator),
        tracer=tracer,
    )


def trace_vector_norm(v: Vector) -> VectorMetricResult:
    """Calcula ||v||² y la forma radical, con cada suma de cuadrados en el trazador."""
    tracer = StepTracer()
    column = v.to_column_matrix()
    tracer.record_initial(
        column,
        description="La norma euclidiana cumple ||v||² = v · v = Σ v_i², un racional exacto.",
        latex_title=r"\|v\|^2 = \sum_i v_i^2",
    )
    squared = Fraction(0, 1)
    pieces: list[str] = []
    for index in range(v.dimension):
        term = v[index] * v[index]
        squared += term
        pieces.append(f"({format_scalar(v[index])})² = {format_scalar(term)}")
    coefficient, radical_numerator, radical_denominator = vector_norm_exact(v)
    shown = format_exact_sqrt(coefficient, radical_numerator, radical_denominator)
    tracer.record_step(
        column,
        latex_formula=(
            rf"\|v\|^2 = {' + '.join(format_scalar(v[index] * v[index], mode='latex') for index in range(v.dimension))}"
            rf" = {format_scalar(squared, mode='latex')}"
        ),
        heuristic_text=(
            "Se suman los cuadrados: "
            + ", ".join(pieces)
            + f". ||v||² = {format_scalar(squared)}. "
            f"La forma radical simplificada es ||v|| = {shown}."
        ),
    )
    return _metric_result(squared, coefficient, radical_numerator, radical_denominator, tracer)


def trace_vector_distance(u: Vector, v: Vector) -> VectorMetricResult:
    """Calcula d(u, v) = ||u − v|| con la diferencia y la norma en el trazador."""
    difference = vector_sub(u, v)
    metric = trace_vector_norm(difference)
    tracer = StepTracer()
    tracer.record_initial(
        difference.to_column_matrix(),
        description=(
            "La distancia euclidiana es la norma de la diferencia: d(u, v) = ||u − v||. "
            + ", ".join(
                f"(u − v)_{index + 1} = {format_scalar(difference[index])}"
                for index in range(difference.dimension)
            )
            + "."
        ),
        latex_title=r"d(u, v) = \|u - v\|",
    )
    for step in metric.tracer.get_steps():
        if step.step_number == 0:
            continue
        tracer.record_step(
            step.matrix,
            latex_formula=step.latex_formula,
            heuristic_text=step.heuristic_text,
            pivot_pos=step.pivot_pos,
        )
    return _metric_result(
        metric.squared,
        metric.coefficient,
        metric.radical_numerator,
        metric.radical_denominator,
        tracer,
    )


def trace_vector_outer_product(u: Vector, v: Vector) -> OuterProductResult:
    """Construye u vᵀ y registra la regla M_ij = u_i · v_j."""
    product = vector_outer_product(u, v)
    tracer = StepTracer()
    tracer.record_initial(
        u.to_column_matrix(),
        description=(
            f"u está en {_space(u.dimension)} y v en {_space(v.dimension)}. "
            f"El producto exterior u vᵀ es una matriz {u.dimension}×{v.dimension}."
        ),
        latex_title=r"M = u v^{T}",
    )
    tracer.record_step(
        product,
        latex_formula=r"M_{ij} = u_i v_j",
        heuristic_text=(
            "Cada entrada es el producto de una componente de u por una de v. "
            f"La matriz resultante es {product.rows}×{product.cols}."
        ),
    )
    return OuterProductResult(matrix=product, tracer=tracer)


@dataclass(frozen=True)
class VectorOperationResult:
    """Resultado de u ± v o k · v con el desglose componente a componente."""

    vector: Vector
    tracer: StepTracer


def _signed(value: Fraction) -> str:
    """Escribe un sumando con paréntesis si es negativo: 3, (−1/2)."""
    text = format_scalar(value)
    return f"({text})" if value < 0 else text


def _signed_latex(value: Fraction) -> str:
    text = format_scalar(value, mode="latex")
    return f"\\left({text}\\right)" if value < 0 else text


def trace_vector_sum(u: Vector, v: Vector, *, subtract: bool = False) -> VectorOperationResult:
    """u + v (o u − v) con un paso por componente: w_i = u_i ± v_i.

    Cada paso muestra la matriz [u  v | w] con la fila i resaltada, de modo que
    el estudiante ve qué componentes se combinan y qué valor resulta.
    """
    result = vector_sub(u, v) if subtract else vector_add(u, v)
    symbol = "-" if subtract else "+"
    shown = "−" if subtract else "+"
    tracer = StepTracer(split_col=2)
    rows = [[u[i], v[i], result[i]] for i in range(u.dimension)]
    board = Matrix(rows)
    tracer.record_initial(
        Matrix([[u[i], v[i]] for i in range(u.dimension)]),
        description=(
            f"u y v están en {_space(u.dimension)}. La {'resta' if subtract else 'suma'} se hace "
            f"componente a componente: (u {shown} v)ᵢ = uᵢ {shown} vᵢ."
        ),
        latex_title=rf"(u {symbol} v)_i = u_i {symbol} v_i",
    )
    for i in range(u.dimension):
        tracer.record_step(
            board,
            latex_formula=(
                rf"(u {symbol} v)_{{{i + 1}}} = {_signed_latex(u[i])} {symbol} "
                rf"{_signed_latex(v[i])} = {format_scalar(result[i], mode='latex')}"
            ),
            heuristic_text=(
                f"Componente {i + 1}: {_signed(u[i])} {shown} {_signed(v[i])} = "
                f"{format_scalar(result[i])}."
            ),
            affected_rows=(i,),
            highlight_cells=((i, 0), (i, 1), (i, 2)),
        )
    return VectorOperationResult(vector=result, tracer=tracer)


def trace_vector_scale(v: Vector, scalar: Any) -> VectorOperationResult:
    """k · v con un paso por componente: (k v)_i = k · v_i."""
    k = parse_scalar(scalar)
    result = vector_scale(v, k)
    tracer = StepTracer(split_col=1)
    board = Matrix([[v[i], result[i]] for i in range(v.dimension)])
    tracer.record_initial(
        v.to_column_matrix(),
        description=(
            f"Se multiplica cada componente de v por k = {format_scalar(k)}: (k v)ᵢ = k · vᵢ."
        ),
        latex_title=rf"(k v)_i = k \cdot v_i,\quad k = {format_scalar(k, mode='latex')}",
    )
    for i in range(v.dimension):
        tracer.record_step(
            board,
            latex_formula=(
                rf"(k v)_{{{i + 1}}} = {_signed_latex(k)} \cdot {_signed_latex(v[i])} = "
                rf"{format_scalar(result[i], mode='latex')}"
            ),
            heuristic_text=(
                f"Componente {i + 1}: {_signed(k)} · {_signed(v[i])} = {format_scalar(result[i])}."
            ),
            affected_rows=(i,),
            highlight_cells=((i, 0), (i, 1)),
        )
    if k == 0:
        tracer.record_step(
            board,
            latex_formula=r"0 \cdot v = \mathbf{0}",
            heuristic_text="Con k = 0 todo vector se anula: 0 · v es el vector cero de ℝⁿ.",
        )
    return VectorOperationResult(vector=result, tracer=tracer)
