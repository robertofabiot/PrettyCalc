"""Métodos iterativos de Jacobi y Gauss-Seidel para A x = b.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM). Programa 8.

Los dos métodos parten de la descomposición A = D + L + U (diagonal, parte
estrictamente inferior y parte estrictamente superior) y despejan xᵢ de la
ecuación i:

- Jacobi:        xᵢ⁽ᵏ⁺¹⁾ = (b_i − Σ_{j≠i} a_ij xⱼ⁽ᵏ⁾) / aᵢᵢ
- Gauss-Seidel:  xᵢ⁽ᵏ⁺¹⁾ = (b_i − Σ_{j<i} a_ij xⱼ⁽ᵏ⁺¹⁾ − Σ_{j>i} a_ij xⱼ⁽ᵏ⁾) / aᵢᵢ

En forma matricial ambos son x⁽ᵏ⁺¹⁾ = T x⁽ᵏ⁾ + c, con
T_J = −D⁻¹(L + U) y T_GS = −(D + L)⁻¹ U. El método converge para cualquier
x⁽⁰⁾ si y solo si el radio espectral ρ(T) < 1. La dominancia diagonal
estricta por filas es una condición suficiente (no necesaria) para ambos, y
si A es simétrica definida positiva, Gauss-Seidel converge.

Decisiones de implementación:

- Las iteraciones se calculan con ``Fraction``, igual que el resto del motor:
  así el error que se ve es solo el del método (truncar la sucesión), nunca
  redondeo de punto flotante. La interfaz las muestra en decimales.
- El criterio de paro es ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ < ε (absoluto) o
  ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ / ‖x⁽ᵏ⁾‖∞ < ε (relativo), con un máximo de iteraciones.
- La divergencia se declara cuando ‖x⁽ᵏ⁾‖∞ supera un umbral grande, o al
  agotar las iteraciones si ρ(T) ≥ 1.
- ρ(T) se obtiene del polinomio característico exacto (Faddeev-LeVerrier),
  sin raíces repetidas (p / mcd(p, p')), y sus raíces se aproximan con
  Durand-Kerner en complejos. Sin NumPy.
"""

from __future__ import annotations

import cmath
import itertools
import math
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from prettycalc.core.classifier import classify_system
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, subscript

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


class IterativeMethod(Enum):
    JACOBI = "jacobi"
    GAUSS_SEIDEL = "gauss_seidel"

    @property
    def label(self) -> str:
        return "Jacobi" if self is IterativeMethod.JACOBI else "Gauss-Seidel"

    @property
    def matrix_symbol(self) -> str:
        return "T_J" if self is IterativeMethod.JACOBI else "T_{GS}"

    @property
    def plain_symbol(self) -> str:
        return "T_J" if self is IterativeMethod.JACOBI else "T_GS"


class StopCriterion(Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class IterationStatus(Enum):
    CONVERGED = "converged"
    DIVERGED = "diverged"
    MAX_ITERATIONS = "max_iterations"

    @property
    def label(self) -> str:
        return {
            IterationStatus.CONVERGED: "Converge",
            IterationStatus.DIVERGED: "Diverge",
            IterationStatus.MAX_ITERATIONS: "Sin converger aún",
        }[self]


class ZeroDiagonalError(ValueError):
    """Algún aᵢᵢ es 0: no se puede despejar xᵢ de la ecuación i."""

    def __init__(self, message: str, rows: Tuple[int, ...], tracer: Optional[StepTracer] = None) -> None:
        super().__init__(message)
        self.rows = rows
        self.tracer = tracer


#: Por encima de este múltiplo de la escala inicial se declara divergencia.
DIVERGENCE_FACTOR = Fraction(10) ** 8
DEFAULT_TOLERANCE = Fraction(1, 10_000)
DEFAULT_MAX_ITERATIONS = 50
MAX_ALLOWED_ITERATIONS = 200
#: Decimales con los que se escriben los valores en la explicación de cada paso.
TEXT_DIGITS = 6


@dataclass(frozen=True)
class IterationRecord:
    """Estado del método al terminar la iteración k (k = 0 es x⁽⁰⁾)."""

    k: int
    x: Tuple[Fraction, ...]
    delta_norm: Optional[Fraction]
    relative_delta: Optional[Fraction]
    residual_norm: Fraction
    error_norm: Optional[Fraction]
    component_lines: Tuple[str, ...] = ()

    @property
    def stop_measure(self) -> Optional[Fraction]:
        return self.delta_norm


@dataclass(frozen=True)
class DominanceRow:
    """Comparación |aᵢᵢ| contra Σ_{j≠i} |a_ij| en una fila."""

    row: int
    diagonal: Fraction
    off_diagonal_sum: Fraction

    @property
    def strict(self) -> bool:
        return self.diagonal > self.off_diagonal_sum

    @property
    def weak(self) -> bool:
        return self.diagonal >= self.off_diagonal_sum


@dataclass(frozen=True)
class SpectralInfo:
    """Matriz de iteración T, vector c, polinomio característico y ρ(T)."""

    method: IterativeMethod
    T: Matrix
    c: Vector
    char_poly: Tuple[Fraction, ...]
    eigenvalues: Tuple[complex, ...]
    radius: float

    @property
    def converges(self) -> bool:
        return self.radius < 1 - 1e-9

    @property
    def borderline(self) -> bool:
        return abs(self.radius - 1) <= 1e-9


@dataclass(frozen=True)
class ConvergenceAnalysis:
    """Criterios de convergencia de A para Jacobi y Gauss-Seidel."""

    A: Matrix
    rows: Tuple[DominanceRow, ...]
    zero_diagonal_rows: Tuple[int, ...]
    symmetric: bool
    leading_minors: Tuple[Fraction, ...]
    jacobi: Optional[SpectralInfo]
    gauss_seidel: Optional[SpectralInfo]

    @property
    def strictly_dominant(self) -> bool:
        return all(row.strict for row in self.rows)

    @property
    def positive_definite(self) -> bool:
        return self.symmetric and all(minor > 0 for minor in self.leading_minors)

    def spectral(self, method: IterativeMethod) -> Optional[SpectralInfo]:
        return self.jacobi if method is IterativeMethod.JACOBI else self.gauss_seidel

    def predicts_convergence(self, method: IterativeMethod) -> Optional[bool]:
        info = self.spectral(method)
        return None if info is None else info.converges

    def verdict(self, method: IterativeMethod) -> str:
        """Conclusión en una frase para el método dado."""
        if self.zero_diagonal_rows:
            rows = ", ".join(str(r + 1) for r in self.zero_diagonal_rows)
            return f"No aplicable: aᵢᵢ = 0 en la fila {rows}. Reordena las filas."
        info = self.spectral(method)
        assert info is not None
        rho = f"ρ({method.plain_symbol}) ≈ {format_decimal(Fraction(info.radius), 4)}"
        if info.converges:
            reason = []
            if self.strictly_dominant:
                reason.append("A es estrictamente diagonal dominante")
            if method is IterativeMethod.GAUSS_SEIDEL and self.positive_definite:
                reason.append("A es simétrica definida positiva")
            extra = f" ({'; '.join(reason)})" if reason else ""
            return f"Converge: {rho} < 1{extra}."
        if info.borderline:
            return f"No se garantiza: {rho} = 1."
        return f"Diverge: {rho} > 1."


@dataclass(frozen=True)
class IterativeResult:
    """Sucesión x⁽⁰⁾, x⁽¹⁾, … de un método, su estado final y su traza."""

    method: IterativeMethod
    A: Matrix
    b: Vector
    x0: Vector
    tolerance: Fraction
    max_iterations: int
    criterion: StopCriterion
    iterations: Tuple[IterationRecord, ...]
    status: IterationStatus
    exact_solution: Optional[Vector]
    analysis: ConvergenceAnalysis
    tracer: StepTracer
    summary: str

    @property
    def approximation(self) -> Vector:
        return Vector(list(self.iterations[-1].x))

    @property
    def iteration_count(self) -> int:
        return self.iterations[-1].k

    @property
    def converged(self) -> bool:
        return self.status is IterationStatus.CONVERGED

    @property
    def final_error(self) -> Optional[Fraction]:
        return self.iterations[-1].error_norm

    @property
    def final_residual(self) -> Fraction:
        return self.iterations[-1].residual_norm


@dataclass(frozen=True)
class MethodComparison:
    """Jacobi y Gauss-Seidel sobre el mismo sistema, con la misma x⁽⁰⁾ y ε."""

    jacobi: IterativeResult
    gauss_seidel: IterativeResult
    summary: str = field(default="")


@dataclass(frozen=True)
class RowReordering:
    """Permutación de filas de [A | b] que busca la dominancia diagonal."""

    permutation: Tuple[int, ...]
    A: Matrix
    b: Vector
    strictly_dominant: bool
    changed: bool
    explanation: str


# ---------------------------------------------------------------------------
# Formato
# ---------------------------------------------------------------------------

_SUPERSCRIPT = str.maketrans("0123456789+-k()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ᵏ⁽⁾")


def superscript_iter(k: int | str) -> str:
    """Superíndice de iteración de libro: 3 → ⁽³⁾."""
    return f"({k})".translate(_SUPERSCRIPT)


def var(index: int, k: int | str | None = None) -> str:
    """x₁, o x₁⁽³⁾ si se indica la iteración."""
    base = f"x{subscript(index + 1)}"
    return base if k is None else base + superscript_iter(k)


def format_decimal(value: Fraction, digits: int = TEXT_DIGITS, *, fixed: bool = False) -> str:
    """Decimal de libro con signo «−». Notación científica para magnitudes extremas."""
    if value == 0:
        return "0" if not fixed else f"{0:.{digits}f}"
    if value.denominator == 1 and abs(value) < 10**7 and not fixed:
        return str(value.numerator).replace("-", "−")
    magnitude = abs(value)
    if magnitude >= 10**7 or magnitude < Fraction(1, 10**digits) / 2:
        text = f"{float(value):.3e}"
        mantissa, exponent = text.split("e")
        exp = int(exponent)
        return f"{mantissa}×10{str(exp).translate(_SUPERSCRIPT)}".replace("-", "−")
    text = f"{float(value):.{digits}f}"
    if not fixed:
        text = text.rstrip("0").rstrip(".")
    return text.replace("-", "−")


def format_vector(values: Sequence[Fraction], digits: int = TEXT_DIGITS) -> str:
    return "(" + ", ".join(format_decimal(v, digits) for v in values) + ")"


def _show_exact(value: Fraction) -> str:
    text = str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return text.replace("-", "−")


def _paren(value: Fraction, digits: int = TEXT_DIGITS) -> str:
    text = format_decimal(value, digits)
    return f"({text})" if value < 0 else text


# ---------------------------------------------------------------------------
# Álgebra auxiliar exacta
# ---------------------------------------------------------------------------


def _inf_norm(values: Sequence[Fraction]) -> Fraction:
    return max((abs(v) for v in values), default=Fraction(0))


def _residual(A: Matrix, b: Vector, x: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    n = A.rows
    return tuple(b[i] - sum((A.get(i, j) * x[j] for j in range(n)), Fraction(0)) for i in range(n))


def _mat_mul(left: List[List[Fraction]], right: List[List[Fraction]]) -> List[List[Fraction]]:
    n = len(left)
    m = len(right[0])
    inner = len(right)
    return [
        [sum((left[i][k] * right[k][j] for k in range(inner)), Fraction(0)) for j in range(m)]
        for i in range(n)
    ]


def _determinant(rows: List[List[Fraction]]) -> Fraction:
    work = [list(r) for r in rows]
    n = len(work)
    det = Fraction(1)
    for col in range(n):
        pivot = next((r for r in range(col, n) if work[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            work[col], work[pivot] = work[pivot], work[col]
            det = -det
        det *= work[col][col]
        for r in range(col + 1, n):
            factor = work[r][col] / work[col][col]
            if factor:
                work[r] = [a - factor * p for a, p in zip(work[r], work[col])]
    return det


def _require_system(A: Matrix, b: Vector) -> int:
    if A.rows != A.cols:
        raise NonSquareMatrixError(
            f"Jacobi y Gauss-Seidel necesitan A cuadrada: A es {A.rows}×{A.cols}. "
            "Cada ecuación i se usa para despejar la incógnita xᵢ."
        )
    if b.dimension != A.rows:
        raise DimensionMismatchError(
            f"b debe tener {A.rows} componentes y tiene {b.dimension}.",
            left_shape=A.shape,
            right_shape=(b.dimension,),
            operation="iterar A x = b",
        )
    return A.rows


# ---------------------------------------------------------------------------
# Matrices de iteración y radio espectral
# ---------------------------------------------------------------------------


def iteration_matrix(A: Matrix, b: Vector, method: IterativeMethod) -> Tuple[Matrix, Vector]:
    """T y c tales que x⁽ᵏ⁺¹⁾ = T x⁽ᵏ⁾ + c. Exige aᵢᵢ ≠ 0."""
    n = A.rows
    a = [[A.get(i, j) for j in range(n)] for i in range(n)]
    if method is IterativeMethod.JACOBI:
        T = [[Fraction(0) if i == j else -a[i][j] / a[i][i] for j in range(n)] for i in range(n)]
        c = [b[i] / a[i][i] for i in range(n)]
        return Matrix(T), Vector(c)
    # (D + L) T = −U  y  (D + L) c = b, columna por columna, por sustitución hacia adelante.
    def forward(rhs: List[Fraction]) -> List[Fraction]:
        out: List[Fraction] = []
        for i in range(n):
            acc = rhs[i] - sum((a[i][j] * out[j] for j in range(i)), Fraction(0))
            out.append(acc / a[i][i])
        return out

    columns = []
    for col in range(n):
        rhs = [-a[i][col] if col > i else Fraction(0) for i in range(n)]
        columns.append(forward(rhs))
    T = [[columns[j][i] for j in range(n)] for i in range(n)]
    c = forward([b[i] for i in range(n)])
    return Matrix(T), Vector(c)


def characteristic_polynomial(T: Matrix) -> Tuple[Fraction, ...]:
    """Coeficientes de det(λI − T) de mayor a menor grado (Faddeev-LeVerrier, exacto)."""
    n = T.rows
    t = [[T.get(i, j) for j in range(n)] for i in range(n)]
    coeffs = [Fraction(1)]
    M = [[Fraction(0)] * n for _ in range(n)]
    for k in range(1, n + 1):
        prev = coeffs[-1]
        M = _mat_mul(t, M)
        for i in range(n):
            M[i][i] += prev
        TM = _mat_mul(t, M)
        trace = sum((TM[i][i] for i in range(n)), Fraction(0))
        coeffs.append(-trace / k)
    return tuple(coeffs)


def _poly_trim(p: List[Fraction]) -> List[Fraction]:
    while len(p) > 1 and p[0] == 0:
        p = p[1:]
    return p


def _poly_divmod(num: List[Fraction], den: List[Fraction]) -> Tuple[List[Fraction], List[Fraction]]:
    num = list(num)
    den = _poly_trim(list(den))
    if len(num) < len(den):
        return [Fraction(0)], num
    quotient = []
    while len(num) >= len(den):
        factor = num[0] / den[0]
        quotient.append(factor)
        for i in range(len(den)):
            num[i] -= factor * den[i]
        num = num[1:]
    return quotient, _poly_trim(num) if num else [Fraction(0)]


def _poly_gcd(p: List[Fraction], q: List[Fraction]) -> List[Fraction]:
    p, q = _poly_trim(list(p)), _poly_trim(list(q))
    while not (len(q) == 1 and q[0] == 0):
        _, r = _poly_divmod(p, q)
        p, q = q, r
    lead = p[0]
    return [c / lead for c in p]


def _squarefree(p: Sequence[Fraction]) -> List[Fraction]:
    p = list(p)
    if len(p) <= 2:
        return p
    degree = len(p) - 1
    derivative = [c * (degree - i) for i, c in enumerate(p[:-1])]
    g = _poly_gcd(p, derivative)
    if len(g) == 1:
        return p
    q, _ = _poly_divmod(p, g)
    lead = q[0]
    return [c / lead for c in q]


def _durand_kerner(coeffs: Sequence[Fraction]) -> List[complex]:
    degree = len(coeffs) - 1
    if degree <= 0:
        return []
    c = [complex(float(x)) / complex(float(coeffs[0])) for x in coeffs]
    if degree == 1:
        return [-c[1]]
    bound = 1 + max(abs(x) for x in c[1:])
    roots = [bound * cmath.exp(complex(0, 0.4 + 2 * cmath.pi * k / degree)) for k in range(degree)]

    def evaluate(z: complex) -> complex:
        acc = complex(0)
        for coefficient in c:
            acc = acc * z + coefficient
        return acc

    for _ in range(2000):
        biggest = 0.0
        for i in range(degree):
            denominator = complex(1)
            for j in range(degree):
                if i != j:
                    denominator *= roots[i] - roots[j]
            if denominator == 0:
                denominator = complex(1e-12)
            step = evaluate(roots[i]) / denominator
            roots[i] -= step
            biggest = max(biggest, abs(step))
        if biggest < 1e-15:
            break
    return roots


def eigenvalues_of(T: Matrix) -> Tuple[Tuple[Fraction, ...], Tuple[complex, ...]]:
    """Polinomio característico exacto y sus raíces distintas (aproximadas)."""
    poly = characteristic_polynomial(T)
    reduced = list(poly)
    roots: List[complex] = []
    if reduced[-1] == 0:
        roots.append(0j)
        while len(reduced) > 1 and reduced[-1] == 0:
            reduced = reduced[:-1]
    roots.extend(_durand_kerner(_squarefree(reduced)))
    cleaned = []
    for z in roots:
        real = 0.0 if abs(z.real) < 1e-12 else z.real
        imag = 0.0 if abs(z.imag) < 1e-12 else z.imag
        cleaned.append(complex(real, imag))
    return poly, tuple(cleaned)


def spectral_info(A: Matrix, b: Vector, method: IterativeMethod) -> SpectralInfo:
    T, c = iteration_matrix(A, b, method)
    poly, eigen = eigenvalues_of(T)
    radius = max((abs(z) for z in eigen), default=0.0)
    return SpectralInfo(method=method, T=T, c=c, char_poly=poly, eigenvalues=eigen, radius=radius)


def format_polynomial(coeffs: Sequence[Fraction], variable: str = "λ") -> str:
    """λ³ − (1/4)λ + 1/8 con coeficientes exactos."""
    degree = len(coeffs) - 1
    parts: List[str] = []
    for i, coefficient in enumerate(coeffs):
        power = degree - i
        if coefficient == 0:
            continue
        sign = "−" if coefficient < 0 else "+"
        magnitude = abs(coefficient)
        if power == 0:
            body = _show_exact(magnitude)
        else:
            mono = variable if power == 1 else variable + str(power).translate(_SUPERSCRIPT)
            if magnitude == 1:
                body = mono
            elif magnitude.denominator == 1:
                body = f"{magnitude.numerator}{mono}"
            else:
                body = f"({_show_exact(magnitude)}){mono}"
        if not parts:
            parts.append(body if sign == "+" else f"−{body}")
        else:
            parts.append(f" {sign} {body}")
    return "".join(parts) if parts else "0"


def format_complex(z: complex, digits: int = 4) -> str:
    def real(v: float) -> str:
        return format_decimal(Fraction(v).limit_denominator(10**12), digits)

    if abs(z.imag) < 1e-12:
        return real(z.real)
    imag = abs(z.imag)
    sign = "−" if z.imag < 0 else "+"
    imag_text = real(imag)
    if abs(z.real) < 1e-12:
        return f"{'−' if z.imag < 0 else ''}{imag_text}i"
    return f"{real(z.real)} {sign} {imag_text}i"


# ---------------------------------------------------------------------------
# Análisis de convergencia
# ---------------------------------------------------------------------------


def analyze_convergence(A: Matrix, b: Optional[Vector] = None) -> ConvergenceAnalysis:
    """Dominancia diagonal, simetría, menores principales y ρ(T) de ambos métodos."""
    if A.rows != A.cols:
        raise NonSquareMatrixError(f"El análisis de convergencia exige A cuadrada: A es {A.rows}×{A.cols}.")
    n = A.rows
    b = b if b is not None else Vector.zeros(n)
    rows = tuple(
        DominanceRow(
            row=i,
            diagonal=abs(A.get(i, i)),
            off_diagonal_sum=sum((abs(A.get(i, j)) for j in range(n) if j != i), Fraction(0)),
        )
        for i in range(n)
    )
    zero_rows = tuple(i for i in range(n) if A.get(i, i) == 0)
    symmetric = all(A.get(i, j) == A.get(j, i) for i in range(n) for j in range(i + 1, n))
    a = [[A.get(i, j) for j in range(n)] for i in range(n)]
    minors = tuple(_determinant([row[:k] for row in a[:k]]) for k in range(1, n + 1))
    jacobi = gauss_seidel = None
    if not zero_rows:
        jacobi = spectral_info(A, b, IterativeMethod.JACOBI)
        gauss_seidel = spectral_info(A, b, IterativeMethod.GAUSS_SEIDEL)
    return ConvergenceAnalysis(
        A=A.copy(),
        rows=rows,
        zero_diagonal_rows=zero_rows,
        symmetric=symmetric,
        leading_minors=minors,
        jacobi=jacobi,
        gauss_seidel=gauss_seidel,
    )


def dominance_lines(A: Matrix, analysis: ConvergenceAnalysis) -> List[str]:
    """«Fila 1: |10| > |−1| + |2| + |0| = 3 ✓» para cada fila."""
    n = A.rows
    lines = []
    for row in analysis.rows:
        i = row.row
        terms = " + ".join(f"|{_show_exact(A.get(i, j))}|" for j in range(n) if j != i) or "0"
        relation = ">" if row.strict else ("=" if row.diagonal == row.off_diagonal_sum else "<")
        mark = "✓" if row.strict else "✗"
        lines.append(
            f"Fila {i + 1}: |{_show_exact(A.get(i, i))}| {relation} {terms} = "
            f"{_show_exact(row.off_diagonal_sum)}  {mark}"
        )
    return lines


# ---------------------------------------------------------------------------
# Reordenamiento de filas
# ---------------------------------------------------------------------------


def reorder_for_dominance(A: Matrix, b: Vector) -> Optional[RowReordering]:
    """Permuta las filas de [A | b] buscando dominancia diagonal estricta.

    Si existe una permutación estrictamente dominante es única en cada fila:
    una fila solo puede ir a la posición j si 2|a_ij| > Σ_k |a_ik|, y eso lo
    cumple a lo sumo una columna. Si no existe, se elige la permutación con
    diagonal no nula que más filas dominantes deja. Retorna None si ninguna
    permutación deja la diagonal sin ceros.
    """
    n = _require_system(A, b)
    sums = [sum((abs(A.get(i, j)) for j in range(n)), Fraction(0)) for i in range(n)]
    target = {}
    for i in range(n):
        for j in range(n):
            if 2 * abs(A.get(i, j)) > sums[i]:
                target[i] = j
    permutation: Optional[Tuple[int, ...]] = None
    strictly = False
    if len(target) == n and len(set(target.values())) == n:
        order = [0] * n
        for row, col in target.items():
            order[col] = row
        permutation = tuple(order)
        strictly = True
    else:
        ratio = [
            [float(abs(A.get(i, j)) / sums[i]) if sums[i] else 0.0 for j in range(n)] for i in range(n)
        ]
        best_score = None
        for perm in itertools.permutations(range(n)):
            if any(A.get(perm[pos], pos) == 0 for pos in range(n)):
                continue
            dominant = sum(1 for pos in range(n) if ratio[perm[pos]][pos] > 0.5)
            score = (dominant, sum(ratio[perm[pos]][pos] for pos in range(n)), -sum(
                1 for pos in range(n) if perm[pos] != pos
            ))
            if best_score is None or score > best_score:
                best_score = score
                permutation = perm
        if permutation is None:
            return None
    assert permutation is not None
    new_A = Matrix([[A.get(permutation[i], j) for j in range(n)] for i in range(n)])
    new_b = Vector([b[permutation[i]] for i in range(n)])
    changed = permutation != tuple(range(n))
    moves = [f"la fila {old + 1} pasa a la posición {new + 1}" for new, old in enumerate(permutation) if old != new]
    if not changed:
        explanation = (
            "El orden actual ya es el mejor posible."
            if not strictly
            else "A ya es estrictamente diagonal dominante: no hace falta reordenar."
        )
    elif strictly:
        explanation = (
            "Se reordenaron las ecuaciones (" + "; ".join(moves) + "). "
            "Ahora A es estrictamente diagonal dominante: Jacobi y Gauss-Seidel convergen."
        )
    else:
        explanation = (
            "Se reordenaron las ecuaciones (" + "; ".join(moves) + ") para dejar la diagonal sin ceros. "
            "Ningún orden hace a A estrictamente dominante: la convergencia la decide ρ(T)."
        )
    return RowReordering(
        permutation=permutation,
        A=new_A,
        b=new_b,
        strictly_dominant=strictly,
        changed=changed,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Iteración
# ---------------------------------------------------------------------------


def _clearing_lines(A: Matrix, b: Vector, method: IterativeMethod) -> List[str]:
    """Despeje de cada xᵢ con los coeficientes reales del sistema."""
    n = A.rows
    lines = []
    for i in range(n):
        terms = []
        for j in range(n):
            if j == i or A.get(i, j) == 0:
                continue
            coefficient = -A.get(i, j)
            if method is IterativeMethod.JACOBI:
                k = "k"
            else:
                k = "k+1" if j < i else "k"
            magnitude = abs(coefficient)
            factor = "" if magnitude == 1 else f"{_show_exact(magnitude)}"
            sign = "−" if coefficient < 0 else "+"
            terms.append(f" {sign} {factor}{var(j, k)}")
        numerator = _show_exact(b[i]) + "".join(terms)
        diagonal = A.get(i, i)
        if diagonal == 1:
            lines.append(f"{var(i, 'k+1')} = {numerator}")
        else:
            shown = _show_exact(diagonal)
            if diagonal < 0 or diagonal.denominator != 1:
                shown = f"({shown})"
            lines.append(f"{var(i, 'k+1')} = ({numerator}) / {shown}")
    return lines


def _component_line(
    A: Matrix,
    b: Vector,
    i: int,
    sources: Sequence[Fraction],
    value: Fraction,
    k: int,
) -> str:
    n = A.rows
    pieces = [format_decimal(b[i])]
    for j in range(n):
        if j == i or A.get(i, j) == 0:
            continue
        pieces.append(f" − ({_show_exact(A.get(i, j))})({format_decimal(sources[j])})")
    diagonal = A.get(i, i)
    numerator = "".join(pieces)
    expression = numerator if diagonal == 1 else f"({numerator}) / {_show_exact(diagonal)}"
    return f"{var(i, k)} = {expression} = {format_decimal(value)}"


def _iterate_once(
    A: Matrix, b: Vector, previous: Sequence[Fraction], method: IterativeMethod, k: int
) -> Tuple[List[Fraction], List[str]]:
    n = A.rows
    current = list(previous)
    lines = []
    for i in range(n):
        sources = previous if method is IterativeMethod.JACOBI else current
        acc = b[i] - sum((A.get(i, j) * sources[j] for j in range(n) if j != i), Fraction(0))
        value = acc / A.get(i, i)
        lines.append(_component_line(A, b, i, sources, value, k))
        current[i] = value
    return current, lines


def _diagonal_cells(n: int) -> Tuple[Tuple[int, int], ...]:
    return tuple((i, i) for i in range(n))


def _vector_row_matrix(*rows: Sequence[Fraction]) -> Matrix:
    return Matrix([list(r) for r in rows])


def solve_iterative(
    A: Matrix,
    b: Vector,
    method: IterativeMethod,
    *,
    x0: Optional[Vector] = None,
    tolerance: Fraction = DEFAULT_TOLERANCE,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    criterion: StopCriterion = StopCriterion.ABSOLUTE,
    analysis: Optional[ConvergenceAnalysis] = None,
) -> IterativeResult:
    """Aplica Jacobi o Gauss-Seidel y registra cada iteración en un StepTracer.

    Raises:
        NonSquareMatrixError: A no es cuadrada.
        DimensionMismatchError: b o x⁽⁰⁾ no tienen n componentes.
        ZeroDiagonalError: algún aᵢᵢ = 0 (no se puede despejar xᵢ).
        ValueError: tolerancia ≤ 0 o máximo de iteraciones fuera de rango.
    """
    n = _require_system(A, b)
    tolerance = Fraction(tolerance)
    if tolerance <= 0:
        raise ValueError("La tolerancia ε debe ser positiva.")
    if not 1 <= max_iterations <= MAX_ALLOWED_ITERATIONS:
        raise ValueError(f"El máximo de iteraciones debe estar entre 1 y {MAX_ALLOWED_ITERATIONS}.")
    x0 = x0 if x0 is not None else Vector.zeros(n)
    if x0.dimension != n:
        raise DimensionMismatchError(
            f"x⁽⁰⁾ debe tener {n} componentes y tiene {x0.dimension}.",
            left_shape=A.shape,
            right_shape=(x0.dimension,),
            operation="iterar A x = b",
        )
    label = method.label
    tracer = StepTracer(split_col=n)
    augmented = A.augment(b)

    # Paso 0: el sistema y su diagonal.
    zero_rows = tuple(i for i in range(n) if A.get(i, i) == 0)
    tracer.record_initial(
        augmented,
        description=(
            f"Método de {label}. Se separa A = D + L + U: D es la diagonal (resaltada), "
            "L la parte estrictamente inferior y U la estrictamente superior. "
            "Para despejar xᵢ de la ecuación i hace falta aᵢᵢ ≠ 0."
        ),
        latex_title=r"A x = b,\quad A = D + L + U",
        highlight_cells=_diagonal_cells(n),
    )
    if zero_rows:
        rows_text = ", ".join(str(r + 1) for r in zero_rows)
        tracer.record_step(
            augmented,
            latex_formula=r"a_{ii} = 0",
            heuristic_text=(
                f"En la fila {rows_text} el elemento diagonal es 0: no se puede despejar esa incógnita "
                "y el método no puede empezar. Reordena las ecuaciones para que la diagonal no tenga ceros."
            ),
            alert_rows=zero_rows,
            highlight_cells=_diagonal_cells(n),
        )
        raise ZeroDiagonalError(
            f"{label} no se puede aplicar: aᵢᵢ = 0 en la fila {rows_text}. "
            "Reordena las ecuaciones para que la diagonal no tenga ceros.",
            rows=zero_rows,
            tracer=tracer,
        )
    analysis = analysis or analyze_convergence(A, b)
    info = analysis.spectral(method)
    assert info is not None

    # Paso 1: dominancia diagonal (condición suficiente).
    lines = dominance_lines(A, analysis)
    if analysis.strictly_dominant:
        dominance_text = (
            "Conclusión: A es estrictamente diagonal dominante por filas, así que "
            f"{label} converge para cualquier x⁽⁰⁾."
        )
    else:
        dominance_text = (
            "Conclusión: A no es estrictamente diagonal dominante. Esa condición es suficiente, "
            "no necesaria: la convergencia la decide el radio espectral."
        )
    if method is IterativeMethod.GAUSS_SEIDEL and analysis.positive_definite:
        minors = ", ".join(_show_exact(m) for m in analysis.leading_minors)
        dominance_text += (
            f" Además A es simétrica y sus menores principales ({minors}) son positivos: "
            "es definida positiva, y con eso Gauss-Seidel siempre converge."
        )
    tracer.record_step(
        augmented,
        latex_formula=r"|a_{ii}| > \sum_{j \ne i} |a_{ij}|",
        heuristic_text="Criterio de dominancia diagonal estricta.\n" + "\n".join(lines) + "\n" + dominance_text,
        alert_rows=tuple(r.row for r in analysis.rows if not r.strict),
        highlight_cells=_diagonal_cells(n),
    )

    # Paso 2: despeje y forma de punto fijo.
    if method is IterativeMethod.JACOBI:
        rule = (
            "Jacobi: cada xᵢ⁽ᵏ⁺¹⁾ se calcula solo con los valores de la iteración anterior x⁽ᵏ⁾. "
            "En forma matricial T_J = −D⁻¹(L + U) y c = D⁻¹b."
        )
        latex = r"x^{(k+1)} = T_J x^{(k)} + c_J"
    else:
        rule = (
            "Gauss-Seidel: en cuanto se calcula xᵢ⁽ᵏ⁺¹⁾ se usa en las ecuaciones siguientes; "
            "las xⱼ con j < i ya son de la iteración k+1. En forma matricial "
            "T_GS = −(D + L)⁻¹U y c = (D + L)⁻¹b."
        )
        latex = r"x^{(k+1)} = T_{GS} x^{(k)} + c_{GS}"
    tracer.record_step(
        info.T.augment(info.c),
        latex_formula=latex,
        heuristic_text="Se despeja xᵢ de la ecuación i:\n" + "\n".join(_clearing_lines(A, b, method)) + "\n" + rule
        + " La matriz mostrada es [T | c].",
    )

    # Paso 3: radio espectral (condición necesaria y suficiente).
    eigen_parts = []
    for z in info.eigenvalues:
        if abs(z.imag) < 1e-12:
            eigen_parts.append(f"λ = {format_complex(z)}")
        elif z.imag > 0:
            modulus = format_decimal(Fraction(abs(z)).limit_denominator(10**12), 4)
            shown = format_complex(z)
            shown = shown.replace(" + ", " ± ") if " + " in shown else f"±{shown}"
            eigen_parts.append(f"λ = {shown} (|λ| = {modulus})")
    eigen_text = ", ".join(eigen_parts)
    rho = format_decimal(Fraction(info.radius).limit_denominator(10**12), 4)
    if info.converges:
        verdict = f"ρ({method.plain_symbol}) ≈ {rho} < 1: la sucesión converge para cualquier x⁽⁰⁾."
        if info.radius < 1e-12:
            verdict += f" Como ρ = 0, {method.plain_symbol} es nilpotente y llega a la solución en a lo sumo {n} iteraciones."
    elif info.borderline:
        verdict = f"ρ({method.plain_symbol}) ≈ {rho} = 1: no se garantiza la convergencia."
    else:
        verdict = f"ρ({method.plain_symbol}) ≈ {rho} > 1: el error crece y la sucesión diverge (salvo x⁽⁰⁾ muy particulares)."
    tracer.record_step(
        info.T,
        latex_formula=rf"\rho({method.matrix_symbol}) = \max_i |\lambda_i|",
        heuristic_text=(
            f"Polinomio característico de {method.plain_symbol}: p(λ) = {format_polynomial(info.char_poly)}.\n"
            f"Valores propios distintos: {eigen_text}. ρ = máx |λ|.\n{verdict}"
        ),
        split_col=None,
    )

    # Solución exacta para medir el error real de cada iterado.
    exact: Optional[Vector] = None
    classification = classify_system(augmented, split_col=n)
    if classification.unique_solution is not None:
        exact = Vector(classification.unique_solution)

    def error_of(x: Sequence[Fraction]) -> Optional[Fraction]:
        if exact is None:
            return None
        return _inf_norm([x[i] - exact[i] for i in range(n)])

    x_prev = list(x0.components)
    records = [
        IterationRecord(
            k=0,
            x=tuple(x_prev),
            delta_norm=None,
            relative_delta=None,
            residual_norm=_inf_norm(_residual(A, b, x_prev)),
            error_norm=error_of(x_prev),
        )
    ]
    criterion_text = (
        "‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ < ε"
        if criterion is StopCriterion.ABSOLUTE
        else "‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ / ‖x⁽ᵏ⁾‖∞ < ε"
    )
    tracer.record_step(
        _vector_row_matrix(x_prev),
        latex_formula=r"x^{(0)}",
        heuristic_text=(
            f"Vector inicial x⁽⁰⁾ = {format_vector(x_prev)}. Se itera hasta que {criterion_text} "
            f"con ε = {format_decimal(tolerance, 10)}, o hasta {max_iterations} iteraciones."
        ),
        split_col=None,
    )

    scale = max(Fraction(1), _inf_norm(x_prev), _inf_norm(info.c.components))
    blow_up = DIVERGENCE_FACTOR * scale
    status = IterationStatus.MAX_ITERATIONS
    for k in range(1, max_iterations + 1):
        x_new, comp_lines = _iterate_once(A, b, x_prev, method, k)
        diffs = [abs(x_new[i] - x_prev[i]) for i in range(n)]
        delta = max(diffs)
        norm_new = _inf_norm(x_new)
        relative = delta / norm_new if norm_new != 0 else None
        record = IterationRecord(
            k=k,
            x=tuple(x_new),
            delta_norm=delta,
            relative_delta=relative,
            residual_norm=_inf_norm(_residual(A, b, x_new)),
            error_norm=error_of(x_new),
            component_lines=tuple(comp_lines),
        )
        records.append(record)
        measure = delta if criterion is StopCriterion.ABSOLUTE else relative
        delta_text = f"‖x{superscript_iter(k)} − x{superscript_iter(k - 1)}‖∞ = {format_decimal(delta)}"
        if criterion is StopCriterion.RELATIVE:
            delta_text += (
                f"; relativo = {format_decimal(relative)}" if relative is not None else "; relativo indefinido (x = 0)"
            )
        if method is IterativeMethod.JACOBI:
            intro = f"Iteración {k}: se sustituye x{superscript_iter(k - 1)} en todas las fórmulas a la vez."
        else:
            intro = (
                f"Iteración {k}: cada componente nueva se usa de inmediato en las filas de abajo "
                f"(x₁{superscript_iter(k)} entra en la fórmula de x₂{superscript_iter(k)}, …)."
            )
        argmax = diffs.index(delta)
        converged_now = measure is not None and measure < tolerance
        diverged_now = norm_new > blow_up
        if converged_now:
            decision = f"{delta_text} < ε → se detiene: convergió en {k} iteraciones."
            status = IterationStatus.CONVERGED
        elif diverged_now:
            decision = (
                f"{delta_text}. ‖x{superscript_iter(k)}‖∞ = {format_decimal(norm_new)} se disparó: "
                "la sucesión diverge y se detiene."
            )
            status = IterationStatus.DIVERGED
        elif k == max_iterations:
            decision = f"{delta_text} ≥ ε y se alcanzó el máximo de {max_iterations} iteraciones."
        else:
            decision = f"{delta_text} ≥ ε → se continúa."
        tracer.record_step(
            _vector_row_matrix(x_prev, x_new, diffs),
            latex_formula=rf"x^{{({k})}} \text{{ a partir de }} x^{{({k - 1})}}",
            heuristic_text=intro + "\n" + "\n".join(comp_lines) + "\n"
            + f"Filas: x{superscript_iter(k - 1)}, x{superscript_iter(k)} y |x{superscript_iter(k)} − x{superscript_iter(k - 1)}| "
            + f"(su máximo, resaltado, es la norma ∞).\n{decision}",
            actor_row=0,
            affected_rows=(1,),
            alert_rows=(1,) if diverged_now else (),
            highlight_cells=((2, argmax),),
            split_col=None,
        )
        x_prev = x_new
        if converged_now or diverged_now:
            break

    if status is IterationStatus.MAX_ITERATIONS and not info.converges:
        status = IterationStatus.DIVERGED

    final = records[-1]
    x_final = list(final.x)
    if status is IterationStatus.CONVERGED:
        summary = f"{label} convergió en {final.k} iteraciones: x ≈ {format_vector(x_final)}."
    elif status is IterationStatus.DIVERGED:
        summary = (
            f"{label} no converge: tras {final.k} iteraciones ‖x⁽ᵏ⁾‖∞ = {format_decimal(_inf_norm(x_final))} "
            f"y ρ({method.plain_symbol}) ≈ {rho} ≥ 1."
        )
    else:
        summary = (
            f"{label} no alcanzó ε en {final.k} iteraciones, aunque ρ({method.plain_symbol}) ≈ {rho} < 1: "
            "converge, pero necesita más iteraciones."
        )

    # Paso final: comparación con la solución exacta.
    final_lines = [summary]
    if exact is not None:
        final_lines.append(f"Solución exacta por Gauss-Jordan: x* = {format_vector(exact.components)}.")
        if final.error_norm is not None:
            final_lines.append(f"Error real ‖x⁽ᵏ⁾ − x*‖∞ = {format_decimal(final.error_norm)}.")
    else:
        final_lines.append("A es singular: A x = b no tiene solución única que aproximar.")
    final_lines.append(f"Residuo ‖b − A x⁽ᵏ⁾‖∞ = {format_decimal(final.residual_norm)}.")
    if status is not IterationStatus.CONVERGED and not analysis.strictly_dominant:
        final_lines.append(
            "Sugerencias: reordenar las ecuaciones para buscar dominancia diagonal, probar el otro "
            "método o resolver directamente con Gauss-Jordan."
        )
    if exact is not None:
        final_matrix = _vector_row_matrix(x_final, exact.components, [abs(x_final[i] - exact[i]) for i in range(n)])
        final_caption = "Filas: aproximación x⁽ᵏ⁾, solución exacta x* y |x⁽ᵏ⁾ − x*|."
    else:
        final_matrix = _vector_row_matrix(x_final)
        final_caption = "Fila: última aproximación x⁽ᵏ⁾."
    tracer.record_step(
        final_matrix,
        latex_formula=(
            r"x^{(k)} \approx x^{*}" if status is IterationStatus.CONVERGED else r"x^{(k)} \text{ no converge a } x^{*}"
        ),
        heuristic_text="\n".join(final_lines) + "\n" + final_caption,
        alert_rows=() if status is IterationStatus.CONVERGED else (0,),
        split_col=None,
    )

    return IterativeResult(
        method=method,
        A=A.copy(),
        b=b.copy(),
        x0=x0.copy(),
        tolerance=tolerance,
        max_iterations=max_iterations,
        criterion=criterion,
        iterations=tuple(records),
        status=status,
        exact_solution=exact,
        analysis=analysis,
        tracer=tracer,
        summary=summary,
    )


def jacobi(A: Matrix, b: Vector, **kwargs) -> IterativeResult:
    """Método de Jacobi. Ver ``solve_iterative``."""
    return solve_iterative(A, b, IterativeMethod.JACOBI, **kwargs)


def gauss_seidel(A: Matrix, b: Vector, **kwargs) -> IterativeResult:
    """Método de Gauss-Seidel. Ver ``solve_iterative``."""
    return solve_iterative(A, b, IterativeMethod.GAUSS_SEIDEL, **kwargs)


def compare_methods(A: Matrix, b: Vector, **kwargs) -> MethodComparison:
    """Ejecuta ambos métodos con los mismos datos y resume cuál conviene."""
    _require_system(A, b)
    analysis = kwargs.pop("analysis", None) or analyze_convergence(A, b)
    j = solve_iterative(A, b, IterativeMethod.JACOBI, analysis=analysis, **kwargs)
    g = solve_iterative(A, b, IterativeMethod.GAUSS_SEIDEL, analysis=analysis, **kwargs)
    return MethodComparison(jacobi=j, gauss_seidel=g, summary=comparison_summary(j, g))


def comparison_summary(j: IterativeResult, g: IterativeResult) -> str:
    """Frase que compara iteraciones, ρ(T) y velocidad asintótica."""
    rj = j.analysis.jacobi.radius if j.analysis.jacobi else None
    rg = j.analysis.gauss_seidel.radius if j.analysis.gauss_seidel else None
    if j.converged and g.converged:
        if g.iteration_count < j.iteration_count:
            text = (
                f"Ambos convergen. Gauss-Seidel necesitó {g.iteration_count} iteraciones y Jacobi "
                f"{j.iteration_count}: usar los valores nuevos en cuanto existen acelera la convergencia."
            )
        elif g.iteration_count > j.iteration_count:
            text = (
                f"Ambos convergen, pero aquí Jacobi fue más rápido ({j.iteration_count} contra "
                f"{g.iteration_count} iteraciones): Gauss-Seidel no siempre gana."
            )
        else:
            text = f"Ambos convergen en {j.iteration_count} iteraciones."
        if rj is not None and rg is not None and 0 < rj < 1 and 0 < rg < 1:
            speed = math.log(rg) / math.log(rj)
            text += (
                f" Asintóticamente el error se multiplica por ρ en cada paso: ρ(T_J) ≈ {rj:.4f} y "
                f"ρ(T_GS) ≈ {rg:.4f}, así que Gauss-Seidel avanza ≈ {speed:.2f} veces lo que Jacobi por iteración."
            )
        return text
    if j.converged and not g.converged:
        return (
            f"Solo Jacobi converge ({j.iteration_count} iteraciones). Gauss-Seidel diverge porque "
            f"ρ(T_GS) ≈ {rg:.4f} > 1: Gauss-Seidel no es siempre mejor."
        )
    if g.converged and not j.converged:
        return (
            f"Solo Gauss-Seidel converge ({g.iteration_count} iteraciones). Jacobi no, porque "
            f"ρ(T_J) ≈ {rj:.4f} ≥ 1."
        )
    return (
        "Ninguno de los dos converge"
        + (f": ρ(T_J) ≈ {rj:.4f} y ρ(T_GS) ≈ {rg:.4f}, ambos ≥ 1." if rj is not None and rg is not None else ".")
        + " Reordenar las ecuaciones para lograr dominancia diagonal suele resolverlo."
    )
