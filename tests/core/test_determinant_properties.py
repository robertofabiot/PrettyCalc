"""Propiedades multiplicativas del determinante, sesión 11."""

from fractions import Fraction

import pytest

from prettycalc.core.determinants import (
    verify_determinant_inverse,
    verify_determinant_multiplicative,
    verify_determinant_properties,
    verify_determinant_scalar_scaling,
    verify_determinant_transpose,
)
from prettycalc.core.matrix_inversion import SingularMatrixError
from prettycalc.core.types import Matrix


_A = Matrix([[6, 1], [3, 2]])
_B = Matrix([[4, 3], [1, 2]])


def test_session11_product_of_determinants_is_forty_five():
    det_a, det_b, det_ab, holds, tracer = verify_determinant_multiplicative(_A, _B)
    assert det_a == 9
    assert det_b == 5
    assert det_ab == 45
    assert holds
    assert tracer.total_steps >= 2


def test_transpose_inverse_and_scaling_hold_on_the_class_matrix():
    det_a, det_transpose, transpose_ok, _tracer = verify_determinant_transpose(_A)
    assert det_a == det_transpose == 9
    assert transpose_ok

    _same, det_inverse, inverse_ok, _inverse_tracer = verify_determinant_inverse(_A)
    assert det_inverse == Fraction(1, 9)
    assert inverse_ok

    det_scaled, expected, scaling_ok, _scale_tracer = verify_determinant_scalar_scaling(_A, Fraction(2, 1))
    assert expected == Fraction(36, 1)
    assert det_scaled == expected
    assert scaling_ok


def test_properties_bundle_covers_the_four_laws():
    result = verify_determinant_properties(_A, _B, Fraction(3, 1))
    assert result.det_A == 9
    assert result.det_B == 5
    assert result.det_AB == 45
    assert result.is_multiplicative_valid
    assert result.is_transpose_valid
    assert result.det_transpose == 9
    assert result.is_inverse_valid
    assert result.det_inverse == Fraction(1, 9)
    assert result.inverse_reciprocal == Fraction(1, 9)
    assert result.is_scaling_valid
    assert result.det_scaled == Fraction(81, 1)
    assert result.tracer.total_steps >= 3


def test_inverse_property_rejects_a_singular_matrix():
    singular = Matrix([[1, 2], [2, 4]])
    with pytest.raises(SingularMatrixError):
        verify_determinant_inverse(singular)
    bundled = verify_determinant_properties(singular, k=Fraction(2, 1))
    assert bundled.det_A == 0
    assert bundled.is_inverse_valid is None
    assert bundled.is_transpose_valid
    assert bundled.is_scaling_valid
