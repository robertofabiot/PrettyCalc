"""Regla de Cramer con los sistemas de la Sesión 11 y del plan del sprint."""

from fractions import Fraction

import pytest

from prettycalc.core.cramer import format_cramer_component, solve_cramer
from prettycalc.core.matrix_inversion import (
    NonSquareMatrixError,
    SingularMatrixError,
    solve_via_inverse,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


def test_cramer_plan_2x2_solution_is_3_and_1():
    """Sistema citado en el plan: 3x1 − 2x2 = 7, 2x1 + 5x2 = 11."""
    coefficients = Matrix([[3, -2], [2, 5]])
    constants = Vector([7, 11])
    result = solve_cramer(coefficients, constants)
    assert result.is_applicable is True
    assert result.failure_reason is None
    assert result.det_A == Fraction(19)
    assert result.column_determinants[0][0] == 0
    assert result.column_determinants[0][1] == Matrix([[7, -2], [11, 5]])
    assert result.column_determinants[0][2] == Fraction(57)
    assert result.column_determinants[1][2] == Fraction(19)
    assert result.solution == [Fraction(3), Fraction(1)]
    assert format_cramer_component(0, Fraction(57), Fraction(19), Fraction(3)) == (
        "x1 = det(A1(b)) / det(A) = 57 / 19 = 3"
    )


def test_cramer_session11_slide29():
    """Diapositiva 29: 2x1 + 3x2 = 1, −x1 + x2 = −3, solución (2, −1)."""
    result = solve_cramer(Matrix([[2, 3], [-1, 1]]), Vector([1, -3]))
    assert result.det_A == Fraction(5)
    assert result.column_determinants[0][2] == Fraction(10)
    assert result.column_determinants[1][2] == Fraction(-5)
    assert result.solution == [Fraction(2), Fraction(-1)]


def test_cramer_session11_slides32_to_36():
    """Sistema 3×3: det(A) = 6, det(A1) = 24, x = (4, −2, 3)."""
    coefficients = Matrix([
        [2, 4, 6],
        [4, 5, 6],
        [3, 1, -2],
    ])
    constants = Vector([18, 24, 4])
    result = solve_cramer(coefficients, constants)
    assert result.det_A == Fraction(6)
    assert [column[2] for column in result.column_determinants] == [
        Fraction(24),
        Fraction(-12),
        Fraction(18),
    ]
    assert result.solution == [Fraction(4), Fraction(-2), Fraction(3)]
    inverse_solution, _ = solve_via_inverse(coefficients, constants)
    assert inverse_solution.components == result.solution


def test_cramer_rejects_singular_square_system():
    with pytest.raises(SingularMatrixError, match="det\\(A\\) = 0"):
        solve_cramer(Matrix([[1, 2], [2, 4]]), Vector([3, 6]))


def test_cramer_rejects_nonsquare_coefficient_matrix():
    with pytest.raises(NonSquareMatrixError, match="cuadradas"):
        solve_cramer(Matrix([[1, 2, 3], [4, 5, 6]]), Vector([1, 2]))


def test_cramer_rejects_vector_of_wrong_length():
    with pytest.raises(DimensionMismatchError, match="dim\\(b\\) = n"):
        solve_cramer(Matrix.identity(2), Vector([1, 2, 3]))
