"""Pruebas unitarias para prettycalc.core.linear_independence."""

from fractions import Fraction
import pytest

from prettycalc.core.linear_independence import (
    LinearIndependenceResult,
    evaluate_linear_independence,
)
from prettycalc.core.types import DimensionMismatchError, Vector


def test_empty_vectors_raises():
    with pytest.raises(ValueError, match="al menos un vector"):
        evaluate_linear_independence([])


def test_dimension_mismatch_raises():
    v1 = Vector([1, 2])
    v2 = Vector([1, 2, 3])
    with pytest.raises(DimensionMismatchError):
        evaluate_linear_independence([v1, v2])


def test_canonical_basis_r3_is_li():
    e1 = Vector([1, 0, 0])
    e2 = Vector([0, 1, 0])
    e3 = Vector([0, 0, 1])
    res = evaluate_linear_independence([e1, e2, e3])

    assert res.k == 3
    assert res.n == 3
    assert res.num_pivots == 3
    assert res.is_linearly_independent is True
    assert len(res.free_variables) == 0
    assert res.basic_variables == [0, 1, 2]
    assert res.nontrivial_weights is None
    assert res.theorem_k_greater_n is False
    assert res.zero_vector_index is None


def test_general_invertible_matrix_r3_is_li():
    v1 = Vector([1, 2, 3])
    v2 = Vector([4, 5, 6])
    v3 = Vector([7, 8, 10])  # det != 0
    res = evaluate_linear_independence([v1, v2, v3])

    assert res.num_pivots == 3
    assert res.is_linearly_independent is True
    assert len(res.free_variables) == 0


def test_dependent_sum_r3_is_ld():
    v1 = Vector([1, 2, 3])
    v2 = Vector([4, 5, 6])
    v3 = Vector([5, 7, 9])  # v3 = v1 + v2
    res = evaluate_linear_independence([v1, v2, v3])

    assert res.num_pivots == 2
    assert res.is_linearly_independent is False
    assert res.free_variables == [2]
    assert res.nontrivial_weights is not None

    weights = res.nontrivial_weights
    # Comprobar que sum(w_j * v_j) == 0
    for dim in range(3):
        acc = sum(weights[j] * [v1, v2, v3][j][dim] for j in range(3))
        assert acc == Fraction(0, 1)

    assert len(res.verification_checklist) == 3
    assert all(chk[2] for chk in res.verification_checklist)


def test_theorem_k_greater_than_n_is_ld():
    v1 = Vector([1, 0, 0])
    v2 = Vector([0, 1, 0])
    v3 = Vector([0, 0, 1])
    v4 = Vector([1, 1, 1])
    res = evaluate_linear_independence([v1, v2, v3, v4])

    assert res.k == 4
    assert res.n == 3
    assert res.theorem_k_greater_n is True
    assert res.is_linearly_independent is False
    assert res.num_pivots == 3
    assert len(res.free_variables) == 1


def test_zero_vector_present_is_ld():
    v1 = Vector([0, 0, 0])
    v2 = Vector([1, 2, 3])
    res = evaluate_linear_independence([v1, v2])

    assert res.zero_vector_index == 0
    assert res.is_linearly_independent is False


def test_k_less_than_n_independent_vectors():
    v1 = Vector([1, 0, 2])
    v2 = Vector([0, 1, -1])
    res = evaluate_linear_independence([v1, v2])

    assert res.k == 2
    assert res.n == 3
    assert res.num_pivots == 2
    assert res.is_linearly_independent is True
    assert len(res.free_variables) == 0


def test_single_vector():
    # Non-zero single vector is L.I.
    v_nonzero = Vector([3, -1])
    res1 = evaluate_linear_independence([v_nonzero])
    assert res1.is_linearly_independent is True
    assert res1.num_pivots == 1

    # Zero single vector is L.D.
    v_zero = Vector([0, 0])
    res2 = evaluate_linear_independence([v_zero])
    assert res2.is_linearly_independent is False
    assert res2.num_pivots == 0
