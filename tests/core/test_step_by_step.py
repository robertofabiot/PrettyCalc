"""Ningún procedimiento muestra un resultado intermedio sin su desarrollo.

Laplace, la adjunta, las propiedades del determinante y Cramer desarrollan
cada determinante; A ± B, k·A, A·B y Aᵀ tienen un paso por fila o por
entrada; núcleo, imagen y conjuntos generadores explican lo que se lee de la
RREF.
"""

from fractions import Fraction

from prettycalc.core.adjugate import calculate_adjugate_and_inverse
from prettycalc.core.cramer import solve_cramer
from prettycalc.core.determinants import (
    determinant_laplace_expansion,
    determinant_working,
    verify_determinant_properties,
)
from prettycalc.core.linear_transformations import compute_kernel_and_image
from prettycalc.core.matrix_ops import (
    trace_matrix_product,
    trace_matrix_scale,
    trace_matrix_sum,
    trace_matrix_transpose,
)
from prettycalc.core.types import Matrix, Vector
from prettycalc.core.vector_spaces import check_generating_set, compute_subspace_basis

SESSION11 = Matrix([[1, 3, -3], [2, 0, 1], [-1, 4, -2]])
FOUR = Matrix([[1, 2, 0, 1], [0, 1, 3, 2], [2, 0, 1, 1], [1, 1, 1, 0]])


def _texts(tracer):
    return [step.heuristic_text for step in tracer.get_steps()]


def test_determinant_working_spells_out_2x2_and_sarrus():
    value, text = determinant_working(Matrix([[0, 1], [4, -2]]), "M₁₁")
    assert value == -4
    assert text == "M₁₁ = ad − bc = (0)·(-2) − (1)·(4) = 0 − (4) = -4"
    value, text = determinant_working(SESSION11, "det(A)")
    assert value == -19
    assert "por Sarrus" in text and "det(A) = " in text and text.endswith("= -19")


def test_laplace_shows_each_minor_and_skips_zero_entries():
    result = determinant_laplace_expansion(SESSION11, along="row", index=1)
    texts = _texts(result.tracer)
    assert result.value == -19
    assert any("M₂₁ = ad − bc = (3)·(-2) − (-3)·(4)" in text for text in texts)
    assert any("a₂₂ = 0" in text and "sin calcular el menor" in text for text in texts)
    assert "(-12) + 0 + (-7) = -19" in texts[-1]


def test_laplace_on_4x4_triangulates_each_minor_step_by_step():
    result = determinant_laplace_expansion(FOUR, along="row", index=0)
    texts = _texts(result.tracer)
    assert result.value == -15
    assert any(text.startswith("Se tachan la fila 1 y la columna 1") for text in texts)
    big = determinant_laplace_expansion(
        Matrix([[1, 2, 0, 1, 1], [0, 1, 3, 2, 0], [2, 0, 1, 1, 1], [1, 1, 1, 0, 2], [0, 1, 0, 1, 1]]),
        along="row",
        index=0,
    )
    assert any(text.startswith("M₁₁: Se multiplicó") for text in _texts(big.tracer))


def test_adjugate_procedure_covers_every_stage():
    result = calculate_adjugate_and_inverse(SESSION11)
    steps = result.tracer.get_steps()
    texts = [step.heuristic_text for step in steps]
    assert sum(text.startswith("Menor ") for text in texts) == 9
    assert any(text.startswith("Matriz de cofactores") for text in texts)
    assert any(text.startswith("Adjunta: se transpone C") for text in texts)
    assert any("det(A) por la fila 1" in text and "= -19" in text for text in texts)
    assert steps[-1].matrix == result.inverse_via_adjugate


def test_adjugate_without_inverse_says_why():
    result = calculate_adjugate_and_inverse(Matrix([[1, 2], [2, 4]]))
    assert result.inverse_via_adjugate is None
    assert "no hay A⁻¹" in result.tracer.get_steps()[-1].heuristic_text


def test_determinant_properties_build_every_matrix_they_compare():
    result = verify_determinant_properties(Matrix([[2, 1], [1, 3]]), Matrix([[1, 2], [0, 1]]), Fraction(2))
    texts = _texts(result.tracer)
    assert any(text.startswith("det(B) = ad − bc") for text in texts)
    assert any(text.startswith("AB: c₁₂ = fila 1 de A · columna 2 de B") for text in texts)
    assert any(text.startswith("Aᵀ: La fila 1 de A") for text in texts)
    assert any(text.startswith("A⁻¹: ") for text in texts)
    assert any(text.startswith("kA: Fila 1") for text in texts)
    assert sum("Segundo factor B" in text for text in texts) == 0


def test_cramer_develops_every_determinant():
    result = solve_cramer(
        Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]),
        Vector([Fraction(8), Fraction(-11), Fraction(-3)]),
    )
    texts = _texts(result.tracer)
    assert result.solution == [2, 3, -1]
    assert any(text.startswith("det(A) por Sarrus") for text in texts)
    for i, value in (("₁", "2"), ("₂", "3"), ("₃", "-1")):
        assert any(f"det(A{i}(b)) por Sarrus" in text for text in texts)
        assert any(text.startswith(f"x{i} = det(A{i}(b)) / det(A)") and text.endswith(f"= {value}.") for text in texts)
    assert "/ (-1)" in texts[-1]


def test_matrix_operations_have_one_step_per_row_or_entry():
    A = Matrix([[1, 2, 3], [4, 5, 6]])
    B = Matrix([[7, 8], [9, 10], [11, 12]])
    product = trace_matrix_product(A, B)
    steps = product.tracer.get_steps()
    assert len(steps) == 2 + 4
    assert steps[2].heuristic_text == (
        "c₁₁ = fila 1 de A · columna 1 de B = (1)(7) + (2)(9) + (3)(11) = (7) + (18) + (33) = 58."
    )
    assert steps[2].pivot_pos is None and steps[2].highlight_cells == ((0, 0),)
    assert len(trace_matrix_sum(A, A, subtract=True).tracer.get_steps()) == 2 + 2
    assert trace_matrix_scale(A, "1/2").tracer.get_steps()[1].heuristic_text.startswith("Fila 1: (1/2)·(1) = 1/2")
    transpose_steps = trace_matrix_transpose(A).tracer.get_steps()
    assert transpose_steps[2].highlight_cells == ((0, 1), (1, 1), (2, 1))


def test_kernel_and_image_are_read_from_the_rref_step_by_step():
    result = compute_kernel_and_image(Matrix([[1, -3, 0, 2], [-2, 6, 1, -1], [0, 0, 1, 3]]))
    texts = _texts(result.tracer)
    assert any("rango es 2" in text and "x₂, x₄" in text for text in texts)
    assert any(text.startswith("Vector n₁: x₂ = 1 y x₄ = 0") and text.endswith("(3, 1, 0, 0).") for text in texts)
    assert any(text.startswith("Base de la imagen") and "c₂ = columna 3 = (0, 1, 1)" in text for text in texts)
    assert texts[-1].startswith("Teorema de la Dimensión") and "4 = 2 + 2" in texts[-1]


def test_vector_space_procedures_end_with_their_conclusion():
    generating = check_generating_set(Matrix([[1, 0], [0, 1], [1, 1]]))
    conclusion = generating.tracer.get_steps()[-1]
    assert "la fila 3 de la RREF es nula" in conclusion.heuristic_text
    assert conclusion.alert_rows == (2,)
    trivial = compute_subspace_basis(Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
    assert any("Ker(A) = {0}" in text for text in _texts(trivial.tracer))
