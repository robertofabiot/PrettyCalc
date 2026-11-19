"""Jacobi y Gauss-Seidel (Programa 8): convergencia, divergencia y pasos."""

from fractions import Fraction

import pytest

from prettycalc.core.iterative_methods import (
    IterationStatus,
    IterativeMethod,
    StopCriterion,
    ZeroDiagonalError,
    analyze_convergence,
    characteristic_polynomial,
    compare_methods,
    eigenvalues_of,
    gauss_seidel,
    iteration_matrix,
    jacobi,
    reorder_for_dominance,
    solve_iterative,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector

# Burden & Faires: diagonal dominante, x* = (1, 2, −1, 1).
DOMINANT_A = Matrix([[10, -1, 2, 0], [-1, 11, -1, 3], [2, -1, 10, -1], [0, 3, -1, 8]])
DOMINANT_B = Vector([6, 25, -11, 15])
# ρ(T_J) = √5/2 > 1, ρ(T_GS) = 1/2: solo Gauss-Seidel converge. x* = (1, 2, −1).
GS_ONLY_A = Matrix([[2, -1, 1], [2, 2, 2], [-1, -1, 2]])
GS_ONLY_B = Vector([-1, 4, -5])
# ρ(T_J) = 0, ρ(T_GS) = 2: solo Jacobi converge. x* = (1, 2, −1).
JACOBI_ONLY_A = Matrix([[1, 2, -2], [1, 1, 1], [2, 2, 1]])
JACOBI_ONLY_B = Vector([7, 2, 5])
# Ninguno converge; intercambiar las ecuaciones da dominancia. x* = (1, 1).
NEITHER_A = Matrix([[1, -5], [7, -1]])
NEITHER_B = Vector([-4, 6])

TOL = Fraction(1, 10**6)


def _close(vector, expected, tolerance=Fraction(1, 10**4)):
    return all(abs(vector[i] - Fraction(value)) < tolerance for i, value in enumerate(expected))


# ---------------------------------------------------------------------------
# Algoritmo
# ---------------------------------------------------------------------------


def test_jacobi_first_iteration_matches_the_hand_computation():
    result = jacobi(DOMINANT_A, DOMINANT_B, max_iterations=1)
    assert result.iterations[1].x == (Fraction(3, 5), Fraction(25, 11), Fraction(-11, 10), Fraction(15, 8))


def test_gauss_seidel_uses_the_new_components_immediately():
    result = gauss_seidel(DOMINANT_A, DOMINANT_B, max_iterations=1)
    x1, x2, _x3, _x4 = result.iterations[1].x
    assert x1 == Fraction(3, 5)
    # x₂⁽¹⁾ = (25 + x₁⁽¹⁾ + x₃⁽⁰⁾ − 3x₄⁽⁰⁾)/11 con x₁⁽¹⁾ = 0.6, no con x₁⁽⁰⁾ = 0.
    assert x2 == (25 + Fraction(3, 5)) / 11


def test_both_methods_converge_on_a_diagonally_dominant_system():
    for method in IterativeMethod:
        result = solve_iterative(DOMINANT_A, DOMINANT_B, method, tolerance=TOL)
        assert result.status is IterationStatus.CONVERGED
        assert _close(result.approximation, [1, 2, -1, 1])
        assert result.iterations[-1].delta_norm < TOL
        assert result.final_error < Fraction(1, 10**5)


def test_gauss_seidel_needs_fewer_iterations_on_the_dominant_example():
    comparison = compare_methods(DOMINANT_A, DOMINANT_B, tolerance=TOL)
    assert comparison.gauss_seidel.iteration_count < comparison.jacobi.iteration_count
    assert "Ambos convergen" in comparison.summary


def test_only_gauss_seidel_converges_when_rho_jacobi_exceeds_one():
    comparison = compare_methods(GS_ONLY_A, GS_ONLY_B, tolerance=TOL)
    assert comparison.jacobi.status is IterationStatus.DIVERGED
    assert comparison.gauss_seidel.status is IterationStatus.CONVERGED
    assert _close(comparison.gauss_seidel.approximation, [1, 2, -1])
    assert comparison.summary.startswith("Solo Gauss-Seidel")


def test_only_jacobi_converges_and_gauss_seidel_is_not_always_better():
    comparison = compare_methods(JACOBI_ONLY_A, JACOBI_ONLY_B, tolerance=TOL)
    assert comparison.jacobi.status is IterationStatus.CONVERGED
    # ρ(T_J) = 0: T_J es nilpotente y x⁽³⁾ ya es exacta; x⁽⁴⁾ lo confirma (Δ = 0).
    assert comparison.jacobi.iterations[3].x == (1, 2, -1)
    assert comparison.jacobi.iteration_count == 4
    assert comparison.gauss_seidel.status is IterationStatus.DIVERGED
    assert "no es siempre mejor" in comparison.summary


def test_divergence_is_detected_before_the_iteration_limit():
    for method in IterativeMethod:
        result = solve_iterative(NEITHER_A, NEITHER_B, method, max_iterations=100)
        assert result.status is IterationStatus.DIVERGED
        assert result.iteration_count < 100
        assert "no converge" in result.summary


def test_relative_criterion_stops_on_the_relative_change():
    result = jacobi(DOMINANT_A, DOMINANT_B, tolerance=Fraction(1, 1000), criterion=StopCriterion.RELATIVE)
    last = result.iterations[-1]
    assert result.converged
    assert last.relative_delta < Fraction(1, 1000)
    assert result.iterations[-2].relative_delta >= Fraction(1, 1000)


def test_initial_vector_is_respected():
    x0 = Vector([1, 2, -1, 1])
    result = jacobi(DOMINANT_A, DOMINANT_B, x0=x0)
    assert result.iteration_count == 1
    assert result.iterations[1].delta_norm == 0


def test_max_iterations_without_convergence_keeps_the_honest_status():
    result = jacobi(DOMINANT_A, DOMINANT_B, tolerance=Fraction(1, 10**10), max_iterations=3)
    assert result.status is IterationStatus.MAX_ITERATIONS
    assert "necesita más iteraciones" in result.summary


# ---------------------------------------------------------------------------
# Criterios de convergencia
# ---------------------------------------------------------------------------


def test_iteration_matrices_follow_their_definitions():
    T, c = iteration_matrix(DOMINANT_A, DOMINANT_B, IterativeMethod.JACOBI)
    assert T.get(0, 1) == Fraction(1, 10) and T.get(0, 0) == 0
    assert c[0] == Fraction(3, 5)
    T_gs, c_gs = iteration_matrix(DOMINANT_A, DOMINANT_B, IterativeMethod.GAUSS_SEIDEL)
    # La primera columna de T_GS es nula: x₁ nunca se usa de la iteración anterior.
    assert all(T_gs.get(i, 0) == 0 for i in range(4))
    # x⁽ᵏ⁺¹⁾ = T x⁽ᵏ⁾ + c reproduce la iteración componente a componente.
    first = gauss_seidel(DOMINANT_A, DOMINANT_B, max_iterations=1).iterations[1].x
    assert tuple(c_gs) == first


def test_spectral_radii_of_the_textbook_counterexamples():
    gs_only = analyze_convergence(GS_ONLY_A, GS_ONLY_B)
    assert gs_only.jacobi.radius == pytest.approx(5 ** 0.5 / 2, abs=1e-9)
    assert gs_only.gauss_seidel.radius == pytest.approx(0.5, abs=1e-9)
    jacobi_only = analyze_convergence(JACOBI_ONLY_A, JACOBI_ONLY_B)
    assert jacobi_only.jacobi.radius == 0
    assert jacobi_only.gauss_seidel.radius == pytest.approx(2, abs=1e-9)
    assert jacobi_only.predicts_convergence(IterativeMethod.JACOBI) is True
    assert jacobi_only.predicts_convergence(IterativeMethod.GAUSS_SEIDEL) is False


def test_characteristic_polynomial_is_exact():
    T, _ = iteration_matrix(GS_ONLY_A, GS_ONLY_B, IterativeMethod.JACOBI)
    # det(λI − T_J) = λ³ + (5/4)λ para este ejemplo.
    assert characteristic_polynomial(T) == (1, 0, Fraction(5, 4), 0)
    _poly, eigen = eigenvalues_of(T)
    # Raíces 0 y ±(√5/2)i: dos complejas conjugadas con el mismo módulo.
    radius = round(5 ** 0.5 / 2, 9)
    assert sorted(round(abs(z), 9) for z in eigen) == [0, radius, radius]
    assert any(abs(z.imag) > 1 for z in eigen)


def test_dominance_and_positive_definiteness():
    analysis = analyze_convergence(DOMINANT_A, DOMINANT_B)
    assert analysis.strictly_dominant
    assert analysis.positive_definite
    assert analysis.leading_minors[0] == 10
    assert not analyze_convergence(GS_ONLY_A).strictly_dominant
    assert not analyze_convergence(GS_ONLY_A).symmetric


def test_reordering_turns_the_divergent_system_into_a_dominant_one():
    reordering = reorder_for_dominance(NEITHER_A, NEITHER_B)
    assert reordering.permutation == (1, 0)
    assert reordering.strictly_dominant and reordering.changed
    result = gauss_seidel(reordering.A, reordering.b, tolerance=TOL)
    assert result.converged and _close(result.approximation, [1, 1])


def test_reordering_removes_zero_diagonals_when_dominance_is_impossible():
    A = Matrix([[0, 1, 1], [1, 0, 2], [3, 1, 0]])
    reordering = reorder_for_dominance(A, Vector([2, 3, 4]))
    assert reordering is not None
    assert all(reordering.A.get(i, i) != 0 for i in range(3))


def test_reordering_returns_none_for_a_column_of_zeros():
    A = Matrix([[0, 1], [0, 2]])
    assert reorder_for_dominance(A, Vector([1, 1])) is None


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------


def test_zero_diagonal_is_rejected_with_its_trace():
    with pytest.raises(ZeroDiagonalError) as info:
        jacobi(Matrix([[0, 1], [1, 1]]), Vector([1, 2]))
    assert info.value.rows == (0,)
    assert info.value.tracer is not None and info.value.tracer[-1].alert_rows == (0,)


def test_shape_and_parameter_errors():
    with pytest.raises(NonSquareMatrixError):
        jacobi(Matrix([[1, 2, 3], [4, 5, 6]]), Vector([1, 2]))
    with pytest.raises(DimensionMismatchError):
        jacobi(DOMINANT_A, Vector([1, 2]))
    with pytest.raises(DimensionMismatchError):
        jacobi(DOMINANT_A, DOMINANT_B, x0=Vector([0, 0]))
    with pytest.raises(ValueError):
        jacobi(DOMINANT_A, DOMINANT_B, tolerance=0)
    with pytest.raises(ValueError):
        jacobi(DOMINANT_A, DOMINANT_B, max_iterations=0)


# ---------------------------------------------------------------------------
# Paso a paso
# ---------------------------------------------------------------------------


def test_trace_shows_setup_criteria_every_iteration_and_conclusion():
    result = gauss_seidel(DOMINANT_A, DOMINANT_B, tolerance=TOL)
    steps = result.tracer.get_steps()
    # Inicial, dominancia, despeje, ρ(T), x⁽⁰⁾, una por iteración y la conclusión.
    assert len(steps) == 5 + result.iteration_count + 1
    assert steps[0].highlight_cells == ((0, 0), (1, 1), (2, 2), (3, 3))
    assert "Fila 1: |10| > |−1| + |2| + |0| = 3" in steps[1].heuristic_text
    assert "x₂⁽ᵏ⁺¹⁾ = (25 + x₁⁽ᵏ⁺¹⁾ + x₃⁽ᵏ⁾ − 3x₄⁽ᵏ⁾) / 11" in steps[2].heuristic_text
    assert "ρ(T_GS)" in steps[3].heuristic_text
    first = steps[5].heuristic_text
    assert "x₁⁽¹⁾ = (6 − (−1)(0) − (2)(0)) / 10 = 0.6" in first
    assert "x₂⁽¹⁾ = (25 − (−1)(0.6)" in first  # Gauss-Seidel sustituye x₁⁽¹⁾
    assert steps[5].matrix.rows == 3  # x⁽ᵏ⁻¹⁾, x⁽ᵏ⁾ y |Δ|
    assert "se detiene" in steps[-2].heuristic_text
    assert "Solución exacta por Gauss-Jordan" in steps[-1].heuristic_text


def test_every_iteration_step_writes_each_component():
    result = jacobi(DOMINANT_A, DOMINANT_B)
    for record, step in zip(result.iterations[1:], result.tracer.get_steps()[5:]):
        assert len(record.component_lines) == 4
        for line in record.component_lines:
            assert line in step.heuristic_text
