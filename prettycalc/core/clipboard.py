"""Serialización y parseo de matrices para operaciones de portapapeles (Copiar y Pegar).

Proporciona soporte bidireccional estándar TSV (compatible con Excel, Google Sheets y texto plano),
así como soporte para CSV, sintaxis de listas Python [[...]] y formato matricial delimitado por espacios.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any, List, Optional, Sequence, Union

from prettycalc.core.types import Matrix, format_scalar, parse_scalar


def matrix_to_tsv(matrix: Union[Matrix, Sequence[Sequence[Any]]], mode: str = "fraction") -> str:
    """Convierte una matriz o lista bidimensional a texto TSV estándar.

    Las columnas se separan por tabulaciones (\\t) y las filas por saltos de línea (\\n).
    Este formato es el estándar universal reconocido por Microsoft Excel,
    Google Sheets, LibreOffice Calc y procesadores de texto.
    """
    if isinstance(matrix, Matrix):
        raw_grid = matrix.to_list()
    else:
        raw_grid = matrix

    lines: List[str] = []
    for row in raw_grid:
        line_items: List[str] = []
        for val in row:
            if isinstance(val, Fraction):
                formatted = format_scalar(val, mode=mode)
            elif isinstance(val, (int, float)):
                formatted = format_scalar(val, mode=mode)
            else:
                formatted = str(val).strip()
            line_items.append(formatted)
        lines.append("\t".join(line_items))

    return "\n".join(lines)


def _split_row_tokens(line: str) -> List[str]:
    """Extrae los valores de una fila separada por tabulaciones, comas, punto y coma o espacios."""
    cleaned = line.strip()
    if not cleaned:
        return []

    # 1. Tabulaciones (\t) - Estándar TSV / Excel
    if "\t" in cleaned:
        return [tok.strip() for tok in cleaned.split("\t") if tok.strip()]

    # 2. Comas o punto y coma (CSV)
    if ";" in cleaned:
        return [tok.strip() for tok in cleaned.split(";") if tok.strip()]
    if "," in cleaned and not cleaned.startswith("["):
        return [tok.strip() for tok in cleaned.split(",") if tok.strip()]

    # 3. Delimitado por espacios múltiples
    return [tok.strip() for tok in cleaned.split() if tok.strip()]


def _clean_token(tok: str) -> str:
    """Limpia un token numérico soportando signos unicode y fracciones LaTeX."""
    cleaned = tok.replace("−", "-").replace(" ", "").strip()
    cleaned = re.sub(r"(-?)\\frac\{([^}]+)\}\{([^}]+)\}", r"\1\2/\3", cleaned)
    if cleaned.startswith("--"):
        cleaned = cleaned[2:]
    return cleaned


def parse_matrix_text(text: str) -> Optional[List[List[Fraction]]]:
    """Parsea una cadena de texto a una cuadrícula rectangular de objetos Fraction.

    Admite:
    - Tabulaciones (Excel / Sheets TSV)
    - Comas o puntos y comas (CSV)
    - Listas Python: [[1, 2], [3, 4]] o [1, 2, 3]
    - Matrices LaTeX: \\begin{...} a & b \\\\ c & d \\end{...}
    - Valores numéricos en enteros (5), fracciones (1/2, \\frac{1}{2}), decimales (0.75)
      y signos negativos unicode (−).

    Retorna:
        Lista 2D rectangular de Fraction si el contenido es válido, o None en caso contrario.
    """
    if not text or not text.strip():
        return None

    cleaned_text = text.strip()

    # Manejo de sintaxis LaTeX básica (\begin{...} ... & ... \\ ... \end{...})
    if "\\begin{" in cleaned_text and "\\end{" in cleaned_text:
        # Extraer el interior del entorno matricial
        inner = re.sub(r"\\begin\{[^}]+\}", "", cleaned_text)
        inner = re.sub(r"\\end\{[^}]+\}", "", inner)
        rows_latex = [r.strip() for r in inner.split("\\\\") if r.strip()]
        result_grid: List[List[Fraction]] = []
        for r_str in rows_latex:
            cols = [c.strip() for c in r_str.split("&") if c.strip()]
            if not cols:
                continue
            try:
                row_vals = [parse_scalar(_clean_token(c)) for c in cols]
                result_grid.append(row_vals)
            except Exception:
                return None
        if result_grid and all(len(r) == len(result_grid[0]) for r in result_grid):
            return result_grid
        return None

    # Manejo de listas tipo Python: [[1, 2], [3, 4]]
    if cleaned_text.startswith("[") and cleaned_text.endswith("]"):
        # Buscar filas entre corchetes internos [...]
        bracket_rows = re.findall(r"\[([^\[\]]+)\]", cleaned_text)
        if bracket_rows:
            result_grid = []
            for r_str in bracket_rows:
                items = [it.strip() for it in r_str.split(",") if it.strip()]
                if not items:
                    items = [it.strip() for it in r_str.split() if it.strip()]
                if not items:
                    continue
                try:
                    row_vals = [parse_scalar(_clean_token(it)) for it in items]
                    result_grid.append(row_vals)
                except Exception:
                    return None
            if result_grid and all(len(r) == len(result_grid[0]) for r in result_grid):
                return result_grid

    # Manejo de texto con saltos de línea (TSV, CSV, espacios)
    lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]
    if not lines:
        return None

    grid: List[List[Fraction]] = []
    for line in lines:
        tokens = _split_row_tokens(line)
        if not tokens:
            continue
        row: List[Fraction] = []
        for tok in tokens:
            try:
                row.append(parse_scalar(_clean_token(tok)))
            except Exception:
                return None
        grid.append(row)

    if not grid or not grid[0]:
        return None

    # Verificar que sea rectangular
    expected_cols = len(grid[0])
    if any(len(r) != expected_cols for r in grid):
        return None

    return grid


def parse_matrix_to_matrix(text: str) -> Optional[Matrix]:
    """Parsea texto del portapapeles directamente a una instancia Matrix de PrettyCalc.

    Retorna None si el formato no es válido o está vacío.
    """
    grid = parse_matrix_text(text)
    if grid is None:
        return None
    try:
        return Matrix(grid)
    except Exception:
        return None
