"""Operaciones elementales de fila con generación de notación formal LaTeX y heurísticas explicativas.

100% Python estándar (sin NumPy/SciPy).
"""

from __future__ import annotations
from fractions import Fraction
from typing import Any, Tuple
from prettycalc.core.types import Matrix, parse_scalar, format_scalar


def swap_rows(matrix: Matrix, r1: int, r2: int) -> Matrix:
    """Retorna una nueva matriz con las filas r1 y r2 intercambiadas (0-based).

    Raises:
        IndexError: Si r1 o r2 están fuera del rango de filas.
    """
    if r1 < 0 or r1 >= matrix.rows or r2 < 0 or r2 >= matrix.rows:
        raise IndexError(f"Índices de fila fuera de rango: r1={r1}, r2={r2} (filas={matrix.rows}).")

    if r1 == r2:
        return matrix.copy()

    new_mat = matrix.copy()
    row1 = new_mat.get_row(r1)
    row2 = new_mat.get_row(r2)
    new_mat.set_row(r1, row2)
    new_mat.set_row(r2, row1)
    return new_mat


def scale_row(matrix: Matrix, r: int, scalar: Any) -> Matrix:
    """Retorna una nueva matriz con la fila r multiplicada por un escalar no nulo (0-based).

    Raises:
        ValueError: Si el escalar es cero.
        IndexError: Si r está fuera de rango.
    """
    if r < 0 or r >= matrix.rows:
        raise IndexError(f"Índice de fila fuera de rango: r={r} (filas={matrix.rows}).")

    k = parse_scalar(scalar)
    if k == Fraction(0, 1):
        raise ValueError("Operación inválida: no se puede multiplicar una fila por un escalar cero.")

    if k == Fraction(1, 1):
        return matrix.copy()

    new_mat = matrix.copy()
    current_row = new_mat.get_row(r)
    scaled_row = [val * k for val in current_row]
    new_mat.set_row(r, scaled_row)
    return new_mat


def add_row_multiple(matrix: Matrix, target_r: int, source_r: int, scalar: Any) -> Matrix:
    """Retorna una nueva matriz sumando a la fila target_r un múltiplo de la fila source_r (0-based).

    Transformación: f_{target} -> k * f_{source} + f_{target}

    Raises:
        IndexError: Si target_r o source_r están fuera de rango.
        ValueError: Si target_r == source_r.
    """
    if target_r < 0 or target_r >= matrix.rows or source_r < 0 or source_r >= matrix.rows:
        raise IndexError(
            f"Índices de fila fuera de rango: target={target_r}, source={source_r} (filas={matrix.rows})."
        )

    if target_r == source_r:
        raise ValueError("La fila destino y la fila origen no pueden ser la misma en una combinación lineal.")

    k = parse_scalar(scalar)
    if k == Fraction(0, 1):
        return matrix.copy()

    new_mat = matrix.copy()
    target_row = new_mat.get_row(target_r)
    source_row = new_mat.get_row(source_r)

    combined_row = [
        target_val + (k * source_val)
        for target_val, source_val in zip(target_row, source_row)
    ]
    new_mat.set_row(target_r, combined_row)
    return new_mat


# ==============================================================================
# Generadores de Notación Formal (LaTeX) y Textos Heurísticos
# ==============================================================================

def get_swap_metadata(r1: int, r2: int) -> Tuple[str, str]:
    """Genera (latex_formula, heuristic_text) para un intercambio de filas (índices 0-based)."""
    i1, i2 = r1 + 1, r2 + 1
    latex = f"f_{{{i1}}} \\leftrightarrow f_{{{i2}}}"
    heuristic = f"Se intercambió la Fila {i1} con la Fila {i2}."
    return latex, heuristic


def get_scale_metadata(r: int, scalar: Any) -> Tuple[str, str]:
    """Genera (latex_formula, heuristic_text) para un escalamiento de fila."""
    k = parse_scalar(scalar)
    i = r + 1
    k_latex = format_scalar(k, mode="latex")
    k_str = format_scalar(k, mode="fraction")

    latex = f"f_{{{i}}} \\underset{{\\sim}}\\rightarrow {k_latex} \\cdot f_{{{i}}}"
    heuristic = f"Se multiplicó la Fila {i} por el escalar {k_str}."
    return latex, heuristic


def get_add_multiple_metadata(target_r: int, source_r: int, scalar: Any) -> Tuple[str, str]:
    """Genera (latex_formula, heuristic_text) para una combinación lineal."""
    k = parse_scalar(scalar)
    t = target_r + 1
    s = source_r + 1
    k_str = format_scalar(k, mode="fraction")

    if k == Fraction(1, 1):
        k_latex_term = f"f_{{{s}}}"
        k_heuristic_term = f"la Fila {s}"
    elif k == Fraction(-1, 1):
        k_latex_term = f"-f_{{{s}}}"
        k_heuristic_term = f"-1 por la Fila {s}"
    else:
        k_latex = format_scalar(k, mode="latex")
        k_latex_term = f"{k_latex} \\cdot f_{{{s}}}" if "/" in format_scalar(k, mode="fraction") else f"{k_latex}f_{{{s}}}"
        k_heuristic_term = f"la Fila {s} por {k_str}"

    latex = f"f_{{{t}}} \\underset{{\\sim}}\\rightarrow {k_latex_term} + f_{{{t}}}"
    heuristic = f"Se multiplicó {k_heuristic_term} y se sumó a la Fila {t}."
    return latex, heuristic
