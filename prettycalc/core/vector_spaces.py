"""Espacios Vectoriales: conjuntos generadores, bases y dimensión.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.

Implementa dos algoritmos sobre subespacios de ℝⁿ mediante reducción
de Gauss-Jordan (RREF) con aritmética exacta:

  1. check_generating_set(A):
       Los vectores columna de A generan ℝᵐ  ↔  rango(A) = m.
  2. compute_subspace_basis(A):
       La solución de Ax = 0 (espacio nulo de A) da la base de un
       subespacio definido por ecuaciones homogéneas.

Restricciones:
  - Aritmética 100 % exacta con fractions.Fraction.
  - PROHIBIDO importar NumPy, SciPy o cualquier módulo de prettycalc.ui.

En resumen:
matemática exacta sin librerías externas. Este archivo tiene solo dos funciones centrales: una que usa Gauss-Jordan
 para ver si el rango alcanza a generar todo el espacio, y otra que resuelve el sistema homogéneo 
 (Ax=0) para extraer los vectores de la base de un subespacio.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List

from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import Matrix, Vector, format_scalar


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GeneratingSetResult:
    """Resultado de verificar si un conjunto de vectores genera ℝᵐ.

    Attributes:
        rref: Forma escalonada reducida por filas (RREF) de la matriz A
              cuyos vectores columna son los vectores del conjunto.
        pivot_cols: Índices (0-based) de las columnas con pivote principal.
        rank: Rango de A = número de columnas pivote.
        n_rows: Dimensión del espacio ℝᵐ (número de filas de A / codominio).
        n_cols: Número de vectores en el conjunto (número de columnas de A).
        generates: True si rango == n_rows (el conjunto genera ℝᵐ).
        tracer: StepTracer con cada transformación elemental de la RREF.
    """
    rref: Matrix
    pivot_cols: List[int]
    rank: int
    n_rows: int
    n_cols: int
    generates: bool
    tracer: StepTracer


@dataclass(frozen=True)
class SubspaceBasisResult:
    """Resultado de encontrar la base de un subespacio definido por Ax = 0.

    Attributes:
        rref: RREF del sistema homogéneo A (coeficientes de las ecuaciones).
        pivot_cols: Índices (0-based) de las columnas con pivote principal.
        free_cols: Índices (0-based) de las columnas sin pivote (variables libres).
        basis: Vectores base del espacio nulo (subespacio solución de Ax = 0).
        dimension: Dimensión del subespacio = nulidad = len(free_cols).
        n_vars: Número de variables / dimensión del espacio ambiente (A.cols).
        tracer: StepTracer con cada transformación elemental de la RREF.
    """
    rref: Matrix
    pivot_cols: List[int]
    free_cols: List[int]
    basis: List[Vector]
    dimension: int
    n_vars: int
    tracer: StepTracer


# ---------------------------------------------------------------------------
# Helpers internos (idénticos a los de linear_transformations.py)
# ---------------------------------------------------------------------------

def _find_pivot_cols(rref: Matrix) -> List[int]:
    """Devuelve los índices de columnas con pivote principal en la RREF.

    El pivote de una fila es la primera entrada ≠ 0 de esa fila.
    Las filas completamente nulas no producen pivote.
    """
    pivots: List[int] = []
    zero = Fraction(0)
    for r in range(rref.rows):
        for c in range(rref.cols):
            val = rref.get(r, c)
            if val != zero:
                if c not in pivots:
                    pivots.append(c)
                break
    return sorted(pivots)


def _build_null_basis(
    rref: Matrix,
    pivot_cols: List[int],
    free_cols: List[int],
) -> List[Vector]:
    """Construye una base del espacio nulo a partir de la RREF de A.

    Algoritmo de parametrización:
    Para cada variable libre x_j (índice en ``free_cols``):
      1. Fija x_j = 1; el resto de las variables libres = 0.
      2. Cada variable básica x_p (pivote en columna p, fila r de la RREF)
         se obtiene:  x_p = -RREF[r, j]  (puesto que RREF[r,p]=1 y solo x_j=1)
      3. El vector resultante pertenece al espacio nulo y es linealmente
         independiente del resto de vectores de la base.

    Si no hay variables libres (espacio nulo trivial), retorna [].
    """
    n = rref.cols
    zero = Fraction(0)

    # Mapa: columna_pivote → fila donde aparece ese pivote
    pivot_row_of: Dict[int, int] = {}
    for r, pc in enumerate(pivot_cols):
        if r < rref.rows:
            pivot_row_of[pc] = r

    basis: List[Vector] = []

    for free_col in free_cols:
        components: List[Fraction] = [zero] * n
        components[free_col] = Fraction(1)

        # Expresar cada variable básica en función de x_{free_col} = 1
        for pc in pivot_cols:
            r = pivot_row_of.get(pc)
            if r is None:
                continue
            # Fila de la RREF: 1·x_pc + Σ_{libre k} RREF[r,k]·x_k = 0
            # Con x_{free_col}=1 y el resto de libres=0:
            #   x_pc = -RREF[r, free_col]
            components[pc] = -rref.get(r, free_col)

        basis.append(Vector(components))

    return basis


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------

def check_generating_set(A: Matrix) -> GeneratingSetResult:
    """Determina si los vectores columna de A generan ℝᵐ (m = A.rows).

    Algoritmo:
      1. Los vectores v₁, …, vₖ se interpretan como columnas de A (m × k).
      2. Reducción Gauss-Jordan de A → RREF.
      3. Cuenta columnas pivote → rango r.
      4. El conjunto genera ℝᵐ  ↔  r = m  (ninguna fila de la RREF es nula).

    Args:
        A: Matriz m × k cuyas columnas son los vectores del conjunto generador.

    Returns:
        ``GeneratingSetResult`` con RREF, pivotes, rango y booleano de si
        el conjunto genera ℝᵐ.
    """
    tracer = StepTracer(split_col=None)
    rref, tracer = gauss_jordan_elimination(
        A,
        split_col=A.cols,
        tracer=tracer,
        initial_description=(
            f"Vectores como columnas de A ({A.rows}×{A.cols}). "
            "Aplicamos Gauss-Jordan para obtener la RREF y determinar el rango."
        ),
        initial_latex=r"\text{Reducción de } A \text{ a RREF — Conjunto Generador}",
    )

    pivot_cols = _find_pivot_cols(rref)
    rank = len(pivot_cols)
    generates = (rank == A.rows)

    return GeneratingSetResult(
        rref=rref,
        pivot_cols=pivot_cols,
        rank=rank,
        n_rows=A.rows,
        n_cols=A.cols,
        generates=generates,
        tracer=tracer,
    )


def compute_subspace_basis(A: Matrix) -> SubspaceBasisResult:
    """Encuentra la base del subespacio solución de Ax = 0 (espacio nulo de A).

    Algoritmo:
      1. Las filas de A son los coeficientes de las ecuaciones homogéneas.
      2. Reducción Gauss-Jordan de A → RREF.
      3. Columnas pivote → variables básicas; columnas libres → variables libres.
      4. Parametrización estándar → vectores base del espacio nulo.

    El subespacio resultante es el espacio nulo (Ker A) cuya dimensión es la
    nulidad de A:  dim(Ker A) = n − rango(A).

    Args:
        A: Matriz m × n de coeficientes del sistema homogéneo (una ecuación
           por fila, n incógnitas).

    Returns:
        ``SubspaceBasisResult`` con la base del espacio nulo, su dimensión,
        pivotes/variables libres y el tracer de pasos.
    """
    tracer = StepTracer(split_col=None)
    rref, tracer = gauss_jordan_elimination(
        A,
        split_col=A.cols,
        tracer=tracer,
        initial_description=(
            f"Sistema homogéneo Ax = 0 con A de tamaño {A.rows}×{A.cols}. "
            "Reducimos A a RREF para identificar variables libres y construir "
            "la base del subespacio solución."
        ),
        initial_latex=r"\text{Reducción de } A \text{ a RREF (sistema homogéneo } Ax=0\text{)}",
    )

    pivot_cols = _find_pivot_cols(rref)
    free_cols = [c for c in range(A.cols) if c not in pivot_cols]
    basis = _build_null_basis(rref, pivot_cols, free_cols)
    dimension = len(free_cols)

    return SubspaceBasisResult(
        rref=rref,
        pivot_cols=pivot_cols,
        free_cols=free_cols,
        basis=basis,
        dimension=dimension,
        n_vars=A.cols,
        tracer=tracer,
    )


# ---------------------------------------------------------------------------
# Utilidades de formato (texto plano, sin UI)
# ---------------------------------------------------------------------------

def format_basis_vectors(vectors: List[Vector], name: str = "v") -> str:
    """Representa una lista de vectores base como { v₁, v₂, … } en texto plano."""
    if not vectors:
        return "{0}  (sólo el vector cero — subespacio trivial)"
    parts = []
    for k, vec in enumerate(vectors, start=1):
        comps = ", ".join(format_scalar(c, mode="fraction") for c in vec.components)
        parts.append(f"{name}{k} = [{comps}]ᵀ")
    return "{ " + ",  ".join(parts) + " }"


def generating_summary(result: GeneratingSetResult) -> str:
    """Resumen en texto plano del resultado del conjunto generador."""
    status = "GENERA" if result.generates else "NO GENERA"
    return (
        f"Rango = {result.rank}  /  dim(ℝᵐ) = {result.n_rows}  →  "
        f"El conjunto {status} ℝ^{result.n_rows}."
    )


def subspace_summary(result: SubspaceBasisResult) -> str:
    """Resumen en texto plano de la base del subespacio."""
    if result.dimension == 0:
        return "El subespacio es {0} — la única solución de Ax=0 es el vector cero."
    base_str = format_basis_vectors(result.basis, name="b")
    return (
        f"Dimensión = {result.dimension},  base = {base_str}"
    )

