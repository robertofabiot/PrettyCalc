"""Tablas de datos: flujo horizontal y números alineados por el punto decimal.

Las tablas de iteraciones (bisección, Jacobi, Gauss-Seidel, comparación) no
dibujan bordes verticales: solo una línea sutil de 1 px separa las filas
(``QTableView::item`` en ``theme.py``). Los números van a la derecha y, en
fuente monoespaciada, se rellenan con espacios a la derecha para que los
puntos decimales queden en la misma vertical aunque cada valor tenga una
cantidad distinta de decimales. El valor mostrado no cambia: no se agregan
ceros que sugieran una precisión que el cálculo no tiene.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence

try:
    from PySide6.QtCore import QEvent, QObject, Qt, QTimer
    from PySide6.QtGui import QFontMetrics
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QHeaderView,
        QStyledItemDelegate,
        QTableWidget,
        QTableWidgetItem,
    )
except ImportError:  # pragma: no cover
    QTableWidget = object  # type: ignore
    QStyledItemDelegate = object  # type: ignore
    QObject = object  # type: ignore

from prettycalc.ui.theme import FONT_FAMILY_MONO

#: Un número escrito en decimal o en notación científica (con − tipográfico o -).
_NUMBER = re.compile(r"^[−+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?$")


def is_number(text: str) -> bool:
    return bool(_NUMBER.match((text or "").strip()))


def _tail(text: str) -> int:
    """Caracteres a la derecha del punto decimal (−1 si no hay punto)."""
    mantissa = re.split(r"[eE]", text, maxsplit=1)[0]
    if "." not in mantissa:
        return -1
    return len(text) - text.index(".") - 1


def _is_scientific(text: str) -> bool:
    return "e" in text.lower()


def align_decimals(texts: Sequence[str]) -> List[str]:
    """Rellena con espacios para que, alineados a la derecha, los puntos coincidan.

    Los textos que no son números («—», «No definido») quedan como están.
    """
    numeric = [t.strip() for t in texts if is_number(t)]
    if not numeric:
        return list(texts)
    # La notación científica no fija el ancho: su exponente puede sobresalir.
    plain = [t for t in numeric if not _is_scientific(t)] or numeric
    width = max(_tail(t) for t in plain)
    if width < 0:
        return list(texts)
    aligned: List[str] = []
    for text in texts:
        value = text.strip()
        if not is_number(value):
            aligned.append(text)
            continue
        tail = _tail(value)
        missing = width - tail if tail >= 0 else width + 1
        aligned.append(value + " " * max(0, missing))
    return aligned


def numeric_item(text: str, tooltip: Optional[str] = None) -> "QTableWidgetItem":
    """Celda numérica: alineada a la derecha y centrada en vertical."""
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    if tooltip is not None:
        item.setToolTip(tooltip)
    return item


def text_item(text: str) -> "QTableWidgetItem":
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return item


class DecimalAlignDelegate(QStyledItemDelegate):
    """Muestra sin relleno las columnas cuyos valores alineados no caben.

    La decisión es por columna (no por celda), así una columna nunca mezcla
    valores alineados por el punto con valores que no lo están. En una
    ventana angosta, ``"2        "`` recortado se leería «2 …».
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.raw_columns: set = set()

    def initStyleOption(self, option, index) -> None:  # noqa: N802
        super().initStyleOption(option, index)
        if index.column() in self.raw_columns and option.text:
            option.text = option.text.rstrip()


#: Relleno horizontal de cada celda (QSS y margen del estilo).
_CELL_SLACK = 12
#: Separación extra entre la columna índice y los datos.
_FIRST_GAP = 0
#: Por debajo de este ancho (px) una columna no se encoge al faltar espacio.
_SHORT_COLUMN = 48


def _column_need(
    table: "QTableWidget", col: int, metrics: "QFontMetrics", header: "QFontMetrics", *, raw: bool = False
) -> int:
    need = 0
    header_item = table.horizontalHeaderItem(col)
    if header_item is not None:
        need = header.horizontalAdvance(header_item.text())
    for row in range(table.rowCount()):
        item = table.item(row, col)
        if item is not None:
            text = item.text().rstrip() if raw else item.text()
            need = max(need, metrics.horizontalAdvance(text))
    return need + _CELL_SLACK


def fit_columns(table: "QTableWidget") -> None:
    """Reparte el ancho según lo que necesita cada columna, sin desplazamiento horizontal.

    Si no alcanza, primero se quita el relleno de alineación a las columnas
    que más ahorran (una columna entera a la vez) y, si aun así no cabe, todas
    se encogen en la misma proporción.
    """
    columns = table.columnCount()
    if columns == 0:
        return
    table.ensurePolished()
    available = table.viewport().width()
    if available <= 0:
        return
    metrics = QFontMetrics(table.font())
    header_metrics = QFontMetrics(table.horizontalHeader().font())
    aligned = [_column_need(table, col, metrics, header_metrics) for col in range(columns)]
    raw = [_column_need(table, col, metrics, header_metrics, raw=True) for col in range(columns)]
    # La primera columna (k, el índice) se separa un poco más de los datos.
    aligned[0] += _FIRST_GAP
    raw[0] += _FIRST_GAP
    needs = list(aligned)
    raw_columns: set = set()
    while sum(needs) > available:
        savings = [(needs[col] - raw[col], col) for col in range(columns) if col not in raw_columns]
        saving, col = max(savings, default=(0, -1))
        if saving <= 0:
            break
        raw_columns.add(col)
        needs[col] = raw[col]
    total = sum(needs)
    header = table.horizontalHeader()
    header.setMinimumSectionSize(16)
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.Fixed)
    # Las columnas cortas (índices, enteros) nunca se encogen: el resto absorbe la falta.
    short = {col for col in range(columns) if needs[col] <= _SHORT_COLUMN}
    fixed = sum(needs[col] for col in short)
    flexible = total - fixed
    scale = (available - fixed) / flexible if flexible > 0 and total > available else (available / total if total else 1.0)
    widths = [needs[col] if (col in short and total > available) else max(16, int(needs[col] * scale)) for col in range(columns)]
    # El último toma el resto: la suma nunca pasa del ancho visible.
    widths[-1] = max(16, available - sum(widths[:-1]))
    for col, width in enumerate(widths):
        table.setColumnWidth(col, width)
    delegate = table.itemDelegate()
    if isinstance(delegate, DecimalAlignDelegate):
        delegate.raw_columns = raw_columns | {col for col in range(columns) if widths[col] < aligned[col] and col not in raw_columns and scale < 1}
        table.viewport().update()


class _ColumnFitter(QObject):
    """Vuelve a repartir las columnas cuando la tabla cambia de ancho."""

    def __init__(self, table: "QTableWidget") -> None:
        super().__init__(table)
        self._table = table
        self._pending = False
        table.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self._table and event.type() == QEvent.Type.Resize and not self._pending:
            self._pending = True
            QTimer.singleShot(0, self, self._fit)
        return False

    def _fit(self) -> None:
        self._pending = False
        fit_columns(self._table)


def style_data_table(table: "QTableWidget", *, text_columns: Iterable[int] = ()) -> None:
    """Tabla de datos sin cuadrícula ni filas alternas; encabezados alineados como su columna."""
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setWordWrap(False)
    table.horizontalHeader().setHighlightSections(False)
    table.verticalHeader().setVisible(False)
    delegate = DecimalAlignDelegate(table)
    table.setItemDelegate(delegate)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    _ColumnFitter(table)
    align_headers(table, text_columns=text_columns)


def align_headers(table: "QTableWidget", *, text_columns: Iterable[int] = ()) -> None:
    """Encabezados de columnas numéricas a la derecha; los de texto, a la izquierda."""
    texts = set(text_columns)
    for col in range(table.columnCount()):
        item = table.horizontalHeaderItem(col)
        if item is None:
            continue
        flag = Qt.AlignLeft if col in texts else Qt.AlignRight
        item.setTextAlignment(flag | Qt.AlignVCenter)


def fill_numeric_rows(table: "QTableWidget", rows: Sequence[Sequence[str]], *, text_columns: Iterable[int] = ()) -> None:
    """Llena la tabla alineando cada columna numérica por su punto decimal."""
    texts = set(text_columns)
    table.setRowCount(len(rows))
    columns = max((len(r) for r in rows), default=0)
    for col in range(columns):
        column = [row[col] if col < len(row) else "" for row in rows]
        shown = column if col in texts else align_decimals(column)
        for row_index, (raw, display) in enumerate(zip(column, shown)):
            if col in texts:
                table.setItem(row_index, col, text_item(raw))
            else:
                table.setItem(row_index, col, numeric_item(display, tooltip=raw.strip()))
    fit_columns(table)


#: Tablas angostas de muchas columnas (bisección): fuente monoespaciada y
#: relleno mínimo, para que los valores alineados quepan sin recortarse.
MONO_TABLE_STYLE = (
    f"QTableView {{ font-family: {FONT_FAMILY_MONO}; font-size: 12px; }}"
    "QTableView::item { padding: 3px 1px; }"
    "QHeaderView::section { padding: 6px 1px; }"
)
