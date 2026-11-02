"""Transformaciones lineales T: ℝⁿ → ℝᵐ  —  evaluación, núcleo, imagen y rango.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.

Reutiliza exclusivamente módulos existentes del core:
  - matrix_vector_ops.py  (producto A · v con detalle pedagógico)
  - elimination.py        (Gauss-Jordan para obtener la RREF de A)
  - tracer.py             (registro de pasos para la UI)
  - types.py              (Matrix, Vector, format_scalar)

Restricciones:
  - Aritmética 100 % exacta con fractions.Fraction.
  - PROHIBIDO importar NumPy, SciPy o cualquier módulo de prettycalc.ui.

  
En Resumen:
 En este archivo importamos fracciones exactas y nuestro módulo de Gauss-Jordan.
 Aquí hacemos todo el trabajo matemático duro de forma aislada: evaluamos el vector resultante 
 T(v) y reducimos la matriz para extraer los pivotes y las variables libres, armando así las bases del Núcleo y la Imagen.

"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Tuple

from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.matrix_vector_ops import matrix_vector_multiply_with_details
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import Matrix, Vector, format_scalar


# ---------------------------------------------------------------------------
# Dataclass de resultado
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LinearTransformResult:
    """Resultado completo del análisis de la transformación lineal T(x) = A · x.

    Attributes:
        rref: Forma escalonada reducida por filas (RREF) de A.
        pivot_cols: Índices (0-based) de las columnas con pivote principal.
        free_cols: Índices (0-based) de las columnas sin pivote (variables libres).
        kernel_basis: Base del Núcleo de T  [nu(T)].  Lista vacía si T es inyectiva.
        image_basis: Base de la Imagen de T  [im(T)].  Lista vacía sólo si A = 0.
        rank: Rango de T = número de columnas pivote = dim(im T).
        nullity: Nulidad de T = número de variables libres = dim(nu T).
        domain_dim: Dimensión del dominio  (n = A.cols).
        codomain_dim: Dimensión del codominio  (m = A.rows).
        theorem_holds: True si rank + nullity == domain_dim (Teorema de la Dimensión).
        tracer: StepTracer con cada transformación elemental de la RREF.
    """

    rref: Matrix
    pivot_cols: List[int]
    free_cols: List[int]
    kernel_basis: List[Vector]
    image_basis: List[Vector]
    rank: int
    nullity: int
    domain_dim: int
    codomain_dim: int
    theorem_holds: bool
    tracer: StepTracer


# ---------------------------------------------------------------------------
# Evaluación de T(v)
# ---------------------------------------------------------------------------

def evaluate_transform(
    A: Matrix,
    v: Vector,
) -> Tuple[Vector, List[str]]:
    """Evalúa T(v) = A · v y devuelve el vector imagen con detalle pedagógico.

    Delega en ``matrix_vector_multiply_with_details`` del módulo existente
    ``matrix_vector_ops``, sin duplicar lógica.

    Args:
        A: Matriz de transformación de tamaño m × n.
        v: Vector de entrada en ℝⁿ.

    Returns:
        (Tv, steps) donde ``Tv`` ∈ ℝᵐ es la imagen y ``steps`` es la lista de
        cadenas que explican el cálculo fila a fila.

    Raises:
        DimensionMismatchError: Si A.cols ≠ dim(v).
    """
    return matrix_vector_multiply_with_details(A, v, vector_name="v")


# ---------------------------------------------------------------------------
# Helpers internos
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
                if c not in pivots:          # evita duplicados por robustez
                    pivots.append(c)
                break
    return sorted(pivots)


def _build_kernel_basis(
    rref: Matrix,
    pivot_cols: List[int],
    free_cols: List[int],
) -> List[Vector]:
    """Construye una base del Núcleo a partir de la RREF de A.

    Algoritmo estándar de expresión paramétrica:
    Para cada variable libre x_j (índice en ``free_cols``):
      1. Fija x_j = 1; el resto de las variables libres = 0.
      2. Cada variable básica x_{p} (pivote en columna p, fila r de la RREF)
         se obtiene despejando la única incógnita no libre de la fila r:
             x_p = -RREF[r, j]  (puesto que solo x_j = 1)
      3. El vector resultante pertenece a nu(T) y es linealmente independiente
         del resto de vectores de la base.

    Si no hay variables libres (núcleo trivial), retorna [].
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


def _build_image_basis(A: Matrix, pivot_cols: List[int]) -> List[Vector]:
    """Base de la Imagen: columnas originales de A en las posiciones pivote.

    Teorema: Las columnas de A que corresponden a columnas pivote de su RREF
    forman una base de im(T).
    """
    basis: List[Vector] = []
    for pc in pivot_cols:
        col_components = [A.get(r, pc) for r in range(A.rows)]
        basis.append(Vector(col_components))
    return basis


# ---------------------------------------------------------------------------
# Análisis completo
# ---------------------------------------------------------------------------

def compute_kernel_and_image(A: Matrix) -> LinearTransformResult:
    """Analiza completamente la transformación lineal T(x) = A · x.

    Pasos del algoritmo:
      1. Aplica Gauss-Jordan a A (toda la matriz, sin columna b) para obtener
         la RREF, registrando cada operación elemental en un ``StepTracer``.
      2. Detecta columnas pivote → base de im(T) (columnas originales de A).
      3. Detecta columnas libres → base de nu(T) (vectores paramétricos).
      4. Calcula rango = |pivot_cols| y nulidad = |free_cols|.
      5. Verifica el Teorema de la Dimensión: rank + nullity = n = dim(dominio).

    Args:
        A: Matriz de la transformación de tamaño m × n (m, n ≥ 1).

    Returns:
        ``LinearTransformResult`` con todos los datos del análisis.
    """
    n = A.cols   # dimensión del dominio ℝⁿ
    m = A.rows   # dimensión del codominio ℝᵐ

    tracer = StepTracer(split_col=None)

    # Reducción Gauss-Jordan de A (sin columna aumentada)
    # split_col = A.cols trata toda la matriz como bloque de coeficientes
    rref, tracer = gauss_jordan_elimination(
        A,
        split_col=A.cols,
        tracer=tracer,
        initial_description=(
            "Matriz de transformación A. "
            "Aplicamos Gauss-Jordan para obtener la RREF "
            "y determinar el núcleo y la imagen de T."
        ),
        initial_latex=r"\text{Reducción de } A \text{ a RREF (Gauss-Jordan)}",
    )

    pivot_cols = _find_pivot_cols(rref)
    free_cols = [c for c in range(n) if c not in pivot_cols]

    rank = len(pivot_cols)
    nullity = len(free_cols)
    theorem_holds = (rank + nullity == n)

    kernel_basis = _build_kernel_basis(rref, pivot_cols, free_cols)
    image_basis = _build_image_basis(A, pivot_cols)

    return LinearTransformResult(
        rref=rref,
        pivot_cols=pivot_cols,
        free_cols=free_cols,
        kernel_basis=kernel_basis,
        image_basis=image_basis,
        rank=rank,
        nullity=nullity,
        domain_dim=n,
        codomain_dim=m,
        theorem_holds=theorem_holds,
        tracer=tracer,
    )


# ---------------------------------------------------------------------------
# Utilidades de formato (texto plano, sin UI)
# ---------------------------------------------------------------------------

def format_vector_set(vectors: List[Vector], name: str = "v") -> str:
    """Representa una lista de vectores como  { v₁, v₂, … } en texto plano."""
    if not vectors:
        return "{0}  (sólo el vector cero)"
    parts = []
    for k, vec in enumerate(vectors, start=1):
        comps = ", ".join(format_scalar(c, mode="fraction") for c in vec.components)
        parts.append(f"{name}{k} = [{comps}]ᵀ")
    return "{ " + ",  ".join(parts) + " }"


def kernel_summary(result: LinearTransformResult) -> str:
    """Resumen en texto plano del núcleo de T."""
    if result.nullity == 0:
        return "nu(T) = {0}  —  T es inyectiva (núcleo trivial)."
    base_str = format_vector_set(result.kernel_basis, name="n")
    return f"nu(T): nulidad = {result.nullity},  base = {base_str}"


def image_summary(result: LinearTransformResult) -> str:
    """Resumen en texto plano de la imagen de T."""
    base_str = format_vector_set(result.image_basis, name="c")
    return f"im(T): rango = {result.rank},  base = {base_str}"


def theorem_summary(result: LinearTransformResult) -> str:
    """Frase que verifica el Teorema del Rango-Nulidad."""
    check = "✓ CUMPLE" if result.theorem_holds else "✗ ERROR"
    return (
        f"Teorema de la Dimensión  {check}:  "
        f"dim(dominio) = nulidad + rango  →  "
        f"{result.domain_dim} = {result.nullity} + {result.rank}"
    )

