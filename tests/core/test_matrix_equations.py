"""Pruebas de ecuaciones matriciales A x = b y de la verificación A · x = b."""

import pytest

from prettycalc.core.classifier import SystemType
from prettycalc.core.matrix_equations import solve_matrix_equation
from prettycalc.core.matrix_ops import matrix_multiply
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


def test_square_determined_system_matches_product():
    a = Matrix([
        [1, 1, 1],
        [2, -1, 1],
        [1, 2, -1],
    ])
    b = Vector([4, 4, 3])
    result = solve_matrix_equation(a, b)

    assert result.analysis.system_type == SystemType.CONSISTENT_DETERMINED
    assert result.solution is not None
    assert result.product_matches is True
    reconstructed = Vector.from_column_matrix(
        matrix_multiply(a, result.solution.to_column_matrix())
    )
    assert reconstructed == b
    assert all(ok for _label, _got, _exp, ok in result.verification_checklist)


def test_wide_rectangular_system_sci():
    # m < n: una ecuación, tres incógnitas, consistente.
    a = Matrix([[1, 2, 3]])
    b = Vector([6])
    result = solve_matrix_equation(a, b)

    assert result.analysis.system_type == SystemType.CONSISTENT_INDETERMINED
    assert result.solution is not None
    assert result.product_matches is True
    assert result.parametric_solution is not None
    assert "libre" in result.parametric_solution


def test_tall_rectangular_inconsistent():
    # m > n: tres ecuaciones, dos incógnitas, b fuera de la imagen.
    a = Matrix([[1, 0], [0, 1], [1, 1]])
    b = Vector([1, 1, 0])
    result = solve_matrix_equation(a, b)

    assert result.analysis.system_type == SystemType.INCONSISTENT
    assert result.solution is None
    assert result.product_matches is False


def test_tall_rectangular_consistent_overdetermined():
    a = Matrix([[1, 0], [0, 1], [1, 1]])
    b = Vector([1, 2, 3])  # tercera fila = suma de las dos primeras
    result = solve_matrix_equation(a, b)

    assert result.analysis.system_type == SystemType.CONSISTENT_DETERMINED
    assert result.solution == Vector([1, 2])
    assert result.product_matches is True


def test_matrix_equation_dimension_mismatch():
    a = Matrix([[1, 2], [3, 4]])
    b = Vector([1, 2, 3])
    with pytest.raises(DimensionMismatchError, match="no es conformable"):
        solve_matrix_equation(a, b)
