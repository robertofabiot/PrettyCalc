"""Norma, distancia y producto exterior con los ejercicios de las sesiones 5 y 9."""

from fractions import Fraction

import pytest

from prettycalc.core.types import DimensionMismatchError, Matrix, Vector
from prettycalc.core.vector_ops import (
    format_exact_sqrt,
    trace_vector_distance,
    trace_vector_norm,
    trace_vector_outer_product,
    vector_distance_exact,
    vector_distance_squared,
    vector_norm_exact,
    vector_norm_squared,
    vector_outer_product,
)


def test_session5_norm_of_three_four_is_five():
    vector = Vector([3, 4])
    assert vector_norm_squared(vector) == Fraction(25, 1)
    coefficient, radical, denominator = vector_norm_exact(vector)
    assert (coefficient, radical, denominator) == (Fraction(5, 1), 1, 1)
    assert format_exact_sqrt(coefficient, radical, denominator) == "5"
    traced = trace_vector_norm(vector)
    assert traced.squared == Fraction(25, 1)
    assert traced.display == "5"
    assert traced.tracer.total_steps >= 2
    assert "25" in traced.tracer.get_steps()[-1].heuristic_text


def test_norm_keeps_a_simplified_radical():
    coefficient, radical, denominator = vector_norm_exact(Vector([1, 2]))
    assert (coefficient, radical, denominator) == (Fraction(1, 1), 5, 1)
    assert format_exact_sqrt(coefficient, radical, denominator) == "√5"

    half = vector_norm_exact(Vector(["1/2", "1/2"]))
    assert half == (Fraction(1, 2), 2, 1)
    assert format_exact_sqrt(*half) == "(1/2)√2"
    assert vector_norm_exact(Vector([0, 0, 0])) == (Fraction(0, 1), 1, 1)


def test_session5_distance_is_five():
    start = Vector([1, 2])
    end = Vector([4, 6])
    assert vector_distance_squared(start, end) == Fraction(25, 1)
    assert vector_distance_exact(start, end) == (Fraction(5, 1), 1, 1)
    traced = trace_vector_distance(start, end)
    assert traced.display == "5"
    assert traced.tracer.total_steps >= 2


def test_distance_rejects_different_dimensions():
    with pytest.raises(DimensionMismatchError):
        vector_distance_squared(Vector([1, 2]), Vector([1, 2, 3]))


def test_session9_outer_product_of_a_vector_with_itself():
    vector = Vector([1, -2, 3])
    product = vector_outer_product(vector, vector)
    assert product == Matrix([
        [1, -2, 3],
        [-2, 4, -6],
        [3, -6, 9],
    ])
    traced = trace_vector_outer_product(vector, vector)
    assert traced.matrix == product
    assert traced.matrix.rows == 3
    assert traced.matrix.cols == 3
    assert "M_{ij}" in traced.tracer.get_steps()[-1].latex_formula


def test_outer_product_allows_different_dimensions():
    product = vector_outer_product(Vector([1, 2]), Vector([3, 4, 5]))
    assert product == Matrix([
        [3, 4, 5],
        [6, 8, 10],
    ])
    assert product.shape == (2, 3)
