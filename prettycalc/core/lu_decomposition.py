"""Factorización A = LU y resolución encadenada Ly = b, Ux = y.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM). Sesión 12.
Aritmética exacta con fractions.Fraction. Sin NumPy, SciPy ni SymPy.

L es triangular inferior unitaria (unos en la diagonal y los multiplicadores
debajo). U es la forma escalonada de A obtenida solo con reemplazos de fila
hacia abajo, sin intercambios. Si un pivote es cero y debajo hay una entrada
no nula, no existe A = LU y hace falta PLU: se lanza LUPivotZeroError.

L tiene tantas filas como A. Si A es m×n, L es m×m y U es m×n. Así entra el
ejemplo 4×5 de la sesión, donde una columna queda sin pivote.

`plu_decompose` sí permuta filas cuando el pivote es cero y construye P tal
que P A = L U. `lu_decompose` se mantiene sin intercambios.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.matrix_ops import matrix_multiply
from prettycalc.core.matrix_vector_ops import matrix_vector_multiply
from prettycalc.core.operations import (
    add_row_multiple,
    get_add_multiple_metadata,
    get_scale_metadata,
    get_swap_metadata,
    scale_row,
    swap_rows,
)
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar


class LUPivotZeroError(ValueError):
    """Pivote nulo con una entrada no nula debajo: A = LU exigiría permutar filas."""

    def __init__(self, message: str, tracer: Optional[StepTracer] = None) -> None:
        super().__init__(message)
        self.tracer = tracer


class LUSingularError(ValueError):
    """U (o L) tiene un cero en la diagonal: Ax = b no tiene solución única."""

    def __init__(self, message: str, tracer: Optional[StepTracer] = None) -> None:
        super().__init__(message)
        self.tracer = tracer


@dataclass(frozen=True)
class LUFactorizationResult:
    """Factores L y U, con la traza de los multiplicadores guardados en L."""

    L: Matrix
    U: Matrix
    original: Matrix
    is_valid: bool
    tracer: StepTracer
    multipliers_table: List[Tuple[int, int, Fraction]]


@dataclass(frozen=True)
class LUSystemSolutionResult:
    """Solución de Ax = b reutilizando una factorización ya calculada."""

    factorization: LUFactorizationResult
    b: Vector
    y_intermediate: Vector
    x_solution: Vector
    forward_steps: List[str]
    backward_steps: List[str]
    verification_passed: bool
    forward_tracer: StepTracer
    backward_tracer: StepTracer


def _show(value: Fraction) -> str:
    return format_scalar(value, mode="fraction")


def _require_square(matrix: Matrix, operation: str) -> int:
    if matrix.rows != matrix.cols:
        raise NonSquareMatrixError(
            f"No se puede {operation}: la matriz es {matrix.rows}×{matrix.cols}. "
            "Esta etapa está definida para matrices cuadradas (n×n)."
        )
    return matrix.rows


def _require_vector_length(length: int, vector: Vector, operation: str) -> None:
    if vector.dimension != length:
        raise DimensionMismatchError(
            f"No se puede {operation}: se esperaba un vector de ℝ^{length} "
            f"y se recibió uno de ℝ^{vector.dimension}.",
            left_shape=(length, length),
            right_shape=(vector.dimension,),
            operation=operation,
        )


def _require_lower_triangular(L: Matrix) -> int:
    order = _require_square(L, "sustituir hacia adelante con L")
    for row_index in range(order):
        for col_index in range(row_index + 1, order):
            entry = L.get(row_index, col_index)
            if entry != 0:
                raise ValueError(
                    "La sustitución hacia adelante exige L triangular inferior. "
                    f"L_{row_index + 1}{col_index + 1} = {_show(entry)} no es cero."
                )
    return order


def _require_upper_triangular(U: Matrix) -> int:
    order = _require_square(U, "sustituir hacia atrás con U")
    for row_index in range(order):
        for col_index in range(row_index):
            entry = U.get(row_index, col_index)
            if entry != 0:
                raise ValueError(
                    "La sustitución hacia atrás exige U triangular superior. "
                    f"U_{row_index + 1}{col_index + 1} = {_show(entry)} no es cero."
                )
    return order


def lu_decompose(A: Matrix) -> LUFactorizationResult:
    """Calcula A = LU sin permutar filas.

    L es m×m, con unos en la diagonal. U es m×n y coincide con la forma
    escalonada de A. Cada multiplicador es la entrada bajo el pivote dividida
    por el pivote, y se anula con f_i → f_i − ℓ_ij f_j.

    Raises:
        LUPivotZeroError: Si un candidato a pivote es 0 y debajo hay un no nulo.
    """
    row_count = A.rows
    col_count = A.cols
    upper = A.copy()
    lower = Matrix.identity(row_count)
    multipliers: List[Tuple[int, int, Fraction]] = []
    tracer = StepTracer(split_col=row_count)
    tracer.record_initial(
        lower.augment(upper),
        description=(
            "L comienza como la identidad y U como una copia de A. "
            "Solo se usan reemplazos de fila hacia abajo, sin intercambios."
        ),
        latex_title=r"\text{Inicio: } L = I \text{ y } U = A",
    )

    pivot_row = 0
    for col in range(col_count):
        if pivot_row >= row_count:
            break
        pivot = upper.get(pivot_row, col)
        if pivot == 0:
            if any(upper.get(row, col) != 0 for row in range(pivot_row + 1, row_count)):
                raise LUPivotZeroError(
                    "No existe la factorización A = LU sin permutar filas: "
                    f"en la fila {pivot_row + 1}, columna {col + 1}, el pivote es 0 "
                    "y hay una entrada no nula debajo. Haría falta una factorización PLU, "
                    "que esta sesión no construye.",
                    tracer=tracer,
                )
            tracer.record_step(
                lower.augment(upper),
                latex_formula=rf"\text{{La columna {col + 1} no tiene pivote}}",
                heuristic_text=(
                    f"La columna {col + 1} no tiene pivote: es cero desde la fila {pivot_row + 1} "
                    "hacia abajo. No hace falta intercambiar filas; se sigue con la columna siguiente."
                ),
            )
            continue

        for row in range(pivot_row + 1, row_count):
            entry = upper.get(row, col)
            if entry == 0:
                continue
            multiplier = entry / pivot
            lower.set(row, pivot_row, multiplier)
            multipliers.append((row, pivot_row, multiplier))
            coefficient = -multiplier
            upper = add_row_multiple(upper, row, pivot_row, coefficient)
            latex, row_text = get_add_multiple_metadata(row, pivot_row, coefficient)
            tracer.record_step(
                lower.augment(upper),
                latex_formula=latex,
                heuristic_text=(
                    f"Multiplicador ℓ_{row + 1},{pivot_row + 1} = "
                    f"{_show(entry)}/{_show(pivot)} = {_show(multiplier)}. "
                    f"Se guarda en la columna {pivot_row + 1} de L. {row_text}"
                ),
                pivot_pos=(row, pivot_row),
                actor_row=pivot_row,
                affected_rows=(row,),
            )
        pivot_row += 1

    product = matrix_multiply(lower, upper)
    return LUFactorizationResult(
        L=lower.copy(),
        U=upper.copy(),
        original=A.copy(),
        is_valid=product == A,
        tracer=tracer,
        multipliers_table=multipliers,
    )


def _forward_substitution(
    L: Matrix,
    b: Vector,
    *,
    description: str = "Etapa 1. Sustitución hacia adelante: se resuelve el sistema triangular L y = b.",
    latex_title: str = r"\text{Etapa 1: } Ly = b",
) -> Tuple[Vector, List[str], StepTracer]:
    """Resuelve Ly = b y registra la reducción de [L | b] hasta [I | y]."""
    order = _require_lower_triangular(L)
    _require_vector_length(order, b, "resolver L y = b")
    work = L.augment(b)
    tracer = StepTracer(split_col=order)
    tracer.record_initial(
        work,
        description=description,
        latex_title=latex_title,
    )
    steps: List[str] = []
    solved: List[Fraction] = []

    for index in range(order):
        diagonal = L.get(index, index)
        if diagonal == 0:
            raise LUSingularError(
                f"No se puede despejar y_{index + 1}: el pivote L_{index + 1}{index + 1} es 0.",
                tracer=tracer,
            )
        remainder = b[index]
        consumed: List[str] = []
        for previous in range(index):
            coefficient = L.get(index, previous)
            if coefficient == 0:
                continue
            remainder -= coefficient * solved[previous]
            consumed.append(f"({_show(coefficient)})({_show(solved[previous])})")
        value = remainder / diagonal
        solved.append(value)
        if not consumed and diagonal == 1:
            steps.append(f"y_{index + 1} = b_{index + 1} = {_show(value)}.")
        elif not consumed:
            steps.append(
                f"y_{index + 1} = b_{index + 1} / L_{index + 1}{index + 1} = "
                f"{_show(b[index])} / {_show(diagonal)} = {_show(value)}."
            )
        elif diagonal == 1:
            steps.append(
                f"y_{index + 1} = b_{index + 1} − Σ L_{index + 1}j y_j = "
                f"{_show(b[index])} − ({' + '.join(consumed)}) = {_show(value)}."
            )
        else:
            steps.append(
                f"y_{index + 1} = (b_{index + 1} − Σ L_{index + 1}j y_j) / L_{index + 1}{index + 1} = "
                f"({_show(b[index])} − ({' + '.join(consumed)})) / {_show(diagonal)} = {_show(value)}."
            )

        pivot = work.get(index, index)
        if pivot != 1:
            work = scale_row(work, index, Fraction(1) / pivot)
            latex, row_text = get_scale_metadata(index, Fraction(1) / pivot)
            tracer.record_step(
                work,
                latex_formula=latex,
                heuristic_text=f"{steps[-1]} {row_text}",
                pivot_pos=(index, index),
                actor_row=index,
                affected_rows=(index,),
            )
        for target in range(index + 1, order):
            entry = work.get(target, index)
            if entry == 0:
                continue
            work = add_row_multiple(work, target, index, -entry)
            latex, row_text = get_add_multiple_metadata(target, index, -entry)
            tracer.record_step(
                work,
                latex_formula=latex,
                heuristic_text=f"Se arrastra y_{index + 1} = {_show(value)} hacia las filas de abajo. {row_text}",
                pivot_pos=(index, index),
                actor_row=index,
                affected_rows=(target,),
            )

    return Vector(solved), steps, tracer


def _backward_substitution(
    U: Matrix,
    y: Vector,
) -> Tuple[Vector, List[str], StepTracer]:
    """Resuelve Ux = y desde la última incógnita y reduce [U | y] hasta [I | x]."""
    order = _require_upper_triangular(U)
    _require_vector_length(order, y, "resolver U x = y")
    work = U.augment(y)
    tracer = StepTracer(split_col=order)
    tracer.record_initial(
        work,
        description="Etapa 2. Sustitución hacia atrás: se resuelve el sistema triangular U x = y.",
        latex_title=r"\text{Etapa 2: } Ux = y",
    )
    steps: List[str] = []
    solved = [Fraction(0) for _ in range(order)]

    for index in range(order - 1, -1, -1):
        diagonal = U.get(index, index)
        if diagonal == 0:
            raise LUSingularError(
                f"No se puede despejar x_{index + 1}: el pivote u_{index + 1}{index + 1} de U es 0. "
                "A es singular, así que Ax = b no tiene solución única por sustitución hacia atrás. "
                "Eso no pide un intercambio de filas: la factorización A = LU puede existir igual.",
                tracer=tracer,
            )
        remainder = y[index]
        consumed: List[str] = []
        for following in range(index + 1, order):
            coefficient = U.get(index, following)
            if coefficient == 0:
                continue
            remainder -= coefficient * solved[following]
            consumed.append(f"({_show(coefficient)})({_show(solved[following])})")
        value = remainder / diagonal
        solved[index] = value
        if not consumed and diagonal == 1:
            steps.append(f"x_{index + 1} = y_{index + 1} = {_show(value)}.")
        elif not consumed:
            steps.append(
                f"x_{index + 1} = y_{index + 1} / u_{index + 1}{index + 1} = "
                f"{_show(y[index])} / {_show(diagonal)} = {_show(value)}."
            )
        elif diagonal == 1:
            steps.append(
                f"x_{index + 1} = y_{index + 1} − Σ u_{index + 1}j x_j = "
                f"{_show(y[index])} − ({' + '.join(consumed)}) = {_show(value)}."
            )
        else:
            steps.append(
                f"x_{index + 1} = (y_{index + 1} − Σ u_{index + 1}j x_j) / u_{index + 1}{index + 1} = "
                f"({_show(y[index])} − ({' + '.join(consumed)})) / {_show(diagonal)} = {_show(value)}."
            )

        pivot = work.get(index, index)
        if pivot != 1:
            work = scale_row(work, index, Fraction(1) / pivot)
            latex, row_text = get_scale_metadata(index, Fraction(1) / pivot)
            tracer.record_step(
                work,
                latex_formula=latex,
                heuristic_text=f"{steps[-1]} {row_text}",
                pivot_pos=(index, index),
                actor_row=index,
                affected_rows=(index,),
            )
        for target in range(index - 1, -1, -1):
            entry = work.get(target, index)
            if entry == 0:
                continue
            work = add_row_multiple(work, target, index, -entry)
            latex, row_text = get_add_multiple_metadata(target, index, -entry)
            tracer.record_step(
                work,
                latex_formula=latex,
                heuristic_text=f"Se sustituye x_{index + 1} = {_show(value)} en las filas de arriba. {row_text}",
                pivot_pos=(index, index),
                actor_row=index,
                affected_rows=(target,),
            )

    return Vector(solved), steps, tracer


def forward_substitution(L: Matrix, b: Vector) -> Tuple[Vector, List[str]]:
    """Resuelve L y = b para L triangular inferior. La L de esta sesión es unitaria."""
    solution, steps, _tracer = _forward_substitution(L, b)
    return solution, steps


def backward_substitution(U: Matrix, y: Vector) -> Tuple[Vector, List[str]]:
    """Resuelve U x = y para U triangular superior con diagonal distinta de cero."""
    solution, steps, _tracer = _backward_substitution(U, y)
    return solution, steps


def solve_from_factorization(
    factorization: LUFactorizationResult,
    b: Vector,
) -> LUSystemSolutionResult:
    """Resuelve Ax = b con una factorización ya hecha: Ly = b y después Ux = y.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada. La factorización rectangular
            sigue disponible; la solución única en dos etapas, no.
        DimensionMismatchError: Si la dimensión de b no es el orden de A.
        LUSingularError: Si algún pivote diagonal de U es cero.
    """
    original = factorization.original
    if original.rows != original.cols:
        raise NonSquareMatrixError(
            "La resolución en dos etapas Ly = b, Ux = y está definida para A cuadrada. "
            f"A es {original.rows}×{original.cols}. Los factores L y U sí pueden usarse; "
            "un sistema rectangular no tiene una solución única por sustitución diagonal."
        )
    _require_vector_length(original.rows, b, "resolver A x = b con los factores L y U")
    y_vector, forward_steps, forward_tracer = _forward_substitution(factorization.L, b)
    x_vector, backward_steps, backward_tracer = _backward_substitution(factorization.U, y_vector)
    lu_matches = matrix_multiply(factorization.L, factorization.U) == original
    ax_matches = matrix_vector_multiply(original, x_vector) == b
    ly_matches = matrix_vector_multiply(factorization.L, y_vector) == b
    ux_matches = matrix_vector_multiply(factorization.U, x_vector) == y_vector
    return LUSystemSolutionResult(
        factorization=factorization,
        b=b.copy(),
        y_intermediate=y_vector,
        x_solution=x_vector,
        forward_steps=forward_steps,
        backward_steps=backward_steps,
        verification_passed=lu_matches and ax_matches and ly_matches and ux_matches,
        forward_tracer=forward_tracer,
        backward_tracer=backward_tracer,
    )


@dataclass(frozen=True)
class PLUFactorizationResult:
    """Factores de P A = L U, con el conteo de intercambios de fila."""

    P: Matrix
    L: Matrix
    U: Matrix
    original: Matrix
    is_valid: bool
    permutation_count: int
    tracer: StepTracer
    multipliers_table: List[Tuple[int, int, Fraction]]


@dataclass(frozen=True)
class PLUSystemSolutionResult:
    """Solución de A x = b por L y = P b y U x = y."""

    factorization: PLUFactorizationResult
    b: Vector
    permuted_b: Vector
    y_intermediate: Vector
    x_solution: Vector
    forward_steps: List[str]
    backward_steps: List[str]
    verification_passed: bool
    forward_tracer: StepTracer
    backward_tracer: StepTracer


def _swap_recorded_multipliers(lower: Matrix, first: int, second: int, pivot_row: int) -> None:
    """Intercambia en L solo los multiplicadores de columnas anteriores al pivote actual."""
    for column in range(pivot_row):
        first_value = lower.get(first, column)
        second_value = lower.get(second, column)
        lower.set(first, column, second_value)
        lower.set(second, column, first_value)


def plu_decompose(A: Matrix) -> PLUFactorizationResult:
    """Factoriza A en P, L y U con pivoteo de filas: P A = L U.

    P empieza como I. Si el candidato a pivote es 0 y hay una entrada no nula
    debajo, se intercambia con la primera de esas filas. Si no hace falta
    permutar, P = I y los factores coinciden con A = L U.

    Una columna de ceros desde la fila actual no tiene pivote: se sigue con la
    siguiente, igual que en la factorización sin permutación.
    """
    row_count = A.rows
    col_count = A.cols
    upper = A.copy()
    lower = Matrix.identity(row_count)
    permutation = Matrix.identity(row_count)
    multipliers: List[Tuple[int, int, Fraction]] = []
    permutation_count = 0
    tracer = StepTracer(split_col=row_count)
    tracer.record_initial(
        lower.augment(upper),
        description=(
            "P comienza como la identidad, L como la identidad y U como una copia de A. "
            "Solo se intercambian filas cuando el pivote es cero y debajo hay una entrada no nula."
        ),
        latex_title=r"\text{Inicio: } P = I,\ L = I,\ U = A",
    )

    pivot_row = 0
    for col in range(col_count):
        if pivot_row >= row_count:
            break
        pivot = upper.get(pivot_row, col)
        if pivot == 0:
            swap_with = None
            for row in range(pivot_row + 1, row_count):
                if upper.get(row, col) != 0:
                    swap_with = row
                    break
            if swap_with is None:
                tracer.record_step(
                    lower.augment(upper),
                    latex_formula=rf"\text{{La columna {col + 1} no tiene pivote}}",
                    heuristic_text=(
                        f"La columna {col + 1} no tiene pivote: es cero desde la fila {pivot_row + 1} "
                        "hacia abajo. No hace falta intercambiar filas; se sigue con la columna siguiente."
                    ),
                )
                continue
            upper = swap_rows(upper, pivot_row, swap_with)
            permutation = swap_rows(permutation, pivot_row, swap_with)
            _swap_recorded_multipliers(lower, pivot_row, swap_with, pivot_row)
            permutation_count += 1
            latex, row_text = get_swap_metadata(pivot_row, swap_with)
            tracer.record_step(
                lower.augment(upper),
                latex_formula=latex,
                heuristic_text=(
                    f"{row_text} El pivote de la columna {col + 1} era 0. "
                    "Se aplica el mismo intercambio a P y a los multiplicadores ya guardados en L."
                ),
                pivot_pos=(pivot_row, col),
                affected_rows=(pivot_row, swap_with),
            )
            pivot = upper.get(pivot_row, col)

        for row in range(pivot_row + 1, row_count):
            entry = upper.get(row, col)
            if entry == 0:
                continue
            multiplier = entry / pivot
            lower.set(row, pivot_row, multiplier)
            multipliers.append((row, pivot_row, multiplier))
            coefficient = -multiplier
            upper = add_row_multiple(upper, row, pivot_row, coefficient)
            latex, row_text = get_add_multiple_metadata(row, pivot_row, coefficient)
            tracer.record_step(
                lower.augment(upper),
                latex_formula=latex,
                heuristic_text=(
                    f"Multiplicador ℓ_{row + 1},{pivot_row + 1} = "
                    f"{_show(entry)}/{_show(pivot)} = {_show(multiplier)}. "
                    f"Se guarda en la columna {pivot_row + 1} de L. {row_text}"
                ),
                pivot_pos=(row, pivot_row),
                actor_row=pivot_row,
                affected_rows=(row,),
            )
        pivot_row += 1

    product = matrix_multiply(lower, upper)
    permuted = matrix_multiply(permutation, A)
    return PLUFactorizationResult(
        P=permutation.copy(),
        L=lower.copy(),
        U=upper.copy(),
        original=A.copy(),
        is_valid=product == permuted,
        permutation_count=permutation_count,
        tracer=tracer,
        multipliers_table=multipliers,
    )


def solve_from_plu_factorization(
    plu: PLUFactorizationResult,
    b: Vector,
) -> PLUSystemSolutionResult:
    """Resuelve A x = b con P A = L U: primero L y = P b y después U x = y.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
        DimensionMismatchError: Si dim(b) no es el orden de A.
        LUSingularError: Si algún pivote diagonal de U es cero.
    """
    original = plu.original
    if original.rows != original.cols:
        raise NonSquareMatrixError(
            "La resolución en dos etapas L y = P b, U x = y está definida para A cuadrada. "
            f"A es {original.rows}×{original.cols}."
        )
    _require_vector_length(original.rows, b, "resolver A x = b con los factores P, L y U")
    permuted_b = matrix_vector_multiply(plu.P, b)
    y_vector, forward_steps, forward_tracer = _forward_substitution(
        plu.L,
        permuted_b,
        description=(
            "Etapa 1. Sustitución hacia adelante: se resuelve L y = P b, "
            "con el vector de carga ya permutado."
        ),
        latex_title=r"\text{Etapa 1: } Ly = Pb",
    )
    x_vector, backward_steps, backward_tracer = _backward_substitution(plu.U, y_vector)
    factors_match = matrix_multiply(plu.P, original) == matrix_multiply(plu.L, plu.U)
    ax_matches = matrix_vector_multiply(original, x_vector) == b
    ly_matches = matrix_vector_multiply(plu.L, y_vector) == permuted_b
    ux_matches = matrix_vector_multiply(plu.U, x_vector) == y_vector
    return PLUSystemSolutionResult(
        factorization=plu,
        b=b.copy(),
        permuted_b=permuted_b,
        y_intermediate=y_vector,
        x_solution=x_vector,
        forward_steps=forward_steps,
        backward_steps=backward_steps,
        verification_passed=factors_match and ax_matches and ly_matches and ux_matches,
        forward_tracer=forward_tracer,
        backward_tracer=backward_tracer,
    )


def solve_via_plu(A: Matrix, b: Vector) -> PLUSystemSolutionResult:
    """Factoriza P A = L U y resuelve A x = b en las dos etapas L y = P b, U x = y."""
    if A.rows != A.cols:
        raise NonSquareMatrixError(
            "La resolución en dos etapas L y = P b, U x = y está definida para A cuadrada. "
            f"A es {A.rows}×{A.cols}."
        )
    return solve_from_plu_factorization(plu_decompose(A), b)


def solve_via_lu(A: Matrix, b: Vector) -> LUSystemSolutionResult:
    """Factoriza A y resuelve Ax = b en las dos etapas Ly = b, Ux = y."""
    if A.rows != A.cols:
        raise NonSquareMatrixError(
            "La resolución en dos etapas Ly = b, Ux = y está definida para A cuadrada. "
            f"A es {A.rows}×{A.cols}."
        )
    return solve_from_factorization(lu_decompose(A), b)


def solve_many_via_lu(
    A: Matrix,
    loads: Sequence[Vector],
) -> List[LUSystemSolutionResult]:
    """Factoriza A una sola vez y resuelve Ax = b para cada vector de carga.

    Raises:
        ValueError: Si no hay ningún vector de carga.
    """
    if len(loads) == 0:
        raise ValueError("Se necesita al menos un vector de carga para reutilizar L y U.")
    factorization = lu_decompose(A)
    return [solve_from_factorization(factorization, load) for load in loads]
