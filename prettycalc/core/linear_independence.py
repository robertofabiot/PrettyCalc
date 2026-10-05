"""Evaluador del núcleo de Independencia y Dependencia Lineal en ℝⁿ.

100% Python estándar. Aritmética exacta con `fractions.Fraction`.
Cero dependencias externas (sin NumPy, SciPy o SymPy).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from prettycalc.core.elimination import (
    gauss_jordan_elimination,
    gaussian_elimination,
)
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    Vector,
    format_scalar,
)


@dataclass(frozen=True)
class LinearIndependenceResult:
    """Diagnóstico exhaustivo de Independencia / Dependencia Lineal en ℝⁿ.

    Attributes:
        vectors: Conjunto de vectores analizados {v₁, …, vₖ}.
        k: Cantidad de vectores en el conjunto.
        n: Dimensión del espacio euclidiano ℝⁿ.
        is_linearly_independent: True si es L.I., False si es L.D.
        num_pivots: Número de posiciones pivote (rango de la matriz columna A).
        pivots: Lista de coordenadas (fila, columna) de los pivotes en la matriz REF.
        basic_variables: Índices (0-indexed) de las columnas con pivote (variables básicas).
        free_variables: Índices (0-indexed) de las columnas sin pivote (variables libres).
        augmented_matrix: Matriz aumentada inicial [A | 0] del sistema homogéneo A·c = 0.
        ref_matrix: Matriz en Forma Escalonada por Filas (REF).
        rref_matrix: Matriz en Forma Escalonada Reducida por Filas (RREF).
        tracer: Historial de operaciones elementales de fila en la eliminación gaussiana.
        theorem_k_greater_n: True si k > n (por teorema de dimensión, necesariamente L.D.).
        zero_vector_index: Índice del vector nulo 0 si está presente en el conjunto.
        nontrivial_weights: Coeficientes cᵢ no todos nulos tales que Σ cᵢ vᵢ = 0 (cuando es L.D.).
        verification_checklist: Lista de tuplas (dim_etiqueta, valor_calculado, coincide_cero).
    """

    vectors: Sequence[Vector]
    k: int
    n: int
    is_linearly_independent: bool
    num_pivots: int
    pivots: List[Tuple[int, int]]
    basic_variables: List[int]
    free_variables: List[int]
    augmented_matrix: Matrix
    ref_matrix: Matrix
    rref_matrix: Matrix
    tracer: StepTracer
    theorem_k_greater_n: bool
    zero_vector_index: Optional[int]
    nontrivial_weights: Optional[List[Fraction]]
    verification_checklist: List[Tuple[str, Fraction, bool]]


def _require_homogeneous_vectors(vectors: Sequence[Vector]) -> int:
    """Valida que el conjunto no esté vacío y que todos los vectores pertenezcan al mismo ℝⁿ."""
    if not vectors:
        raise ValueError("Se requiere al menos un vector para evaluar la independencia lineal.")

    n = vectors[0].dimension
    for idx, vec in enumerate(vectors[1:], start=1):
        if vec.dimension != n:
            raise DimensionMismatchError(
                f"El vector v{idx + 1} vive en ℝ^{vec.dimension} pero v1 vive en ℝ^{n}. "
                "Todos los vectores deben pertenecer al mismo espacio ℝⁿ.",
                left_shape=(vec.dimension,),
                right_shape=(n,),
                operation="evaluación de independencia lineal",
            )
    return n


def _build_augmented_homogeneous_matrix(vectors: Sequence[Vector], dim_n: int) -> Matrix:
    """Construye [A | 0] con vectores como columnas y la columna aumentada en cero."""
    k = len(vectors)
    data: List[List[Fraction]] = []
    zero = Fraction(0, 1)
    for i in range(dim_n):
        row = [vectors[j][i] for j in range(k)]
        row.append(zero)
        data.append(row)
    return Matrix(data)


def evaluate_linear_independence(vectors: Sequence[Vector]) -> LinearIndependenceResult:
    """Evalúa algebraicamente si un conjunto de vectores en ℝⁿ es L.I. o L.D.

    Algoritmo:
        1. Modela la ecuación homogénea c₁·v₁ + … + cₖ·vₖ = 0 como el sistema A·c = 0.
        2. Construye la matriz aumentada [A | 0] donde cada columna j es el vector vⱼ.
        3. Aplica eliminación gaussiana por filas para obtener la Forma Escalonada por Filas (REF).
        4. Identifica las posiciones pivote r = rango(A) y cuenta las variables libres (k - r).
        5. Criterio de decisión:
           - Si r == k: No hay variables libres → Solución única trivial (c = 0) → L.I.
           - Si r < k: Hay al menos una variable libre → Infinitas soluciones no triviales → L.D.
        6. Si el conjunto es L.D., calcula una combinación no trivial c ≠ 0 mediante Gauss-Jordan.

    Args:
        vectors: Colección de vectores columna en ℝⁿ.

    Returns:
        LinearIndependenceResult con todo el diagnóstico algebraico y trazabilidad paso a paso.
    """
    n = _require_homogeneous_vectors(vectors)
    k = len(vectors)

    # 1. Comprobaciones teóricas preliminares
    zero_idx: Optional[int] = None
    for idx, v in enumerate(vectors):
        if all(comp == Fraction(0, 1) for comp in v):
            zero_idx = idx
            break

    theorem_k_greater_n = (k > n)

    # 2. Construcción del sistema homogéneo [A | 0]
    aug = _build_augmented_homogeneous_matrix(vectors, n)

    # 3. Reducción por filas a Forma Escalonada por Filas (REF) con StepTracer
    tracer = StepTracer(split_col=k)
    ref_mat, tracer = gaussian_elimination(aug, split_col=k, tracer=tracer)

    # 4. Identificación de pivotes en la matriz de coeficientes A
    num_rows, num_cols = ref_mat.shape
    pivots: List[Tuple[int, int]] = []
    curr_col = 0
    for r in range(num_rows):
        while curr_col < k:
            if ref_mat.get(r, curr_col) != Fraction(0, 1):
                pivots.append((r, curr_col))
                curr_col += 1
                break
            curr_col += 1

    num_pivots = len(pivots)
    basic_vars = [c for _, c in pivots]
    basic_set = set(basic_vars)
    free_vars = [c for c in range(k) if c not in basic_set]

    is_li = (num_pivots == k)

    # 5. Obtención de RREF y solución no trivial si es L.D.
    rref_tracer = StepTracer(split_col=k)
    rref_mat, _ = gauss_jordan_elimination(aug, split_col=k, tracer=rref_tracer)

    nontrivial_weights: Optional[List[Fraction]] = None
    verification: List[Tuple[str, Fraction, bool]] = []

    if not is_li and free_vars:
        target_free = free_vars[0]
        weights = [Fraction(0, 1) for _ in range(k)]
        weights[target_free] = Fraction(1, 1)

        for r_idx, piv_c in pivots:
            coeff = rref_mat.get(r_idx, target_free)
            weights[piv_c] = - coeff

        nontrivial_weights = weights

        # Verificación componente a componente
        for i in range(n):
            accum = sum(weights[j] * vectors[j][i] for j in range(k))
            verification.append((f"Fila {i + 1}", accum, accum == Fraction(0, 1)))

    return LinearIndependenceResult(
        vectors=vectors,
        k=k,
        n=n,
        is_linearly_independent=is_li,
        num_pivots=num_pivots,
        pivots=pivots,
        basic_variables=basic_vars,
        free_variables=free_vars,
        augmented_matrix=aug,
        ref_matrix=ref_mat,
        rref_matrix=rref_mat,
        tracer=tracer,
        theorem_k_greater_n=theorem_k_greater_n,
        zero_vector_index=zero_idx,
        nontrivial_weights=nontrivial_weights,
        verification_checklist=verification,
    )
