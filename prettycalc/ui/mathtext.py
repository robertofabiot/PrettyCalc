"""Notación matemática tipo libro: subíndices, flechas y conversión desde LaTeX."""

from __future__ import annotations

import re
from typing import Optional

from prettycalc.ui.theme import COLOR_TEXT_PRIMARY, FONT_FAMILY_SANS

_SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

_LATEX_FRAC = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
_LATEX_TEXT = re.compile(r"\\text\{([^}]*)\}")
_F_SUB_BRACES = re.compile(r"f_\{(\d+)\}")
_F_SUB_PLAIN = re.compile(r"\bf(\d+)\b")
_X_SUB = re.compile(r"\bx(\d+)\b")


def to_subscript(value: int | str) -> str:
    """Convierte dígitos a subíndices tipográficos (1 → ₁)."""
    return str(value).translate(_SUBSCRIPTS)


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
