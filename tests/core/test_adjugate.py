"""Matriz de cofactores, adjunta e inversa analítica de la Sesión 11."""

from fractions import Fraction

import pytest

from prettycalc.core.adjugate import (
    adjugate_matrix,
    calculate_adjugate_and_inverse,
    cofactor_matrix,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError, matrix_inverse
from prettycalc.core.matrix_ops import matrix_multiply, matrix_scale
from prettycalc.core.types import Matrix


def _session11_matrix() -> Matrix:
    return Matrix([
        [1, 3, -3],
        [2, 0, 1],
        [-1, 4, -2],
    ])


def _expected_cofactors() -> Matrix:
    return Matrix([
        [-4, 3, 8],
        [-6, -5, -7],
        [3, -7, -6],
    ])


def _expected_adjugate() -> Matrix:
    return Matrix([
        [-4, -6, 3],
        [3, -5, -7],
        [8, -7, -6],
    ])


def test_session11_cofactors_adjugate_and_inverse():
    matrix = _session11_matrix()
    result = calculate_adjugate_and_inverse(matrix)
    assert result.det_A == Fraction(-19)
    assert result.cofactors_matrix == _expected_cofactors()
    assert result.adjugate_matrix == _expected_adjugate()
    assert cofactor_matrix(matrix) == _expected_cofactors()
    assert adjugate_matrix(matrix) == _expected_adjugate()
    assert result.inverse_via_adjugate is not None
    assert result.inverse_via_adjugate == matrix_scale(
        _expected_adjugate(),
        Fraction(1, 1) / Fraction(-19),
    )
    assert result.inverse_via_adjugate == matrix_inverse(matrix).inverse
    identity = Matrix.identity(3)
    assert matrix_multiply(matrix, result.inverse_via_adjugate) == identity
    assert matrix_multiply(result.adjugate_matrix, matrix) == matrix_scale(identity, result.det_A)


def test_minors_of_session11_match_cofactor_signs():
    result = calculate_adjugate_and_inverse(_session11_matrix())
    assert result.minors_matrix == Matrix([
        [-4, -3, 8],
        [6, -5, 7],
        [3, 7, -6],
    ])


def test_singular_adjugate_has_no_inverse():
    singular = Matrix([[1, 2], [2, 4]])
    result = calculate_adjugate_and_inverse(singular)
    assert result.det_A == 0
    assert result.inverse_via_adjugate is None
    assert result.adjugate_matrix == Matrix([[4, -2], [-2, 1]])


def test_one_by_one_adjugate_uses_empty_minor_convention():
    result = calculate_adjugate_and_inverse(Matrix([[5]]))
    assert result.minors_matrix == Matrix([[1]])
    assert result.cofactors_matrix == Matrix([[1]])
    assert result.adjugate_matrix == Matrix([[1]])
    assert result.inverse_via_adjugate == Matrix([[Fraction(1, 5)]])


def test_nonsquare_adjugate_is_rejected():
    with pytest.raises(NonSquareMatrixError):
        calculate_adjugate_and_inverse(Matrix([[1, 2, 3], [4, 5, 6]]))
