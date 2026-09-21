"""Pruebas de álgebra matricial: suma, resta, escala, producto y no conmutatividad."""

from fractions import Fraction

import pytest

from prettycalc.core.matrix_ops import (
    matrix_add,
    matrix_multiply,
    matrix_multiply_with_details,
    matrix_scale,
    matrix_sub,
)
from prettycalc.core.types import DimensionMismatchError, Matrix


def test_matrix_add_sub_compatible_shapes():
    a22 = Matrix([[1, 2], [3, 4]])
    b22 = Matrix([[5, 6], [7, 8]])
    assert matrix_add(a22, b22) == Matrix([[6, 8], [10, 12]])
    assert matrix_sub(a22, b22) == Matrix([[-4, -4], [-4, -4]])

    a33 = Matrix.identity(3)
    b33 = Matrix([[1, 1, 1], [0, 1, 0], [2, 0, 1]])
    assert matrix_add(a33, b33) == Matrix([[2, 1, 1], [0, 2, 0], [2, 0, 2]])

    a24 = Matrix([[1, 2, 3, 4], [5, 6, 7, 8]])
    z24 = Matrix.zeros(2, 4)
    assert matrix_add(a24, z24) == a24
    assert matrix_sub(a24, a24) == z24


def test_matrix_add_incompatible_shapes_raises():
    a = Matrix([[1, 2, 3], [4, 5, 6]])  # 2×3
    b = Matrix([[1, 2], [3, 4], [5, 6]])  # 3×2
    with pytest.raises(DimensionMismatchError, match="2×3"):
        matrix_add(a, b)
    with pytest.raises(DimensionMismatchError):
        matrix_sub(a, b)


def test_matrix_scale_exact_fractions():
    a = Matrix([[2, -4], ["1/2", 0]])
    scaled = matrix_scale(a, "1/2")
    assert scaled == Matrix([[1, -2], ["1/4", 0]])
    assert matrix_scale(a, 0) == Matrix.zeros(2, 2)


def test_matrix_multiply_2x3_by_3x2():
    a = Matrix([[1, 2, 3], [4, 5, 6]])
    b = Matrix([[7, 8], [9, 10], [11, 12]])
    c = matrix_multiply(a, b)
    assert c.shape == (2, 2)
    assert c == Matrix([[58, 64], [139, 154]])


def test_matrix_multiply_column_by_row_and_row_by_column():
    col = Matrix([[1], ["1/2"], [3]])  # 3×1
    row = Matrix([[2, 4, 6]])  # 1×3
    outer = matrix_multiply(col, row)
    assert outer.shape == (3, 3)
    assert outer == Matrix([[2, 4, 6], [1, 2, 3], [6, 12, 18]])

    inner = matrix_multiply(row, col)
    assert inner.shape == (1, 1)
    # 2*1 + 4*(1/2) + 6*3 = 2 + 2 + 18 = 22
    assert inner.get(0, 0) == Fraction(22, 1)


def test_matrix_multiply_is_not_commutative():
    a = Matrix([[1, 2], [3, 4]])
    b = Matrix([[0, 1], [1, 0]])
    ab = matrix_multiply(a, b)
    ba = matrix_multiply(b, a)
    assert ab != ba
    assert ab == Matrix([[2, 1], [4, 3]])
    assert ba == Matrix([[3, 4], [1, 2]])


def test_matrix_multiply_incompatible_raises():
    a = Matrix([[1, 2, 3], [4, 5, 6]])  # 2×3
    b = Matrix([[1, 2], [3, 4]])  # 2×2
    with pytest.raises(DimensionMismatchError, match="columnas de A"):
        matrix_multiply(a, b)


def test_matrix_multiply_with_details_matches_product():
    a = Matrix([[1, "1/2"], [0, 2]])
    b = Matrix([[3, 0], [1, 4]])
    product, details = matrix_multiply_with_details(a, b)
    assert product == matrix_multiply(a, b)
    assert len(details) == 4
    cell_00 = next(d for d in details if d.row == 0 and d.col == 0)
    # (1)(3) + (1/2)(1) = 3 + 1/2 = 7/2
    assert cell_00.total == Fraction(7, 2)
    assert cell_00.products[-1][2] == Fraction(1, 2)
    assert "C_1,1" in cell_00.formula
