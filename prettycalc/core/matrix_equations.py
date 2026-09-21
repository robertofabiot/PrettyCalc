"""Resolución y comprobación de ecuaciones matriciales A x = b.

Conecta formalmente la eliminación por filas de [A | b] con la verificación
del producto matricial A · x ≟ b.

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Tuple

from prettycalc.core.classifier import SystemAnalysis, SystemType, classify_system
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.matrix_ops import matrix_multiply
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


@dataclass(frozen=True)
class MatrixEquationResult:
    """Resultado de resolver A x = b y comprobar A · x = b.

    Attributes:
        analysis: Clasificación SCD / SCI / SI del sistema.
        solution: Vector x (único o particular si hay variables libres).
        product_Ax: Producto A · x reconstruido, si hay solución.
        product_matches: True si A · x coincide exactamente con b.
        verification_checklist: (etiqueta, (A x)_i, b_i, coincide).
        augmented_matrix: [A | b] original.
        tracer: Historial de Gauss-Jordan.
        parametric_solution: Texto de la solución general (SCI).
    """

    analysis: SystemAnalysis
    solution: Optional[Vector]
    product_Ax: Optional[Vector]
    product_matches: bool
    verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]
    augmented_matrix: Matrix
    tracer: StepTracer
    parametric_solution: Optional[str]


def _format_parametric_x(analysis: SystemAnalysis) -> str:
    """Solución general x en función de las variables libres."""
    n = analysis.num_variables
    names = [f"x{j + 1}" for j in range(n)]
    parts: List[str] = []
    for idx in range(n):
        if idx in analysis.free_variables:
            parts.append(f"{names[idx]} libre")
            continue
        if analysis.parametric_solutions and idx in analysis.parametric_solutions:
            expr = analysis.parametric_solutions[idx].to_string(var_names=names)
            parts.append(f"{names[idx]} = {expr}")
    return "; ".join(parts)


def _verify_product(A: Matrix, x: Vector, b: Vector) -> Tuple[Vector, List[Tuple[str, Fraction, Fraction, bool]], bool]:
    """Calcula A · x y compara componente a componente con b."""
    product_matrix = matrix_multiply(A, x.to_column_matrix())
    product = Vector.from_column_matrix(product_matrix)
    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    all_match = True
    for i in range(b.dimension):
        computed = product[i]
        expected = b[i]
        matches = computed == expected
        all_match = all_match and matches
        checklist.append((f"componente {i + 1}", computed, expected, matches))
    return product, checklist, all_match


def solve_matrix_equation(A: Matrix, b: Vector) -> MatrixEquationResult:
    """Resuelve A x = b por eliminación de Gauss-Jordan y verifica A · x = b.

    Conformabilidad: A debe tener tantas filas como componentes de b
    (A ∈ M_{m×n}, x ∈ ℝⁿ, b ∈ ℝᵐ).

    Raises:
        DimensionMismatchError: Si A.rows ≠ dim(b).
    """
    if A.rows != b.dimension:
        raise DimensionMismatchError(
            f"La ecuación A x = b no es conformable: A es {A.rows}×{A.cols} "
            f"y b ∈ ℝ^{b.dimension}. Se requiere dim(b) = filas de A (= {A.rows}).",
            left_shape=A.shape,
            right_shape=(b.dimension,),
            operation="ecuación matricial A x = b",
        )

    augmented = A.augment(b.to_list())
    split_col = A.cols
    _, tracer = gauss_jordan_elimination(augmented, split_col=split_col)
    analysis = classify_system(augmented, split_col=split_col)

    if analysis.system_type == SystemType.INCONSISTENT or analysis.unique_solution is None:
        return MatrixEquationResult(
            analysis=analysis,
            solution=None,
            product_Ax=None,
            product_matches=False,
            verification_checklist=[],
            augmented_matrix=augmented,
            tracer=tracer,
            parametric_solution=None,
        )

    solution = Vector(analysis.unique_solution)
    product, checklist, matches = _verify_product(A, solution, b)
    parametric = None
    if analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
        parametric = _format_parametric_x(analysis)

    return MatrixEquationResult(
        analysis=analysis,
        solution=solution,
        product_Ax=product,
        product_matches=matches,
        verification_checklist=checklist,
        augmented_matrix=augmented,
        tracer=tracer,
        parametric_solution=parametric,
    )


def format_equation_summary(A: Matrix, b: Vector) -> str:
    """Etiqueta dimensional de A x = b para la UI."""
    return (
        f"A_{{{A.rows}×{A.cols}}} · x_{{{A.cols}×1}} = b_{{{b.dimension}×1}}"
    )
