"""Notación matemática tipo libro: subíndices, flechas y conversión desde LaTeX."""

from __future__ import annotations

import re
from typing import Optional

from prettycalc.ui.theme import COLOR_TEXT_PRIMARY, FONT_FAMILY_SANS

_SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

_LATEX_FRAC = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
_LATEX_TEXT = re.compile(r"\\text\{([^}]*)\}")
_F_SUB_BRACES = re.compile(r"f_\{(\d+)\}")
_F_SUB_PLAIN = re.compile(r"\bf(\d+)\b")
_X_SUB = re.compile(r"\bx(\d+)\b")
_SUB_DIGITS_BRACES = re.compile(r"_\{(\d+)\}")
_SUB_DIGITS_PLAIN = re.compile(r"_(\d+)")
_SUB_HTML_BRACES = re.compile(r"_\{([^}]+)\}")
_SUB_HTML_PLAIN = re.compile(r"_([0-9a-zA-Z]+)")
_UNICODE_SUB_DIGITS = re.compile(r"([₀₁₂₃₄₅₆₇₈₉]+)")


def to_subscript(value: int | str) -> str:
    """Convierte dígitos a subíndices tipográficos (1 → ₁)."""
    return str(value).translate(_SUBSCRIPTS)


def to_superscript(value: int | str) -> str:
    """Convierte dígitos a superíndices tipográficos (n → ⁿ)."""
    return str(value).translate(_SUPERSCRIPTS)


def variable_symbol(index_0: int) -> str:
    """Nombre de variable con subíndice de libro: x₁, x₂, …"""
    return f"x{to_subscript(index_0 + 1)}"


_REV_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_VAR_PATTERN = re.compile(r"x([0-9]+|[\u2080-\u2089]+)", re.IGNORECASE)


def variable_html(index_0: int, sub_size_px: Optional[int] = None, italic_x: bool = True) -> str:
    """Nombre de variable en HTML con subíndice visualmente reducido.

    Ejemplo: <i>x</i><sub style='font-size:11px;'>1</sub> o <i>x</i><sub>1</sub>
    """
    style_attr = f" style='font-size:{sub_size_px}px;'" if sub_size_px else ""
    x_part = "<i>x</i>" if italic_x else "x"
    return f"{x_part}<sub{style_attr}>{index_0 + 1}</sub>"


def to_html_subscripts(text: str, sub_size_px: Optional[int] = None, italic_x: bool = True) -> str:
    """Convierte apariciones de x1, x2 o x₁, x₂ a HTML con subíndice reducido y bajado."""
    if not text:
        return ""
    style_attr = f" style='font-size:{sub_size_px}px;'" if sub_size_px else ""
    x_part = "<i>x</i>" if italic_x else "x"

    def _repl(m: re.Match) -> str:
        digits = m.group(1).translate(_REV_SUBSCRIPTS)
        return f"{x_part}<sub{style_attr}>{digits}</sub>"

    return _VAR_PATTERN.sub(_repl, text)


def row_symbol(index_0: int) -> str:
    """Nombre de fila con subíndice de libro: F₁, F₂, …"""
    return f"F{to_subscript(index_0 + 1)}"


def prettify_math_text(text: str) -> str:
    """Normaliza texto algebraico ASCII a notación de libro."""
    if not text:
        return ""

    result = text
    result = _F_SUB_BRACES.sub(lambda m: row_symbol(int(m.group(1)) - 1), result)
    result = _F_SUB_PLAIN.sub(lambda m: row_symbol(int(m.group(1)) - 1), result)
    result = _X_SUB.sub(lambda m: variable_symbol(int(m.group(1)) - 1), result)
    result = _SUB_DIGITS_BRACES.sub(lambda m: to_subscript(m.group(1)), result)
    result = _SUB_DIGITS_PLAIN.sub(lambda m: to_subscript(m.group(1)), result)
    result = result.replace("*", "")
    result = re.sub(r"(?<![\d.])1(?=x)", "", result)
    result = re.sub(r"(-?\d+/\d+)(?=x)", r"(\1)", result)
    result = re.sub(r"(^|[\s+−-])1\(", r"\1(", result)
    result = result.replace("->", "→")
    result = result.replace("!=", "≠")
    result = result.replace("+ -", " − ")
    result = result.replace("+-", " − ")
    result = result.replace(" - ", " − ")
    return result


def format_subscripts_html(text: str, sub_size_px: Optional[int] = None) -> str:
    r"""Convierte subíndices de notación LaTeX (_\{k\}), ASCII (_k) o Unicode (ₖ) a HTML <sub>."""
    if not text:
        return ""
    style_attr = f" style='font-size:{sub_size_px}px;'" if sub_size_px else ""
    res = _SUB_HTML_BRACES.sub(rf"<sub{style_attr}>\1</sub>", text)
    res = _SUB_HTML_PLAIN.sub(rf"<sub{style_attr}>\1</sub>", res)
    res = _UNICODE_SUB_DIGITS.sub(
        lambda m: f"<sub{style_attr}>{m.group(1).translate(_REV_SUBSCRIPTS)}</sub>", res
    )
    return res


def latex_to_book_html(latex: str) -> str:
    """Convierte una fórmula LaTeX de operación elemental a HTML de libro."""
    if not latex:
        return ""

    if "\\text{" in latex:
        text_clean = _LATEX_TEXT.sub(r"\1", latex)
        text_clean = text_clean.replace("\\mid", "|").replace("\\[", "[").replace("\\]", "]")
        text_clean = text_clean.replace("  ", " ").strip()
        return (
            f"<span style='font-size:20px; font-style:italic; color:{COLOR_TEXT_PRIMARY}; "
            f"font-family:{FONT_FAMILY_SANS};'>{text_clean}</span>"
        )

    result = latex
    result = _LATEX_FRAC.sub(r"(\1/\2)", result)
    result = result.replace("\\underset{\\sim}\\rightarrow", " → ")
    result = result.replace("\\underset{\\sim}{\\rightarrow}", " → ")
    result = result.replace("\\rightarrow", " → ")
    result = result.replace("\\leftrightarrow", " ↔ ")
    result = result.replace("\\cdot", "·")
    result = result.replace("\\mid", "|")
    result = result.replace("−", "-")
    result = _F_SUB_BRACES.sub(lambda m: f"F{to_subscript(m.group(1))}", result)
    result = _F_SUB_PLAIN.sub(lambda m: f"F{to_subscript(m.group(1))}", result)
    result = result.replace(" + -", " − ")
    result = re.sub(r"\s+", " ", result).strip()
    result = result.replace("-", "−")

    return (
        f"<span style='font-size:22px; font-weight:500; letter-spacing:0.04em; "
        f"color:{COLOR_TEXT_PRIMARY}; font-family:{FONT_FAMILY_SANS};'>{result}</span>"
    )


def format_equation_book(equation_str: str) -> str:
    """Ecuación original en notación de libro (2x₁ + x₂ = 4)."""
    return prettify_math_text(equation_str)


def format_substitution_book(substitution_str: str) -> str:
    """Sustitución de libro: 2(2) + (1) = 4. Descarta el sufijo de esperado."""
    cleaned = substitution_str.split("(Esperado:")[0].strip()
    return prettify_math_text(cleaned)


def format_parametric_book(expression_text: str, var_names: Optional[list[str]] = None) -> str:
    """Expresión paramétrica en notación de libro."""
    del var_names
    return prettify_math_text(expression_text)


def format_comparison_row_html(
    mark: str,
    label: str,
    lhs_expr: str,
    rhs_expr: str,
    ok: bool,
    font_size_px: int = 22,
) -> str:
    """Fila de comprobación formal en HTML con tipografía grande y colores semánticos."""
    from prettycalc.ui.theme import (
        COLOR_FEEDBACK_ERROR,
        COLOR_FEEDBACK_SUCCESS,
        COLOR_INTERACTIVE_IDLE,
        COLOR_SURFACE_INNER,
        FONT_FAMILY_MONO,
    )

    mark_color = COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR
    bg_color = "rgba(129, 178, 154, 0.10)" if ok else "rgba(238, 108, 77, 0.10)"
    border_color = "rgba(129, 178, 154, 0.40)" if ok else "rgba(238, 108, 77, 0.40)"
    status_text = "Coinciden exactamente" if ok else "No coinciden"

    lhs_has_eq = "=" in lhs_expr and not lhs_expr.startswith("=")
    rhs_has_eq = "=" in rhs_expr and not rhs_expr.startswith("=")

    if lhs_has_eq and rhs_has_eq:
        lhs_name, lhs_val = [p.strip() for p in lhs_expr.split("=", 1)]
        rhs_name, rhs_val = [p.strip() for p in rhs_expr.split("=", 1)]

        lhs_name_clean = format_subscripts_html(prettify_math_text(lhs_name))
        rhs_name_clean = format_subscripts_html(prettify_math_text(rhs_name))
        lhs_val_clean = format_subscripts_html(prettify_math_text(lhs_val))
        rhs_val_clean = format_subscripts_html(prettify_math_text(rhs_val))

        if ok and (lhs_val == rhs_val or not rhs_val):
            comparison_content = (
                f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{lhs_name_clean}</span>'
                f'&nbsp;&nbsp;<span style="color:{COLOR_INTERACTIVE_IDLE}; font-size:{font_size_px}px; font-weight:700;">=</span>&nbsp;&nbsp;'
                f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{rhs_name_clean}</span>'
                f'&nbsp;&nbsp;<span style="color:{COLOR_INTERACTIVE_IDLE}; font-size:{font_size_px}px; font-weight:700;">=</span>&nbsp;&nbsp;'
                f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{lhs_val_clean}</span>'
            )
        else:
            comparison_content = (
                f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{lhs_name_clean} = {lhs_val_clean}</span>'
                f'&nbsp;&nbsp;<span style="color:{COLOR_INTERACTIVE_IDLE}; font-size:{font_size_px}px; font-weight:700;">≠</span>&nbsp;&nbsp;'
                f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{rhs_name_clean} = {rhs_val_clean}</span>'
            )
    else:
        eq_symbol = "=" if ok else "≠"
        lhs_clean = format_subscripts_html(prettify_math_text(lhs_expr))
        rhs_clean = format_subscripts_html(prettify_math_text(rhs_expr))
        comparison_content = (
            f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{lhs_clean}</span>'
            f'&nbsp;&nbsp;<span style="color:{COLOR_INTERACTIVE_IDLE}; font-size:{font_size_px}px; font-weight:700;">{eq_symbol}</span>&nbsp;&nbsp;'
            f'<span style="color:{COLOR_TEXT_PRIMARY}; font-size:{font_size_px}px; font-weight:600;">{rhs_clean}</span>'
        )

    return (
        f'<div style="background-color:{bg_color}; border:1px solid {border_color}; '
        f'border-radius:6px; padding:10px 14px; margin:6px 0; font-family:{FONT_FAMILY_MONO};">'
        f'<span style="color:{mark_color}; font-weight:700; font-size:{font_size_px + 2}px;">{mark}</span>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;'
        f'<span style="color:{COLOR_INTERACTIVE_IDLE}; font-weight:600; font-size:{font_size_px - 2}px;">{label}:</span>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;'
        f'{comparison_content}'
        f'&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:{mark_color}; font-size:{font_size_px - 4}px; font-style:italic;">({status_text})</span>'
        f'</div>'
    )


def format_steps_to_rich_html(title: str, steps: Sequence[str]) -> str:
    """Convierte listas de pasos algebraicos en bloques HTML estructurados y estilizados."""
    from prettycalc.ui.theme import (
        COLOR_INTERACTIVE_IDLE,
        COLOR_SURFACE_INNER,
        COLOR_TEXT_PRIMARY,
        FONT_FAMILY_MONO,
        FONT_FAMILY_SANS,
    )

    rows: list[str] = [
        f'<div style="font-family:{FONT_FAMILY_SANS}; padding:6px 0;">',
        f'<div style="font-size:18px; font-weight:700; color:{COLOR_INTERACTIVE_IDLE}; '
        f'padding-bottom:10px; border-bottom:1px solid {COLOR_INTERACTIVE_IDLE};">{title}</div>',
    ]

    for step in steps:
        s = step.strip()
        if not s or s.startswith("===="):
            continue
        if s.startswith("---") and s.endswith("---"):
            section_name = s.replace("---", "").strip()
            rows.append(
                f'<div style="font-size:16px; font-weight:700; color:{COLOR_INTERACTIVE_IDLE}; '
                f'margin-top:14px; margin-bottom:6px;">{section_name}</div>'
            )
        elif s.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            rows.append(
                f'<div style="font-size:15px; font-weight:600; color:{COLOR_TEXT_PRIMARY}; '
                f'margin-top:8px; margin-bottom:4px;">{s}</div>'
            )
        else:
            pretty_s = prettify_math_text(s)
            rows.append(
                f'<div style="font-family:{FONT_FAMILY_MONO}; font-size:14px; color:{COLOR_TEXT_PRIMARY}; '
                f'padding-left:18px; margin:2px 0;">{pretty_s}</div>'
            )

    rows.append('</div>')
    return "".join(rows)
