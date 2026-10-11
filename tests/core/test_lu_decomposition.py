"""Factorización LU y las dos sustituciones de la Sesión 12."""

from fractions import Fraction

import pytest

from prettycalc.core.lu_decomposition import (
    LUPivotZeroError,
    LUSingularError,
    backward_substitution,
    forward_substitution,
    lu_decompose,
    solve_many_via_lu,
    solve_via_lu,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.matrix_ops import matrix_multiply
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


def _example1():
    matrix = Matrix([
        [3, -7, -2],
        [-3, 5, 1],
        [6, -4, 0],
    ])
    lower = Matrix([
        [1, 0, 0],
        [-1, 1, 0],
        [2, -5, 1],
    ])
    upper = Matrix([
        [3, -7, -2],
        [0, -2, -1],
        [0, 0, -1],
    ])
    load = Vector([-7, 5, 2])
    return matrix, lower, upper, load


def _example2():
    matrix = Matrix([
        [3, -7, -2, 2],
        [-3, 5, 1, 0],
        [6, -4, 0, -5],
        [-9, 5, -5, 12],
    ])
    lower = Matrix([
        [1, 0, 0, 0],
        [-1, 1, 0, 0],
        [2, -5, 1, 0],
        [-3, 8, 3, 1],
    ])
    upper = Matrix([
        [3, -7, -2, 2],
        [0, -2, -1, 2],
        [0, 0, -1, 1],
        [0, 0, 0, -1],
    ])
    load = Vector([-9, 5, 7, 11])
    return matrix, lower, upper, load


def _example3():
    matrix = Matrix([
        [2, 4, -1, 5, -2],
        [-4, -5, 3, -8, 1],
        [2, -5, -4, 1, 8],
        [-6, 0, 7, -3, 1],
    ])
    lower = Matrix([
        [1, 0, 0, 0],
        [-2, 1, 0, 0],
        [1, -3, 1, 0],
        [-3, 4, 2, 1],
    ])
    upper = Matrix([
        [2, 4, -1, 5, -2],
        [0, 3, 1, 2, -3],
        [0, 0, 0, 2, 1],
        [0, 0, 0, 0, 5],
    ])
    return matrix, lower, upper


def _right_column(matrix: Matrix) -> Vector:
    return Vector(matrix.get_col(matrix.cols - 1))


def test_session12_example1_factors_and_solves():
    matrix, lower, upper, load = _example1()
    factorization = lu_decompose(matrix)

    assert factorization.L == lower
    assert factorization.U == upper
    assert factorization.is_valid
    assert matrix_multiply(factorization.L, factorization.U) == matrix
    assert factorization.multipliers_table == [
        (1, 0, Fraction(-1)),
        (2, 0, Fraction(2)),
        (2, 1, Fraction(-5)),
    ]
    assert factorization.tracer.total_steps == 4

    solution = solve_via_lu(matrix, load)
    assert solution.y_intermediate == Vector([-7, -2, 6])
    assert solution.x_solution == Vector([3, 4, -6])
    assert solution.verification_passed
    assert solution.forward_steps[0] == "y_1 = b_1 = -7."
    assert "y_2" in solution.forward_steps[1]
    assert "-2" in solution.forward_steps[1]
    assert _right_column(solution.forward_tracer[-1].matrix) == solution.y_intermediate
    assert solution.forward_tracer[-1].matrix.split_augmented(3)[0] == Matrix.identity(3)
    assert _right_column(solution.backward_tracer[-1].matrix) == solution.x_solution
    assert solution.backward_tracer[-1].matrix.split_augmented(3)[0] == Matrix.identity(3)


def test_session12_example2_four_by_four():
    matrix, lower, upper, load = _example2()
    solution = solve_via_lu(matrix, load)

    assert solution.factorization.L == lower
    assert solution.factorization.U == upper
    assert solution.factorization.is_valid
    assert solution.y_intermediate == Vector([-9, -4, 5, 1])
    assert solution.x_solution == Vector([3, 4, -6, -1])
    assert solution.verification_passed
    assert "x_4" in solution.backward_steps[0]
    assert "-1" in solution.backward_steps[0]


def test_session12_example3_rectangular_skips_a_zero_column():
    matrix, lower, upper = _example3()
    factorization = lu_decompose(matrix)

    assert factorization.L == lower
    assert factorization.U == upper
    assert factorization.L.shape == (4, 4)
    assert factorization.U.shape == (4, 5)
    assert factorization.is_valid
    assert any("no tiene pivote" in step.heuristic_text for step in factorization.tracer)
    with pytest.raises(NonSquareMatrixError):
        solve_via_lu(matrix, Vector([1, 0, 0, 0]))


def test_fraction_factorization_stays_exact():
    matrix = Matrix([
        [2, 1],
        [1, 3],
    ])
    factorization = lu_decompose(matrix)
    assert factorization.L == Matrix([
        [1, 0],
        [Fraction(1, 2), 1],
    ])
    assert factorization.U == Matrix([
        [2, 1],
        [0, Fraction(5, 2)],
    ])
    assert factorization.is_valid

    solution = solve_via_lu(matrix, Vector([1, 1]))
    assert solution.y_intermediate == Vector([1, Fraction(1, 2)])
    assert solution.x_solution == Vector([Fraction(2, 5), Fraction(1, 5)])
    assert solution.verification_passed
    assert "1/2" in " ".join(solution.forward_steps)
    assert "1/5" in " ".join(solution.backward_steps)


def test_zero_pivot_requires_permutation():
    matrix = Matrix([
        [0, 1],
        [1, 1],
    ])
    with pytest.raises(LUPivotZeroError, match="PLU") as captured:
        lu_decompose(matrix)
    assert captured.value.tracer is not None
    assert captured.value.tracer.total_steps >= 1


def test_singular_matrix_factors_but_does_not_solve():
    matrix = Matrix([
        [1, 2],
        [2, 4],
    ])
    factorization = lu_decompose(matrix)
    assert factorization.is_valid
    assert factorization.U == Matrix([
        [1, 2],
        [0, 0],
    ])
    with pytest.raises(LUSingularError, match="singular"):
        solve_via_lu(matrix, Vector([3, 6]))


def test_many_loads_reuse_the_same_factors():
    matrix, _lower, _upper, load = _example1()
    second = Vector([0, 0, 0])
    first, other = solve_many_via_lu(matrix, [load, second])

    assert first.factorization is other.factorization
    assert first.x_solution == Vector([3, 4, -6])
    assert other.x_solution == Vector([0, 0, 0])
    assert other.verification_passed
    with pytest.raises(ValueError):
        solve_many_via_lu(matrix, [])


def test_substitution_rejects_a_vector_of_the_wrong_length():
    _matrix, lower, upper, _load = _example1()
    with pytest.raises(DimensionMismatchError):
        forward_substitution(lower, Vector([1, 2]))
    with pytest.raises(DimensionMismatchError):
        backward_substitution(upper, Vector([1]))


def test_identity_and_one_by_one():
    identity = Matrix.identity(3)
    factorization = lu_decompose(identity)
    assert factorization.L == identity
    assert factorization.U == identity
    assert factorization.multipliers_table == []

    solution = solve_via_lu(Matrix([[4]]), Vector([8]))
    assert solution.x_solution == Vector([2])
    assert solution.y_intermediate == Vector([8])
    assert solution.verification_passed


@pytest.mark.parametrize(
    ("matrix", "lower", "upper", "load"),
    [
        (
            Matrix([[2, -6, 4], [-4, 8, 0], [0, -4, 6]]),
            Matrix([[1, 0, 0], [-2, 1, 0], [0, 1, 1]]),
            Matrix([[2, -6, 4], [0, -4, 8], [0, 0, -2]]),
            Vector([2, -4, 6]),
        ),
        (
            Matrix([[2, -4, 2], [-4, 5, 2], [6, -9, 1]]),
            Matrix([[1, 0, 0], [-2, 1, 0], [3, -1, 1]]),
            Matrix([[2, -4, 2], [0, -3, 6], [0, 0, 1]]),
            Vector([6, 0, 6]),
        ),
        (
            Matrix([[1, -1, 2], [1, -3, 1], [3, 7, 5]]),
            Matrix([[1, 0, 0], [1, 1, 0], [3, -5, 1]]),
            Matrix([[1, -1, 2], [0, -2, -1], [0, 0, -6]]),
            Vector([0, -5, 7]),
        ),
    ],
)
def test_session12_assignment_factors(matrix, lower, upper, load):
    solution = solve_via_lu(matrix, load)
    assert solution.factorization.L == lower
    assert solution.factorization.U == upper
    assert solution.verification_passed


def test_forward_and_backward_match_the_chained_solver():
    _matrix, lower, upper, load = _example1()
    y_vector, forward_steps = forward_substitution(lower, load)
    x_vector, backward_steps = backward_substitution(upper, y_vector)
    chained = solve_via_lu(_matrix, load)
    assert y_vector == chained.y_intermediate
    assert x_vector == chained.x_solution
    assert forward_steps == chained.forward_steps
    assert backward_steps == chained.backward_steps
