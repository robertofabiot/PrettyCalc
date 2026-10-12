"""Exportación del procedimiento y de los resultados: PDF, HTML, LaTeX y texto.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (Nielsen #7, flexibilidad y eficiencia): un clic lleva el
procedimiento completo a un informe imprimible o a LaTeX para la tarea.
Las funciones ``steps_to_*`` son puras (sin Qt) para poder probarlas.
El PDF usa las fuentes empaquetadas, así que sale igual en Windows y Linux.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Optional, Sequence

from prettycalc.core.tracer import CalculationStep
from prettycalc.core.types import Matrix
from prettycalc.ui.mathtext import latex_to_book_html, prettify_math_text

_STYLE_COLOR = re.compile(r"color\s*:\s*#[0-9A-Fa-f]{3,8}\s*;?")
_STYLE_FONT_SIZE = re.compile(r"font-size\s*:\s*\d+px\s*;?")

_EXPORT_CSS = """
body { font-family: Inter, 'DejaVu Sans', sans-serif; color: #1E1A24; background: #FFFFFF; margin: 24px; }
h1 { font-size: 22px; margin: 0 0 4px 0; }
h2 { font-size: 16px; margin: 18px 0 6px 0; color: #24658C; }
p.meta { color: #4F4859; font-size: 12px; margin: 0 0 16px 0; }
div.step { border-left: 3px solid #2D7A57; padding: 6px 12px; margin: 10px 0 14px 0; }
div.formula { font-size: 16px; margin: 4px 0; }
div.note { font-style: italic; color: #2F2A36; margin: 4px 0 8px 0; }
table.matrix { border-collapse: collapse; margin: 6px 0; font-family: 'Fira Code', 'DejaVu Sans', monospace; }
table.matrix td { padding: 3px 10px; text-align: center; }
table.matrix td.split { border-left: 2px solid #24658C; }
table.matrix td.pivot { background: #D7EEE2; font-weight: 700; }
table.matrix tr.alert td { background: #FBEBD0; }
"""


def _plain_formula(latex: str) -> str:
    """Fórmula legible en texto plano (Unicode) a partir del LaTeX del trazador."""
    rendered = latex_to_book_html(latex)
    rendered = re.sub(r"<sub[^>]*>(.*?)</sub>", r"_\1", rendered)
    rendered = re.sub(r"<sup[^>]*>(.*?)</sup>", r"^\1", rendered)
    rendered = re.sub(r"<[^>]+>", "", rendered)
    return html.unescape(rendered).strip()


def _print_safe_html(fragment: str) -> str:
    """Quita colores y tamaños pensados para el tema oscuro: el informe es blanco."""
    cleaned = _STYLE_COLOR.sub("", fragment)
    return _STYLE_FONT_SIZE.sub("", cleaned)


def matrix_to_html_table(
    matrix: Matrix,
    *,
    split_col: Optional[int] = None,
    pivot: Optional[tuple] = None,
    alert_rows: Sequence[int] = (),
) -> str:
    rows_html = []
    cells = matrix.to_str_list(mode="fraction")
    for r, row in enumerate(cells):
        tds = []
        for c, value in enumerate(row):
            classes = []
            if split_col is not None and c == split_col:
                classes.append("split")
            if pivot is not None and (r, c) == tuple(pivot):
                classes.append("pivot")
            cls = f' class="{" ".join(classes)}"' if classes else ""
            tds.append(f"<td{cls}>{html.escape(value.replace('-', '−'))}</td>")
        row_cls = ' class="alert"' if r in alert_rows else ""
        rows_html.append(f"<tr{row_cls}>{''.join(tds)}</tr>")
    return f'<table class="matrix">{"".join(rows_html)}</table>'


def steps_to_html(steps: Sequence[CalculationStep], title: str, subtitle: str = "") -> str:
    """Documento HTML autocontenido e imprimible del procedimiento."""
    blocks = [
        "<html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title><style>{_EXPORT_CSS}</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<p class='meta'>{html.escape(subtitle or 'PrettyCalc · Álgebra Lineal')} · {len(steps)} paso(s)</p>",
    ]
    for index, step in enumerate(steps):
        label = "Paso inicial" if index == 0 else f"Paso {index + 1}"
        blocks.append("<div class='step'>")
        blocks.append(f"<h2>{label}</h2>")
        blocks.append(f"<div class='formula'>{_print_safe_html(latex_to_book_html(step.latex_formula))}</div>")
        if step.heuristic_text:
            blocks.append(f"<div class='note'>{html.escape(prettify_math_text(step.heuristic_text))}</div>")
        blocks.append(
            matrix_to_html_table(
                step.matrix,
                split_col=step.split_col,
                pivot=step.pivot_pos,
                alert_rows=getattr(step, "alert_rows", ()),
            )
        )
        blocks.append("</div>")
    blocks.append("</body></html>")
    return "".join(blocks)


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def steps_to_latex(steps: Sequence[CalculationStep], title: str) -> str:
    """Documento LaTeX compilable con cada paso: fórmula, explicación y matriz."""
    lines = [
        r"\documentclass{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{amsmath,amssymb}",
        r"\begin{document}",
        rf"\section*{{{_latex_escape(title)}}}",
    ]
    for index, step in enumerate(steps):
        label = "Paso inicial" if index == 0 else f"Paso {index + 1}"
        lines.append(rf"\subsection*{{{label}}}")
        lines.append(rf"\[ {step.latex_formula} \]")
        if step.heuristic_text:
            lines.append(_latex_escape(step.heuristic_text) + r"\par")
        lines.append(r"\[")
        lines.append(step.matrix.to_latex(split_col=step.split_col))
        lines.append(r"\]")
    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"


def steps_to_text(steps: Sequence[CalculationStep], title: str) -> str:
    """Resumen en texto plano (para pegar en un chat, correo o cuaderno)."""
    out = [title, "=" * len(title)]
    for index, step in enumerate(steps):
        label = "Paso inicial" if index == 0 else f"Paso {index + 1}"
        out.append("")
        out.append(f"{label}: {_plain_formula(step.latex_formula)}")
        if step.heuristic_text:
            out.append(f"  {prettify_math_text(step.heuristic_text)}")
        for line in str(step.matrix).splitlines():
            out.append(f"  {line}")
    return "\n".join(out) + "\n"


def write_report(path: str, steps: Sequence[CalculationStep], title: str, subtitle: str = "") -> str:
    """Escribe el informe según la extensión (.pdf, .html, .tex o .txt). Devuelve la ruta."""
    target = Path(path)
    suffix = target.suffix.lower()
    if suffix == ".tex":
        target.write_text(steps_to_latex(steps, title), encoding="utf-8")
    elif suffix == ".txt":
        target.write_text(steps_to_text(steps, title), encoding="utf-8")
    elif suffix in (".html", ".htm"):
        target.write_text(steps_to_html(steps, title, subtitle), encoding="utf-8")
    else:
        if suffix != ".pdf":
            target = target.with_suffix(".pdf")
        from PySide6.QtGui import QPageSize, QPdfWriter, QTextDocument
        from prettycalc.ui.platform_setup import load_bundled_fonts, make_font

        load_bundled_fonts()
        document = QTextDocument()
        document.setDefaultFont(make_font(13))
        document.setHtml(steps_to_html(steps, title, subtitle))
        writer = QPdfWriter(str(target))
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setResolution(110)
        writer.setTitle(title)
        writer.setCreator("PrettyCalc")
        document.print_(writer)
    return str(target)
