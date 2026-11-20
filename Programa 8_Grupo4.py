"""================================================================================
UNIVERSIDAD AMERICANA (UAM)
Facultad de Ingeniería y Arquitectura (FIA)
Asignatura: Álgebra Lineal (MTM0120)
PROGRAMA 8: Métodos Iterativos de Jacobi y Gauss-Seidel para Sistemas A·x = b
Grupo 4
Integrantes:
    • Roberto Fabio Tercero Morán
    • Steven Alexander Flores Obregón
    • Kellys Bellanger
    • Raúl Valverde Ruiz
================================================================================
Restricción estricta del Contrato Didáctico:
    100% Python estándar puro. Prohibido NumPy, SciPy y álgebra lineal de math.
    Toda la aritmética iterativa se realiza con fractions.Fraction (exacta,
    sin redondeo acumulado). Las matrices de iteración y sus polinomios
    característicos se calculan mediante el algoritmo exacto de Faddeev-LeVerrier.

Fundamentación Teórica y Lógica Algorítmica:
    1. Descomposición Canónica de la Matriz de Coeficientes:
       Dada A ∈ ℝⁿˣⁿ no singular con aᵢᵢ ≠ 0 para todo i, se descompone aditivamente:
           A = D + L + U
       donde D es diagonal, L es triangular inferior estricta y U triangular superior estricta.

    2. Método Iterativo de Jacobi (Desplazamiento Simultáneo):
       Se despeja cada incógnita xᵢ de la i-ésima ecuación utilizando ÚNICAMENTE los
       valores de la iteración previa x⁽ᵏ⁾:
           xᵢ⁽ᵏ⁺¹⁾ = (bᵢ - ∑_{j ≠ i} aᵢⱼ · xⱼ⁽ᵏ⁾) / aᵢᵢ
       En forma matricial compacta:
           x⁽ᵏ⁺¹⁾ = T_J · x⁽ᵏ⁾ + c_J
           donde T_J = -D⁻¹(L + U)  y  c_J = D⁻¹·b.

    3. Método Iterativo de Gauss-Seidel (Desplazamiento Sucesivo):
       Se actualiza cada incógnita xᵢ utilizando INMEDIATAMENTE los nuevos valores
       calculados x₁⁽ᵏ⁺¹⁾, ..., x_{i-1}⁽ᵏ⁺¹⁾ en la misma iteración:
           xᵢ⁽ᵏ⁺¹⁾ = (bᵢ - ∑_{j < i} aᵢⱼ · xⱼ⁽ᵏ⁺¹⁾ - ∑_{j > i} aᵢⱼ · xⱼ⁽ᵏ⁾) / aᵢᵢ
       En forma matricial compacta:
           x⁽ᵏ⁺¹⁾ = T_GS · x⁽ᵏ⁾ + c_GS
           donde T_GS = -(D + L)⁻¹ · U  y  c_GS = (D + L)⁻¹·b.

    4. Condiciones de Convergencia:
       a) Condición Suficiente (Dominancia Diagonal Estricta por Filas):
          Si |aᵢᵢ| > ∑_{j ≠ i} |aᵢⱼ|  ∀ i = 1, ..., n,
          entonces AMBOS métodos (Jacobi y Gauss-Seidel) convergen para CUALQUIER
          vector inicial x⁽⁰⁾ ∈ ℝⁿ.
       b) Condición Necesaria y Suficiente (Radio Espectral):
          El método x⁽ᵏ⁺¹⁾ = T·x⁽ᵏ⁾ + c converge para todo x⁽⁰⁾ si y solo si
          el radio espectral ρ(T) = máx |λᵢ| < 1, donde λᵢ son los autovalores de T.
       c) Matrices Simétricas y Definidas Positivas (Criterio de Ostrowski-Reich):
          Si A es simétrica (A = Aᵀ) y definida positiva (todos sus menores principales
          tienen determinante positivo), Gauss-Seidel converge garantizado para cualquier x⁽⁰⁾.
       d) Teorema de Stein-Rosenberg:
          Para matrices con aᵢⱼ ≤ 0 para i ≠ j y aᵢᵢ > 0, se cumple:
          - Si ρ(T_J) < 1, entonces ρ(T_GS) < ρ(T_J) < 1 (Gauss-Seidel converge más rápido).
          - Si ρ(T_J) ≥ 1, entonces ρ(T_GS) ≥ ρ(T_J) ≥ 1 (ambos divergen).
          *NOTA*: Si no se cumple la hipótesis de signos, Gauss-Seidel NO siempre es
          mejor que Jacobi (existen casos donde Jacobi converge y Gauss-Seidel diverge).

    5. Criterios de Paro:
       - Error Absoluto: ‖x⁽ᵏ⁾ - x⁽ᵏ⁻¹⁾‖_∞ < ε
       - Error Relativo: ‖x⁽ᵏ⁾ - x⁽ᵏ⁻¹⁾‖_∞ / ‖x⁽ᵏ⁾‖_∞ < ε
       - Límite de seguridad de iteraciones máximas para prevenir ciclos infinitos.
       - Detección temprana de divergencia cuando la norma explota (‖x⁽ᵏ⁾‖_∞ > 10⁸).
================================================================================
"""

from __future__ import annotations

import cmath
import itertools
import math
import sys
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ------------------------------------------------------------------------------
# Enumeraciones y Clases de Datos
# ------------------------------------------------------------------------------

class IterativeMethod(Enum):
    JACOBI = "Jacobi"
    GAUSS_SEIDEL = "Gauss-Seidel"


class StopCriterion(Enum):
    ABSOLUTE = "Absoluto (||x^(k) - x^(k-1)||_inf < ε)"
    RELATIVE = "Relativo (||x^(k) - x^(k-1)||_inf / ||x^(k)||_inf < ε)"


class IterationStatus(Enum):
    CONVERGED = "CONVERGIÓ"
    DIVERGED = "DIVERGIÓ"
    MAX_ITERATIONS = "LÍMITE DE ITERACIONES ALCANZADO"


@dataclass(frozen=True)
class IterationRow:
    """Representa el estado numérico en la iteración k."""
    k: int
    x: Tuple[Fraction, ...]
    delta_norm: Optional[Fraction]
    relative_delta: Optional[Fraction]
    residual_norm: Fraction
    substitutions: Tuple[str, ...] = ()


@dataclass
class IterationResult:
    """Resultado completo de la ejecución de un método iterativo."""
    method: IterativeMethod
    status: IterationStatus
    iterations: List[IterationRow]
    tolerance: Fraction
    stop_criterion: StopCriterion
    spectral_radius: Optional[float]
    strictly_dominant: bool
    is_symmetric_positive_definite: bool
    summary: str


# ------------------------------------------------------------------------------
# Utilidades de Entrada / Salida y Aritmética Exacta
# ------------------------------------------------------------------------------

def parse_scalar(text: str) -> Fraction:
    """Convierte texto en Fraction exacta (soporta enteros, fracciones a/b y decimales)."""
    cleaned = text.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("Entrada vacía.")
    if "/" in cleaned:
        parts = cleaned.split("/")
        if len(parts) != 2:
            raise ValueError("Formato de fracción no válido (use ej. 3/4 o -5/2).")
        num, den = int(parts[0]), int(parts[1])
        if den == 0:
            raise ZeroDivisionError("El denominador no puede ser cero.")
        return Fraction(num, den)
    return Fraction(cleaned)


def fmt(val: Fraction) -> str:
    """Representación en texto limpio de una fracción irreductible."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def fmt_dec(val: Optional[Fraction], decimals: int = 6) -> str:
    """Representación en punto flotante formateado a una cantidad de decimales."""
    if val is None:
        return "—"
    return f"{float(val):.{decimals}f}"


def read_scalar(prompt: str) -> Fraction:
    """Lee un escalar desde la consola con validación rigurosa y reintento."""
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   ⚠️  Entrada inválida ({exc}). Reintente (ej. 4, -2, 5/3, 0.25):")


def read_positive_int(prompt: str, default: Optional[int] = None) -> int:
    """Lee un entero positivo mayor a cero."""
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            val = int(raw)
            if val <= 0:
                print("   ⚠️  Debe ser un entero mayor que cero.")
                continue
            return val
        except ValueError:
            print("   ⚠️  Entrada no numérica. Ingrese un entero válido.")


def read_tolerance(prompt: str, default: Fraction = Fraction(1, 10000)) -> Fraction:
    """Lee la tolerancia ε > 0."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            val = parse_scalar(raw)
            if val <= 0:
                print("   ⚠️  La tolerancia debe ser estrictamente positiva (ε > 0).")
                continue
            return val
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   ⚠️  Valor de tolerancia inválido ({exc}).")


# ------------------------------------------------------------------------------
# Álgebra Matricial Lineal Estándar (100% Python Puro con Fractions)
# ------------------------------------------------------------------------------

def mat_zeros(rows: int, cols: int) -> List[List[Fraction]]:
    return [[Fraction(0, 1) for _ in range(cols)] for _ in range(rows)]


def mat_identity(n: int) -> List[List[Fraction]]:
    I = mat_zeros(n, n)
    for i in range(n):
        I[i][i] = Fraction(1, 1)
    return I


def mat_copy(A: List[List[Fraction]]) -> List[List[Fraction]]:
    return [row[:] for row in A]


def mat_mul(A: List[List[Fraction]], B: List[List[Fraction]]) -> List[List[Fraction]]:
    m, n, p = len(A), len(A[0]), len(B[0])
    C = mat_zeros(m, p)
    for i in range(m):
        for k in range(n):
            if A[i][k] != 0:
                for j in range(p):
                    C[i][j] += A[i][k] * B[k][j]
    return C


def mat_vec_mul(A: List[List[Fraction]], v: Sequence[Fraction]) -> List[Fraction]:
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def mat_trace(A: List[List[Fraction]]) -> Fraction:
    return sum(A[i][i] for i in range(len(A)))


def vec_sub(u: Sequence[Fraction], v: Sequence[Fraction]) -> List[Fraction]:
    return [u[i] - v[i] for i in range(len(u))]


def norm_inf(v: Sequence[Fraction]) -> Fraction:
    """Norma infinito (del máximo): ||v||_∞ = máx |vᵢ|."""
    return max((abs(x) for x in v), default=Fraction(0, 1))


def determinant_exact(A: List[List[Fraction]]) -> Fraction:
    """Calcula el determinante exacto mediante eliminación gaussiana por filas."""
    n = len(A)
    M = mat_copy(A)
    det = Fraction(1, 1)
    for j in range(n):
        pivot = j
        while pivot < n and M[pivot][j] == 0:
            pivot += 1
        if pivot == n:
            return Fraction(0, 1)
        if pivot != j:
            M[j], M[pivot] = M[pivot], M[j]
            det = -det
        det *= M[j][j]
        pj = M[j][j]
        for i in range(j + 1, n):
            factor = M[i][j] / pj
            for k in range(j, n):
                M[i][k] -= factor * M[j][k]
    return det


# ------------------------------------------------------------------------------
# Análisis Teórico de Convergencia: Dominancia, Polinomio y Radio Espectral
# ------------------------------------------------------------------------------

def check_strict_diagonal_dominance(A: List[List[Fraction]]) -> Tuple[bool, List[Tuple[Fraction, Fraction, bool]]]:
    """Evalúa la condición suficiente de dominancia diagonal estricta por filas.
    Retorna (es_dominante, [(|a_ii|, suma_resto, fila_es_dominante)]).
    """
    n = len(A)
    details = []
    strictly = True
    for i in range(n):
        diag = abs(A[i][i])
        off_diag_sum = sum(abs(A[i][j]) for j in range(n) if j != i)
        row_ok = diag > off_diag_sum
        if not row_ok:
            strictly = False
        details.append((diag, off_diag_sum, row_ok))
    return strictly, details


def check_symmetric_positive_definite(A: List[List[Fraction]]) -> Tuple[bool, bool, List[Fraction]]:
    """Evalúa el Criterio de Sylvester para matrices simétricas definidas positivas.
    Retorna (es_simetrica, es_definida_positiva, lista_menores_principales).
    """
    n = len(A)
    # 1. Simetría: A == Aᵀ
    symmetric = True
    for i in range(n):
        for j in range(i + 1, n):
            if A[i][j] != A[j][i]:
                symmetric = False
                break
        if not symmetric:
            break

    if not symmetric:
        return False, False, []

    # 2. Menores principales directos
    minors = []
    spd = True
    for k in range(1, n + 1):
        submatrix = [A[r][:k] for r in range(k)]
        det_k = determinant_exact(submatrix)
        minors.append(det_k)
        if det_k <= 0:
            spd = False

    return True, spd, minors


def invert_diagonal_matrix(A: List[List[Fraction]]) -> List[List[Fraction]]:
    """Inversa de D (donde D es la diagonal de A). Lanza ZeroDivisionError si a_ii = 0."""
    n = len(A)
    D_inv = mat_zeros(n, n)
    for i in range(n):
        if A[i][i] == 0:
            raise ZeroDivisionError(f"Cero en la diagonal en fila {i+1}: a_{i+1}{i+1} = 0.")
        D_inv[i][i] = Fraction(1, 1) / A[i][i]
    return D_inv


def invert_lower_triangular(M: List[List[Fraction]]) -> List[List[Fraction]]:
    """Invierte una matriz triangular inferior M cuadrada (usada para (D + L)⁻¹)."""
    n = len(M)
    inv = mat_zeros(n, n)
    for j in range(n):
        if M[j][j] == 0:
            raise ZeroDivisionError(f"Cero diagonal en triangular inferior en fila {j+1}.")
        inv[j][j] = Fraction(1, 1) / M[j][j]
        for i in range(j + 1, n):
            s = sum(M[i][k] * inv[k][j] for k in range(j, i))
            inv[i][j] = -s / M[i][i]
    return inv


def build_iteration_matrices(A: List[List[Fraction]], b: List[Fraction], method: IterativeMethod) -> Tuple[List[List[Fraction]], List[Fraction]]:
    """Construye la matriz de iteración T y el vector de traslación c.
    Para Jacobi:       T_J = -D⁻¹(L + U),         c_J = D⁻¹·b
    Para Gauss-Seidel: T_GS = -(D + L)⁻¹·U,       c_GS = (D + L)⁻¹·b
    """
    n = len(A)
    if method == IterativeMethod.JACOBI:
        D_inv = invert_diagonal_matrix(A)
        # R = L + U = A - D
        R = mat_zeros(n, n)
        for i in range(n):
            for j in range(n):
                if i != j:
                    R[i][j] = A[i][j]
        # T_J = - D⁻¹ · R
        T_J = mat_zeros(n, n)
        for i in range(n):
            for j in range(n):
                T_J[i][j] = - D_inv[i][i] * R[i][j]
        c_J = [D_inv[i][i] * b[i] for i in range(n)]
        return T_J, c_J

    elif method == IterativeMethod.GAUSS_SEIDEL:
        # D_L = D + L
        D_L = mat_zeros(n, n)
        U = mat_zeros(n, n)
        for i in range(n):
            for j in range(n):
                if j <= i:
                    D_L[i][j] = A[i][j]
                else:
                    U[i][j] = A[i][j]
        D_L_inv = invert_lower_triangular(D_L)
        # T_GS = - (D + L)⁻¹ · U
        T_GS = mat_zeros(n, n)
        for i in range(n):
            for j in range(n):
                val = sum(D_L_inv[i][k] * U[k][j] for k in range(n))
                T_GS[i][j] = -val
        c_GS = mat_vec_mul(D_L_inv, b)
        return T_GS, c_GS

    raise ValueError(f"Método desconocido: {method}")


def characteristic_polynomial(M: List[List[Fraction]]) -> List[Fraction]:
    """Calcula los coeficientes del polinomio característico p(λ) = det(λI - M)
    mediante el algoritmo exacto de Faddeev-LeVerrier en fractions.Fraction:
    p(λ) = λⁿ + c₁ λⁿ⁻¹ + c₂ λⁿ⁻² + ... + cₙ.
    Retorna la lista [1, c₁, c₂, ..., cₙ].
    """
    n = len(M)
    if n == 0:
        return [Fraction(1, 1)]
    coeffs = [Fraction(1, 1)]
    B = mat_identity(n)
    for k in range(1, n + 1):
        MB = mat_mul(M, B)
        c_k = - mat_trace(MB) / Fraction(k, 1)
        coeffs.append(c_k)
        if k < n:
            # B_{k} = MB + c_k * I
            B = mat_zeros(n, n)
            for i in range(n):
                for j in range(n):
                    diag_add = c_k if i == j else Fraction(0, 1)
                    B[i][j] = MB[i][j] + diag_add
    return coeffs


def find_polynomial_roots_durand_kerner(coeffs: List[Fraction], max_iter: int = 100, tol: float = 1e-12) -> List[complex]:
    """Halla todas las raíces (reales y complejas) de un polinomio mónico
    utilizando el método numérico de Durand-Kerner (Weierstrass).
    """
    n = len(coeffs) - 1
    if n <= 0:
        return []
    if n == 1:
        # λ + c₁ = 0 => λ = -c₁
        return [complex(-float(coeffs[1]))]

    # Inicialización estándar de Durand-Kerner en el plano complejo
    # z_j = (0.4 + 0.9i)^j
    w = complex(0.4, 0.9)
    roots = [w ** j for j in range(n)]

    def poly_eval(z: complex) -> complex:
        res = complex(1.0, 0.0)
        for c in coeffs[1:]:
            res = res * z + complex(float(c), 0.0)
        return res

    for _ in range(max_iter):
        max_diff = 0.0
        for i in range(n):
            denom = complex(1.0, 0.0)
            for j in range(n):
                if i != j:
                    diff_ij = roots[i] - roots[j]
                    if abs(diff_ij) == 0:
                        diff_ij = complex(1e-14, 1e-14)
                    denom *= diff_ij
            pz = poly_eval(roots[i])
            delta = pz / denom
            roots[i] -= delta
            if abs(delta) > max_diff:
                max_diff = abs(delta)
        if max_diff < tol:
            break

    return roots


def compute_spectral_radius(T: List[List[Fraction]]) -> Tuple[float, List[complex]]:
    """Calcula el radio espectral exacto-numérico ρ(T) = máx |λᵢ|."""
    coeffs = characteristic_polynomial(T)
    roots = find_polynomial_roots_durand_kerner(coeffs)
    rho = max((abs(r) for r in roots), default=0.0)
    return rho, roots


def reorder_for_dominance(A: List[List[Fraction]], b: List[Fraction]) -> Tuple[List[List[Fraction]], List[Fraction], List[int], bool]:
    """Intenta permutar las ecuaciones (filas de A y b) para alcanzar dominancia
    diagonal estricta. Si existe una permutación exitosa, la retorna con success=True.
    Si ninguna da dominancia estricta, retorna la mejor disponible.
    """
    n = len(A)
    best_perm: Optional[Tuple[int, ...]] = None
    best_strictly = False
    best_score = -1e9

    for perm in itertools.permutations(range(n)):
        perm_A = [A[r] for r in perm]
        strictly, details = check_strict_diagonal_dominance(perm_A)
        score = sum(float(d - s) for d, s, _ in details)
        if strictly:
            return perm_A, [b[r] for r in perm], list(perm), True
        if score > best_score:
            best_score = score
            best_perm = perm

    chosen_perm = list(best_perm) if best_perm is not None else list(range(n))
    return [A[r] for r in chosen_perm], [b[r] for r in chosen_perm], chosen_perm, False


# ------------------------------------------------------------------------------
# Algoritmos Iterativos Principales (Jacobi y Gauss-Seidel)
# ------------------------------------------------------------------------------

def solve_iterative(
    A: List[List[Fraction]],
    b: List[Fraction],
    method: IterativeMethod,
    x0: Optional[Sequence[Fraction]] = None,
    tolerance: Fraction = Fraction(1, 10000),
    max_iter: int = 50,
    criterion: StopCriterion = StopCriterion.ABSOLUTE,
) -> IterationResult:
    """Ejecuta el método de Jacobi o Gauss-Seidel con aritmética exacta de Fraction.
    Genera el desglose paso a paso de cada iteración.
    """
    n = len(A)
    # Validar dimensiones cuadradas y diagonal no nula
    if any(len(row) != n for row in A) or len(b) != n:
        raise ValueError("La matriz de coeficientes debe ser cuadrada (n × n) y b de tamaño n.")

    for i in range(n):
        if A[i][i] == 0:
            raise ZeroDivisionError(
                f"Elemento diagonal nulo detectado en fila {i+1}: a_{i+1}{i+1} = 0.\n"
                f"No es posible despejar x{i+1}. Se requiere reordenar ecuaciones."
            )

    # Diagnóstico previo de convergencia
    strictly_dom, _ = check_strict_diagonal_dominance(A)
    _, is_spd, _ = check_symmetric_positive_definite(A)

    # Radio espectral
    try:
        T, _ = build_iteration_matrices(A, b, method)
        rho, _ = compute_spectral_radius(T)
    except Exception:
        rho = None

    if x0 is None:
        curr_x: List[Fraction] = [Fraction(0, 1) for _ in range(n)]
    else:
        curr_x = list(x0)

    # Iteración 0 (Vector Inicial)
    Ax0 = mat_vec_mul(A, curr_x)
    res0 = vec_sub(b, Ax0)
    norm_res0 = norm_inf(res0)

    history: List[IterationRow] = [
        IterationRow(
            k=0,
            x=tuple(curr_x),
            delta_norm=None,
            relative_delta=None,
            residual_norm=norm_res0,
            substitutions=("Vector inicial x⁽⁰⁾ registrado.",),
        )
    ]

    status = IterationStatus.MAX_ITERATIONS
    summary = ""
    initial_scale = max(norm_inf(curr_x), norm_inf(b), Fraction(1, 1))

    for k in range(1, max_iter + 1):
        prev_x = curr_x[:]
        sub_lines: List[str] = []

        if method == IterativeMethod.JACOBI:
            next_x = [Fraction(0, 1) for _ in range(n)]
            for i in range(n):
                aii = A[i][i]
                bi = b[i]
                off_diag_sum = sum(A[i][j] * prev_x[j] for j in range(n) if j != i)
                val_i = (bi - off_diag_sum) / aii
                next_x[i] = val_i

                # Explicación paso a paso
                terms = [f"{fmt(A[i][j])}·({fmt_dec(prev_x[j], 4)})" for j in range(n) if j != i]
                eq_str = f"x{i+1}⁽{k}⁾ = [{fmt(bi)} - ({' + '.join(terms)})] / {fmt(aii)} = {fmt_dec(val_i, 6)}"
                sub_lines.append(eq_str)
            curr_x = next_x

        elif method == IterativeMethod.GAUSS_SEIDEL:
            next_x = prev_x[:]
            for i in range(n):
                aii = A[i][i]
                bi = b[i]
                # Usa curr_x (que ya contiene los nuevos x_j para j < i)
                lower_sum = sum(A[i][j] * next_x[j] for j in range(i))
                upper_sum = sum(A[i][j] * prev_x[j] for j in range(i + 1, n))
                val_i = (bi - lower_sum - upper_sum) / aii
                next_x[i] = val_i

                # Explicación paso a paso
                terms_used = []
                for j in range(i):
                    terms_used.append(f"{fmt(A[i][j])}·({fmt_dec(next_x[j], 4)}*)")
                for j in range(i + 1, n):
                    terms_used.append(f"{fmt(A[i][j])}·({fmt_dec(prev_x[j], 4)})")
                eq_str = f"x{i+1}⁽{k}⁾ = [{fmt(bi)} - ({' + '.join(terms_used) if terms_used else '0'})] / {fmt(aii)} = {fmt_dec(val_i, 6)}"
                sub_lines.append(eq_str)
            curr_x = next_x

        # Métricas de la iteración k
        delta_vec = vec_sub(curr_x, prev_x)
        d_norm = norm_inf(delta_vec)
        x_norm = norm_inf(curr_x)

        rel_delta = (d_norm / x_norm) if x_norm > 0 else d_norm
        Ax_k = mat_vec_mul(A, curr_x)
        res_k = vec_sub(b, Ax_k)
        r_norm = norm_inf(res_k)

        history.append(
            IterationRow(
                k=k,
                x=tuple(curr_x),
                delta_norm=d_norm,
                relative_delta=rel_delta,
                residual_norm=r_norm,
                substitutions=tuple(sub_lines),
            )
        )

        # 1. Detección Temprana de Divergencia
        if d_norm > initial_scale * (Fraction(10) ** 8) or x_norm > initial_scale * (Fraction(10) ** 8):
            status = IterationStatus.DIVERGED
            rho_txt = f"ρ(T) ≈ {rho:.4f} ≥ 1" if rho is not None else "ρ(T) ≥ 1"
            summary = (
                f"El método diverge exponencialmente ({rho_txt}). "
                f"La norma de los valores explotó en la iteración {k} (‖x⁽ᵏ⁾‖_∞ > 10⁸)."
            )
            break

        # 2. Criterio de Paro por Convergencia
        measure = d_norm if criterion == StopCriterion.ABSOLUTE else rel_delta
        if measure < tolerance:
            status = IterationStatus.CONVERGED
            crit_name = "absoluto" if criterion == StopCriterion.ABSOLUTE else "relativo"
            summary = (
                f"Convergencia alcanzada exitosamente en la iteración {k} bajo criterio {crit_name} "
                f"(‖Δx⁽ᵏ⁾‖_∞ = {fmt_dec(d_norm, 8)} < ε = {fmt_dec(tolerance, 8)})."
            )
            break
    else:
        # Fin de bucle sin break
        status = IterationStatus.MAX_ITERATIONS
        summary = (
            f"Se alcanzó el límite máximo de {max_iter} iteraciones sin satisfacer la tolerancia ε = {fmt_dec(tolerance, 6)}. "
            f"Última discrepancia: {fmt_dec(history[-1].delta_norm, 8)}."
        )

    return IterationResult(
        method=method,
        status=status,
        iterations=history,
        tolerance=tolerance,
        stop_criterion=criterion,
        spectral_radius=rho,
        strictly_dominant=strictly_dom,
        is_symmetric_positive_definite=is_spd,
        summary=summary,
    )


# ------------------------------------------------------------------------------
# Visualización en Consola: Tablas, Banners y Diagnósticos
# ------------------------------------------------------------------------------

def print_banner_programa8() -> None:
    """Imprime el encabezado oficial del Programa 8."""
    print("=" * 78)
    print(r"""
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║                 UNIVERSIDAD AMERICANA (UAM) — FIA                        ║
  ║                   ÁLGEBRA LINEAL (MTM0120)                               ║
  ║            PROGRAMA 8: MÉTODOS ITERATIVOS DE RESOLUCIÓN                  ║
  ║                     JACOBI Y GAUSS-SEIDEL                                ║
  ║       100% Python Estándar · Aritmética de Fracciones Exactas            ║
  ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    print("  Grupo 4: Roberto F. Tercero, Steven Flores, Kellys Bellanger, Raúl Valverde")
    print("=" * 78)


def print_system(A: List[List[Fraction]], b: List[Fraction], title: str = "SISTEMA DE ECUACIONES [A | b]:") -> None:
    """Muestra el sistema aumentado en formato tabular alineado."""
    n = len(A)
    print(f"\n{title}")
    print("-" * (12 * n + 16))
    for i in range(n):
        row_str = "  ".join(f"{fmt(A[i][j]):>9}" for j in range(n))
        print(f"  [ {row_str}  |  {fmt(b[i]):>9} ]")
    print("-" * (12 * n + 16))


def print_preliminary_diagnostics(A: List[List[Fraction]], b: List[Fraction]) -> None:
    """Imprime el diagnóstico analítico de la matriz antes de iterar."""
    print("\n" + "=" * 78)
    print(" 🔍 DIAGNÓSTICO TEÓRICO PREVIO DE CONVERGENCIA")
    print("=" * 78)

    # 1. Ceros en diagonal
    n = len(A)
    zero_diags = [i + 1 for i in range(n) if A[i][i] == 0]
    if zero_diags:
        print(f" ⚠️  ALERTA CRÍTICA: Elementos diagonales nulos en ecuaciones: {zero_diags}.")
        print("    No es posible despejar directamente. Se requiere permutar filas.")
    else:
        print(" ✓ Diagonal no nula: aᵢᵢ ≠ 0 para todas las ecuaciones (despejes válidos).")

    # 2. Dominancia diagonal estricta
    strictly, details = check_strict_diagonal_dominance(A)
    print("\n • Análisis de Dominancia Diagonal Estricta por Filas (|aᵢᵢ| > ∑_{j≠i} |aᵢⱼ|):")
    for i, (diag, off, ok) in enumerate(details):
        mark = "✓ Cumple" if ok else "✗ No cumple"
        print(f"   Ecuación {i+1}: |{fmt(A[i][i])}| = {fmt_dec(diag, 4)}   vs   Suma off-diag = {fmt_dec(off, 4)}  -->  {mark}")

    if strictly:
        print("\n 🟢 TEOREMA GARANTIZADO: La matriz A es ESTRICTAMENTE DIAGONAL DOMINANTE.")
        print("    Por teorema fundamental, TANTO Jacobi COMO Gauss-Seidel CONVERGEN para")
        print("    cualquier vector inicial x⁽⁰⁾ ∈ ℝⁿ.")
    else:
        print("\n 🟡 AVISO TEÓRICO: La matriz NO es estrictamente diagonal dominante.")
        print("    La convergencia NO está garantizada a priori; dependerá del radio espectral ρ(T).")

    # 3. Matriz simétrica definida positiva
    is_sym, is_spd, minors = check_symmetric_positive_definite(A)
    if is_sym:
        print(f"\n • Simetría: La matriz A es Simétrica (A = Aᵀ).")
        print(f"   Menores principales de Sylvester: {[fmt(m) for m in minors]}")
        if is_spd:
            print(" 🟢 TEOREMA DE OSTROWSKI-REICH: A es SIMÉTRICA DEFINIDA POSITIVA (todos det > 0).")
            print("    Se GARANTIZA la convergencia de Gauss-Seidel para cualquier x⁽⁰⁾.")
        else:
            print(" 🟡 La matriz no es definida positiva (algún menor principal ≤ 0).")

    # 4. Radios espectrales
    try:
        T_J, _ = build_iteration_matrices(A, b, IterativeMethod.JACOBI)
        rho_j, _ = compute_spectral_radius(T_J)
        print(f"\n • Matriz de Iteración de Jacobi (T_J):        Radio espectral ρ(T_J)  ≈ {rho_j:.4f}")
        print(f"   Condición necesaria y suficiente: {'🟢 ρ(T_J) < 1 (CONVERGE)' if rho_j < 1.0 else '🔴 ρ(T_J) ≥ 1 (DIVERGE)'}")
    except Exception as exc:
        print(f"   No se pudo calcular T_J: {exc}")

    try:
        T_GS, _ = build_iteration_matrices(A, b, IterativeMethod.GAUSS_SEIDEL)
        rho_gs, _ = compute_spectral_radius(T_GS)
        print(f" • Matriz de Iteración de Gauss-Seidel (T_GS): Radio espectral ρ(T_GS) ≈ {rho_gs:.4f}")
        print(f"   Condición necesaria y suficiente: {'🟢 ρ(T_GS) < 1 (CONVERGE)' if rho_gs < 1.0 else '🔴 ρ(T_GS) ≥ 1 (DIVERGE)'}")
    except Exception as exc:
        print(f"   No se pudo calcular T_GS: {exc}")

    print("=" * 78)


def print_iteration_table(result: IterationResult, show_fractions: bool = False) -> None:
    """Imprime la tabla formal de iteraciones con columnas alineadas y métricas de error."""
    n = len(result.iterations[0].x)
    print(f"\n" + "=" * 88)
    print(f" TABLA DE ITERACIONES — MÉTODO DE {result.method.value.upper()}")
    print(f" Criterio de Paro: {result.stop_criterion.value} | Tolerancia ε = {fmt_dec(result.tolerance, 8)}")
    print("=" * 88)

    # Cabecera
    var_headers = "".join(f"{f'x{i+1}':>12}" for i in range(n))
    print(f"{'k':>4} | {var_headers} | {'||Δx||_∞':>12} | {'Err. Relat.':>12} | {'||r^(k)||_∞':>12}")
    print("-" * 88)

    # Filas
    for row in result.iterations:
        if show_fractions:
            vals = "".join(f"{fmt(xi):>12}" for xi in row.x)
        else:
            vals = "".join(f"{fmt_dec(xi, 6):>12}" for xi in row.x)

        delta_txt = fmt_dec(row.delta_norm, 6) if row.delta_norm is not None else "—"
        rel_txt = fmt_dec(row.relative_delta, 6) if row.relative_delta is not None else "—"
        res_txt = fmt_dec(row.residual_norm, 6)

        print(f"{row.k:>4} | {vals} | {delta_txt:>12} | {rel_txt:>12} | {res_txt:>12}")

    print("=" * 88)
    print(f" ESTADO FINAL: {result.status.value}")
    print(f" RESUMEN: {result.summary}")
    print("=" * 88)


def print_comparison_table(res_j: IterationResult, res_gs: IterationResult) -> None:
    """Muestra una comparación exhaustiva frente a frente entre Jacobi y Gauss-Seidel."""
    print("\n" + "=" * 80)
    print(" ⚖️  COMPARACIÓN FRENTE A FRENTE: JACOBI vs GAUSS-SEIDEL")
    print("=" * 80)

    print(f" {'Métrica / Característica':<35} | {'Jacobi':<20} | {'Gauss-Seidel':<20}")
    print("-" * 80)

    # 1. Estado
    print(f" {'Estado de Convergencia':<35} | {res_j.status.value:<20} | {res_gs.status.value:<20}")

    # 2. Iteraciones
    it_j = len(res_j.iterations) - 1
    it_gs = len(res_gs.iterations) - 1
    print(f" {'Iteraciones ejecutadas':<35} | {it_j:<20} | {it_gs:<20}")

    # 3. Radio Espectral
    rho_j_str = f"{res_j.spectral_radius:.4f}" if res_j.spectral_radius is not None else "N/A"
    rho_gs_str = f"{res_gs.spectral_radius:.4f}" if res_gs.spectral_radius is not None else "N/A"
    print(f" {'Radio Espectral ρ(T)':<35} | {rho_j_str:<20} | {rho_gs_str:<20}")

    # 4. Norma final de discrepancia ||Δx||_∞
    delta_j = fmt_dec(res_j.iterations[-1].delta_norm, 8) if res_j.iterations[-1].delta_norm else "—"
    delta_gs = fmt_dec(res_gs.iterations[-1].delta_norm, 8) if res_gs.iterations[-1].delta_norm else "—"
    print(f" {'Norma final de paso ||Δx||_∞':<35} | {delta_j:<20} | {delta_gs:<20}")

    # 5. Norma final del residuo ||b - Ax||_∞
    res_j_val = fmt_dec(res_j.iterations[-1].residual_norm, 8)
    res_gs_val = fmt_dec(res_gs.iterations[-1].residual_norm, 8)
    print(f" {'Residuo final ||b - Ax||_∞':<35} | {res_j_val:<20} | {res_gs_val:<20}")

    print("-" * 80)
    print("\n 💡 CONCLUSIÓN COMPARATIVA:")
    if res_j.status == IterationStatus.CONVERGED and res_gs.status == IterationStatus.CONVERGED:
        if it_gs < it_j:
            ratio = (it_j / it_gs) if it_gs > 0 else 1.0
            print(f"   ✓ Ambos métodos convergieron. Gauss-Seidel fue {ratio:.2f} veces más rápido")
            print(f"     (requirió {it_gs} iteraciones frente a {it_j} de Jacobi).")
            print(f"     Esto concuerda con que ρ(T_GS) < ρ(T_J).")
        elif it_j < it_gs:
            print(f"   ✓ Ambos métodos convergieron, pero Jacobi requirió menos iteraciones ({it_j} vs {it_gs}).")
        else:
            print("   ✓ Ambos métodos convergieron en la misma cantidad exacta de iteraciones.")
    elif res_j.status == IterationStatus.DIVERGED and res_gs.status == IterationStatus.CONVERGED:
        print(f"   ✓ Solo Gauss-Seidel converge ({it_gs} iteraciones). Jacobi diverge porque ρ(T_J) ≥ 1.")
    elif res_j.status == IterationStatus.CONVERGED and res_gs.status == IterationStatus.DIVERGED:
        print(f"   ✓ ¡Solo Jacobi converge ({it_j} iteraciones)! Gauss-Seidel diverge porque ρ(T_GS) ≥ 1.")
        print("     Demuestra formalmente que Gauss-Seidel NO siempre es superior a Jacobi.")
    else:
        print("   ✗ Ninguno de los dos métodos converge en el orden actual de las ecuaciones.")
        print("     Se sugiere probar la opción de reordenamiento de filas para forzar dominancia diagonal.")

    print("=" * 80)


# ------------------------------------------------------------------------------
# Casos de Prueba Didácticos Preconfigurados (Requerimiento Universitario)
# ------------------------------------------------------------------------------

def get_didactic_cases():
    """Retorna los casos de prueba pedagógicos diseñados para demostrar todos los
    comportamientos teóricos (convergencia simultánea, superioridad de GS,
    superioridad de Jacobi, divergencia y reordenamiento).
    """
    cases = [
        {
            "id": 1,
            "title": "Caso 1: Matriz Estrictamente Diagonal Dominante (Burden & Faires 4x4)",
            "description": "Ambos convergen; Gauss-Seidel converge en casi la mitad de iteraciones. Solución: (1, 2, -1, 1).",
            "A": [
                [Fraction(10), Fraction(-1), Fraction(2), Fraction(0)],
                [Fraction(-1), Fraction(11), Fraction(-1), Fraction(3)],
                [Fraction(2), Fraction(-1), Fraction(10), Fraction(-1)],
                [Fraction(0), Fraction(3), Fraction(-1), Fraction(8)],
            ],
            "b": [Fraction(6), Fraction(25), Fraction(-11), Fraction(15)],
            "x_exact": (1, 2, -1, 1),
            "expected": "Ambos convergen. GS requiere menos iteraciones.",
        },
        {
            "id": 2,
            "title": "Caso 2: Solo Gauss-Seidel Converge (ρ(T_J) > 1 y ρ(T_GS) < 1)",
            "description": "ρ(T_J) = √5/2 ≈ 1.118 (diverge). ρ(T_GS) = 0.5 (converge). Solución: (1, 2, -1).",
            "A": [
                [Fraction(2), Fraction(-1), Fraction(1)],
                [Fraction(2), Fraction(2), Fraction(2)],
                [Fraction(-1), Fraction(-1), Fraction(2)],
            ],
            "b": [Fraction(-1), Fraction(4), Fraction(-5)],
            "x_exact": (1, 2, -1),
            "expected": "Jacobi diverge exponencialmente. Gauss-Seidel converge.",
        },
        {
            "id": 3,
            "title": "Caso 3: Solo Jacobi Converge (¡Gauss-Seidel NO siempre es mejor!)",
            "description": "T_J es nilpotente (ρ(T_J) = 0, converge en 3 iteraciones). ρ(T_GS) = 2 > 1 (diverge). Solución: (1, 2, -1).",
            "A": [
                [Fraction(1), Fraction(2), Fraction(-2)],
                [Fraction(1), Fraction(1), Fraction(1)],
                [Fraction(2), Fraction(2), Fraction(1)],
            ],
            "b": [Fraction(7), Fraction(2), Fraction(5)],
            "x_exact": (1, 2, -1),
            "expected": "Jacobi converge rápidamente. Gauss-Seidel diverge.",
        },
        {
            "id": 4,
            "title": "Caso 4: Divergencia de Ambos Métodos (No Diagonal Dominante 2x2)",
            "description": "A = [[1, -5], [7, -1]]. Ninguno converge; las iteraciones explotan en magnitud.",
            "A": [
                [Fraction(1), Fraction(-5)],
                [Fraction(7), Fraction(-1)],
            ],
            "b": [Fraction(-4), Fraction(6)],
            "x_exact": (1, 1),
            "expected": "Ambos divergen.",
        },
        {
            "id": 5,
            "title": "Caso 5: Reordenamiento Exitoso de Ecuaciones (Restaura Dominancia y Convergencia)",
            "description": "Intercambia E1 ↔ E2 del Caso 4: A' = [[7, -1], [1, -5]]. ¡Ahora ambos convergen a (1, 1)!",
            "A": [
                [Fraction(7), Fraction(-1)],
                [Fraction(1), Fraction(-5)],
            ],
            "b": [Fraction(6), Fraction(-4)],
            "x_exact": (1, 1),
            "expected": "El reordenamiento transforma un sistema divergente en convergente.",
        },
        {
            "id": 6,
            "title": "Caso 6: Cero en la Diagonal Principal (a₁₁ = 0)",
            "description": "A = [[0, 2], [3, 1]]. Genera división por cero sin reordenamiento previo.",
            "A": [
                [Fraction(0), Fraction(2)],
                [Fraction(3), Fraction(1)],
            ],
            "b": [Fraction(4), Fraction(5)],
            "x_exact": (1, 2),
            "expected": "Detecta elemento diagonal cero y previene división por cero.",
        },
    ]
    return cases


def run_didactic_case_interactive() -> None:
    """Submenú interactivo para seleccionar y ejecutar los casos de prueba pedagógicos."""
    cases = get_didactic_cases()
    while True:
        print("\n" + "=" * 78)
        print(" 🧪 CASOS DE PRUEBA DIDÁCTICOS PRECONFIGURADOS")
        print(" Demostración de Convergencia, Divergencia y Comparación")
        print("=" * 78)
        for c in cases:
            print(f" {c['id']}. {c['title']}")
            print(f"    --> {c['description']}")
        print(" 0. Regresar al Menú Principal")
        print("=" * 78)

        opc = input("Seleccione un caso de prueba (0-6): ").strip()
        if opc == "0":
            break

        matching = [c for c in cases if str(c["id"]) == opc]
        if not matching:
            print(" ⚠️  Opción no válida. Ingrese un número de 0 a 6.")
            continue

        selected = matching[0]
        print("\n" + "=" * 78)
        print(f" EJECUTANDO: {selected['title']}")
        print("=" * 78)

        A = selected["A"]
        b = selected["b"]
        print_system(A, b, title="Sistema de Ecuaciones del Caso:")
        print_preliminary_diagnostics(A, b)

        # Si tiene cero en la diagonal, mostrar el manejo
        n = len(A)
        has_zero_diag = any(A[i][i] == 0 for i in range(n))
        if has_zero_diag:
            print("\n ⚠️  El sistema contiene ceros en la diagonal.")
            print("     Intentando reordenamiento automático de ecuaciones (pivoteo)...")
            A_reord, b_reord, perm, ok = reorder_for_dominance(A, b)
            if ok:
                print(f" ✓ Reordenamiento exitoso (permutación de filas: {[p+1 for p in perm]}).")
                print_system(A_reord, b_reord, title="Sistema Permutado:")
                A, b = A_reord, b_reord
            else:
                print(" ✗ No fue posible reordenar para eliminar ceros diagonales.")
                input("\nPresione ENTER para continuar...")
                continue

        tol = Fraction(1, 100000)
        max_iter = 40
        print(f"\n⚙️  Ejecutando con Tolerancia ε = {fmt_dec(tol, 6)} y máx iteraciones = {max_iter}...")

        res_j = solve_iterative(A, b, IterativeMethod.JACOBI, tolerance=tol, max_iter=max_iter)
        res_gs = solve_iterative(A, b, IterativeMethod.GAUSS_SEIDEL, tolerance=tol, max_iter=max_iter)

        print_iteration_table(res_j)
        print_iteration_table(res_gs)
        print_comparison_table(res_j, res_gs)

        if "x_exact" in selected:
            print(f"\n 🎯 Solución exacta esperada: {selected['x_exact']}")

        input("\nPresione ENTER para volver a la lista de casos de prueba...")


# ------------------------------------------------------------------------------
# Compendio de Teoremas y Preguntas de Defensa Individual
# ------------------------------------------------------------------------------

def mostrar_teoremas_iterativos() -> None:
    """Muestra el compendio de teoremas teóricos de métodos iterativos."""
    print("=" * 78)
    print(" 📖 COMPENDIO DE TEOREMAS CLAVE — MÉTODOS ITERATIVOS (JACOBI Y GAUSS-SEIDEL)")
    print("=" * 78)
    print("""
1. DESCOMPOSICIÓN MATRICIAL ADITIVA:
   Sea A ∈ ℝⁿˣⁿ con elementos diagonales aᵢᵢ ≠ 0. Se descompone A = D + L + U:
   • D = diag(a₁₁, a₂₂, ..., aₙₙ)
   • L = elementos estrictamente por debajo de la diagonal (lᵢⱼ = aᵢⱼ para i > j)
   • U = elementos estrictamente por encima de la diagonal (uᵢⱼ = aᵢⱼ para i < j)

2. MÉTODO DE JACOBI (Desplazamiento Simultáneo):
   • Forma por componentes:
       xᵢ⁽ᵏ⁺¹⁾ = (bᵢ - ∑_{j ≠ i} aᵢⱼ · xⱼ⁽ᵏ⁾) / aᵢᵢ
   • Forma matricial:
       x⁽ᵏ⁺¹⁾ = T_J · x⁽ᵏ⁾ + c_J
       donde T_J = -D⁻¹(L + U)  y  c_J = D⁻¹ · b.
   • Características: Todas las componentes nuevas se calculan simultáneamente
     empleando únicamente los valores de la iteración previa. Apto para cómputo en paralelo.

3. MÉTODO DE GAUSS-SEIDEL (Desplazamiento Sucesivo):
   • Forma por componentes:
       xᵢ⁽ᵏ⁺¹⁾ = (bᵢ - ∑_{j < i} aᵢⱼ · xⱼ⁽ᵏ⁺¹⁾ - ∑_{j > i} aᵢⱼ · xⱼ⁽ᵏ⁾) / aᵢᵢ
   • Forma matricial:
       x⁽ᵏ⁺¹⁾ = T_GS · x⁽ᵏ⁾ + c_GS
       donde T_GS = -(D + L)⁻¹ · U  y  c_GS = (D + L)⁻¹ · b.
   • Características: Cada nueva componente calculada se sustituye inmediatamente
     para evaluar las siguientes incógnitas dentro de la misma iteración.

4. CONDICIÓN SUFICIENTE: DOMINANCIA DIAGONAL ESTRICTA:
   • Definición: |aᵢᵢ| > ∑_{j ≠ i} |aᵢⱼ| para toda fila i = 1, ..., n.
   • Teorema: Si A es estrictamente diagonal dominante por filas, TANTO Jacobi
     COMO Gauss-Seidel CONVERGEN para cualquier vector inicial x⁽⁰⁾ ∈ ℝⁿ.
   • La dominancia diagonal es condición SUFICIENTE, pero NO NECESARIA.

5. CONDICIÓN NECESARIA Y SUFICIENTE: RADIO ESPECTRAL ρ(T):
   • El radio espectral se define como ρ(T) = máx |λᵢ|, donde λᵢ son los autovalores de T.
   • Teorema Fundamental: El método x⁽ᵏ⁺¹⁾ = T·x⁽ᵏ⁾ + c converge para todo x⁽⁰⁾ si
     y solo si:
         ρ(T) < 1.
   • Tasa asintótica de convergencia: R = -ln(ρ(T)). A menor ρ(T), mayor velocidad de convergencia.

6. MATRICES SIMÉTRICAS DEFINIDAS POSITIVAS (Teorema de Ostrowski-Reich):
   • Si A es simétrica (A = Aᵀ) y definida positiva (todos sus menores principales det > 0),
     el método de Gauss-Seidel converge garantizado para cualquier x⁽⁰⁾.

7. TEOREMA DE STEIN-ROSENBERG:
   • Si los elementos fuera de la diagonal son no positivos (aᵢⱼ ≤ 0 para i ≠ j) y aᵢᵢ > 0:
     a) Si ρ(T_J) < 1, entonces ρ(T_GS) < ρ(T_J) < 1 (Gauss-Seidel converge más rápido).
     b) Si ρ(T_J) ≥ 1, entonces ρ(T_GS) ≥ ρ(T_J) ≥ 1 (ambos divergen).
   • NOTA: Si la matriz tiene entradas de signos mixtos, Gauss-Seidel NO siempre es
     mejor; existen matrices donde Jacobi converge y Gauss-Seidel diverge.
""")
    print("=" * 78)


def mostrar_guia_defensa_individual() -> None:
    """Muestra la guía completa de defensa individual y preguntas frecuentes de examen."""
    print("=" * 78)
    print(" 🎓 GUÍA DE DEFENSA INDIVIDUAL — PREGUNTAS Y RESPUESTAS CONCEPTUALES")
    print(" Asignatura: Álgebra Lineal (MTM0120) — Grupo 4")
    print("=" * 78)
    print("""
PREGUNTA 1: ¿Cuál es la diferencia algorítmica fundamental entre Jacobi y Gauss-Seidel?
  RESPUESTA:
  • Jacobi utiliza "desplazamiento simultáneo": para calcular el vector x⁽ᵏ⁺¹⁾,
    todas las incógnitas se evalúan únicamente con los datos del vector anterior x⁽ᵏ⁾.
    Requiere almacenar dos vectores completos en memoria (el actual y el anterior).
  • Gauss-Seidel utiliza "desplazamiento sucesivo": en cuanto se calcula la nueva
    componente xᵢ⁽ᵏ⁺¹⁾, se sobrescribe en memoria y se utiliza de inmediato para
    calcular x_{i+1}⁽ᵏ⁺¹⁾ en esa misma iteración.

PREGUNTA 2: ¿Por qué la dominancia diagonal es suficiente pero no necesaria?
  RESPUESTA:
  • Es suficiente porque por el Teorema de Círculos de Gershgorin, si |aᵢᵢ| > ∑_{j≠i}|aᵢⱼ|,
    los autovalores de la matriz de iteración T_J caen estrictamente dentro del disco
    unitario abierto (|λ| < 1), asegurando ρ(T) < 1.
  • No es necesaria porque existen infinitas matrices que no son diagonal dominantes
    pero cuya matriz de iteración satisface ρ(T) < 1 (como demostramos en el Caso 2
    donde Gauss-Seidel converge con ρ = 0.5 a pesar de no haber dominancia).

PREGUNTA 3: ¿Es Gauss-Seidel SIEMPRE más rápido o mejor que Jacobi?
  RESPUESTA:
  • NO. Es una creencia común errónea. Gauss-Seidel es superior cuando se satisfacen
    las hipótesis del Teorema de Stein-Rosenberg (entradas no diagonales no positivas).
  • Si no se cumplen esas condiciones, Jacobi puede converger mientras Gauss-Seidel
    diverge. En el Caso de Prueba 3 demostramos un sistema con ρ(T_J) = 0 (Jacobi converge
    en 3 iteraciones) y ρ(T_GS) = 2 (Gauss-Seidel diverge exponencialmente).

PREGUNTA 4: ¿Por qué el equipo eligió usar fractions.Fraction en lugar de floats de Python?
  RESPUESTA:
  • En métodos numéricos, los números de punto flotante introducen errores de redondeo
    en cada multiplicación y división, enmascarando el error propio del método matemático.
  • Con `fractions.Fraction`, la aritmética es 100% exacta sin pérdida de dígitos. El
    único error observado en la tabla de iteraciones es el error de truncamiento del
    algoritmo iterativo, garantizando rigor algebraico y consistencia didáctica.

PREGUNTA 5: ¿Cómo detecta el programa cuándo detenerse y evitar ciclos infinitos si diverge?
  RESPUESTA:
  • Se implementaron tres salvaguardas simultáneas:
    1) Criterio de parada por tolerancia: ‖x⁽ᵏ⁾ - x⁽ᵏ⁻¹⁾‖_∞ < ε (o relativo).
    2) Cota máxima de iteraciones (por defecto 50 o 100 iteraciones).
    3) Detección temprana de divergencia por explosión de norma: si ‖x⁽ᵏ⁾‖_∞ supera
       10⁸ veces la escala inicial del problema, se aborta y se declara DIVERGENCIA
       inmediata sin esperar a agotar todas las iteraciones.

PREGUNTA 6: Si una matriz tiene ceros en la diagonal principal, ¿qué se debe hacer?
  RESPUESTA:
  • Un cero en la diagonal (aᵢᵢ = 0) provocaría una división por cero al despejar xᵢ.
  • El programa detecta esta condición y aplica el algoritmo `reorder_for_dominance`,
    que busca una permutación de filas que coloque los coeficientes de mayor magnitud
    en la diagonal principal (pivoteo de ecuaciones), restaurando la viabilidad del método.
""")
    print("=" * 78)


# ------------------------------------------------------------------------------
# Flujo Interactivo de Entrada del Usuario
# ------------------------------------------------------------------------------

def resolver_sistema_interactivo(modo: str = "ambos") -> None:
    """Solicita al usuario los datos de un sistema A·x = b y ejecuta la resolución."""
    print("\n" + "=" * 78)
    print(" INGRESO DE SISTEMA DE ECUACIONES [A | b]")
    print(" (Puede ingresar enteros, fracciones como '3/4' o decimales como '0.5')")
    print("=" * 78)

    n = read_positive_int("Ingrese el número de incógnitas y ecuaciones (dimensión n): ")

    A: List[List[Fraction]] = []
    print("\n>> Ingrese los coeficientes de la matriz A (fila por fila):")
    for i in range(n):
        row: List[Fraction] = []
        print(f"   --- Fila {i+1} ---")
        for j in range(n):
            val = read_scalar(f"      a[{i+1},{j+1}]: ")
            row.append(val)
        A.append(row)

    b: List[Fraction] = []
    print("\n>> Ingrese los términos independientes del vector b:")
    for i in range(n):
        val = read_scalar(f"   b[{i+1}]: ")
        b.append(val)

    print_system(A, b)
    print_preliminary_diagnostics(A, b)

    # Verificar diagonal
    has_zero_diag = any(A[i][i] == 0 for i in range(n))
    if has_zero_diag:
        print("\n⚠️  ¡Atención! La matriz contiene al menos un elemento diagonal nulo.")
        resp = input("¿Desea que el sistema intente reordenar las ecuaciones automáticamente? (s/n): ").strip().lower()
        if resp in ("s", "si", "sí", "y", "yes"):
            A_reord, b_reord, perm, ok = reorder_for_dominance(A, b)
            if ok:
                print(f" ✓ Reordenamiento exitoso a matriz diagonal dominante (orden: {[p+1 for p in perm]}).")
                A, b = A_reord, b_reord
                print_system(A, b, title="Sistema Reordenado:")
            else:
                print(" ⚠️  No se encontró permutación estrictamente dominante, pero se aplicó la mejor disponible.")
                A, b = A_reord, b_reord
                print_system(A, b, title="Sistema Mejor Reordenado:")

    # Parámetros del método
    print("\n" + "-" * 78)
    print("PARÁMETROS DEL MÉTODO ITERATIVO:")
    print("-" * 78)
    tol = read_tolerance("Tolerancia ε (ENTER para 0.0001): ", default=Fraction(1, 10000))
    max_iter = read_positive_int("Máximo de iteraciones (ENTER para 50): ", default=50)

    print("\nSeleccione el criterio de parada:")
    print("  1. Criterio Absoluto: ||x^(k) - x^(k-1)||_inf < ε")
    print("  2. Criterio Relativo: ||x^(k) - x^(k-1)||_inf / ||x^(k)||_inf < ε")
    crit_opc = input("Opción (1 o 2, ENTER para 1): ").strip()
    criterion = StopCriterion.RELATIVE if crit_opc == "2" else StopCriterion.ABSOLUTE

    # Vector inicial
    use_custom_x0 = input("\n¿Desea ingresar un vector inicial x⁽⁰⁾ personalizado? (s/n, ENTER para vector cero [0, ..., 0]): ").strip().lower()
    x0: Optional[List[Fraction]] = None
    if use_custom_x0 in ("s", "si", "sí", "y", "yes"):
        x0 = []
        print(">> Ingrese los valores de x⁽⁰⁾:")
        for i in range(n):
            x0.append(read_scalar(f"   x⁽⁰⁾[{i+1}]: "))

    # Ejecución
    if modo in ("jacobi", "ambos"):
        res_j = solve_iterative(A, b, IterativeMethod.JACOBI, x0=x0, tolerance=tol, max_iter=max_iter, criterion=criterion)
        print_iteration_table(res_j)

    if modo in ("gauss_seidel", "ambos"):
        res_gs = solve_iterative(A, b, IterativeMethod.GAUSS_SEIDEL, x0=x0, tolerance=tol, max_iter=max_iter, criterion=criterion)
        print_iteration_table(res_gs)

    if modo == "ambos":
        print_comparison_table(res_j, res_gs)


# ------------------------------------------------------------------------------
# Menú Principal de Consola del Programa 8
# ------------------------------------------------------------------------------

def menu_programa8() -> None:
    """Bucle del Menú Principal del Programa 8_Grupo4."""
    while True:
        print_banner_programa8()
        print(" Menú de Opciones:")
        print("   0. 📖 Ver Compendio de Teoremas Clave del Módulo")
        print("   1. 🔄 Resolver Sistema por Método de Jacobi (Paso a Paso)")
        print("   2. ⚡ Resolver Sistema por Método de Gauss-Seidel (Paso a Paso)")
        print("   3. ⚖️  Comparar Ambos Métodos en el Mismo Sistema (Frente a Frente)")
        print("   4. 🧪 Demostración Guiada de Casos de Prueba Didácticos")
        print("   5. 🎓 Guía de Defensa Individual para el Grupo (Preguntas de Examen)")
        print("   6. 🚪 Salir del Programa")
        print("=" * 78)

        opc = input("Seleccione una opción (0-6): ").strip()

        if opc == "0":
            mostrar_teoremas_iterativos()
            input("\nPresione ENTER para regresar al menú principal...")
        elif opc == "1":
            try:
                resolver_sistema_interactivo(modo="jacobi")
            except Exception as exc:
                print(f"\n⚠️  Error durante la ejecución: {exc}")
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            try:
                resolver_sistema_interactivo(modo="gauss_seidel")
            except Exception as exc:
                print(f"\n⚠️  Error durante la ejecución: {exc}")
            input("\nPresione ENTER para continuar...")
        elif opc == "3":
            try:
                resolver_sistema_interactivo(modo="ambos")
            except Exception as exc:
                print(f"\n⚠️  Error durante la ejecución: {exc}")
            input("\nPresione ENTER para continuar...")
        elif opc == "4":
            run_didactic_case_interactive()
        elif opc == "5":
            mostrar_guia_defensa_individual()
            input("\nPresione ENTER para regresar al menú principal...")
        elif opc == "6":
            print("\n" + "=" * 78)
            print(" ¡Gracias por utilizar PrettyCalc - Álgebra Lineal Grupo 4!")
            print(" Sesión del Programa 8 finalizada exitosamente.")
            print("=" * 78 + "\n")
            break
        else:
            print("   ⚠️  Opción no válida. Por favor ingrese un número entre 0 y 6.")
            input("Presione ENTER para reintentar...")


if __name__ == "__main__":
    menu_programa8()
