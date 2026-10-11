"""Determinantes 2×2, Sarrus, triangulación y desarrollo de Laplace."""

from fractions import Fraction

import pytest

from prettycalc.core.determinants import (
    DeterminantMethod,
    determinant_2x2,
    determinant_laplace_expansion,
    determinant_sarrus_3x3,
    determinant_triangulation,
    matrix_determinant,
    minor_determinant,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.matrix_ops import matrix_scale, matrix_transpose
from prettycalc.core.operations import swap_rows
from prettycalc.core.types import Matrix


def _session11_matrix() -> Matrix:
    """Sesión 11, diapositiva 40."""
    return Matrix([
        [1, 3, -3],
        [2, 0, 1],
        [-1, 4, -2],
    ])


def _sarrus_slide26() -> Matrix:
    """Sesión 11, diapositiva 26: det(B) = 36."""
    return Matrix([
        [2, -1, 0],
        [-2, 3, 4],
        [-5, 1, 6],
    ])


def test_direct_2x2_formula():
    result = determinant_2x2(Matrix([[1, 2], [3, 4]]))
    assert result.value == Fraction(-2)
    assert result.method is DeterminantMethod.DIRECT_2X2
    assert result.is_singular is False
    assert "ad" in result.tracer[0].latex_formula
    assert result.step_descriptions


def test_direct_2x2_rejects_other_orders():
    with pytest.raises(ValueError, match="2×2"):
        determinant_2x2(Matrix.identity(3))


def test_sarrus_session11_slide40_is_minus_19():
    result = determinant_sarrus_3x3(_session11_matrix())
    assert result.value == Fraction(-19)
    assert result.is_singular is False
    assert "Sarrus" in result.tracer[0].latex_formula or "Sarrus" in result.tracer[0].heuristic_text


def test_sarrus_session11_slide26_is_36():
    result = determinant_sarrus_3x3(_sarrus_slide26())
    assert result.value == Fraction(36)


def test_sarrus_rejects_non_3x3():
    with pytest.raises(ValueError, match="3×3"):
        determinant_sarrus_3x3(Matrix.identity(2))


def test_triangulation_matches_sarrus_and_tracks_swaps():
    result = determinant_triangulation(_session11_matrix())
    assert result.value == Fraction(-19)
    assert result.triangular_matrix is not None
    assert result.triangular_matrix.rows == 3
    for row_index in range(3):
        for col_index in range(row_index):
            assert result.triangular_matrix.get(row_index, col_index) == 0
    assert f"(-1)^{{{result.row_swaps_count}}}" in result.tracer[-1].latex_formula
    assert result.step_descriptions


def test_triangulation_permutation_matrix_changes_sign():
    swapped = Matrix([[0, 1], [1, 0]])
    result = determinant_triangulation(swapped)
    assert result.value == Fraction(-1)
    assert result.row_swaps_count == 1


def test_triangulation_singular_is_zero():
    result = determinant_triangulation(Matrix([[1, 2], [2, 4]]))
    assert result.value == Fraction(0)
    assert result.is_singular is True
    assert result.triangular_matrix is not None
    assert "det(A) = 0" in result.step_descriptions[-1]


def test_triangular_determinant_is_diagonal_product():
    triangular = Matrix([
        [2, 5, -1],
        [0, 3, 4],
        [0, 0, -2],
    ])
    result = determinant_triangulation(triangular)
    assert result.value == Fraction(-12)
    assert result.row_swaps_count == 0


def test_one_by_one_determinant():
    result = determinant_triangulation(Matrix([[Fraction(3, 4)]]))
    assert result.value == Fraction(3, 4)
    laplace = determinant_laplace_expansion(Matrix([[Fraction(3, 4)]]))
    assert laplace.value == Fraction(3, 4)


def test_laplace_row_and_column_match_triangulation():
    matrix = _session11_matrix()
    expected = Fraction(-19)
    by_row = determinant_laplace_expansion(matrix, along="row", index=1)
    by_col = determinant_laplace_expansion(matrix, along="col", index=2)
    assert by_row.value == expected
    assert by_col.value == expected
    assert by_row.method is DeterminantMethod.LAPLACE_ROW
    assert by_col.method is DeterminantMethod.LAPLACE_COL
    assert minor_determinant(matrix, 0, 0) == Fraction(-4)


def test_laplace_index_out_of_range():
    with pytest.raises(IndexError, match="fila 4"):
        matrix_determinant(
            Matrix.identity(3),
            DeterminantMethod.LAPLACE_ROW,
            expansion_index=3,
        )


def test_nonsquare_determinant_is_rejected():
    with pytest.raises(NonSquareMatrixError, match="cuadradas"):
        matrix_determinant(Matrix([[1, 2, 3], [4, 5, 6]]))


def test_all_methods_agree_on_session11_matrix():
    matrix = _session11_matrix()
    values = [
        determinant_sarrus_3x3(matrix).value,
        determinant_triangulation(matrix).value,
        matrix_determinant(matrix, DeterminantMethod.LAPLACE_ROW, 0).value,
        matrix_determinant(matrix, DeterminantMethod.LAPLACE_COL, 1).value,
    ]
    assert values == [Fraction(-19)] * 4


def test_transpose_preserves_determinant_and_scalar_scales_by_power():
    matrix = _session11_matrix()
    assert determinant_triangulation(matrix_transpose(matrix)).value == Fraction(-19)
    scaled = matrix_scale(matrix, 2)
    assert determinant_triangulation(scaled).value == Fraction(-19) * (2 ** 3)


def test_row_swap_negates_determinant():
    matrix = _session11_matrix()
    swapped = swap_rows(matrix, 0, 2)
    assert determinant_triangulation(swapped).value == Fraction(19)
