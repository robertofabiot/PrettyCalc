"""Pasos que siguen a la RREF: pivotes, rango, núcleo e imagen.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Transformaciones Lineales y Espacios Vectoriales terminaban el carrusel en
la RREF y mostraban las bases solo como resultado. Estas funciones registran
cómo se leen de la RREF: qué columnas tienen pivote (rango), qué variables
quedan libres (nulidad), cómo sale cada vector del núcleo al fijar una
variable libre en 1 y por qué las columnas pivote de A forman la imagen.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List

from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import Matrix, Vector, format_scalar, subscript


def _x(col: int) -> str:
    return f"x{subscript(col + 1)}"


def _columns(cols: List[int]) -> str:
    return ", ".join(str(col + 1) for col in cols) if cols else "ninguna"


def _vector(v: Vector) -> str:
    return "(" + ", ".join(format_scalar(c) for c in v.components) + ")"


def _pivot_rows(pivot_cols: List[int]) -> Dict[int, int]:
    """Columna pivote → fila de la RREF donde está su pivote."""
    return {col: row for row, col in enumerate(pivot_cols)}


def record_pivot_analysis(
    tracer: StepTracer,
    rref: Matrix,
    pivot_cols: List[int],
    free_cols: List[int],
) -> None:
    """Pivotes resaltados en la RREF: rango y variables libres."""
    rows = _pivot_rows(pivot_cols)
    free = ", ".join(_x(col) for col in free_cols) if free_cols else "ninguna"
    tracer.record_step(
        rref,
        latex_formula=rf"\text{{rango}} = {len(pivot_cols)},\quad \text{{nulidad}} = {len(free_cols)}",
        heuristic_text=(
            f"RREF terminada. Columnas con pivote (resaltados): {_columns(pivot_cols)}, "
            f"así que el rango es {len(pivot_cols)}. Variables libres (columnas sin pivote): "
            f"{free}, así que la nulidad es {len(free_cols)}."
        ),
        highlight_cells=tuple((rows[col], col) for col in pivot_cols),
    )


def record_kernel_basis(
    tracer: StepTracer,
    rref: Matrix,
    pivot_cols: List[int],
    free_cols: List[int],
    basis: List[Vector],
    name: str,
    space: str,
) -> None:
    """Un paso por variable libre: se fija en 1 y se despejan las básicas."""
    if not free_cols:
        tracer.record_step(
            rref,
            latex_formula=rf"{space} = \{{\mathbf{{0}}\}}",
            heuristic_text=(
                f"No hay variables libres: la única solución de A x = 0 es x = 0, "
                f"así que {space} = {{0}} y su base es vacía."
            ),
        )
        return
    rows = _pivot_rows(pivot_cols)
    for number, (free_col, vector) in enumerate(zip(free_cols, basis), start=1):
        others = [col for col in free_cols if col != free_col]
        fixed = f"{_x(free_col)} = 1" + (
            " y " + ", ".join(_x(col) for col in others) + " = 0" if others else ""
        )
        solved = "; ".join(
            f"fila {rows[col] + 1}: {_x(col)} = −({format_scalar(rref.get(rows[col], free_col))}) "
            f"= {format_scalar(-rref.get(rows[col], free_col))}"
            for col in pivot_cols
        ) or "no hay variables básicas"
        tracer.record_step(
            rref,
            latex_formula=rf"{name}_{{{number}}} \in {space}",
            heuristic_text=(
                f"Vector {name}{subscript(number)}: {fixed}. Cada fila de la RREF despeja su "
                f"variable básica: {solved}. Resultado: {name}{subscript(number)} = {_vector(vector)}."
            ),
            highlight_cells=tuple((row, free_col) for row in range(rref.rows)),
        )


def record_image_basis(
    tracer: StepTracer,
    A: Matrix,
    pivot_cols: List[int],
    basis: List[Vector],
) -> None:
    """Las columnas de A (no de la RREF) en las posiciones pivote forman la base de im(T)."""
    if not pivot_cols:
        tracer.record_step(
            A,
            latex_formula=r"\text{im}(T) = \{\mathbf{0}\}",
            heuristic_text="A no tiene pivotes (es la matriz nula): im(T) = {0}.",
        )
        return
    vectors = "; ".join(
        f"c{subscript(number)} = columna {col + 1} = {_vector(vector)}"
        for number, (col, vector) in enumerate(zip(pivot_cols, basis), start=1)
    )
    tracer.record_step(
        A,
        latex_formula=r"\text{im}(T) = \text{gen}\{\text{columnas pivote de } A\}",
        heuristic_text=(
            "Base de la imagen: se toman las columnas de la A original (no de la RREF) "
            f"en las posiciones pivote, resaltadas: {vectors}."
        ),
        highlight_cells=tuple((row, col) for col in pivot_cols for row in range(A.rows)),
    )


def record_dimension_theorem(tracer: StepTracer, rref: Matrix, n: int, rank: int, nullity: int) -> None:
    holds = rank + nullity == n
    tracer.record_step(
        rref,
        latex_formula=rf"n = \text{{nulidad}} + \text{{rango}}:\ {n} = {nullity} + {rank}",
        heuristic_text=(
            f"Teorema de la Dimensión: dim(dominio) = nulidad + rango, {n} = {nullity} + {rank}. "
            + ("Se cumple." if holds else "No se cumple.")
        ),
    )


def record_generating_conclusion(tracer: StepTracer, rref: Matrix, rank: int, m: int) -> None:
    """Genera ℝᵐ si y solo si cada fila de la RREF tiene pivote (rango = m)."""
    space = f"ℝ{str(m).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))}"
    if rank == m:
        text = (
            f"rango = {rank} = m: cada fila de la RREF tiene pivote, así que A x = b tiene "
            f"solución para todo b y el conjunto genera {space}."
        )
    else:
        zero_rows = list(range(rank, rref.rows))
        which = (
            f"la fila {zero_rows[0] + 1} de la RREF es nula"
            if len(zero_rows) == 1
            else f"las filas {_columns(zero_rows)} de la RREF son nulas"
        )
        text = (
            f"rango = {rank} < m = {m}: {which}; "
            f"para algún b esa fila daría 0 = c ≠ 0, así que el conjunto no genera {space}."
        )
    tracer.record_step(
        rref,
        latex_formula=rf"\text{{rango}}(A) = {rank} {'=' if rank == m else '<'} m = {m}",
        heuristic_text=text,
        alert_rows=tuple(range(rank, rref.rows)) if rank < m else (),
    )
