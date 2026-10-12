"""Notación matemática tipo libro: subíndices, flechas y conversión desde LaTeX.

El contrato de presentación está en Docs/latex-rendering-spec.md: el motor entrega
LaTeX puro y solo esta capa puede pintarlo en un QLabel.
"""

from __future__ import annotations

import html
import re
from typing import Optional, Sequence

from prettycalc.ui.theme import COLOR_TEXT_PRIMARY, FONT_FAMILY_SANS

_SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

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


_SUP_GLYPH = str.maketrans(
    {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
        "−": "⁻",
        "+": "⁺",
        "n": "ⁿ",
        "i": "ⁱ",
        "T": "ᵀ",
        "(": "⁽",
        ")": "⁾",
    }
)
_BLACKBOARD = {"R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ"}
_NAMED_COMMANDS: tuple[tuple[str, str], ...] = (
    ("leftrightarrow", " ↔ "),
    ("Leftrightarrow", " ⇔ "),
    ("rightarrow", " → "),
    ("Rightarrow", " ⇒ "),
    ("leftarrow", " ← "),
    ("longleftarrow", " ← "),
    ("infty", "∞"),
    ("forall", "∀"),
    ("cdots", "⋯"),
    ("ldots", "…"),
    ("vdots", "⋮"),
    ("dots", "…"),
    ("times", "×"),
    ("cdot", "·"),
    ("qquad", " "),
    ("quad", " "),
    ("Vert", "‖"),
    ("vert", "|"),
    ("prod", "∏"),
    ("sum", "∑"),
    ("det", "<i>det</i>"),
    ("neq", "≠"),
    ("leq", "≤"),
    ("geq", "≥"),
    ("mid", "|"),
    ("pm", "±"),
    ("mp", "∓"),
    ("ne", "≠"),
    ("le", "≤"),
    ("ge", "≥"),
    ("in", "∈"),
    ("to", " → "),
)
_COMMAND_PATTERN = re.compile(
    r"\\(" + "|".join(name for name, _ in _NAMED_COMMANDS) + r")(?![A-Za-z])"
)
_COMMAND_REPLACEMENTS = dict(_NAMED_COMMANDS)
_ROW_BRACED = re.compile(r"(?<![A-Za-z])[fF]_\{([^{}]*)\}")
_SUB_BRACED = re.compile(r"_\{([^{}]*)\}")
_ROW_PLAIN_DIGITS = re.compile(r"(?<![A-Za-z])[fF]_(\d+)")
_ROW_PLAIN_LETTERS = re.compile(r"(?<![A-Za-z])[fF]_([A-Za-z]+)")
_SUB_PLAIN_DIGITS = re.compile(r"_(\d+)")
_SUB_PLAIN_LETTERS = re.compile(r"_([A-Za-z]+)")
_SUP_BRACED = re.compile(r"\^\{([^{}]*)\}")
_SUP_SIGNED = re.compile(r"\^(-?\d+)")
_SUP_PLAIN = re.compile(r"\^([A-Za-z0-9]+)")
_TAG_SPLIT = re.compile(r"(<[^>]+>)")
_UNDERSET_BRACED = re.compile(
    r"\\underset\s*\{\s*\\sim\s*\}\s*\{\s*\\rightarrow\s*\}"
)
_UNDERSET_PLAIN = re.compile(r"\\underset\s*\{\s*\\sim\s*\}\s*\\rightarrow")


def _read_brace_group(text: str, open_index: int) -> Optional[tuple[str, int]]:
    """Si text[open_index] es '{', devuelve el interior y el índice siguiente al cierre."""
    if open_index >= len(text) or text[open_index] != "{":
        return None
    depth = 0
    index = open_index
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            index += 2
            continue
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : index], index + 1
        index += 1
    return None


def _slot_token(number: int) -> str:
    return f"\uE000{number}\uE001"


def _extract_text_blocks(text: str) -> tuple[str, list[str]]:
    """Saca \\text{...} para que el resto de la fórmula siga procesándose."""
    slots: list[str] = []
    pieces: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("\\text", index) and (
            index + 5 >= len(text) or not text[index + 5].isalpha()
        ):
            cursor = index + 5
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            group = _read_brace_group(text, cursor)
            if group is not None:
                inner, end = group
                slots.append(inner)
                pieces.append(_slot_token(len(slots) - 1))
                index = end
                continue
        pieces.append(text[index])
        index += 1
    return "".join(pieces), slots


def _restore_text_blocks(text: str, slots: list[str]) -> str:
    for number, content in enumerate(slots):
        span = (
            f'<span style="font-family:{FONT_FAMILY_SANS}; font-style:normal;">'
            f"{html.escape(content)}</span>"
        )
        text = text.replace(_slot_token(number), span)
    return text


def _render_nested(content: str, depth: int) -> str:
    if any(token in content for token in ("\\", "_", "^", "{", "}")):
        return _render_math(content, depth + 1)
    return content


def _format_sub(content: str, depth: int) -> str:
    rendered = _render_nested(content, depth).strip()
    if not rendered:
        return ""
    if "<" not in rendered:
        rendered = html.escape(rendered)
    return f"<sub>{rendered}</sub>"


def _format_row(content: str, depth: int) -> str:
    rendered = _render_nested(content, depth).strip()
    if rendered.isdigit():
        return f"F{to_subscript(rendered)}"
    if "<" not in rendered:
        rendered = html.escape(rendered)
    return f"F<sub>{rendered}</sub>"


def _format_sup(content: str, depth: int) -> str:
    rendered = _render_nested(content, depth).strip()
    if not rendered:
        return ""
    if "<" not in rendered and all(char in "0123456789-+−nTi()" for char in rendered):
        return rendered.translate(_SUP_GLYPH)
    if "<" not in rendered:
        rendered = html.escape(rendered)
    return f"<sup>{rendered}</sup>"


def _replace_balanced_command(text: str, name: str, depth: int, replacer) -> str:
    """Reemplaza \\name{...}{...} usando el lector de llaves balanceadas."""
    token = "\\" + name
    guard = 0
    search_from = 0
    while guard < 40:
        guard += 1
        index = text.find(token, search_from)
        if index < 0:
            break
        after = index + len(token)
        if after < len(text) and text[after].isalpha():
            search_from = after
            continue
        cursor = after
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        groups: list[str] = []
        parsed = cursor
        for group_index in range(replacer.group_count):
            group = _read_brace_group(text, parsed)
            if group is None:
                groups = []
                break
            inner, parsed = group
            groups.append(inner)
            if group_index + 1 < replacer.group_count:
                while parsed < len(text) and text[parsed].isspace():
                    parsed += 1
        if len(groups) != replacer.group_count:
            search_from = after
            continue
        rendered = replacer.build(groups, depth)
        text = text[:index] + rendered + text[parsed:]
        search_from = index + len(rendered)
    return text


class _FracBuilder:
    group_count = 2

    @staticmethod
    def build(groups: list[str], depth: int) -> str:
        numerator = _render_math(groups[0], depth + 1).strip()
        denominator = _render_math(groups[1], depth + 1).strip()
        return f"({numerator}/{denominator})"


class _SqrtBuilder:
    group_count = 1

    @staticmethod
    def build(groups: list[str], depth: int) -> str:
        body = _render_math(groups[0], depth + 1).strip()
        return f'√<span style="text-decoration:overline;">{body}</span>'


class _MathbbBuilder:
    group_count = 1

    @staticmethod
    def build(groups: list[str], depth: int) -> str:
        del depth
        letter = groups[0].strip()
        return _BLACKBOARD.get(letter, letter)


def _replace_bmatrix(text: str, depth: int) -> str:
    begin = r"\begin{bmatrix}"
    end = r"\end{bmatrix}"
    guard = 0
    while begin in text and guard < 20:
        guard += 1
        start = text.find(begin)
        finish = text.find(end, start + len(begin))
        if finish < 0:
            break
        inner = text[start + len(begin) : finish]
        rows = [_render_math(row, depth + 1).strip() for row in re.split(r"\\\\", inner)]
        rows = [row for row in rows if row]
        rendered = "[" + " ; ".join(rows) + "]"
        text = text[:start] + rendered + text[finish + len(end) :]
    return text


def _replace_named_commands(text: str) -> str:
    text = _UNDERSET_BRACED.sub(" → ", text)
    text = _UNDERSET_PLAIN.sub(" → ", text)
    text = text.replace("\\|", "‖")
    text = re.sub(r"\\not\s*\\geq?", "≱", text)
    text = re.sub(r"\\not\s*\\leq?", "≰", text)
    text = re.sub(r"\\left\s*\\\{", "{", text)
    text = re.sub(r"\\right\s*\\\}", "}", text)
    text = re.sub(r"\\left\s*\.", "", text)
    text = re.sub(r"\\right\s*\.", "", text)
    text = re.sub(r"\\left\s*‖", "‖", text)
    text = re.sub(r"\\right\s*‖", "‖", text)
    text = re.sub(r"\\left\s*([()\[\]|])", r"\1", text)
    text = re.sub(r"\\right\s*([()\[\]|])", r"\1", text)
    text = text.replace("\\{", "{").replace("\\}", "}")
    text = re.sub(r"\\[,;:!\s]", " ", text)

    def _command(match: re.Match[str]) -> str:
        return _COMMAND_REPLACEMENTS[match.group(1)]

    text = _COMMAND_PATTERN.sub(_command, text)
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    text = text.replace("\\", "")
    return text


def _apply_scripts(text: str, depth: int) -> str:
    text = _ROW_BRACED.sub(lambda match: _format_row(match.group(1), depth), text)
    text = _SUB_BRACED.sub(lambda match: _format_sub(match.group(1), depth), text)
    text = _ROW_PLAIN_DIGITS.sub(lambda match: _format_row(match.group(1), depth), text)
    text = _ROW_PLAIN_LETTERS.sub(lambda match: _format_row(match.group(1), depth), text)
    text = _SUB_PLAIN_DIGITS.sub(lambda match: _format_sub(match.group(1), depth), text)
    text = _SUB_PLAIN_LETTERS.sub(lambda match: _format_sub(match.group(1), depth), text)
    text = _SUP_BRACED.sub(lambda match: _format_sup(match.group(1), depth), text)
    text = _SUP_SIGNED.sub(lambda match: _format_sup(match.group(1), depth), text)
    text = _SUP_PLAIN.sub(lambda match: _format_sup(match.group(1), depth), text)
    return text


def _finalize_plain(text: str) -> str:
    def _one(part: str) -> str:
        part = part.replace("+ -", " − ").replace("+-", " − ")
        part = part.replace("-", "−")
        return re.sub(r"\s+", " ", part)

    pieces = _TAG_SPLIT.split(text)
    finalized = "".join(piece if piece.startswith("<") else _one(piece) for piece in pieces)
    return finalized.strip()


def _render_math(src: str, depth: int = 0) -> str:
    """Pipeline interno: texto literal, estructura, comandos, índices y signos."""
    if not src or depth > 12:
        return src or ""
    text, slots = _extract_text_blocks(src)
    text = _replace_bmatrix(text, depth)
    text = _replace_balanced_command(text, "sqrt", depth, _SqrtBuilder)
    for alias in ("dfrac", "tfrac", "frac"):
        text = _replace_balanced_command(text, alias, depth, _FracBuilder)
    text = _replace_balanced_command(text, "mathbb", depth, _MathbbBuilder)
    text = _replace_named_commands(text)
    text = _apply_scripts(text, depth)
    text = _finalize_plain(text)
    return _restore_text_blocks(text, slots)


def plain_formula_to_html(text: str) -> str:
    """Pasa subíndices ASCII (y_1, A_i, x1) a HTML sin reinterpretar el signo menos."""
    if not text:
        return ""
    rendered = format_subscripts_html(text)
    rendered = re.sub(
        r"\bx(\d+)\b",
        lambda match: variable_html(int(match.group(1)) - 1),
        rendered,
    )
    rendered = re.sub(r"\bA(\d+)(?=\(b\))", r"A<sub>\1</sub>", rendered)
    return rendered


def latex_to_book_html(latex: str) -> str:
    """Convierte LaTeX del StepTracer a HTML de libro para QLabel (Qt.RichText)."""
    if not latex or not latex.strip():
        return ""
    body = _render_math(latex)
    return (
        f"<span style='font-size:22px; font-weight:500; letter-spacing:0.03em; "
        f"color:{COLOR_TEXT_PRIMARY}; font-family:{FONT_FAMILY_SANS};'>{body}</span>"
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
