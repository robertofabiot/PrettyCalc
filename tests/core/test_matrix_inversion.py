"""Inversión por Gauss-Jordan y forma vectorial paramétrica de sistemas indeterminados."""

from fractions import Fraction

import pytest

from prettycalc.core import (
    MatrixInverseResult,
    NonSquareMatrixError,
    ParametricVectorSolution,
    SingularMatrixError,
    matrix_inverse,
    solve_system_via_inverse,
    solve_via_inverse,
)
from prettycalc.core.classifier import SystemType, classify_system
from prettycalc.core.matrix_ops import (
    matrix_inverse as matrix_inverse_from_ops,
    matrix_multiply,
    matrix_transpose,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


def _session10_matrix_3x3() -> Matrix:
    return Matrix([
        [0, 1, 2],
        [1, 0, 3],
        [4, -3, 8],
    ])


def _expected_inverse_3x3() -> Matrix:
    return Matrix([
        [Fraction(-9, 2), 7, Fraction(-3, 2)],
        [-2, 4, -1],
        [Fraction(3, 2), -2, Fraction(1, 2)],
    ])


def test_inverse_session10_slide11_3x3():
    result = matrix_inverse(_session10_matrix_3x3())
    assert isinstance(result, MatrixInverseResult)
    assert result.is_invertible is True
    assert result.identity_check_passed is True
    assert result.inverse == _expected_inverse_3x3()
    assert result.original == _session10_matrix_3x3()
    assert result.tracer.total_steps > 1
    assert result.tracer[0].split_col == 3
    assert "I_n" in result.tracer[0].latex_formula
    left, right = result.tracer[-1].matrix.split_augmented(3)
    assert left == Matrix.identity(3)
    assert right == result.inverse


def test_inverse_session10_slide9_2x2_fractions():
    original = Matrix([[2, 3], [-1, 1]])
    result = matrix_inverse(original)
    assert result.inverse == Matrix([
        [Fraction(1, 5), Fraction(-3, 5)],
        [Fraction(1, 5), Fraction(2, 5)],
    ])
    assert result.identity_check_passed is True
    assert matrix_multiply(original, result.inverse) == Matrix.identity(2)


def test_inverse_of_identity_and_1x1():
    assert matrix_inverse(Matrix.identity(3)).inverse == Matrix.identity(3)
    assert matrix_inverse(Matrix([[4]])).inverse == Matrix([[Fraction(1, 4)]])
    assert matrix_inverse(Matrix([["-1/2"]])).inverse == Matrix([[-2]])


def test_inverse_properties_double_product_and_transpose():
    first = Matrix([[2, 3], [-1, 1]])
    second = Matrix([[1, 2], [0, 1]])
    first_inverse = matrix_inverse(first).inverse
    second_inverse = matrix_inverse(second).inverse
    product = matrix_multiply(first, second)

    assert matrix_inverse(first_inverse).inverse == first
    assert matrix_inverse(product).inverse == matrix_multiply(second_inverse, first_inverse)
    assert matrix_inverse(matrix_transpose(first)).inverse == matrix_transpose(first_inverse)


def test_singular_session10_slide20_raises_with_tracer():
    singular = Matrix([
        [2, 3, 4],
        [2, 3, 4],
        [2, 3, 4],
    ])
    with pytest.raises(SingularMatrixError, match="Teorema de la Matriz Invertible") as caught:
        matrix_inverse(singular)
    assert caught.value.tracer is not None
    assert caught.value.tracer.total_steps >= 1
    assert "singular" in str(caught.value)


def test_zero_and_rank_deficient_are_singular():
    with pytest.raises(SingularMatrixError):
        matrix_inverse(Matrix.zeros(2, 2))
    with pytest.raises(SingularMatrixError):
        matrix_inverse(Matrix([[0, 1], [0, 2]]))


def test_nonsquare_raises():
    with pytest.raises(NonSquareMatrixError, match="cuadradas"):
        matrix_inverse(Matrix([[1, 2, 3], [4, 5, 6]]))
    with pytest.raises(NonSquareMatrixError):
        solve_via_inverse(Matrix([[1, 0, 0], [0, 1, 0]]), Vector([1, 2]))


def test_matrix_ops_reexports_inverse():
    direct = matrix_inverse(Matrix([[2, 3], [-1, 1]]))
    via_ops = matrix_inverse_from_ops(Matrix([[2, 3], [-1, 1]]))
    assert via_ops.inverse == direct.inverse


def test_solve_via_inverse_matches_unique_solution():
    coefficient = Matrix([[2, 3], [-1, 1]])
    constants = Vector([8, 1])
    solution, result = solve_via_inverse(coefficient, constants)
    assert solution == Vector([1, 2])
    assert result.identity_check_passed is True
    assert solve_system_via_inverse is solve_via_inverse

    again, _ = solve_via_inverse(_session10_matrix_3x3(), Vector([1, 0, 0]))
    expected_column = Vector(_expected_inverse_3x3().get_col(0))
    assert again == expected_column


def test_solve_via_inverse_rejects_bad_dimension_and_singular():
    square = Matrix.identity(2)
    with pytest.raises(DimensionMismatchError):
        solve_via_inverse(square, Vector([1, 2, 3]))
    with pytest.raises(SingularMatrixError):
        solve_via_inverse(Matrix([[1, 2], [2, 4]]), Vector([1, 2]))


def test_session7_slide4_parametric_vector_form():
    augmented = Matrix([
        [3, 5, -4, 0],
        [-3, -2, 4, 0],
        [6, 1, -8, 0],
    ])
    analysis = classify_system(augmented)
    assert analysis.system_type == SystemType.CONSISTENT_INDETERMINED
    solution = analysis.parametric_vector_solution
    assert isinstance(solution, ParametricVectorSolution)
    assert solution.particular_vector == Vector([0, 0, 0])
    assert solution.free_var_names == ["x3"]
    assert list(solution.null_basis_vectors) == [2]
    assert solution.null_basis_vectors[2] == Vector([Fraction(4, 3), 0, 1])
    assert solution.to_plain_equation() == "x = [0, 0, 0] + x3*[4/3, 0, 1]"
    latex = solution.to_latex_equation()
    assert r"\frac{4}{3}" in latex
    assert "x_{3}" in latex
    assert r"\begin{bmatrix}" in latex


def test_nonhomogeneous_sci_particular_plus_null_basis():
    # x1 + 2 x2 - x3 = 4, repetida. Libres x2 y x3.
    # x1 = 4 - 2 x2 + x3
    augmented = Matrix([
        [1, 2, -1, 4],
        [2, 4, -2, 8],
    ])
    analysis = classify_system(augmented, split_col=3)
    solution = analysis.parametric_vector_solution
    assert solution is not None
    assert solution.particular_vector == Vector([4, 0, 0])
    assert solution.null_basis_vectors[1] == Vector([-2, 1, 0])
    assert solution.null_basis_vectors[2] == Vector([1, 0, 1])
    assert solution.free_var_names == ["x2", "x3"]


def test_determined_and_inconsistent_have_no_parametric_vector():
    determined = classify_system(Matrix([
        [1, 0, 2],
        [0, 1, 3],
    ]))
    inconsistent = classify_system(Matrix([
        [1, 1, 2],
        [1, 1, 5],
    ]))
    assert determined.system_type == SystemType.CONSISTENT_DETERMINED
    assert determined.parametric_vector_solution is None
    assert inconsistent.system_type == SystemType.INCONSISTENT
    assert inconsistent.parametric_vector_solution is None
