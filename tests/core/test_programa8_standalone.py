"""Tests unitarios para verificar el comportamiento de Programa 8_Grupo4.py."""

from fractions import Fraction
import importlib
import pytest

p8 = importlib.import_module("Programa 8_Grupo4")


def test_didactic_case_1_both_converge():
    cases = p8.get_didactic_cases()
    c1 = cases[0]
    A, b = c1["A"], c1["b"]
    res_j = p8.solve_iterative(A, b, p8.IterativeMethod.JACOBI, tolerance=Fraction(1, 10000))
    res_gs = p8.solve_iterative(A, b, p8.IterativeMethod.GAUSS_SEIDEL, tolerance=Fraction(1, 10000))

    assert res_j.status == p8.IterationStatus.CONVERGED
    assert res_gs.status == p8.IterationStatus.CONVERGED
    assert len(res_gs.iterations) < len(res_j.iterations)
    assert res_j.strictly_dominant is True


def test_didactic_case_2_only_gauss_seidel():
    cases = p8.get_didactic_cases()
    c2 = cases[1]
    A, b = c2["A"], c2["b"]
    res_j = p8.solve_iterative(A, b, p8.IterativeMethod.JACOBI, tolerance=Fraction(1, 10000), max_iter=25)
    res_gs = p8.solve_iterative(A, b, p8.IterativeMethod.GAUSS_SEIDEL, tolerance=Fraction(1, 10000), max_iter=25)

    assert res_j.status != p8.IterationStatus.CONVERGED
    assert res_gs.status == p8.IterationStatus.CONVERGED
    assert res_gs.spectral_radius < 1.0
    assert res_j.spectral_radius > 1.0


def test_didactic_case_3_only_jacobi():
    cases = p8.get_didactic_cases()
    c3 = cases[2]
    A, b = c3["A"], c3["b"]
    res_j = p8.solve_iterative(A, b, p8.IterativeMethod.JACOBI, tolerance=Fraction(1, 10000))
    res_gs = p8.solve_iterative(A, b, p8.IterativeMethod.GAUSS_SEIDEL, tolerance=Fraction(1, 10000))

    assert res_j.status == p8.IterationStatus.CONVERGED
    assert res_gs.status == p8.IterationStatus.DIVERGED
    assert res_j.spectral_radius < 1e-6


def test_didactic_case_4_and_5_divergence_and_reordering():
    cases = p8.get_didactic_cases()
    c4 = cases[3]
    A4, b4 = c4["A"], c4["b"]
    res_j4 = p8.solve_iterative(A4, b4, p8.IterativeMethod.JACOBI, max_iter=20)
    res_gs4 = p8.solve_iterative(A4, b4, p8.IterativeMethod.GAUSS_SEIDEL, max_iter=20)
    assert res_j4.status == p8.IterationStatus.DIVERGED
    assert res_gs4.status == p8.IterationStatus.DIVERGED

    # Reordenar filas
    A_reord, b_reord, perm, ok = p8.reorder_for_dominance(A4, b4)
    assert ok is True
    res_j5 = p8.solve_iterative(A_reord, b_reord, p8.IterativeMethod.JACOBI, tolerance=Fraction(1, 10000))
    res_gs5 = p8.solve_iterative(A_reord, b_reord, p8.IterativeMethod.GAUSS_SEIDEL, tolerance=Fraction(1, 10000))
    assert res_j5.status == p8.IterationStatus.CONVERGED
    assert res_gs5.status == p8.IterationStatus.CONVERGED


def test_zero_diagonal_detection():
    A = [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]
    b = [Fraction(1), Fraction(1)]
    with pytest.raises(ZeroDivisionError):
        p8.solve_iterative(A, b, p8.IterativeMethod.JACOBI)


def test_parse_scalar_exact():
    assert p8.parse_scalar("3/4") == Fraction(3, 4)
    assert p8.parse_scalar("-2.5") == Fraction(-5, 2)
    assert p8.parse_scalar(" 7 ") == Fraction(7, 1)
