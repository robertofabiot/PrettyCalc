"""Integración del portapapeles del sistema (Qt) con las matrices de PrettyCalc.

Proporciona funciones para copiar y pegar matrices bidireccionales de manera transparente
y silenciosa a través de QGuiApplication.clipboard().
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Union
from fractions import Fraction

try:
    from PySide6.QtGui import QGuiApplication
except ImportError:
    QGuiApplication = None  # type: ignore

from prettycalc.core.clipboard import matrix_to_tsv, parse_matrix_text, parse_matrix_to_matrix
from prettycalc.core.types import Matrix


def copy_matrix_to_clipboard(
    matrix: Union[Matrix, Sequence[Sequence[Any]]],
    mode: str = "fraction",
) -> bool:
    """Copia una matriz al portapapeles del sistema en formato TSV universal.

    Retorna True si la copia fue exitosa, False si no hay portapapeles disponible o la matriz es inválida.
    """
    if QGuiApplication is None:
        return False
    app = QGuiApplication.instance()
    if app is None:
        return False
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return False

    tsv_text = matrix_to_tsv(matrix, mode=mode)
    clipboard.setText(tsv_text)
    return True


def get_clipboard_text() -> str:
    """Obtiene el texto sin formato del portapapeles del sistema."""
    if QGuiApplication is None:
        return ""
    app = QGuiApplication.instance()
    if app is None:
        return ""
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return ""
    return clipboard.text() or ""


def get_matrix_grid_from_clipboard() -> Optional[List[List[Fraction]]]:
    """Obtiene y parsea una matriz rectangular del portapapeles como List[List[Fraction]]."""
    text = get_clipboard_text()
    if not text:
        return None
    return parse_matrix_text(text)


def get_matrix_from_clipboard() -> Optional[Matrix]:
    """Obtiene y parsea una matriz del portapapeles como instancia de Matrix."""
    text = get_clipboard_text()
    if not text:
        return None
    return parse_matrix_to_matrix(text)


def has_matrix_in_clipboard() -> bool:
    """Verifica si el portapapeles actual contiene una matriz o lista de escalares válida."""
    text = get_clipboard_text()
    if not text or not text.strip():
        return False
    grid = parse_matrix_text(text)
    return grid is not None and len(grid) > 0 and len(grid[0]) > 0
