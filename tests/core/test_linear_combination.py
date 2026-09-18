"""Pruebas del evaluador de combinación lineal: SCD, SCI, SI y error dimensional."""

from fractions import Fraction

import pytest

from prettycalc.core.classifier import SystemType
from prettycalc.core.linear_combination import evaluate_linear_combination
from prettycalc.core.types import DimensionMismatchError, Vector


def test_unique_linear_combination_standard_basis_scd():
    e1 = Vector([1, 0, 0])
    e2 = Vector([0, 1, 0])
    e3 = Vector([0, 0, 1])
    target = Vector([2, "-1/2", 3])
    result = evaluate_linear_combination([e1, e2, e3], target)

    assert result.is_combination is True
    assert result.system_type == SystemType.CONSISTENT_DETERMINED
    assert result.weights == [Fraction(2, 1), Fraction(-1, 2), Fraction(3, 1)]
    assert result.parametric_solution is None
    assert all(ok for _label, _got, _exp, ok in result.verification_checklist)
    assert len(result.verification_checklist) == 3


def test_infinite_linear_combinations_sci():
    v1 = Vector([1, 2, 3])
    v2 = Vector([2, 4, 6])  # 2 · v1
    target = Vector([3, 6, 9])  # 3 · v1 = (3/2) v2, etc.
    result = evaluate_linear_combination([v1, v2], target)

    assert result.is_combination is True
    assert result.system_type == SystemType.CONSISTENT_INDETERMINED
    assert result.parametric_solution is not None
    assert "libre" in result.parametric_solution
    assert result.weights is not None
    assert all(ok for _label, _got, _exp, ok in result.verification_checklist)


def test_not_a_linear_combination_si():
    # Vectores en el plano xy; el objetivo tiene componente z no nula.
    v1 = Vector([1, 0, 0])
    v2 = Vector([0, 1, 0])
    target = Vector([0, 0, 1])
    result = evaluate_linear_combination([v1, v2], target)

    assert result.is_combination is False
    assert result.system_type == SystemType.INCONSISTENT
    assert result.weights is None
    assert result.contradiction_info is not None
    assert "No es combinación lineal" in result.contradiction_info


def test_linear_combination_dimension_mismatch():
    with pytest.raises(DimensionMismatchError, match="mismo ℝ"):
        evaluate_linear_combination(
            [Vector([1, 0]), Vector([0, 1, 0])],
            Vector([1, 0]),
        )


def test_linear_combination_requires_generators():
    with pytest.raises(ValueError, match="al menos un vector"):
        evaluate_linear_combination([], Vector([1, 0]))
