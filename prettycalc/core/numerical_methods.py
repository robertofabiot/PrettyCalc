"""Métodos Numéricos — Lógica pura del módulo 9 de PrettyCalc.

Asignatura: Álgebra Lineal / Métodos Numéricos, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.

Contenido:
  A. Bisección: raíces de f(x) con historial iterativo y contraste contra SciPy.
  B. Graficador: arrays NumPy X/Y para f(x) con manejo de discontinuidades.
  C. Notación Posicional: descomposición de enteros en base 10 y base 2.
  D. Errores Numéricos: propagación de error y cálculo de error absoluto/relativo.

Restricciones:
  - PROHIBIDO usar eval() de Python. Parseo vía sympy.sympify + lambdify.
  - Sin importaciones de prettycalc.ui.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ── Parseo seguro de expresiones matemáticas ──────────────────────────────────
import sympy
from sympy import sympify, lambdify, symbols, Symbol
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

# ── Librerías numéricas (opcionales: se importan con guardia) ─────────────────
try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:  # pragma: no cover
    _NUMPY_OK = False

try:
    from scipy.optimize import bisect as scipy_bisect
    _SCIPY_OK = True
except ImportError:  # pragma: no cover
    _SCIPY_OK = False

# ---------------------------------------------------------------------------
# Namespace seguro para sympify / lambdify
# ---------------------------------------------------------------------------

_SYMPY_LOCALS: dict = {
    "sin": sympy.sin, "cos": sympy.cos, "tan": sympy.tan,
    "asin": sympy.asin, "acos": sympy.acos, "atan": sympy.atan,
    "sinh": sympy.sinh, "cosh": sympy.cosh, "tanh": sympy.tanh,
    "exp": sympy.exp, "log": sympy.log, "ln": sympy.log,
    "sqrt": sympy.sqrt, "abs": sympy.Abs, "Abs": sympy.Abs,
    "pi": sympy.pi, "e": sympy.E,
    "E": sympy.E,
}

_NUMPY_MODULES = [
    {"sin": np.sin, "cos": np.cos, "tan": np.tan,
     "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
     "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
     "exp": np.exp, "log": np.log, "ln": np.log,
     "sqrt": np.sqrt, "abs": np.abs, "Abs": np.abs,
     "pi": np.pi, "e": np.e, "E": np.e,
     "log2": np.log2, "log10": np.log10,
     "Piecewise": lambda *args: args[0][0],
     } if _NUMPY_OK else {},
    "numpy",
]

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def _parse_function(expr_str: str) -> Tuple[Symbol, sympy.Expr, object]:
    """Parsea un string de función usando sympy (nunca eval).

    Returns:
        (x_sym, sympy_expr, lambda_func)

    Raises:
        ValueError: si la expresión no es válida.
    """
    x = symbols("x")
    try:
        expr = parse_expr(
            expr_str,
            local_dict={"x": x, **_SYMPY_LOCALS},
            transformations=_TRANSFORMATIONS,
        )
    except Exception as exc:
        raise ValueError(f"Expresión inválida: {exc}") from exc

    # Asegurar que contiene solo la variable x
    free = expr.free_symbols - {x}
    if free:
        raise ValueError(
            f"La expresión contiene variables no permitidas: {', '.join(str(s) for s in free)}"
        )

    try:
        func = lambdify(x, expr, modules=_NUMPY_MODULES)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"No se pudo compilar la función: {exc}") from exc

    return x, expr, func


# ===========================================================================
# A. BISECCIÓN
# ===========================================================================

@dataclass
class BisectionRow:
    """Una fila del historial iterativo de la bisección."""
    k: int
    a: float
    b: float
    xr: float
    fa: float
    fb: float
    fxr: float
    eb: float            # cota de error (b-a)/2
    ea: str              # error relativo aproximado (string para manejar "-" y "No definido")


@dataclass
class BisectionResult:
    """Resultado completo del método de bisección."""
    # Parámetros de entrada registrados
    expr_str: str
    a0: float
    b0: float
    tol: float
    max_iter: int

    # Análisis previo
    theoretical_iters: int    # ceil(log2((b-a)/E))
    fa0: float
    fb0: float

    # Historial
    history: List[BisectionRow] = field(default_factory=list)

    # Resultado
    root: Optional[float] = None
    converged: bool = False
    stop_reason: str = ""

    # Contraste SciPy
    scipy_root: Optional[float] = None
    scipy_diff: Optional[float] = None
    scipy_available: bool = False


def bisection(
    expr_str: str,
    a: float,
    b: float,
    tol: float,
    max_iter: int,
) -> BisectionResult:
    """Método de bisección para encontrar raíces de f(x) = 0.

    Args:
        expr_str: Expresión de f(x) como string (ej. "x**3 - 2*x - 5").
        a: Extremo izquierdo del intervalo.
        b: Extremo derecho del intervalo.
        tol: Tolerancia de error (> 0).
        max_iter: Número máximo de iteraciones (≥ 1).

    Returns:
        BisectionResult con historial completo.

    Raises:
        ValueError: Si los parámetros son inválidos o f(a)*f(b) >= 0.
    """
    # ── Validaciones de entrada ───────────────────────────────────────────────
    if a >= b:
        raise ValueError(f"Se requiere a < b. Se recibió a={a}, b={b}.")
    if tol <= 0:
        raise ValueError(f"La tolerancia debe ser positiva. Se recibió E={tol}.")
    if max_iter < 1:
        raise ValueError(f"max_iter debe ser ≥ 1. Se recibió {max_iter}.")

    _x_sym, _expr, func = _parse_function(expr_str)

    # ── Evaluar extremos ──────────────────────────────────────────────────────
    try:
        fa = float(func(a))
        fb = float(func(b))
    except Exception as exc:
        raise ValueError(f"Error al evaluar f en los extremos: {exc}") from exc

    if not math.isfinite(fa):
        raise ValueError(f"f(a) = f({a}) no es finito: {fa}.")
    if not math.isfinite(fb):
        raise ValueError(f"f(b) = f({b}) no es finito: {fb}.")

    # Raíces exactas en los extremos
    if fa == 0.0:
        theo = math.ceil(math.log2((b - a) / tol)) if (b - a) > 0 and tol > 0 else 0
        return BisectionResult(
            expr_str=expr_str, a0=a, b0=b, tol=tol, max_iter=max_iter,
            theoretical_iters=theo, fa0=fa, fb0=fb,
            root=a, converged=True,
            stop_reason=f"f(a) = 0 exacto. La raíz es x = {a}.",
            scipy_available=False,
        )
    if fb == 0.0:
        theo = math.ceil(math.log2((b - a) / tol)) if (b - a) > 0 and tol > 0 else 0
        return BisectionResult(
            expr_str=expr_str, a0=a, b0=b, tol=tol, max_iter=max_iter,
            theoretical_iters=theo, fa0=fa, fb0=fb,
            root=b, converged=True,
            stop_reason=f"f(b) = 0 exacto. La raíz es x = {b}.",
            scipy_available=False,
        )

    if fa * fb >= 0:
        raise ValueError(
            f"f(a)·f(b) = {fa:.6g}·{fb:.6g} ≥ 0. "
            "No se garantiza cambio de signo en el intervalo. "
            "Verifica que el intervalo contenga una raíz."
        )

    # ── Iteraciones teóricas ──────────────────────────────────────────────────
    theo = math.ceil(math.log2((b - a) / tol))

    result = BisectionResult(
        expr_str=expr_str, a0=a, b0=b, tol=tol, max_iter=max_iter,
        theoretical_iters=theo, fa0=fa, fb0=fb,
    )

    # ── Iteraciones ───────────────────────────────────────────────────────────
    ak, bk = a, b
    xr_prev: Optional[float] = None

    for k in range(1, max_iter + 1):
        xr = (ak + bk) / 2.0
        eb = (bk - ak) / 2.0

        try:
            fxr = float(func(xr))
        except Exception:
            fxr = float("nan")

        try:
            fak = float(func(ak))
            fbk = float(func(bk))
        except Exception:
            fak = float("nan")
            fbk = float("nan")

        # Error relativo aproximado
        if k == 1:
            ea_str = "—"
        elif xr == 0.0:
            ea_str = "No definido"
        else:
            ea_val = abs((xr - xr_prev) / xr)  # type: ignore[arg-type]
            ea_str = f"{ea_val:.6e}"

        result.history.append(BisectionRow(
            k=k, a=ak, b=bk, xr=xr,
            fa=fak, fb=fbk, fxr=fxr,
            eb=eb, ea=ea_str,
        ))

        xr_prev = xr

        # ── Criterio de convergencia ──────────────────────────────────────────
        if abs(fxr) == 0.0:
            result.root = xr
            result.converged = True
            result.stop_reason = f"f(xr) = 0 exacto en iteración {k}."
            break

        if eb <= tol:
            result.root = xr
            result.converged = True
            result.stop_reason = (
                f"Convergió en iteración {k}: "
                f"cota de error Eβ = {eb:.6e} ≤ {tol:.6e}."
            )
            break

        # Actualizar intervalo
        if fak * fxr < 0:
            bk = xr
        else:
            ak = xr
    else:
        result.root = xr_prev
        result.converged = False
        result.stop_reason = (
            f"Se alcanzó el límite de {max_iter} iteraciones. "
            f"Mejor aproximación: xr = {xr_prev:.10g}."
        )

    # ── Contraste con SciPy ───────────────────────────────────────────────────
    if _SCIPY_OK and result.root is not None:
        try:
            sp_root = scipy_bisect(func, a, b, xtol=tol * 1e-3, maxiter=1000)
            result.scipy_root = float(sp_root)
            result.scipy_diff = abs(result.root - result.scipy_root)
            result.scipy_available = True
        except Exception:
            result.scipy_available = False
    else:
        result.scipy_available = _SCIPY_OK

    return result


# ===========================================================================
# B. GRAFICADOR
# ===========================================================================

@dataclass
class PlotData:
    """Arrays X/Y para graficar f(x), con NaN en discontinuidades."""
    x: "np.ndarray"
    y: "np.ndarray"
    expr_str: str
    x_min: float
    x_max: float


def compute_plot_data(
    expr_str: str,
    x_min: float,
    x_max: float,
    n_points: int = 1000,
    jump_threshold: float = 1e4,
) -> PlotData:
    """Genera arrays NumPy para graficar f(x) con manejo de discontinuidades.

    Args:
        expr_str: Expresión de f(x) como string.
        x_min: Límite inferior del eje x.
        x_max: Límite superior del eje x.
        n_points: Número de puntos (≥ 1000).
        jump_threshold: Saltos mayores a este valor se marcan como NaN.

    Returns:
        PlotData con arrays X e Y listos para matplotlib.

    Raises:
        ValueError: Si x_min >= x_max o la expresión es inválida.
        ImportError: Si NumPy no está disponible.
    """
    if not _NUMPY_OK:
        raise ImportError("NumPy no está instalado.")
    if x_min >= x_max:
        raise ValueError(f"x_min debe ser menor que x_max. Se recibió [{x_min}, {x_max}].")

    n_points = max(n_points, 1000)
    _x_sym, _expr, func = _parse_function(expr_str)

    x_arr = np.linspace(x_min, x_max, n_points, dtype=float)

    try:
        y_arr = np.array(func(x_arr), dtype=complex)
    except Exception:
        # Evaluar punto a punto como fallback
        y_arr = np.array(
            [func(xi) for xi in x_arr], dtype=complex
        )

    # Descartar partes imaginarias → NaN
    has_imag = np.abs(y_arr.imag) > 1e-10
    y_real = y_arr.real.copy()
    y_real[has_imag] = np.nan

    # Descartar infinitos y NaN originales
    y_real[~np.isfinite(y_real)] = np.nan

    # Detectar valores absurdamente grandes (asíntotas que no dan ±inf exacto)
    with np.errstate(invalid="ignore"):
        abs_y = np.abs(y_real)
        # Umbral adaptativo: si el rango real es pequeño pero algunos puntos son enormes
        finite_vals = abs_y[np.isfinite(abs_y)]
        if len(finite_vals) > 10:
            median_abs = float(np.median(finite_vals))
            # Marcar NaN puntos > 1000× la mediana (protege contra asíntotas suaves)
            extreme_mask = abs_y > max(jump_threshold, median_abs * 1000)
            y_real[extreme_mask] = np.nan

    # Detectar saltos bruscos (asíntotas verticales) → NaN en los bordes
    with np.errstate(invalid="ignore"):
        diffs = np.abs(np.diff(y_real))
        jump_mask = diffs > jump_threshold
        y_real[:-1][jump_mask] = np.nan
        y_real[1:][jump_mask] = np.nan

    return PlotData(x=x_arr, y=y_real, expr_str=expr_str, x_min=x_min, x_max=x_max)


# ===========================================================================
# C. NOTACIÓN POSICIONAL
# ===========================================================================

@dataclass
class PositionalResult:
    """Resultado de la descomposición posicional de un entero."""
    number: int
    abs_number: int
    is_negative: bool

    # Base 10
    digits_10: List[Tuple[int, int]]   # lista de (dígito, potencia)
    base10_expr: str                   # "8·10⁴ + 5·10² + ..."
    base10_sum: str                    # "80000 + 500 + ..."

    # Base 2
    digits_2: List[Tuple[int, int]]    # lista de (bit, potencia)
    base2_repr: str                    # "10011010"
    base2_expr: str                    # "1·2⁷ + 0·2⁶ + ..."
    base2_sum: str                     # "128 + 0 + ..."
    base2_decimal_check: int           # suma de los valores binarios


_SUPS = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")


def _to_superscript(n: int) -> str:
    return str(n).translate(_SUPS)


def compute_positional(number: int) -> PositionalResult:
    """Descompone un entero en notación posicional base 10 y base 2.

    Args:
        number: El entero a descomponer (positivo o negativo).

    Returns:
        PositionalResult con la descomposición completa y texto formateado.

    Raises:
        ValueError: Si number == 0 (caso trivial sin potencias significativas).
        TypeError: Si number no es entero.
    """
    if not isinstance(number, int):
        raise TypeError(f"Se requiere un entero. Se recibió {type(number).__name__}.")
    if number == 0:
        return PositionalResult(
            number=0, abs_number=0, is_negative=False,
            digits_10=[(0, 0)],
            base10_expr="0·10⁰",
            base10_sum="0",
            digits_2=[(0, 0)],
            base2_repr="0",
            base2_expr="0·2⁰",
            base2_sum="0",
            base2_decimal_check=0,
        )

    abs_n = abs(number)
    is_neg = number < 0

    # ── Base 10 ───────────────────────────────────────────────────────────────
    digits_10: List[Tuple[int, int]] = []
    s = str(abs_n)
    n_digits = len(s)
    for i, ch in enumerate(s):
        d = int(ch)
        exp = n_digits - 1 - i
        digits_10.append((d, exp))

    base10_parts_expr = [
        f"{d}·10{_to_superscript(e)}" for d, e in digits_10
    ]
    base10_parts_sum = [
        str(d * (10 ** e)) for d, e in digits_10
    ]
    base10_expr = " + ".join(base10_parts_expr)
    base10_sum = " + ".join(base10_parts_sum)

    # ── Base 2 ────────────────────────────────────────────────────────────────
    digits_2: List[Tuple[int, int]] = []
    n_temp = abs_n
    max_exp = max(int(math.log2(abs_n)), 0) if abs_n > 0 else 0

    bits: List[int] = []
    for exp in range(max_exp, -1, -1):
        bit = 1 if n_temp >= (2 ** exp) else 0
        bits.append(bit)
        if bit:
            n_temp -= 2 ** exp
        digits_2.append((bit, exp))

    base2_repr = "".join(str(b) for b in bits)
    base2_parts_expr = [
        f"{b}·2{_to_superscript(e)}" for b, e in digits_2
    ]
    base2_parts_sum = [
        str(b * (2 ** e)) for b, e in digits_2
    ]
    base2_expr = " + ".join(base2_parts_expr)
    base2_sum = " + ".join(base2_parts_sum)
    base2_decimal_check = sum(b * (2 ** e) for b, e in digits_2)

    return PositionalResult(
        number=number,
        abs_number=abs_n,
        is_negative=is_neg,
        digits_10=digits_10,
        base10_expr=base10_expr,
        base10_sum=base10_sum,
        digits_2=digits_2,
        base2_repr=base2_repr,
        base2_expr=base2_expr,
        base2_sum=base2_sum,
        base2_decimal_check=base2_decimal_check,
    )


# ===========================================================================
# D. ERRORES NUMÉRICOS
# ===========================================================================

@dataclass
class ErrorPropagationResult:
    """Resultado de la propagación de error para f(x) = sin(x) + x²."""
    x: float
    dx: float            # Δx
    fx: float            # f(x)
    fx_dx: float         # f(x + Δx)
    fpx: float           # f'(x) = cos(x) + 2x
    dy_approx: float     # Δy ≈ f'(x)·Δx
    dy_real: float       # Δy_real = f(x+Δx) - f(x)
    abs_diff: float      # |Δy_approx - Δy_real|


@dataclass
class NumericalErrorResult:
    """Resultado del cálculo de errores dado un valor verdadero y aproximado."""
    x_true: float
    x_approx: float
    abs_error: float              # |x_v - x_a|
    rel_error: Optional[float]    # |x_v - x_a| / |x_v|
    rel_error_pct: Optional[float]  # error relativo × 100
    zero_true: bool               # True si x_v == 0 (división imposible)


def propagate_error(x: float, dx: float) -> ErrorPropagationResult:
    """Calcula propagación de error para f(x) = sin(x) + x².

    Args:
        x: Punto de evaluación.
        dx: Perturbación Δx.

    Returns:
        ErrorPropagationResult con el desglose completo.
    """
    fx = math.sin(x) + x ** 2
    fx_dx = math.sin(x + dx) + (x + dx) ** 2
    fpx = math.cos(x) + 2 * x
    dy_approx = fpx * dx
    dy_real = fx_dx - fx
    abs_diff = abs(dy_approx - dy_real)

    return ErrorPropagationResult(
        x=x, dx=dx,
        fx=fx, fx_dx=fx_dx,
        fpx=fpx,
        dy_approx=dy_approx,
        dy_real=dy_real,
        abs_diff=abs_diff,
    )


def compute_numerical_error(x_true: float, x_approx: float) -> NumericalErrorResult:
    """Calcula errores absoluto, relativo y relativo porcentual.

    Args:
        x_true: Valor verdadero (xᵥ).
        x_approx: Valor aproximado (xₐ).

    Returns:
        NumericalErrorResult. Si x_true == 0, rel_error y rel_error_pct son None.
    """
    abs_error = abs(x_true - x_approx)
    if x_true == 0.0:
        return NumericalErrorResult(
            x_true=x_true, x_approx=x_approx,
            abs_error=abs_error,
            rel_error=None, rel_error_pct=None,
            zero_true=True,
        )
    rel_error = abs_error / abs(x_true)
    return NumericalErrorResult(
        x_true=x_true, x_approx=x_approx,
        abs_error=abs_error,
        rel_error=rel_error,
        rel_error_pct=rel_error * 100.0,
        zero_true=False,
    )
