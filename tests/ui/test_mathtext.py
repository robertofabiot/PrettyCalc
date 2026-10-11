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


# Corpus de las sesiones 1 a 12. El centinela recorre esta lista y falla si el
# HTML vuelve a mostrar LaTeX crudo.
_BOOK_FORMULAS = (
    r"f_{2} \rightarrow f_{2} - 3f_{1}",
    r"f_{1} \leftrightarrow f_{2}",
    r"f_{1} \leftrightarrow f_{3}",
    r"f_{2} \underset{\sim}\rightarrow \frac{1}{2} \cdot f_{2}",
    r"f_{2} \underset{\sim}\rightarrow -3f_{1} + f_{2}",
    r"(A^{-1})^{-1} = A",
    r"(AB)^{-1} = B^{-1} A^{-1}",
    r"(A^T)^{-1} = (A^{-1})^T",
    r"[I_n \mid A^{-1}]",
    r"\det(A) = ad - bc",
    r"\det(A_{1}(b))",
    r"\det(AB) = \det(A)\det(B)",
    r"\det(A^{-1}) = \frac{1}{\det(A)}",
    r"\det\left(2 A\right) = 2^{2}\det(A)",
    r"\det(A) = (-1)^{3} \prod u_{ii}",
    r"\det(A)\text{ por Sarrus}",
    r"\det(A) = \sum a_{ij} C_{ij}\ \text{(fila 1)}",
    r"\|v\|^2 = \sum_i v_i^2 = 25",
    r"d(u, v) = \|u - v\|",
    r"M = u v^{T}",
    r"M_{ij} = u_i v_j",
    r"\sqrt{5}",
    r"k^{n}",
    r"\text{Inicio: } P = I,\ L = I,\ U = A",
    r"\text{Etapa 1: } Ly = Pb",
    r"\text{Etapa 2: } Ux = y",
    r"C_3H_8 + 5 O_2 \rightarrow 3 CO_2 + 4 H_2O",
    r"(I - C)\,p = 0",
    r"x \geq 0",
    r"x \not\geq 0",
    r"x = p + \sum t_k v_k",
    r"\mathbb{R}",
    r"\text{Sistema Inicial } [A \mid b]",
    r"x = \begin{bmatrix} 0 \\ -\frac{4}{3} \end{bmatrix} + x_{3} \begin{bmatrix} 1 \\ 0 \end{bmatrix}",
)


def _assert_book_html(latex: str) -> str:
    html = latex_to_book_html(latex)
    visible = html.replace("\\'", "'")
    assert "\\" not in visible, (latex, html)
    assert "{" not in html and "}" not in html, (latex, html)
    assert "_" not in html and "^" not in html, (latex, html)
    assert "font-size:22px" in html
    assert "letter-spacing:0.03em" in html
    return html


def test_text_blocks_do_not_skip_the_rest_of_the_formula():
    html = _assert_book_html(r"\text{Etapa 1: } f_{2} \rightarrow f_{1}")
    assert "Etapa 1:" in html
    assert "F₂" in html
    assert "F₁" in html
    assert "→" in html
    assert "\\text" not in html
    assert "font-style:normal" in html

    initial = _assert_book_html(r"\text{Sistema Inicial } [A \mid b]")
    assert "Sistema Inicial" in initial
    assert "[A | b]" in initial


def test_row_operation_formulas():
    replaced = _assert_book_html(r"f_{2} \rightarrow f_{2} - 3f_{1}")
    assert "F₂" in replaced
    assert "F₁" in replaced
    assert "→" in replaced
    assert "−" in replaced

    swapped = _assert_book_html(r"f_{1} \leftrightarrow f_{2}")
    assert "F₁" in swapped
    assert "F₂" in swapped
    assert "↔" in swapped


def test_inverse_and_augmented_formulas():
    double = _assert_book_html(r"(A^{-1})^{-1} = A")
    assert "(A⁻¹)⁻¹ = A" in double

    product = _assert_book_html(r"(AB)^{-1} = B^{-1} A^{-1}")
    assert "(AB)⁻¹ = B⁻¹ A⁻¹" in product

    transpose = _assert_book_html(r"(A^T)^{-1} = (A^{-1})^T")
    assert "(Aᵀ)⁻¹ = (A⁻¹)ᵀ" in transpose

    augmented = _assert_book_html(r"[I_n \mid A^{-1}]")
    assert "[I<sub>n</sub> | A⁻¹]" in augmented


def test_determinant_formulas():
    direct = _assert_book_html(r"\det(A) = ad - bc")
    assert "<i>det</i>(A) = ad − bc" in direct

    cramer = _assert_book_html(r"\det(A_{1}(b))")
    assert "<i>det</i>(A<sub>1</sub>(b))" in cramer

    multiplicative = _assert_book_html(r"\det(AB) = \det(A)\det(B)")
    assert "<i>det</i>(AB) = <i>det</i>(A)<i>det</i>(B)" in multiplicative

    inverse = _assert_book_html(r"\det(A^{-1}) = \frac{1}{\det(A)}")
    assert "<i>det</i>(A⁻¹) = (1/<i>det</i>(A))" in inverse
    assert "\\frac" not in inverse

    scaled = _assert_book_html(r"\det\left(2 A\right) = 2^{2}\det(A)")
    assert "<i>det</i>(2 A) = 2²<i>det</i>(A)" in scaled

    signed = _assert_book_html(r"\det(A) = (-1)^{swaps} \prod u_{ii}")
    assert "(−1)<sup>swaps</sup>" in signed
    assert "∏" in signed
    assert "u<sub>ii</sub>" in signed


def test_vector_and_sqrt_formulas():
    norm = _assert_book_html(r"\|v\|^2 = \sum_i v_i^2 = 25")
    assert "‖v‖² = ∑<sub>i</sub> v<sub>i</sub>² = 25" in norm

    distance = _assert_book_html(r"d(u, v) = \|u - v\|")
    assert "d(u, v) = ‖u − v‖" in distance

    outer = _assert_book_html(r"M = u v^{T}")
    assert "M = u vᵀ" in outer

    entries = _assert_book_html(r"M_{ij} = u_i v_j")
    assert "M<sub>ij</sub> = u<sub>i</sub> v<sub>j</sub>" in entries

    radical = _assert_book_html(r"\sqrt{5}")
    assert '√<span style="text-decoration:overline;">5</span>' in radical

    power = _assert_book_html(r"k^{n}")
    assert "kⁿ" in power


def test_plu_stage_formulas():
    start = _assert_book_html(r"\text{Inicio: } P = I,\ L = I,\ U = A")
    assert "Inicio:" in start
    assert "P = I, L = I, U = A" in start

    forward = _assert_book_html(r"\text{Etapa 1: } Ly = Pb")
    assert "Etapa 1:" in forward
    assert "Ly = Pb" in forward

    backward = _assert_book_html(r"\text{Etapa 2: } Ux = y")
    assert "Etapa 2:" in backward
    assert "Ux = y" in backward


def test_applied_model_formulas():
    chemistry = _assert_book_html(r"C_3H_8 + 5 O_2 \rightarrow 3 CO_2 + 4 H_2O")
    assert "C<sub>3</sub>H<sub>8</sub>" in chemistry
    assert "O<sub>2</sub>" in chemistry
    assert "CO<sub>2</sub>" in chemistry
    assert "H<sub>2</sub>O" in chemistry
    assert "→" in chemistry

    leontief = _assert_book_html(r"(I - C)\,p = 0")
    assert "(I − C) p = 0" in leontief

    bounds = _assert_book_html(r"x \geq 0")
    assert "x ≥ 0" in bounds

    rejected = _assert_book_html(r"x \not\geq 0")
    assert "x ≱ 0" in rejected

    parametric = _assert_book_html(r"x = p + \sum t_k v_k")
    assert "∑" in parametric
    assert "t<sub>k</sub>" in parametric
    assert "v<sub>k</sub>" in parametric

    reals = _assert_book_html(r"\mathbb{R}")
    assert "ℝ" in reals


def test_sentinel_rejects_raw_latex_in_book_html():
    assert len(_BOOK_FORMULAS) > 20
    for latex in _BOOK_FORMULAS:
        _assert_book_html(latex)


def test_carousel_formula_label_uses_rich_text(qtbot):
    from PySide6.QtCore import Qt

    from prettycalc.core.tracer import StepTracer
    from prettycalc.core.types import Matrix
    from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel

    tracer = StepTracer()
    tracer.record_initial(
        Matrix([[1, 0], [0, 1]]),
        latex_title=r"\text{Etapa 1: } \det(A^{-1}) = \frac{1}{\det(A)}",
    )
    carousel = AlgorithmStepperCarousel()
    qtbot.addWidget(carousel)
    carousel.set_steps(tracer.get_steps())

    html = carousel.formula_label.text()
    assert carousel.formula_label.textFormat() == Qt.TextFormat.RichText
    assert "Etapa 1:" in html
    assert "⁻¹" in html
    assert "(1/" in html
    assert "\\" not in html.replace("\\'", "'")
    assert "{" not in html and "}" not in html
    assert "_" not in html and "^" not in html

