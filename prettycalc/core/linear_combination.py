"""Evaluador de combinación lineal en ℝⁿ: ¿b ∈ span{v₁, …, vₖ}?

Reduce el problema a resolver A c = b, donde las columnas de A son los
vectores vⱼ. Reutiliza Gauss-Jordan y la clasificación SCD/SCI/SI del Sprint 1.

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from prettycalc.core.classifier import SystemAnalysis, SystemType, classify_system
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.vector_ops import vector_add, vector_scale


@dataclass(frozen=True)
class LinearCombinationResult:
    """Diagnóstico de si b es combinación lineal de {v₁, …, vₖ}.

    Attributes:
        is_combination: True para SCD y SCI; False para SI.
        system_type: Clasificación del sistema A c = b.
        weights: Coeficientes cᵢ (solución única o particular si SCI).
        parametric_solution: Expresión paramétrica de los pesos (SCI).
        contradiction_info: Descripción de la fila [0 … 0 | c ≠ 0] (SI).
        verification_checklist: (etiqueta, Σ cᵢ vᵢ[k], b[k], coincide).
        analysis: Análisis completo del sistema auxiliar.
        augmented_matrix: Matriz [v₁ … vₖ | b] original.
        tracer: Historial de eliminación por filas.
    """

    is_combination: bool
    system_type: SystemType
    weights: Optional[List[Fraction]]
    parametric_solution: Optional[str]
    contradiction_info: Optional[str]
    verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]
    analysis: SystemAnalysis
    augmented_matrix: Matrix
    tracer: StepTracer


def _require_homogeneous_dimension(
    vectors: Sequence[Vector],
    target: Vector,
) -> int:
    """Valida que todos los vectores y el objetivo compartan la misma dimensión n."""
    if not vectors:
        raise ValueError("Se requiere al menos un vector generador para la combinación lineal.")

    n = target.dimension
    for idx, vec in enumerate(vectors):
        if vec.dimension != n:
            raise DimensionMismatchError(
                f"El vector v{idx + 1} vive en ℝ^{vec.dimension} pero el objetivo b vive en ℝ^{n}. "
                "Todos los vectores de una combinación lineal deben pertenecer al mismo ℝⁿ.",
                left_shape=(vec.dimension,),
                right_shape=(n,),
                operation="combinación lineal",
            )
    return n


def _build_augmented_span_matrix(vectors: Sequence[Vector], target: Vector) -> Matrix:
    """Construye M = [v₁ | v₂ | … | vₖ | b] con cada vector como columna."""
    n = target.dimension
    k = len(vectors)
    data: List[List[Fraction]] = []
    for i in range(n):
        row = [vectors[j][i] for j in range(k)]
        row.append(target[i])
        data.append(row)
    return Matrix(data)


def _format_parametric_weights(analysis: SystemAnalysis) -> str:
    """Expresa cᵢ en función de las variables libres (pesos no únicos)."""
    k = analysis.num_variables
    names = [f"c{j + 1}" for j in range(k)]
    parts: List[str] = []

    for idx in range(k):
        if idx in analysis.free_variables:
            parts.append(f"{names[idx]} libre")
            continue
        if analysis.parametric_solutions and idx in analysis.parametric_solutions:
            expr = analysis.parametric_solutions[idx].to_string(var_names=names)
            parts.append(f"{names[idx]} = {expr}")
    return "; ".join(parts)


def _verify_combination(
    vectors: Sequence[Vector],
    target: Vector,
    weights: Sequence[Fraction],
) -> List[Tuple[str, Fraction, Fraction, bool]]:
    """Comprueba componente a componente que Σ cᵢ vᵢ = b."""
    reconstructed = Vector.zeros(target.dimension)
    for coeff, vec in zip(weights, vectors):
        reconstructed = vector_add(reconstructed, vector_scale(vec, coeff))

    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    for i in range(target.dimension):
        computed = reconstructed[i]
        expected = target[i]
        label = f"componente {i + 1}"
        checklist.append((label, computed, expected, computed == expected))
    return checklist


def evaluate_linear_combination(
    vectors: Sequence[Vector],
    target: Vector,
) -> LinearCombinationResult:
    """Determina si `target` es combinación lineal de `vectors`.

    Construye el sistema A c = b (columnas de A = vⱼ), lo reduce a RREF y
    clasifica:

    - SCD: combinación única, pesos cᵢ determinados.
    - SCI: infinitas combinaciones, solución paramétrica.
    - SI: b no pertenece al subespacio generado (contradicción).
    """
    _require_homogeneous_dimension(vectors, target)
    augmented = _build_augmented_span_matrix(vectors, target)
    split_col = len(vectors)

    _, tracer = gauss_jordan_elimination(augmented, split_col=split_col)
    analysis = classify_system(augmented, split_col=split_col)

    if analysis.system_type == SystemType.INCONSISTENT:
        inc_row = (analysis.inconsistent_row + 1) if analysis.inconsistent_row is not None else "?"
        contradiction = (
            f"No es combinación lineal. El sistema A c = b es inconsistente: "
            f"aparece la fila contradictoria [0 … 0 | c ≠ 0] en la fila {inc_row}. "
            f"{analysis.summary_message}"
        )
        return LinearCombinationResult(
            is_combination=False,
            system_type=analysis.system_type,
            weights=None,
            parametric_solution=None,
            contradiction_info=contradiction,
            verification_checklist=[],
            analysis=analysis,
            augmented_matrix=augmented,
            tracer=tracer,
        )

    weights = list(analysis.unique_solution) if analysis.unique_solution is not None else None
    parametric: Optional[str] = None
    if analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
        parametric = _format_parametric_weights(analysis)

    checklist: List[Tuple[str, Fraction, Fraction, bool]] = []
    if weights is not None:
        checklist = _verify_combination(vectors, target, weights)

    return LinearCombinationResult(
        is_combination=True,
        system_type=analysis.system_type,
        weights=weights,
        parametric_solution=parametric,
        contradiction_info=None,
        verification_checklist=checklist,
        analysis=analysis,
        augmented_matrix=augmented,
        tracer=tracer,
    )


def format_combination_equation(
    vectors: Sequence[Vector],
    weights: Sequence[Fraction],
) -> str:
    """Texto Σ cᵢ vᵢ con los pesos calculados."""
    terms: List[str] = []
    for idx, coeff in enumerate(weights):
        c_str = format_scalar(coeff, mode="fraction")
        terms.append(f"({c_str})·v{idx + 1}")
    return " + ".join(terms) if terms else "0"
