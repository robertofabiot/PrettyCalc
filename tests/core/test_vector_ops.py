"""Pruebas de vectores en ℝⁿ: suma, resta, escala, producto punto y dimensiones."""

from fractions import Fraction

import pytest

from prettycalc.core.types import DimensionMismatchError, Vector
from prettycalc.core.vector_ops import vector_add, vector_dot, vector_scale, vector_sub


def test_vector_parses_mixed_scalars():
    v = Vector([1, -2, "3/4"])
    assert v.dimension == 3
    assert v.components == [Fraction(1, 1), Fraction(-2, 1), Fraction(3, 4)]
    assert v[2] == Fraction(3, 4)
    assert v.to_column_matrix().shape == (3, 1)


def test_vector_zeros_copy_and_equality():
    z = Vector.zeros(4)
    assert z.dimension == 4
    assert all(comp == Fraction(0, 1) for comp in z)
    copied = z.copy()
    copied[0] = 1
    assert z[0] == Fraction(0, 1)
    assert copied != z


def test_vector_add_sub_r2_r3_r5():
    u2 = Vector([1, "1/2"])
    v2 = Vector([-1, "3/2"])
    assert vector_add(u2, v2) == Vector([0, 2])
    assert vector_sub(u2, v2) == Vector([2, -1])

    u3 = Vector([1, 2, 3])
    v3 = Vector([4, 5, 6])
    assert vector_add(u3, v3) == Vector([5, 7, 9])
    assert vector_sub(u3, v3) == Vector([-3, -3, -3])

    u5 = Vector([1, 0, -1, "2/3", 5])
    v5 = Vector([0, 1, 1, "1/3", -2])
    assert vector_add(u5, v5) == Vector([1, 1, 0, 1, 3])
    assert vector_sub(u5, v5) == Vector([1, -1, -2, "1/3", 7])


def test_vector_scale_integer_fraction_and_zero():
    v = Vector([2, -4, "1/2"])
    assert vector_scale(v, 3) == Vector([6, -12, "3/2"])
    assert vector_scale(v, "1/2") == Vector([1, -2, "1/4"])
    assert vector_scale(v, 0) == Vector.zeros(3)
    assert vector_scale(v, -1) == Vector([-2, 4, "-1/2"])


def test_vector_dot_euclidean():
    assert vector_dot(Vector([1, 2, 3]), Vector([4, -5, 6])) == Fraction(12, 1)
    assert vector_dot(Vector(["1/2", "1/3"]), Vector([2, 3])) == Fraction(2, 1)
    assert vector_dot(Vector([1, 0, 0, 0, 1]), Vector([0, 1, 1, 1, 0])) == Fraction(0, 1)


def test_vector_dimension_mismatch_raises():
    u = Vector([1, 2])
    v = Vector([1, 2, 3])
    with pytest.raises(DimensionMismatchError, match="dim\\(u\\) = 2"):
        vector_add(u, v)
    with pytest.raises(DimensionMismatchError):
        vector_sub(u, v)
    with pytest.raises(DimensionMismatchError):
        vector_dot(u, v)


def test_empty_vector_rejected():
    with pytest.raises(ValueError, match="vacío"):
        Vector([])
