"""Factorización PLU cuando un pivote es cero, sesión 12."""

import pytest

from prettycalc.core.lu_decomposition import (
    LUPivotZeroError,
    lu_decompose,
    plu_decompose,
    solve_from_plu_factorization,
    solve_via_plu,
)
from prettycalc.core.matrix_ops import matrix_multiply
from prettycalc.core.matrix_inversion import solve_via_inverse
from prettycalc.core.classifier import classify_system
from prettycalc.core.types import Matrix, Vector


_PERMUTATION = Matrix([
    [0, 1, 2],
    [1, 0, 3],
    [4, -3, 8],
])


def test_session12_zero_pivot_factors_as_pa_equals_lu():
    with pytest.raises(LUPivotZeroError):
        lu_decompose(_PERMUTATION)

    factors = plu_decompose(_PERMUTATION)
    assert factors.permutation_count == 1
    assert factors.P == Matrix([
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ])
    assert factors.L == Matrix([
        [1, 0, 0],
        [0, 1, 0],
        [4, -3, 1],
    ])
    assert factors.U == Matrix([
        [1, 0, 3],
        [0, 1, 2],
        [0, 0, 2],
    ])
    assert factors.is_valid
    assert matrix_multiply(factors.P, _PERMUTATION) == matrix_multiply(factors.L, factors.U)
    assert any("f_{1}" in step.latex_formula or "F1" in step.heuristic_text or "Fila 1" in step.heuristic_text for step in factors.tracer)


def test_plu_without_swaps_matches_lu():
    matrix = Matrix([
        [3, -7, -2],
        [-3, 5, 1],
        [6, -4, 0],
    ])
    classic = lu_decompose(matrix)
    permuted = plu_decompose(matrix)
    assert permuted.permutation_count == 0
    assert permuted.P == Matrix.identity(3)
    assert permuted.L == classic.L
    assert permuted.U == classic.U
    assert permuted.is_valid


def test_plu_solution_matches_the_inverse_and_gauss_jordan():
    load = Vector([3, 4, 9])
    solution = solve_via_plu(_PERMUTATION, load)
    assert solution.permuted_b == Vector([4, 3, 9])
    assert solution.x_solution == Vector([1, 1, 1])
    assert solution.verification_passed
    inverse_solution, _inverse = solve_via_inverse(_PERMUTATION, load)
    assert solution.x_solution == inverse_solution
    analysis = classify_system(_PERMUTATION.augment(load), split_col=3)
    assert solution.x_solution.components == analysis.unique_solution
    reused = solve_from_plu_factorization(solution.factorization, Vector([0, 0, 0]))
    assert reused.x_solution == Vector([0, 0, 0])
    assert reused.verification_passed
