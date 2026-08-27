"""Algoritmos de eliminación por filas (Gauss y Gauss-Jordan) con trazabilidad paso a paso.

100% Python estándar (sin NumPy/SciPy).
"""

from __future__ import annotations
from fractions import Fraction
from typing import Optional, Tuple, List
from prettycalc.core.types import Matrix
from prettycalc.core.operations import (
    swap_rows,
    scale_row,
    add_row_multiple,
    get_swap_metadata,
    get_scale_metadata,
    get_add_multiple_metadata,
)
from prettycalc.core.tracer import StepTracer


def gaussian_elimination(
    matrix: Matrix,
    split_col: Optional[int] = None,
    tracer: Optional[StepTracer] = None,
) -> Tuple[Matrix, StepTracer]:
    """Ejecuta la eliminación gaussiana hacia adelante (forma escalonada por filas - REF).

    Args:
        matrix: Matriz (típicamente aumentada [A | b]).
        split_col: Índice de la columna divisoria de términos independientes.
        tracer: Instancia opcional de StepTracer; si es None, se creará una nueva.

    Returns:
        (Matriz en forma escalonada, Trazador con el historial completo de pasos).
    """
    effective_split = split_col if split_col is not None else matrix.cols - 1
    if tracer is None:
        tracer = StepTracer(split_col=effective_split)

    tracer.record_initial(matrix)
    current_matrix = matrix.copy()
    num_rows, num_cols = current_matrix.shape

    # Las columnas a evaluar como coeficientes (hasta split_col o num_cols)
    max_pivot_col = effective_split if effective_split < num_cols else num_cols
    pivot_row = 0

    for col in range(max_pivot_col):
        if pivot_row >= num_rows:
            break

        # 1. Búsqueda de pivote no nulo en la columna actual
        selected_row = None
        for r in range(pivot_row, num_rows):
            if current_matrix.get(r, col) != Fraction(0, 1):
                selected_row = r
                break

        # Si toda la columna debajo es cero, pasar a la siguiente columna
        if selected_row is None:
            continue

        # 2. Intercambio de fila si el pivote no está en pivot_row
        if selected_row != pivot_row:
            current_matrix = swap_rows(current_matrix, pivot_row, selected_row)
            latex, heur = get_swap_metadata(pivot_row, selected_row)
            tracer.record_step(
                matrix=current_matrix,
                latex_formula=latex,
                heuristic_text=heur,
                pivot_pos=(pivot_row, col),
                split_col=effective_split,
                affected_rows=(pivot_row, selected_row),
            )

        pivot_val = current_matrix.get(pivot_row, col)

        # 3. Eliminación hacia adelante (generar ceros en las filas inferiores)
        for r in range(pivot_row + 1, num_rows):
            target_val = current_matrix.get(r, col)
            if target_val != Fraction(0, 1):
                factor = - (target_val / pivot_val)
                current_matrix = add_row_multiple(
                    current_matrix,
                    target_r=r,
                    source_r=pivot_row,
                    scalar=factor,
                )
                latex, heur = get_add_multiple_metadata(target_r=r, source_r=pivot_row, scalar=factor)
                tracer.record_step(
                    matrix=current_matrix,
                    latex_formula=latex,
                    heuristic_text=heur,
                    pivot_pos=(pivot_row, col),
                    split_col=effective_split,
                    actor_row=pivot_row,
                    affected_rows=(r,),
                )

        pivot_row += 1

    return current_matrix, tracer


def gauss_jordan_elimination(
    matrix: Matrix,
    split_col: Optional[int] = None,
    tracer: Optional[StepTracer] = None,
) -> Tuple[Matrix, StepTracer]:
    """Ejecuta la reducción completa de Gauss-Jordan (forma escalonada reducida por filas - RREF).

    1. Realiza la fase hacia adelante (Gauss).
    2. Escala cada fila pivote para que el pivote principal sea 1.
    3. Realiza la fase hacia atrás para generar ceros por encima de cada pivote.
    """
    effective_split = split_col if split_col is not None else matrix.cols - 1
    if tracer is None:
        tracer = StepTracer(split_col=effective_split)

    # Fase 1: Escalonamiento hacia adelante
    current_matrix, _ = gaussian_elimination(matrix, split_col=effective_split, tracer=tracer)
    num_rows, num_cols = current_matrix.shape
    max_pivot_col = effective_split if effective_split < num_cols else num_cols

    # Encontrar las posiciones de los pivotes principales (row, col)
    pivots: List[Tuple[int, int]] = []
    curr_col = 0
    for r in range(num_rows):
        while curr_col < max_pivot_col:
            if current_matrix.get(r, curr_col) != Fraction(0, 1):
                pivots.append((r, curr_col))
                curr_col += 1
                break
            curr_col += 1

    # Fase 2 y 3: Normalizar a 1 y eliminar hacia arriba (de abajo hacia arriba)
    for r, col in reversed(pivots):
        pivot_val = current_matrix.get(r, col)

        # Escalar fila pivote a 1 si es distinto de 1
        if pivot_val != Fraction(1, 1):
            scale_factor = Fraction(1, 1) / pivot_val
            current_matrix = scale_row(current_matrix, r, scale_factor)
            latex, heur = get_scale_metadata(r, scale_factor)
            tracer.record_step(
                matrix=current_matrix,
                latex_formula=latex,
                heuristic_text=heur,
                pivot_pos=(r, col),
                split_col=effective_split,
                affected_rows=(r,),
            )

        # Eliminar hacia arriba
        for upper_r in range(r - 1, -1, -1):
            upper_val = current_matrix.get(upper_r, col)
            if upper_val != Fraction(0, 1):
                factor = - upper_val
                current_matrix = add_row_multiple(
                    current_matrix,
                    target_r=upper_r,
                    source_r=r,
                    scalar=factor,
                )
                latex, heur = get_add_multiple_metadata(target_r=upper_r, source_r=r, scalar=factor)
                tracer.record_step(
                    matrix=current_matrix,
                    latex_formula=latex,
                    heuristic_text=heur,
                    pivot_pos=(r, col),
                    split_col=effective_split,
                    actor_row=r,
                    affected_rows=(upper_r,),
                )

    return current_matrix, tracer
