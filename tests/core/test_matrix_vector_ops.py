"""Pruebas unitarias para las operaciones y propiedades del producto matriz-vector A · x."""

from fractions import Fraction
import pytest

from prettycalc.core.matrix_vector_ops import (
    matrix_vector_multiply,
    matrix_vector_multiply_with_details,
    verify_distributive_property,
    verify_homogeneity_property,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


def test_matrix_vector_multiply_square():
    A = Matrix([
        [1, 2],
        [3, 4],
    ])
    x = Vector([2, -1])
    # [1*2 + 2*(-1), 3*2 + 4*(-1)] = [0, 2]
    res = matrix_vector_multiply(A, x)
    assert res == Vector([0, 2])
    assert res.dimension == 2


def test_matrix_vector_multiply_rectangular():
    A = Matrix([
        [1, -2, 3],
        [0, 4, -1],
    ])
    x = Vector([2, 1, 3])
    # Fila 1: 1*2 + (-2)*1 + 3*3 = 2 - 2 + 9 = 9
    # Fila 2: 0*2 + 4*1 + (-1)*3 = 0 + 4 - 3 = 1
    res = matrix_vector_multiply(A, x)
    assert res == Vector([9, 1])
    assert res.dimension == 2


def test_matrix_vector_multiply_dimension_mismatch():
    A = Matrix([
        [1, 2, 3],
        [4, 5, 6],
    ])  # 2x3 -> exige x en R^3
    x = Vector([1, 2])  # R^2
    with pytest.raises(DimensionMismatchError) as exc_info:
        matrix_vector_multiply(A, x)
    err = str(exc_info.value)
    assert "2×3" in err
    assert "ℝ^2" in err
    assert "columnas de A (3)" in err


def test_matrix_vector_multiply_with_details():
    A = Matrix([[2, 3]])
    x = Vector([4, 5])
    res, details = matrix_vector_multiply_with_details(A, x)
    assert res == Vector([23])
    assert len(details) == 1
    assert "(2)·(4) + (3)·(5) = 23" in details[0]


def test_distributive_property_integers():
    A = Matrix([
        [2, -1, 3],
        [1, 0, -2],
    ])
    u = Vector([1, 2, -1])
    v = Vector([3, -1, 4])

    result = verify_distributive_property(A, u, v)

    # u + v = [4, 1, 3]
    assert result.u_plus_v == Vector([4, 1, 3])

    # A(u + v) = [2*4 - 1*1 + 3*3, 1*4 + 0*1 - 2*3] = [8 - 1 + 9, 4 - 6] = [16, -2]
    assert result.lhs_result == Vector([16, -2])

    # Au = [2*1 - 1*2 + 3*(-1), 1*1 + 0*2 - 2*(-1)] = [-3, 3]
    assert result.Au == Vector([-3, 3])

    # Av = [2*3 - 1*(-1) + 3*4, 1*3 + 0*(-1) - 2*4] = [6 + 1 + 12, 3 - 8] = [19, -5]
    assert result.Av == Vector([19, -5])

    # Au + Av = [-3 + 19, 3 - 5] = [16, -2]
    assert result.rhs_result == Vector([16, -2])

    assert result.is_equal is True
    assert result.lhs_result == result.rhs_result
    assert len(result.verification_checklist) == 2
    assert all(item[3] for item in result.verification_checklist)
    assert len(result.lhs_steps) > 0
    assert len(result.rhs_steps) > 0


def test_distributive_property_fractions():
    A = Matrix([
        ["1/2", "-1/3"],
        ["3/4", "2/5"],
    ])
    u = Vector(["1/3", "3/2"])
    v = Vector(["-2/3", "1/4"])

    result = verify_distributive_property(A, u, v)
    assert result.is_equal is True
    assert result.lhs_result == result.rhs_result


def test_distributive_property_mismatch_vectors():
    A = Matrix([[1, 2], [3, 4]])
    u = Vector([1, 2, 3])  # dim 3
    v = Vector([1, 2])     # dim 2
    with pytest.raises(DimensionMismatchError) as exc_info:
        verify_distributive_property(A, u, v)
    assert "dim(u) = 3" in str(exc_info.value)
    assert "dim(v) = 2" in str(exc_info.value)


def test_distributive_property_mismatch_matrix():
    A = Matrix([[1, 2, 3], [4, 5, 6]])  # 2x3 -> columnas=3
    u = Vector([1, 2])                  # dim 2
    v = Vector([3, 4])                  # dim 2
    with pytest.raises(DimensionMismatchError) as exc_info:
        verify_distributive_property(A, u, v)
    assert "2×3" in str(exc_info.value)
    assert "ℝ^2" in str(exc_info.value)


def test_homogeneity_property_integers():
    A = Matrix([
        [1, 2],
        [-3, 4],
    ])
    u = Vector([3, -1])
    c = 5

    result = verify_homogeneity_property(A, u, c)

    # cu = [15, -5]
    assert result.cu == Vector([15, -5])
    # A(cu) = [1*15 + 2*(-5), -3*15 + 4*(-5)] = [15 - 10, -45 - 20] = [5, -65]
    assert result.lhs_result == Vector([5, -65])

    # Au = [1*3 + 2*(-1), -3*3 + 4*(-1)] = [1, -13]
    assert result.Au == Vector([1, -13])
    # c(Au) = 5 * [1, -13] = [5, -65]
    assert result.rhs_result == Vector([5, -65])

    assert result.is_equal is True
    assert result.lhs_result == result.rhs_result
    assert len(result.verification_checklist) == 2
    assert all(item[3] for item in result.verification_checklist)
    assert len(result.lhs_steps) > 0
    assert len(result.rhs_steps) > 0


def test_homogeneity_property_fraction_and_negative():
    A = Matrix([
        ["2/3", "-1/2", 1],
        [0, "3/4", "-2/5"],
    ])
    u = Vector(["-3/4", "2/3", 5])
    c = "-7/3"

    result = verify_homogeneity_property(A, u, c)
    assert result.is_equal is True
    assert result.lhs_result == result.rhs_result
    assert result.c == Fraction(-7, 3)


def test_homogeneity_property_zero_scalar():
    A = Matrix([[3, 4], [1, 2]])
    u = Vector([7, -3])
    result = verify_homogeneity_property(A, u, 0)
    assert result.is_equal is True
    assert result.lhs_result == Vector([0, 0])
    assert result.rhs_result == Vector([0, 0])


def test_homogeneity_property_dimension_mismatch():
    A = Matrix([[1, 2, 3], [4, 5, 6]])  # 2x3 -> exige u en R^3
    u = Vector([1, 2])                  # dim 2
    with pytest.raises(DimensionMismatchError) as exc_info:
        verify_homogeneity_property(A, u, 2)
    assert "2×3" in str(exc_info.value)
    assert "ℝ^2" in str(exc_info.value)


def test_homogeneity_property_invalid_scalar():
    A = Matrix([[1, 2], [3, 4]])
    u = Vector([1, 2])
    with pytest.raises(ValueError):
        verify_homogeneity_property(A, u, "no-es-numero")
