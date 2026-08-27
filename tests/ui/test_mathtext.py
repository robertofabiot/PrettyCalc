"""Pruebas de conversión a notación matemática de libro."""

from prettycalc.ui.mathtext import (
    to_subscript,
    variable_symbol,
    row_symbol,
    latex_to_book_html,
    prettify_math_text,
    format_equation_book,
    format_substitution_book,
)
from prettycalc.core.operations import (
    get_swap_metadata,
    get_scale_metadata,
    get_add_multiple_metadata,
)


def test_subscripts():
    assert to_subscript(12) == "₁₂"
    assert variable_symbol(0) == "x₁"
    assert row_symbol(2) == "F₃"


def test_latex_swap_to_book():
    latex, _ = get_swap_metadata(0, 2)
    html = latex_to_book_html(latex)
    assert "F₁" in html
    assert "F₃" in html
    assert "↔" in html
    assert "\\" not in html


def test_latex_scale_to_book():
    latex, _ = get_scale_metadata(1, "1/2")
    html = latex_to_book_html(latex)
    assert "F₂" in html
    assert "(1/2)" in html
    assert "→" in html
    assert "\\frac" not in html
    assert "underset" not in html


def test_latex_add_multiple_to_book():
    latex, _ = get_add_multiple_metadata(1, 0, -3)
    html = latex_to_book_html(latex)
    assert "F₂" in html
    assert "F₁" in html
    assert "→" in html
    assert "\\" not in html


def test_latex_initial_system():
    html = latex_to_book_html("\\text{Sistema Inicial } [A \\mid b]")
    assert "Sistema Inicial" in html
    assert "[A | b]" in html
    assert "\\text" not in html


def test_prettify_equations():
    assert format_equation_book("2*x1 + 3*x2 = 5") == "2x₁ + 3x₂ = 5"
    assert format_equation_book("1*x1 + 1*x2 + 1*x3 = 4") == "x₁ + x₂ + x₃ = 4"
    assert format_equation_book("1/2*x1 - 2/3*x2 = 1") == "(1/2)x₁ − (2/3)x₂ = 1"
    assert format_substitution_book("2*(1) + 3*(1) = 5 (Esperado: 5)") == "2(1) + 3(1) = 5"
    assert format_substitution_book("1*(2) + 1*(1) = 4 (Esperado: 4)") == "(2) + (1) = 4"
    assert "x₂" in prettify_math_text("6 - 2*x2 - 3*x3")
    assert "−" in prettify_math_text("6 - 2*x2")
