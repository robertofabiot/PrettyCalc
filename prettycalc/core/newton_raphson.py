"""Newton-Raphson — lógica pura (Programa 9).

RESUMEN — qué hace este archivo (devuelve dataclasses, sin PySide6):
  1. Deriva f(x) de forma simbólica con SymPy (sympy.diff).
  2. Itera x_{i+1} = x_i − f(x_i) / f'(x_i) desde un valor inicial x0.
  3. Calcula el error aproximado εa(%) = |x_{i+1} − x_i| / |x_{i+1}| × 100.
     Si x_{i+1} = 0 no se divide: se usa el error absoluto |x_{i+1} − x_i|.
  4. Protege el proceso: f'(x_i) cero o muy cercana a cero, valores no finitos,
     máximo de iteraciones y residuo |f(x_aprox)| al final.

CRITERIOS DE PARADA (en este orden):
  - "converged":       εa ≤ tolerancia (en %; si se usó error absoluto, ≤ tol/100).
  - "derivative_zero": |f'(x_i)| < umbral → no se divide, se explica el motivo.
  - "non_finite":      f(x_i), f'(x_i) o x_{i+1} no son números finitos.
  - "max_iter":        se agotaron las iteraciones sin cumplir la tolerancia.

RESTRICCIONES:
  - Sin eval(): la función se parsea con SymPy (ver numerical_methods._parse_function).
  - No usa scipy.optimize.newton: el método está programado aquí.
  - Sin importaciones de prettycalc.ui (separación estricta core/ui).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

import sympy
from sympy import lambdify

from prettycalc.core.numerical_methods import _NUMPY_MODULES, _parse_function

# Valores por defecto mostrados al usuario en la interfaz.
DEFAULT_TOL_PCT = 0.0001      # tolerancia sobre εa, en porcentaje
DEFAULT_MAX_ITER = 50         # máximo de iteraciones
DEFAULT_DERIV_TOL = 1e-10     # |f'(x)| por debajo de esto se considera cero

STATUS_CONVERGED = "converged"
STATUS_DERIVATIVE_ZERO = "derivative_zero"
STATUS_NON_FINITE = "non_finite"
STATUS_MAX_ITER = "max_iter"


@dataclass
class NewtonRow:
    """Una fila de la tabla de iteraciones."""
    i: int                     # número de iteración (1, 2, …)
    x_i: float                 # aproximación de partida de la iteración
    f_xi: float                # f(x_i)
    df_xi: float               # f'(x_i)
    x_next: Optional[float]    # x_{i+1}; None si no se pudo calcular
    ea: Optional[float]        # error aproximado (valor numérico)
    ea_unit: str               # "%" si es relativo, "abs" si es absoluto (x_{i+1} = 0)


@dataclass
class NewtonResult:
    """Resultado completo del método de Newton-Raphson."""
    expr_str: str
    derivative_str: str        # f'(x) simbólica, como texto
    x0: float
    tol_pct: float
    max_iter: int
    deriv_tol: float

    history: List[NewtonRow] = field(default_factory=list)
    status: str = ""
    message: str = ""
    root: Optional[float] = None   # aproximación obtenida (no es "raíz exacta")
    iterations: int = 0
    last_ea: Optional[float] = None
    last_ea_unit: str = ""
    residual: Optional[float] = None   # |f(x_aprox)|

    @property
    def converged(self) -> bool:
        return self.status == STATUS_CONVERGED


def _to_float(func, value: float) -> Optional[float]:
    """Evalúa func(value) y devuelve float finito, o None si no es posible."""
    try:
        result = float(func(value))
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def newton_raphson(
    expr_str: str,
    x0: float,
    tol_pct: float = DEFAULT_TOL_PCT,
    max_iter: int = DEFAULT_MAX_ITER,
    deriv_tol: float = DEFAULT_DERIV_TOL,
) -> NewtonResult:
    """Aproxima una raíz de f(x) = 0 con el método de Newton-Raphson.

    Args:
        expr_str: f(x) como texto compatible con SymPy (ej. "x**2 - 2").
        x0: valor inicial.
        tol_pct: tolerancia sobre el error aproximado εa, en porcentaje (> 0).
        max_iter: máximo de iteraciones (≥ 1).
        deriv_tol: si |f'(x_i)| < deriv_tol, el proceso se detiene (> 0).

    Returns:
        NewtonResult con el historial y el estado final.

    Raises:
        ValueError: si la expresión o las entradas numéricas no son válidas.
    """
    # ── Validación de entradas ───────────────────────────────────────────────
    if not math.isfinite(x0):
        raise ValueError(f"El valor inicial x0 debe ser finito. Se recibió {x0}.")
    if not (tol_pct > 0 and math.isfinite(tol_pct)):
        raise ValueError(f"La tolerancia debe ser un número positivo. Se recibió {tol_pct}.")
    if max_iter < 1:
        raise ValueError(f"El máximo de iteraciones debe ser ≥ 1. Se recibió {max_iter}.")
    if deriv_tol <= 0:
        raise ValueError(f"El umbral de derivada cero debe ser positivo. Se recibió {deriv_tol}.")

    # ── Derivada simbólica con SymPy ─────────────────────────────────────────
    x_sym, expr, func = _parse_function(expr_str)
    derivative = sympy.diff(expr, x_sym)
    try:
        dfunc = lambdify(x_sym, derivative, modules=_NUMPY_MODULES)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"No se pudo compilar f'(x): {exc}") from exc

    if _to_float(func, x0) is None:
        raise ValueError(f"f(x0) = f({x0}) no es un número finito; elige otro valor inicial.")

    result = NewtonResult(
        expr_str=expr_str,
        derivative_str=str(derivative),
        x0=x0,
        tol_pct=tol_pct,
        max_iter=max_iter,
        deriv_tol=deriv_tol,
    )

    # ── Iteraciones ──────────────────────────────────────────────────────────
    x = x0
    for i in range(1, max_iter + 1):
        f_x = _to_float(func, x)
        df_x = _to_float(dfunc, x)

        # Valores no finitos: no se puede continuar.
        if f_x is None or df_x is None:
            result.history.append(NewtonRow(i, x, math.nan, math.nan, None, None, ""))
            result.status = STATUS_NON_FINITE
            result.message = (
                f"En la iteración {i} f(x) o f'(x) no es finita en x = {x:.6g}. "
                "El proceso se detiene; prueba con otro valor inicial."
            )
            break

        # Derivada nula o muy cercana a cero: NO se divide.
        if abs(df_x) < deriv_tol:
            result.history.append(NewtonRow(i, x, f_x, df_x, None, None, ""))
            result.status = STATUS_DERIVATIVE_ZERO
            result.message = (
                f"En la iteración {i} la derivada es |f'(x)| = {abs(df_x):.3g} < {deriv_tol:.3g} "
                f"(≈ 0). El paso de Newton no se puede calcular de forma estable. "
                "Prueba con otro valor inicial."
            )
            break

        x_next = x - f_x / df_x
        if not math.isfinite(x_next):
            result.history.append(NewtonRow(i, x, f_x, df_x, None, None, ""))
            result.status = STATUS_NON_FINITE
            result.message = (
                f"En la iteración {i} x(i+1) no es finito. El proceso diverge; "
                "prueba con otro valor inicial."
            )
            break

        # Error aproximado: relativo si x_{i+1} ≠ 0, absoluto si x_{i+1} = 0.
        if x_next != 0.0:
            ea = abs((x_next - x) / x_next) * 100.0
            ea_unit = "%"
            ea_for_stop = ea                       # comparado con tol_pct
        else:
            ea = abs(x_next - x)
            ea_unit = "abs"
            ea_for_stop = ea * 100.0               # comparado con tol_pct (equivale a tol/100)

        result.history.append(NewtonRow(i, x, f_x, df_x, x_next, ea, ea_unit))
        result.iterations = i
        result.last_ea = ea
        result.last_ea_unit = ea_unit

        x = x_next

        if ea_for_stop <= tol_pct:
            result.status = STATUS_CONVERGED
            result.message = (
                f"Convergió en la iteración {i}: εa = {ea:.3g} {ea_unit} ≤ "
                f"tolerancia {tol_pct:.3g} %."
            )
            break
    else:
        result.status = STATUS_MAX_ITER
        result.message = (
            f"Se alcanzó el máximo de {max_iter} iteraciones sin cumplir la tolerancia "
            f"{tol_pct:.3g} %. El método no alcanzó el criterio de convergencia."
        )

    # ── Aproximación final y residuo ─────────────────────────────────────────
    # Un estado de derivada nula o no finito no produce una aproximación válida.
    if result.status in (STATUS_CONVERGED, STATUS_MAX_ITER):
        result.root = x
        residual = _to_float(func, x)
        result.residual = abs(residual) if residual is not None else None

    return result
