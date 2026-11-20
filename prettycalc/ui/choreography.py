"""Coreografías entre widgets: valores que viajan de un lugar a otro de la ventana.

Cada trayectoria es verdad matemática: un valor solo viaja de A a B si el
valor de A es, literalmente, el que termina en B. Por eso cada función
comprueba la correspondencia con aritmética exacta antes de lanzar nada y,
si el origen o el destino no se ven enteros en pantalla, no vuela: deja el
estado final como está.

Todo se pinta en la capa de coreografía de la ventana
(:class:`prettycalc.ui.motion.ChoreographyLayer`).
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

try:
    from PySide6.QtCore import QRect, QRectF, Qt
    from PySide6.QtGui import QColor, QPainter, QPixmap, QTextDocument
    from PySide6.QtWidgets import QLabel, QWidget
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui import motion
from prettycalc.ui.book_matrix import BookMatrixWidget, paint_book_scalar
from prettycalc.ui.theme import ui_font

Cell = Tuple[int, int]

#: Fracción de la firma que dura cada vuelo; el resto es el escalonado.
_FLIGHT_SHARE = 0.62


def book_cell_pixmap(book: BookMatrixWidget, row: int, col: int, ink: Optional[str] = None) -> Optional["QPixmap"]:
    """La entrada (fila, columna) del visor pintada una vez en un pixmap."""
    rect = book.cell_rect(row, col)
    if rect is None:
        return None
    text = book.cell_text(row, col)
    color = QColor(ink or book.cell_color(row, col))
    font = ui_font(17, mono=True)

    def paint(painter: "QPainter", area: "QRect") -> None:
        paint_book_scalar(painter, area, text, color, font)

    return motion.text_pixmap(text, "", font, (rect.width(), rect.height()), paint, motion.device_ratio(book))


def flight_timing(count: int) -> Tuple[float, float]:
    """(duración de cada vuelo, retraso entre grupos) para que todo quepa en la firma."""
    total = float(motion.ms(motion.SIGNATURE))
    flight = total * _FLIGHT_SHARE
    if count <= 1:
        return flight, 0.0
    step = min(float(motion.ms(motion.STAGGER)), (total - flight) / (count - 1))
    return flight, step


def grid_matches_book(grid, book: BookMatrixWidget) -> bool:
    """La cuadrícula contiene exactamente la matriz que muestra el visor."""
    shown = book.matrix()
    if shown is None or grid is None or not motion.is_alive(grid):
        return False
    try:
        if not grid.is_all_valid():
            return False
        return grid.get_matrix() == shown
    except Exception:
        return False


def _cells_on_screen(grid, book: BookMatrixWidget, rows: int, cols: int) -> bool:
    try:
        corners = [grid.cells[0][0], grid.cells[rows - 1][cols - 1]]
    except (IndexError, AttributeError):
        return False
    if not all(motion.on_screen(cell) for cell in corners):
        return False
    first, last = book.cell_rect(0, 0), book.cell_rect(rows - 1, cols - 1)
    if first is None or last is None:
        return False
    return motion.on_screen(book, first) and motion.on_screen(book, last)


def arrival_delays(rows: int, cols: int) -> Tuple[Dict[Cell, float], float]:
    flight, step = flight_timing(cols)
    return {(r, c): c * step for r in range(rows) for c in range(cols)}, flight


def hold_book_for_grid(grid, book: BookMatrixWidget) -> bool:
    """Deja vacío el lugar de cada entrada mientras su copia viaja (antes de pintar)."""
    if not motion.motion_enabled() or not grid_matches_book(grid, book):
        return False
    matrix = book.matrix()
    delays, flight = arrival_delays(matrix.rows, matrix.cols)
    return book.animate_arrival(delays, flight) > 0


def fly_grid_into_book(grid, book: BookMatrixWidget) -> int:
    """Las entradas de la cuadrícula viajan a su lugar en el paso inicial del procedimiento.

    Solo si la cuadrícula contiene exactamente la matriz que muestra el visor
    y ambos se ven enteros. Las columnas salen escalonadas; la columna ``b``
    conserva su color. Devuelve cuándo aterriza la última (ms) o 0.
    """
    if not motion.motion_enabled() or not grid_matches_book(grid, book):
        book.finish_transition()
        return 0
    matrix: Matrix = book.matrix()
    rows, cols = matrix.rows, matrix.cols
    if not _cells_on_screen(grid, book, rows, cols):
        book.finish_transition()
        return 0
    layer = motion.layer_for(book)
    if layer is None:
        book.finish_transition()
        return 0
    delays, flight = arrival_delays(rows, cols)
    for (r, c), delay in delays.items():
        pixmap = book_cell_pixmap(book, r, c)
        target = book.cell_rect(r, c)
        if pixmap is None or target is None:
            continue
        layer.add_flight(
            motion.Flight(
                pixmap,
                motion.window_rect(grid.cells[r][c]),
                motion.window_rect(book, target),
                delay,
                flight,
                fade_in=0.08,
                curve=motion.CURVE_TRAVEL,
            )
        )
    book.animate_arrival(delays, flight)
    layer.watch([grid, book])
    layer.on_done(lambda: _release(book))
    layer.play()
    return int(max(delays.values()) + flight)


def _release(book: BookMatrixWidget) -> None:
    """Si la capa se canceló, el visor muestra de inmediato lo que esperaba."""
    if motion.is_alive(book) and book.transition_kind() == "arrival":
        transition = book._transition
        if transition is not None and transition.now < transition.arrival_end:
            book.finish_transition()


def label_text_end(label: "QLabel") -> QRectF:
    """Zona (en la ventana) donde termina el texto de una etiqueta enriquecida."""
    doc = QTextDocument()
    doc.setDefaultFont(label.font())
    doc.setDocumentMargin(0)
    doc.setHtml(label.text())
    contents = label.contentsRect()
    width = min(float(contents.width()), doc.idealWidth())
    rect = QRect(contents.left(), contents.top(), int(width), contents.height())
    return motion.window_rect(label, rect)


def fly_book_cells_to_labels(
    book: BookMatrixWidget,
    cells: Sequence[Cell],
    labels: Sequence["QLabel"],
    pulse_color: str,
    *,
    start: float = 0.0,
) -> int:
    """Cada entrada viaja hasta el final del texto de su etiqueta, que pulsa al recibirla."""
    if not motion.motion_enabled() or not cells or len(cells) != len(labels):
        return 0
    if not all(motion.on_screen(label) for label in labels):
        return 0
    if not all(book.cell_rect(*cell) is not None and motion.on_screen(book, book.cell_rect(*cell)) for cell in cells):
        return 0
    layer = motion.layer_for(book)
    if layer is None:
        return 0
    flight, step = flight_timing(len(cells))
    for index, (cell, label) in enumerate(zip(cells, labels)):
        pixmap = book_cell_pixmap(book, *cell)
        if pixmap is None:
            continue
        end = label_text_end(label)
        ratio = pixmap.devicePixelRatio() or 1.0
        w, h = pixmap.width() / ratio, pixmap.height() / ratio
        dst = QRectF(end.right() - w / 2, end.center().y() - h / 2, w, h)
        delay = start + index * step
        layer.add_flight(
            motion.Flight(
                pixmap,
                motion.window_rect(book, book.cell_rect(*cell)),
                dst,
                delay,
                flight,
                fade_in=0.1,
                fade_out=0.18,
                curve=motion.CURVE_TRAVEL,
            )
        )
        layer.add_mark(
            motion.Mark(
                motion.window_rect(label).adjusted(-4, -2, 4, 2),
                pulse_color,
                delay + flight * 0.86,
                float(motion.ms(motion.EMPHASIS * 0.7)),
                fill=0.16,
                ring=0.7,
                radius=6,
            )
        )
    layer.watch([book, *labels])
    layer.play()
    return int(start + (len(cells) - 1) * step + flight)
