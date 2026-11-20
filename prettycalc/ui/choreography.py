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


def can_fly_grid_into_book(grid, book: BookMatrixWidget) -> bool:
    """La cuadrícula y el visor muestran la misma matriz y ambos se ven enteros."""
    if not motion.motion_enabled() or not grid_matches_book(grid, book):
        return False
    matrix = book.matrix()
    return _cells_on_screen(grid, book, matrix.rows, matrix.cols)


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


# ---------------------------------------------------------------------------
# Correspondencias puras (se prueban sin pintar nada)
# ---------------------------------------------------------------------------


def transpose_pairs(rows: int, cols: int) -> List[Tuple[Cell, Cell]]:
    """Cada entrada (i, j) de A termina en (j, i) de Aᵀ."""
    return [((i, j), (j, i)) for i in range(rows) for j in range(cols)]


def right_block_pairs(rows: int, split: int, cols: int) -> List[Tuple[Cell, Cell]]:
    """La entrada (i, split + j) de [I | B] termina en (i, j) de B."""
    return [((i, split + j), (i, j)) for i in range(rows) for j in range(cols - split)]


def pairs_hold(source: Optional[Matrix], target: Optional[Matrix], pairs: Sequence[Tuple[Cell, Cell]]) -> bool:
    """Cada valor de origen es, literalmente, el valor que queda en su destino."""
    if source is None or target is None or not pairs:
        return False
    try:
        return all(source.get(*src) == target.get(*dst) for src, dst in pairs)
    except (IndexError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Vuelos hacia un visor de matriz
# ---------------------------------------------------------------------------


def fly_cells_into_book(
    pairs: Sequence[Tuple["QRectF", Cell, Cell]],
    dst_book: BookMatrixWidget,
    watch: Sequence["QWidget"],
    *,
    group_of: Callable[[Cell], int],
    arc_of: Callable[[Cell, Cell], float] = lambda _s, _d: 0.0,
    pulse_cells: Sequence[Cell] = (),
    pulse_color: Optional[str] = None,
) -> int:
    """Cada ``(rect_origen, celda_origen, celda_destino)`` viaja a su celda del visor.

    El visor deja vacía cada celda hasta que su valor aterriza. Devuelve
    cuándo termina todo (ms) o 0 si no se lanzó nada.
    """
    if not motion.motion_enabled() or not pairs:
        return 0
    layer = motion.layer_for(dst_book)
    if layer is None:
        return 0
    groups = sorted({group_of(src) for _rect, src, _dst in pairs})
    flight, step = flight_timing(len(groups))
    order = {group: index for index, group in enumerate(groups)}
    delays: Dict[Cell, float] = {}
    for src_rect, src, dst in pairs:
        target = dst_book.cell_rect(*dst)
        pixmap = book_cell_pixmap(dst_book, *dst)
        if target is None or pixmap is None:
            return 0
        delay = order[group_of(src)] * step
        delays[dst] = delay
        layer.add_flight(
            motion.Flight(
                pixmap,
                src_rect,
                motion.window_rect(dst_book, target),
                delay,
                flight,
                arc=arc_of(src, dst),
                fade_in=0.08,
                curve=motion.CURVE_TRAVEL,
            )
        )
    for cell in pulse_cells:
        target = dst_book.cell_rect(*cell)
        if target is None or cell not in delays:
            continue
        layer.add_mark(
            motion.Mark(
                motion.window_rect(dst_book, target).adjusted(3, 5, -3, -5),
                pulse_color or dst_book.cell_color(*cell),
                delays[cell] + flight * 0.9,
                float(motion.ms(motion.SLOW + 80)),
                fill=0.18,
                ring=0.9,
                radius=6,
            )
        )
    dst_book.animate_arrival(delays, flight)
    layer.watch([*watch, dst_book])
    layer.on_done(lambda: _release(dst_book))
    layer.play()
    return int(max(delays.values()) + flight)


def fly_transpose(grid, result_book: BookMatrixWidget, pulse_color: str) -> int:
    """Cada entrada viaja de (i, j) en A a (j, i) en Aᵀ; la diagonal no cruza y pulsa.

    Las entradas fuera de la diagonal describen un arco hacia el otro lado
    de la diagonal; las de la diagonal van en línea recta y pulsan al llegar,
    para mostrar que la diagonal es invariante.
    """
    if not motion.motion_enabled() or grid is None or not motion.is_alive(grid):
        return 0
    try:
        source = grid.get_matrix()
    except Exception:
        return 0
    target = result_book.matrix()
    if target is None:
        return 0
    rows, cols = source.shape
    pairs = transpose_pairs(rows, cols)
    if target.shape != (cols, rows) or not pairs_hold(source, target, pairs):
        return 0
    if not _cells_on_screen(grid, result_book, 1, 1):
        return 0
    last_src = grid.cells[rows - 1][cols - 1]
    last_dst = result_book.cell_rect(cols - 1, rows - 1)
    if not motion.on_screen(last_src) or last_dst is None or not motion.on_screen(result_book, last_dst):
        return 0
    flights = [(motion.window_rect(grid.cells[i][j]), (i, j), (j, i)) for (i, j), _dst in pairs]
    diagonal = [(i, i) for i in range(min(rows, cols))]
    return fly_cells_into_book(
        flights,
        result_book,
        [grid],
        group_of=lambda src: src[0],
        arc_of=lambda src, _dst: 0.0 if src[0] == src[1] else (18.0 if src[0] < src[1] else -18.0),
        pulse_cells=diagonal,
        pulse_color=pulse_color,
    )


def fly_right_block(src_book: BookMatrixWidget, split: int, dst_book: BookMatrixWidget) -> int:
    """El bloque derecho de ``[I | B]`` viaja a su propia tarjeta: es literalmente B."""
    if not motion.motion_enabled():
        return 0
    source, target = src_book.matrix(), dst_book.matrix()
    if source is None or target is None or not 0 < split < source.cols:
        return 0
    pairs = right_block_pairs(source.rows, split, source.cols)
    if target.shape != (source.rows, source.cols - split) or not pairs_hold(source, target, pairs):
        return 0
    rects = []
    for src, dst in pairs:
        src_rect = src_book.cell_rect(*src)
        dst_rect = dst_book.cell_rect(*dst)
        if src_rect is None or dst_rect is None:
            return 0
        if not motion.on_screen(src_book, src_rect) or not motion.on_screen(dst_book, dst_rect):
            return 0
        rects.append((motion.window_rect(src_book, src_rect), src, dst))
    return fly_cells_into_book(rects, dst_book, [src_book], group_of=lambda src: src[1])


def hold_then_fly(owner: "QWidget", book: BookMatrixWidget, launch: Callable[[], int]) -> None:
    """Vacía el visor ya (antes de pintar) y lanza el vuelo cuando el layout se asentó.

    Si al final no se puede volar (fuera de pantalla, datos distintos), el
    visor muestra su estado final de inmediato.
    """
    if not motion.motion_enabled() or book.matrix() is None:
        return
    matrix = book.matrix()
    book.animate_arrival({(r, c): 0.0 for r in range(matrix.rows) for c in range(matrix.cols)}, float(motion.ms(motion.SIGNATURE)))

    def go() -> None:
        if not launch():
            book.finish_transition()

    motion.defer(owner, go)


# ---------------------------------------------------------------------------
# Inspector de producto
# ---------------------------------------------------------------------------


def product_term_cells(row: int, col: int, inner: int) -> List[Tuple[Cell, Cell]]:
    """Pares que forman cᵢⱼ = Σₖ aᵢₖ · bₖⱼ, en orden de k."""
    return [((row, k), (k, col)) for k in range(inner)]


def play_product_terms(grid_a, grid_b, row: int, col: int, result_book: BookMatrixWidget, color: str) -> int:
    """Los pares (aᵢₖ, bₖⱼ) se encienden de a uno, en orden de k; al final cᵢⱼ pulsa.

    Los resaltados se pintan en la capa de coreografía, sin tocar el estilo
    de las celdas de entrada.
    """
    if not motion.motion_enabled():
        return 0
    layer = motion.layer_for(result_book)
    if layer is None:
        return 0
    try:
        inner = len(grid_a.cells[row])
        pairs = product_term_cells(row, col, inner)
        cells = [(grid_a.cells[a[0]][a[1]], grid_b.cells[b[0]][b[1]]) for a, b in pairs]
    except (IndexError, AttributeError):
        return 0
    step = float(motion.ms(motion.stagger_step(len(cells), 90, 540)))
    span = float(motion.ms(motion.SLOW + 80))
    for index, (left, right) in enumerate(cells):
        for widget in (left, right):
            if motion.on_screen(widget):
                layer.add_mark(
                    motion.Mark(motion.window_rect(widget).adjusted(-3, -3, 3, 3), color, index * step, span, fill=0.20, ring=0.9, radius=7)
                )
    end = (len(cells) - 1) * step + span * 0.6
    target = result_book.cell_rect(row, col)
    if target is not None and motion.on_screen(result_book, target):
        layer.add_mark(
            motion.Mark(
                motion.window_rect(result_book, target).adjusted(2, 4, -2, -4),
                color,
                end,
                float(motion.ms(motion.SLOW + 120)),
                fill=0.24,
                ring=1.0,
                radius=6,
            )
        )
    layer.watch([grid_a, grid_b, result_book])
    layer.play()
    return int(end + motion.ms(motion.SLOW + 120))


def pulse_grid_rows(grid, rows: Sequence[int], color: str, *, delay: float = 0.0) -> bool:
    """Una fila de la cuadrícula de entrada pulsa una vez (p. ej. las que P permutó)."""
    if not motion.motion_enabled() or grid is None or not rows:
        return False
    layer = motion.layer_for(grid)
    if layer is None:
        return False
    added = False
    for row in rows:
        try:
            first, last = grid.cells[row][0], grid.cells[row][-1]
        except IndexError:
            continue
        if not (motion.on_screen(first) and motion.on_screen(last)):
            continue
        left, right = motion.window_rect(first), motion.window_rect(last)
        band = QRectF(left.left() - 4, left.top() - 3, right.right() - left.left() + 8, left.height() + 6)
        layer.add_mark(motion.Mark(band, color, delay, float(motion.ms(motion.EMPHASIS)), fill=0.22, ring=0.8, radius=8))
        added = True
    if not added:
        return False
    layer.watch([grid])
    return layer.play()


def pulse_grid_columns(grid, cols: Sequence[int], color: str, *, delay: float = 0.0, step: float = 0.0) -> bool:
    """Columnas de la cuadrícula de entrada que pulsan (pivote en verde, libres en ocre)."""
    if not motion.motion_enabled() or grid is None or not cols:
        return False
    layer = motion.layer_for(grid)
    if layer is None:
        return False
    added = False
    for index, col in enumerate(cols):
        try:
            top, bottom = grid.cells[0][col], grid.cells[-1][col]
        except IndexError:
            continue
        if not (motion.on_screen(top) and motion.on_screen(bottom)):
            continue
        a, b = motion.window_rect(top), motion.window_rect(bottom)
        band = QRectF(a.left() - 3, a.top() - 4, a.width() + 6, b.bottom() - a.top() + 8)
        layer.add_mark(
            motion.Mark(band, color, delay + index * step, float(motion.ms(motion.EMPHASIS)), fill=0.18, ring=0.9, radius=8)
        )
        added = True
    if not added:
        return False
    layer.watch([grid])
    return layer.play()


def pulse_labels(labels: Sequence[Optional["QWidget"]], color: str, *, delay: float = 0.0, step: float = 0.0) -> bool:
    """Las etiquetas pulsan una vez, en orden (p. ej. los vectores de una base)."""
    played = False
    for index, label in enumerate(labels):
        if label is not None and motion.pulse(
            label, color, fill=0.14, ring=0.7, duration=motion.EMPHASIS, delay=int(delay + index * step), margin=2
        ):
            played = True
    return played


def chip_pixmap(text: str, color: str, ratio: float = 1.0) -> "QPixmap":
    """Etiqueta en forma de píldora (``c₂ = −3``) pintada una vez."""
    from prettycalc.ui.theme import COLOR_SURFACE_ELEVATED, COLOR_TEXT_PRIMARY

    font = ui_font(15, mono=True, weight=600)
    from PySide6.QtGui import QFontMetrics, QPen

    fm = QFontMetrics(font)
    w, h = fm.horizontalAdvance(text) + 20, fm.height() + 10

    def paint(painter: "QPainter", area: "QRect") -> None:
        painter.setPen(QPen(QColor(color), 1.4))
        painter.setBrush(QColor(COLOR_SURFACE_ELEVATED))
        painter.drawRoundedRect(QRectF(area).adjusted(1, 1, -1, -1), h / 2 - 1, h / 2 - 1)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        painter.drawText(area, Qt.AlignCenter, text)

    return motion.text_pixmap(text, "", font, (w, h), paint, ratio)


def show_dependence(cards: Sequence["QWidget"], weights: Sequence, names: Sequence[str], color: str) -> int:
    """Conjunto dependiente: cada coeficiente aparece junto a su vector, uno por uno.

    El vector que se escribe con los demás (el último de peso no nulo) se
    enciende al final. Los coeficientes quedan escritos en la combinación
    no trivial del panel; aquí solo se muestran junto a cada tarjeta.
    """
    if not motion.motion_enabled() or not cards or len(cards) != len(weights):
        return 0
    layer = motion.layer_for(cards[0])
    if layer is None:
        return 0
    from prettycalc.core.types import format_scalar as _fmt

    shown = [(i, w) for i, w in enumerate(weights) if w != 0 and motion.on_screen(cards[i])]
    if not shown:
        return 0
    step = float(motion.ms(motion.stagger_step(len(shown), 110, 440)))
    hold = float(motion.ms(1400))
    ratio = motion.device_ratio(cards[0])
    for order, (index, weight) in enumerate(shown):
        card = motion.window_rect(cards[index])
        pixmap = chip_pixmap(f"{names[index]} = {_fmt(weight).replace('-', '−')}", color, ratio)
        w = pixmap.width() / (pixmap.devicePixelRatio() or 1.0)
        h = pixmap.height() / (pixmap.devicePixelRatio() or 1.0)
        spot = QRectF(card.center().x() - w / 2, card.top() - h * 0.35, w, h)
        layer.add_flight(
            motion.Flight(pixmap, spot.translated(0, 8), spot, order * step, hold, fade_in=0.12, fade_out=0.25, curve=motion.CURVE_ENTER)
        )
    last = shown[-1][0]
    layer.add_mark(
        motion.Mark(
            motion.window_rect(cards[last]).adjusted(-3, -3, 3, 3),
            color,
            (len(shown) - 1) * step + float(motion.ms(motion.FAST)),
            float(motion.ms(motion.EMPHASIS)),
            fill=0.12,
            ring=0.9,
            radius=10,
        )
    )
    layer.watch(cards)
    layer.play()
    return int((len(shown) - 1) * step + hold)
