"""Teorema de la Matriz Invertible y las identidades de la inversa, sesión 10."""

from prettycalc.core.matrix_ops import matrix_multiply
from prettycalc.core.theorems import (
    evaluate_invertible_matrix_theorem,
    verify_inverse_algebraic_identities,
)
from prettycalc.core.types import Matrix


_INVERTIBLE = Matrix([
    [1, 0, -2],
    [3, 1, -2],
    [-5, -1, 9],
])

_SINGULAR = Matrix([
    [2, 3, 4],
    [2, 3, 4],
    [2, 3, 4],
])


def _by_code(result, code: str):
    return next(item for item in result.checks if item.code == code)


def test_session10_invertible_matrix_meets_the_starred_conditions():
    result = evaluate_invertible_matrix_theorem(_INVERTIBLE)
    assert result.is_invertible
    assert result.determinant == 3
    assert result.pivot_count == 3
    assert _by_code(result, "*c").holds
    assert _by_code(result, "*e").holds
    assert _by_code(result, "*h").holds
    assert _by_code(result, "det").holds
    assert _by_code(result, "b").holds
    assert all(item.holds for item in result.checks)
    assert len(result.checks) == 13
    assert result.tracer.total_steps >= 2


def test_session10_singular_matrix_fails_every_characterization():
    result = evaluate_invertible_matrix_theorem(_SINGULAR)
    assert not result.is_invertible
    assert result.determinant == 0
    assert result.pivot_count == 1
    assert not _by_code(result, "*c").holds
    assert not _by_code(result, "*e").holds
    assert not _by_code(result, "*h").holds
    assert not _by_code(result, "det").holds
    assert all(not item.holds for item in result.checks)


def test_inverse_identities_reverse_the_product_order():
    second = Matrix([
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 1],
    ])
    result = verify_inverse_algebraic_identities(_INVERTIBLE, second)
    assert [check.status for check in result.checks] == ["cumple", "cumple", "cumple"]
    names = [check.name for check in result.checks]
    assert "(A⁻¹)⁻¹ = A" in names
    assert "(AB)⁻¹ = B⁻¹ A⁻¹" in names
    assert "(Aᵀ)⁻¹ = (A⁻¹)ᵀ" in names
    assert result.tracer.total_steps >= 2
    product = matrix_multiply(_INVERTIBLE, second)
    assert product.rows == 3


def test_singular_matrix_does_not_satisfy_the_inverse_identities():
    result = verify_inverse_algebraic_identities(_SINGULAR, _INVERTIBLE)
    by_name = {check.name: check.status for check in result.checks}
    assert by_name["(A⁻¹)⁻¹ = A"] == "no_cumple"
    assert by_name["(Aᵀ)⁻¹ = (A⁻¹)ᵀ"] == "no_cumple"
    assert by_name["(AB)⁻¹ = B⁻¹ A⁻¹"] == "no_cumple"
