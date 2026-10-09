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


def test_variable_html_and_to_html_subscripts():
    from prettycalc.ui.mathtext import variable_html, to_html_subscripts
    assert "<sub>1</sub>" in variable_html(0)
    assert "<i>x</i>" in variable_html(0)
    assert "font-size:11px" in variable_html(1, sub_size_px=11)
    
    html = to_html_subscripts("2x1 + 3x2 = 5", sub_size_px=10)
    assert "<i>x</i><sub style='font-size:10px;'>1</sub>" in html
    assert "<i>x</i><sub style='font-size:10px;'>2</sub>" in html

    html_unicode = to_html_subscripts("2x₁ + 3x₂ = 5", sub_size_px=12)
    assert "<i>x</i><sub style='font-size:12px;'>1</sub>" in html_unicode
    assert "<i>x</i><sub style='font-size:12px;'>2</sub>" in html_unicode


def test_format_comparison_row_html():
    from prettycalc.ui.mathtext import format_comparison_row_html

    row = format_comparison_row_html("✓", "Componente 1", "A(u + v) = 5", "Au + Av = 5", ok=True, font_size_px=22)
    assert "font-size:22px" in row
    assert "✓" in row
    assert "Componente 1:" in row
    assert "Coinciden exactamente" in row
    assert "A(u + v)" in row
    assert "Au + Av" in row
    assert ">5</span>" in row

    # Test matrix-vector equation verification rendering: (A·x)₁ = b₁ = 4
    row_ax = format_comparison_row_html("✓", "Componente 1", "(A·x)_1 = 4", "b_1 = 4", ok=True, font_size_px=22)
    assert "(A·x)<sub>1</sub>" in row_ax
    assert "b<sub>1</sub>" in row_ax
    assert "(A·x)_1" not in row_ax
    assert "b_1" not in row_ax
    assert "= 4 = b_1 = 4" not in row_ax
    assert "Coinciden exactamente" in row_ax

    # Test inequality when not matching
    row_neq = format_comparison_row_html("✗", "Componente 1", "(A·x)_1 = 4", "b_1 = 5", ok=False, font_size_px=22)
    assert "(A·x)<sub>1</sub> = 4" in row_neq
    assert "b<sub>1</sub> = 5" in row_neq
    assert "≠" in row_neq
    assert "No coinciden" in row_neq


def test_format_subscripts_html():
    from prettycalc.ui.mathtext import format_subscripts_html

    assert format_subscripts_html("(A·x)_1") == "(A·x)<sub>1</sub>"
    assert format_subscripts_html("b_1") == "b<sub>1</sub>"
    assert format_subscripts_html("b_{12}") == "b<sub>12</sub>"
    assert format_subscripts_html("(A·(u + v))_1") == "(A·(u + v))<sub>1</sub>"
    assert format_subscripts_html("(A·x)₁") == "(A·x)<sub>1</sub>"
    assert format_subscripts_html("C_ij") == "C<sub>ij</sub>"
    assert format_subscripts_html("b_1", sub_size_px=14) == "b<sub style='font-size:14px;'>1</sub>"


def test_prettify_math_text_subscripts():
    from prettycalc.ui.mathtext import prettify_math_text

    assert prettify_math_text("(A·x)_1 = 4") == "(A·x)₁ = 4"
    assert prettify_math_text("b_1 = 4") == "b₁ = 4"
    assert prettify_math_text("b_{2} = 5") == "b₂ = 5"
    assert prettify_math_text("(A·(u + v))_1") == "(A·(u + v))₁"


def test_format_steps_to_rich_html():
    from prettycalc.ui.mathtext import format_steps_to_rich_html

    html = format_steps_to_rich_html("DEMOSTRACIÓN", ["1. Suma intermedia", "   (u+v)_1 = 3"])
    assert "DEMOSTRACIÓN" in html
    assert "1. Suma intermedia" in html

