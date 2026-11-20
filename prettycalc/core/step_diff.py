"""Qué cambió entre dos pasos de un procedimiento.

Compara las matrices de dos pasos consecutivos con aritmética exacta y
reconoce la operación elemental de fila que lleva de una a otra:

- intercambio ``Fᵢ ↔ Fⱼ``;
- escalado ``Fᵢ → k·Fᵢ``;
- suma de un múltiplo ``Fᵢ → Fᵢ + k·Fⱼ``.

Los metadatos del paso (``actor_row``, ``affected_rows``) solo orientan la
búsqueda: la operación se devuelve únicamente si la aritmética la confirma
entrada por entrada. Así, quien la use para dibujar una fila que viaja nunca
muestra una operación que no ocurrió.

100 % Python estándar, sin dependencias de interfaz.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, List, Optional, Sequence, Tuple

from prettycalc.core.types import Matrix

Cell = Tuple[int, int]

SWAP = "swap"
SCALE = "scale"
ADD = "add"


@dataclass(frozen=True)
class RowOperation:
    """Operación elemental de fila confirmada entre dos matrices.

    Attributes:
        kind: ``"swap"``, ``"scale"`` o ``"add"``.
        target: Fila que cambia (en un intercambio, la primera de las dos).
        source: Fila que actúa (la otra fila en un intercambio; ``None`` al escalar).
        factor: ``k`` del escalado o de la suma (``None`` en un intercambio).
        columns: Columnas ``[inicio, fin)`` donde se verificó la operación.
    """

    kind: str
    target: int
    source: Optional[int]
    factor: Optional[Fraction]
    columns: Tuple[int, int]

    def rows(self) -> Tuple[int, ...]:
        if self.kind == SWAP and self.source is not None:
            return (self.target, self.source)
        return (self.target,)


def changed_cells(before: Optional[Matrix], after: Optional[Matrix]) -> Optional[Tuple[Cell, ...]]:
    """Entradas cuyo valor cambió, o ``None`` si las formas no coinciden."""
    if before is None or after is None or before.shape != after.shape:
        return None
    return tuple(
        (r, c)
        for r in range(after.rows)
        for c in range(after.cols)
        if before.get(r, c) != after.get(r, c)
    )


def _row(matrix: Matrix, r: int, c0: int, c1: int) -> List[Fraction]:
    return [matrix.get(r, c) for c in range(c0, c1)]


def _proportional(values: Sequence[Fraction], base: Sequence[Fraction]) -> Optional[Fraction]:
    """``k`` tal que ``values == k · base`` (con ``base`` no nula), o ``None``."""
    k: Optional[Fraction] = None
    for value, ref in zip(values, base):
        if ref == 0:
            if value != 0:
                return None
            continue
        ratio = Fraction(value) / Fraction(ref)
        if k is None:
            k = ratio
        elif ratio != k:
            return None
    return k


def detect_row_operation(
    before: Optional[Matrix],
    after: Optional[Matrix],
    *,
    actor_row: Optional[int] = None,
    affected_rows: Iterable[int] = (),
    columns: Optional[Tuple[int, int]] = None,
) -> Optional[RowOperation]:
    """Operación de fila que lleva ``before`` a ``after`` en ``columns``, si existe.

    Solo se reconoce una operación si las demás filas (en esas columnas) no
    cambiaron. Con ``actor_row`` se prefiere la suma de un múltiplo de esa
    fila; sin ella, el escalado.
    """
    if before is None or after is None or before.shape != after.shape:
        return None
    c0, c1 = columns if columns is not None else (0, after.cols)
    if not 0 <= c0 < c1 <= after.cols:
        return None
    rows = after.rows
    changed = [
        r for r in range(rows) if any(before.get(r, c) != after.get(r, c) for c in range(c0, c1))
    ]
    if not changed:
        return None

    if len(changed) == 2:
        i, j = changed
        if _row(before, i, c0, c1) == _row(after, j, c0, c1) and _row(before, j, c0, c1) == _row(after, i, c0, c1):
            return RowOperation(SWAP, i, j, None, (c0, c1))
        return None

    if len(changed) != 1:
        return None
    target = changed[0]
    old = _row(before, target, c0, c1)
    new = _row(after, target, c0, c1)
    delta = [b - a for a, b in zip(old, new)]

    def as_add(source: int) -> Optional[RowOperation]:
        if source == target or not 0 <= source < rows:
            return None
        base = _row(before, source, c0, c1)
        if all(v == 0 for v in base):
            return None
        k = _proportional(delta, base)
        if k is None or k == 0:
            return None
        return RowOperation(ADD, target, source, k, (c0, c1))

    def as_scale() -> Optional[RowOperation]:
        if all(v == 0 for v in old):
            return None
        k = _proportional(new, old)
        if k is None or k in (0, 1):
            return None
        return RowOperation(SCALE, target, None, k, (c0, c1))

    if actor_row is not None:
        found = as_add(actor_row)
        if found is not None:
            return found
    found = as_scale()
    if found is not None:
        return found
    hinted = [r for r in affected_rows if r != target]
    for source in hinted + [r for r in range(rows) if r not in hinted]:
        found = as_add(source)
        if found is not None:
            return found
    return None


def detect_step_operation(
    before: Optional[Matrix],
    after: Optional[Matrix],
    *,
    split_col: Optional[int] = None,
    actor_row: Optional[int] = None,
    affected_rows: Iterable[int] = (),
) -> Optional[RowOperation]:
    """Como :func:`detect_row_operation`, probando primero toda la matriz.

    Si la matriz completa no corresponde a una sola operación y hay una
    partición ``[izquierda | derecha]`` (por ejemplo ``[L | U]`` en una
    factorización), se prueba cada bloque por separado.
    """
    affected = tuple(affected_rows)
    found = detect_row_operation(before, after, actor_row=actor_row, affected_rows=affected)
    if found is not None or after is None or split_col is None:
        return found
    if not 0 < split_col < after.cols:
        return None
    for block in ((split_col, after.cols), (0, split_col)):
        found = detect_row_operation(before, after, actor_row=actor_row, affected_rows=affected, columns=block)
        if found is not None:
            return found
    return None


def replaced_column(base: Optional[Matrix], after: Optional[Matrix], highlight: Iterable[Cell]) -> Optional[int]:
    """Columna que ``after`` reemplazó respecto de ``base`` (como ``Aᵢ(b)`` en Cramer).

    Devuelve ``j`` si ``highlight`` es la columna ``j`` completa, ``after``
    coincide con ``base`` fuera de ella y la columna sí cambió.
    """
    if base is None or after is None or base.shape != after.shape:
        return None
    cells = set(highlight)
    if not cells:
        return None
    cols = {c for _r, c in cells}
    if len(cols) != 1:
        return None
    col = next(iter(cols))
    if cells != {(r, col) for r in range(after.rows)}:
        return None
    for r in range(after.rows):
        for c in range(after.cols):
            if c != col and base.get(r, c) != after.get(r, c):
                return None
    if all(base.get(r, col) == after.get(r, col) for r in range(after.rows)):
        return None
    return col


def leading_entries(matrix: Optional[Matrix], split_col: Optional[int] = None) -> Tuple[Cell, ...]:
    """Primera entrada no nula de cada fila en el bloque de coeficientes."""
    if matrix is None:
        return ()
    limit = split_col if split_col is not None else matrix.cols
    found = []
    for r in range(matrix.rows):
        for c in range(limit):
            if matrix.get(r, c) != 0:
                found.append((r, c))
                break
    return tuple(found)


def is_echelon(matrix: Optional[Matrix], split_col: Optional[int] = None) -> bool:
    """Forma escalonada: pivotes que bajan hacia la derecha y filas nulas al final."""
    if matrix is None:
        return False
    limit = split_col if split_col is not None else matrix.cols
    last = -1
    seen_zero = False
    for r in range(matrix.rows):
        lead = next((c for c in range(limit) if matrix.get(r, c) != 0), None)
        if lead is None:
            seen_zero = True
            continue
        if seen_zero or lead <= last:
            return False
        last = lead
    return True


def contradiction_rows(matrix: Optional[Matrix], split_col: Optional[int]) -> Tuple[int, ...]:
    """Filas ``[0 … 0 | c]`` con ``c ≠ 0``."""
    if matrix is None or split_col is None or not 0 < split_col < matrix.cols:
        return ()
    return tuple(
        r
        for r in range(matrix.rows)
        if all(matrix.get(r, c) == 0 for c in range(split_col))
        and any(matrix.get(r, c) != 0 for c in range(split_col, matrix.cols))
    )
