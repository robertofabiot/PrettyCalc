"""Pruebas rigurosas de las propiedades algebraicas matriciales:

1. Propiedad Distributiva por la izquierda: A · (B + C) = A·B + A·C
2. Propiedad Distributiva por la derecha:   (A + B) · C = A·C + B·C
3. Propiedad Asociativa del producto:       A · (B · C) = (A · B) · C
"""

from fractions import Fraction
import pytest

from prettycalc.core.matrix_properties import (
    analyze_matrix,
    matrix_algebraic_identity_checks,
    verify_matrix_associative,
    verify_matrix_distributive_left,
    verify_matrix_distributive_right,
)
from prettycalc.core.types import DimensionMismatchError, Matrix


def test_matrix_distributive_left_integers():
    """A · (B + C) = A·B + A·C con enteros y matrices rectangulares 2×3 y 3×2."""
    A = Matrix([[1, 2, -1], [0, 3, 4]])
    B = Matrix([[2, 1], [-1, 0], [3, 2]])
    C = Matrix([[-1, 4], [2, -2], [0, 1]])

    res = verify_matrix_distributive_left(A, B, C)

    assert res.is_equal is True
    assert res.is_left is True
    assert res.lhs_result == res.rhs_result
    assert res.lhs_result.shape == (2, 2)
    assert len(res.verification_checklist) == 4
    for _, lhs_val, rhs_val, ok in res.verification_checklist:
        assert ok is True
        assert lhs_val == rhs_val
    assert len(res.lhs_steps) > 0
    assert len(res.rhs_steps) > 0


def test_matrix_distributive_left_fractions():
    """A · (B + C) = A·B + A·C con fracciones exactas."""
    A = Matrix([["1/2", "-1/3"], ["2/5", "3/4"]])
    B = Matrix([["1/4", "2/3"], ["-1/2", "1/5"]])
    C = Matrix([["3/4", "-1/3"], ["1/2", "4/5"]])

    res = verify_matrix_distributive_left(A, B, C)

    assert res.is_equal is True
    assert res.lhs_result == res.rhs_result
    assert res.intermediate_sum == Matrix([[1, "1/3"], [0, 1]])


def test_matrix_distributive_left_mismatch():
    """Lanza DimensionMismatchError si B y C o A y B son incompatibles."""
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[1, 2, 3], [4, 5, 6]])
    C_bad_shape = Matrix([[1, 2], [3, 4]])

    with pytest.raises(DimensionMismatchError, match="incompatibles para la suma"):
        verify_matrix_distributive_left(A, B, C_bad_shape)

    C = Matrix([[7, 8, 9], [10, 11, 12]])
    A_bad_cols = Matrix([[1, 2, 3]])  # cols=3 != B.rows=2
    with pytest.raises(DimensionMismatchError, match="incompatibles para el producto"):
        verify_matrix_distributive_left(A_bad_cols, B, C)


def test_matrix_distributive_right():
    """(A + B) · C = A·C + B·C."""
    A = Matrix([[1, -2, 3], [4, 0, -1]])
    B = Matrix([[2, 1, -1], [-3, 2, 5]])
    C = Matrix([[1, 2], [-1, 3], [2, 0]])

    res = verify_matrix_distributive_right(A, B, C)

    assert res.is_equal is True
    assert res.is_left is False
    assert res.lhs_result == res.rhs_result
    assert res.lhs_result.shape == (2, 2)


def test_matrix_distributive_right_mismatch():
    """Lanza DimensionMismatchError si A y B no coinciden o no son conformables con C."""
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[1, 2, 3], [4, 5, 6]])
    C = Matrix([[1], [2]])

    with pytest.raises(DimensionMismatchError, match="incompatibles para la suma"):
        verify_matrix_distributive_right(A, B, C)

    B_ok = Matrix([[5, 6], [7, 8]])
    C_bad = Matrix([[1, 2, 3]])  # C.rows = 1 != A.cols = 2
    with pytest.raises(DimensionMismatchError, match="incompatibles para el producto"):
        verify_matrix_distributive_right(A, B_ok, C_bad)


def test_matrix_associative():
    """A · (B · C) = (A · B) · C con dimensiones 2×3, 3×2, 2×4."""
    A = Matrix([[1, 2, 3], [4, 5, 6]])
    B = Matrix([[7, 8], [9, 1], [2, 3]])
    C = Matrix([[1, -1, 2, 0], [3, 2, -1, 4]])

    res = verify_matrix_associative(A, B, C)

    assert res.is_equal is True
    assert res.lhs_result == res.rhs_result
    assert res.lhs_result.shape == (2, 4)
    assert len(res.verification_checklist) == 8


def test_matrix_associative_mismatch():
    """Lanza DimensionMismatchError en dimensiones no conformables."""
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])  # B.rows = 3 != A.cols = 2
    C = Matrix([[1], [2], [3]])

    with pytest.raises(DimensionMismatchError, match="incompatibles para A · B"):
        verify_matrix_associative(A, B, C)


def test_analyze_matrix_with_b_and_c():
    """analyze_matrix incluye identidades algebraicas cuando se proporcionan B y C."""
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[5, 6], [7, 8]])
    C = Matrix([[1, 0], [0, 1]])

    checks = analyze_matrix(A, B, scalar=2, C=C)
    names = [c.name for c in checks]
    assert "A · (B + C) = A·B + A·C" in names
    assert "(A + B) · C = A·C + B·C" in names
    assert "A · (B · C) = (A · B) · C" in names

    for c in checks:
        if c.name in ("A · (B + C) = A·B + A·C", "(A + B) · C = A·C + B·C", "A · (B · C) = (A · B) · C"):
            assert c.status == "cumple"
