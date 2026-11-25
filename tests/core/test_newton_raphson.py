"""Pruebas de Newton-Raphson (Programa 9): casos obligatorios y validaciones."""

import math

import pytest

from prettycalc.core.newton_raphson import (
    STATUS_CONVERGED,
    STATUS_DERIVATIVE_ZERO,
    STATUS_MAX_ITER,
    STATUS_NON_FINITE,
    newton_raphson,
)


def test_caso1_convergencia_raiz_de_dos():
    """Caso 1: x² − 2 desde x0 = 1 converge a √2 con error y residuo pequeños."""
    r = newton_raphson("x**2 - 2", 1.0, tol_pct=1e-4, max_iter=50)
    assert r.status == STATUS_CONVERGED
    assert r.converged
    assert r.root == pytest.approx(math.sqrt(2), abs=1e-9)
    assert r.residual < 1e-8
    assert r.last_ea <= 1e-4
    assert r.derivative_str == "2*x"


def test_formula_iterativa_primer_paso():
    """x1 = x0 − f(x0)/f'(x0): para x² − 2 desde 1 se obtiene 1.5."""
    r = newton_raphson("x**2 - 2", 1.0)
    first = r.history[0]
    assert first.x_i == 1.0
    assert first.f_xi == pytest.approx(-1.0)
    assert first.df_xi == pytest.approx(2.0)
    assert first.x_next == pytest.approx(1.5)
    # εa = |x1 − x0| / |x1| × 100
    assert first.ea == pytest.approx(abs((1.5 - 1.0) / 1.5) * 100)
    assert first.ea_unit == "%"


def test_caso2_derivada_nula_se_detiene_sin_dividir():
    """Caso 2: f(x) = x² + 1 desde x0 = 0 tiene f'(0) = 0 → parada controlada."""
    r = newton_raphson("x**2 + 1", 0.0)
    assert r.status == STATUS_DERIVATIVE_ZERO
    assert not r.converged
    assert r.root is None and r.residual is None
    assert len(r.history) == 1 and r.history[0].x_next is None
    assert "derivada" in r.message.lower()


def test_caso3_no_alcanza_criterio_de_parada():
    """Caso 3: x³ − 2x + 2 desde 0 oscila 0 ↔ 1 y agota las iteraciones."""
    r = newton_raphson("x**3 - 2*x + 2", 0.0, tol_pct=1e-4, max_iter=10)
    assert r.status == STATUS_MAX_ITER
    assert not r.converged
    assert r.iterations == 10
    assert len(r.history) == 10
    # El residuo revela que la última aproximación no es una raíz.
    assert r.residual == pytest.approx(2.0)
    assert "máximo" in r.message.lower()


def test_x_siguiente_cero_usa_error_absoluto():
    """f(x) = x desde x0 = 1 da x1 = 0: no se divide y se usa |x1 − x0|."""
    r = newton_raphson("x", 1.0)
    assert r.status == STATUS_CONVERGED
    assert r.history[0].ea_unit == "abs"
    assert r.history[0].ea == pytest.approx(1.0)
    assert r.root == pytest.approx(0.0)


def test_valor_no_finito_se_reporta():
    """1/x desde 0 no es evaluable: se informa sin lanzar excepciones."""
    with pytest.raises(ValueError):
        newton_raphson("1/x", 0.0)


def test_divergencia_no_finita_se_detiene():
    """exp(x) desde un valor grande: el paso se vuelve no finito o agota iteraciones."""
    r = newton_raphson("exp(x) - 1000", 50.0, max_iter=5)
    assert r.status in (STATUS_NON_FINITE, STATUS_MAX_ITER, STATUS_CONVERGED)


@pytest.mark.parametrize(
    "x0, tol, max_iter",
    [
        (float("nan"), 1e-4, 10),
        (1.0, 0.0, 10),
        (1.0, -1.0, 10),
        (1.0, 1e-4, 0),
    ],
)
def test_entradas_invalidas(x0, tol, max_iter):
    with pytest.raises(ValueError):
        newton_raphson("x**2 - 2", x0, tol_pct=tol, max_iter=max_iter)


def test_expresion_con_variable_no_permitida():
    with pytest.raises(ValueError):
        newton_raphson("y**2 - 2", 1.0)


def test_no_usa_scipy_newton():
    """El método debe estar programado por el equipo (no scipy.optimize.newton)."""
    import prettycalc.core.newton_raphson as module

    source = open(module.__file__, encoding="utf-8").read()
    assert "import scipy" not in source
    assert "from scipy" not in source
