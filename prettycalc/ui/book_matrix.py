"""Visor de matriz con notación de libro: corchetes, barra [A | b] y fracciones apiladas.

Sprint 11 (movimiento): el visor anima la transición entre dos pasos con
lo que la matemática dice que ocurrió, todo pintado en ``paintEvent``:

- en ``Fᵢ → Fᵢ + k·Fⱼ`` una copia de la fila ``j`` viaja con su etiqueta
  ``× k`` hasta la fila ``i`` y, al fundirse, las entradas que cambiaron pasan
  del valor viejo al nuevo;
- en ``Fᵢ ↔ Fⱼ`` las dos filas se cruzan en arco;
- en ``Fᵢ → k·Fᵢ`` la etiqueta ``× k`` aterriza sobre la fila y el pivote
  pulsa al quedar en 1;
- el rectángulo del pivote se desliza de su lugar anterior al nuevo;
- en ``Aᵢ(b)`` la columna ``i`` baja y los valores de ``b`` entran desde la derecha.

La operación se confirma con :mod:`prettycalc.core.step_diff`; si no se
puede confirmar, solo se funden las entradas que cambiaron. El estado final
(franja de la fila afectada, pivote, alertas) se pinta igual con o sin
animación.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from PySide6.QtWidgets import QWidget, QSizePolicy, QMenu
    from PySide6.QtCore import Qt, Signal, QRect, QRectF, QSize, Property, QPropertyAnimation, QEasingCurve
    from PySide6.QtGui import (
        QPainter,
        QPen,
        QColor,
        QFont,
        QFontMetrics,
        QPaintEvent,
        QMouseEvent,
        QKeyEvent,
        QContextMenuEvent,
        QKeySequence,
        QAction,
    )
except ImportError:
    QWidget = object  # type: ignore
    Property = lambda *args, **kwargs: None  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core import step_diff
from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui import motion
from prettycalc.ui.clipboard import copy_matrix_to_clipboard
from prettycalc.ui.mathtext import variable_symbol
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_BG_BASE,
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_SURFACE_ELEVATED,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    ACTIVE_THEME,
    ui_font,
)

Cell = Tuple[int, int]

#: Intensidad de los tintes animados por tema: en claro un alfa bajo se pierde.
_WASH = 0.24 if ACTIVE_THEME == "light" else 0.16

#: Tipos de transición entre pasos.
TRANSITION_FORWARD = "forward"
TRANSITION_SHORT = "short"
TRANSITION_BACK = "back"
TRANSITION_JUMP = "jump"


def draw_square_brackets(painter: QPainter, rect: QRect, color: QColor, thickness: int = 2) -> None:
    """Dibuja corchetes cuadrados de libro en los extremos de rect."""
    painter.save()
    pen = QPen(color, thickness)
    pen.setCapStyle(Qt.SquareCap)
    pen.setJoinStyle(Qt.MiterJoin)
    painter.setPen(pen)

    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    serif = max(8, min(14, w // 16))

    painter.drawLine(x + serif, y, x, y)
    painter.drawLine(x, y, x, y + h)
    painter.drawLine(x, y + h, x + serif, y + h)

    painter.drawLine(x + w - serif, y, x + w, y)
    painter.drawLine(x + w, y, x + w, y + h)
    painter.drawLine(x + w, y + h, x + w - serif, y + h)
    painter.restore()


def draw_split_bar(painter: QPainter, x: int, top: int, bottom: int, color: QColor) -> None:
    """Línea vertical continua de la partición aumentada [A | b]."""
    painter.save()
    pen = QPen(color, 2)
    pen.setCapStyle(Qt.FlatCap)
    painter.setPen(pen)
    painter.drawLine(x, top, x, bottom)
    painter.restore()


def paint_book_scalar(
    painter: QPainter,
    rect: QRect,
    text: str,
    color: QColor,
    font: QFont,
) -> None:
    """Pinta un escalar: entero centrado o fracción apilada (numerador / barra / denominador)."""
    painter.save()
    painter.setFont(font)
    painter.setPen(color)
    text = (text or "").strip()

    if not text or "/" not in text:
        display = text.replace("-", "−") if text else ""
        painter.drawText(rect, Qt.AlignCenter, display)
        painter.restore()
        return

    negative = text.startswith("-")
    body = text[1:] if negative else text
    if "/" not in body:
        painter.drawText(rect, Qt.AlignCenter, text.replace("-", "−"))
        painter.restore()
        return

    num, den = body.split("/", 1)
    fm = QFontMetrics(font)
    num_w = fm.horizontalAdvance(num)
    den_w = fm.horizontalAdvance(den)
    bar_w = max(num_w, den_w) + 8
    line_h = fm.height()
    minus_w = fm.horizontalAdvance("−") if negative else 0
    gap = 5 if negative else 0
    total_w = minus_w + gap + bar_w

    cx = rect.center().x()
    cy = rect.center().y()
    left = cx - total_w // 2

    if negative:
        minus_rect = QRect(left, cy - line_h // 2, minus_w, line_h)
        painter.drawText(minus_rect, Qt.AlignCenter, "−")
        left += minus_w + gap

    painter.drawText(
        QRect(left, cy - line_h - 1, bar_w, line_h),
        Qt.AlignHCenter | Qt.AlignBottom,
        num,
    )
    bar_pen = QPen(color, 1)
    painter.setPen(bar_pen)
    painter.drawLine(left + 1, cy, left + bar_w - 1, cy)
    painter.setPen(color)
    painter.drawText(
        QRect(left, cy + 2, bar_w, line_h),
        Qt.AlignHCenter | Qt.AlignTop,
        den,
    )
    painter.restore()


def factor_label(factor, mode: str = "fraction") -> str:
    """Etiqueta ``× k`` de una operación de fila (con el signo menos tipográfico)."""
    return f"× {format_scalar(factor, mode=mode).replace('-', '−')}"


@dataclass
class _Geometry:
    """Todo lo que ``paintEvent`` necesita y no cambia entre fotogramas."""

    key: tuple
    texts: List[List[str]]
    col_widths: List[int]
    row_h: int
    header_h: int
    origin_x: int
    origin_y: int
    bracket_rect: QRect
    bar_x: Optional[int]
    cells: List[List[QRect]]
    bands: List[QRect]


@dataclass
class _Transition:
    """Coreografía en curso entre el paso anterior y el visible."""

    kind: str
    total: float
    now: float = 0.0
    old_text: Dict[Cell, str] = field(default_factory=dict)
    fade: Tuple[float, float] = (0.0, 0.0)
    op: Optional[step_diff.RowOperation] = None
    label: str = ""
    pivot_from: Optional[Cell] = None
    glide: Tuple[float, float] = (0.0, 0.0)
    alert_rows: Tuple[int, ...] = ()
    alert_color: str = COLOR_ACCENT_WARNING
    alert_window: Tuple[float, float] = (0.0, 0.0)
    lead_cells: Tuple[Cell, ...] = ()
    lead_step: float = 0.0
    lead_start: float = 0.0
    lead_color: str = COLOR_FEEDBACK_SUCCESS
    replaced_col: Optional[int] = None
    replaced_old: Dict[int, str] = field(default_factory=dict)
    arrival: Dict[Cell, float] = field(default_factory=dict)
    arrival_end: float = 0.0


class BookMatrixWidget(QWidget):
    """Matriz aumentada pintada como en un libro de álgebra lineal."""

    cellClicked = Signal(int, int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._matrix: Optional[Matrix] = None
        self._split_col: Optional[int] = None
        self._pivot: Optional[Tuple[int, int]] = None
        self._actor_row: Optional[int] = None
        self._affected_rows: Tuple[int, ...] = ()
        self._mode: str = "fraction"
        self._show_headers: bool = True
        self._flash_alpha: float = 0.0
        self._highlight_row: Optional[int] = None
        self._highlight_col: Optional[int] = None
        self._alert_rows: Tuple[int, ...] = ()
        self._highlight_cells: Tuple[Tuple[int, int], ...] = ()
        self._header_roles: Dict[int, str] = {}
        self._contradiction_rows: Tuple[int, ...] = ()
        self._empty_text = "Sin matriz para mostrar"
        self._cell_rects: List[List[QRect]] = []
        self._clickable: bool = False
        self._geometry: Optional[_Geometry] = None
        self._transition: Optional[_Transition] = None
        self._tween = None
        self._flash = QPropertyAnimation(self, b"flashAlpha", self)
        self._flash.setDuration(motion.EMPHASIS)
        self._flash.setStartValue(0.0)
        self._flash.setKeyValueAt(0.28, 0.15)
        self._flash.setEndValue(0.0)
        self._flash.setEasingCurve(QEasingCurve.InOutCubic)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.ClickFocus)

    def _get_flash_alpha(self) -> float:
        return self._flash_alpha

    def _set_flash_alpha(self, value: float) -> None:
        self._flash_alpha = float(value)
        self.update()

    flashAlpha = Property(float, _get_flash_alpha, _set_flash_alpha)

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def set_matrix(
        self,
        matrix: Optional[Matrix],
        split_col: Optional[int] = None,
        pivot: Optional[Tuple[int, int]] = None,
        mode: str = "fraction",
        actor_row: Optional[int] = None,
        affected_rows: Tuple[int, ...] = (),
        animate: bool = False,
        highlight_row: Optional[int] = None,
        highlight_col: Optional[int] = None,
        clickable: Optional[bool] = None,
        show_headers: Optional[bool] = None,
        alert_rows: Tuple[int, ...] = (),
        highlight_cells: Tuple[Tuple[int, int], ...] = (),
        header_roles: Optional[Dict[int, str]] = None,
        contradiction_rows: Tuple[int, ...] = (),
    ) -> None:
        """Fija el estado visible al instante. Una transición en curso salta a su final."""
        self._end_transition()
        self._matrix = matrix
        self._alert_rows = tuple(alert_rows or ())
        self._highlight_cells = tuple(tuple(cell) for cell in (highlight_cells or ()))
        self._split_col = split_col
        self._pivot = pivot
        self._mode = mode
        self._actor_row = actor_row
        self._affected_rows = affected_rows
        self._highlight_row = highlight_row
        self._highlight_col = highlight_col
        self._header_roles = dict(header_roles or {})
        self._contradiction_rows = tuple(contradiction_rows or ())
        if clickable is not None:
            self._clickable = clickable
        if show_headers is not None:
            self._show_headers = show_headers
        self._geometry = None
        self.setCursor(Qt.PointingHandCursor if self._clickable and matrix is not None else Qt.ArrowCursor)
        self._fit_minimum_height()
        self.update()
        self.updateGeometry()
        if animate and affected_rows and motion.motion_enabled():
            self._flash.stop()
            self._flash.start()
            motion.track(self._flash)
        elif not animate:
            self._flash.stop()
            self._flash_alpha = 0.0

    def _fit_minimum_height(self) -> None:
        """Garantiza que quepan todas las filas (misma geometría que paintEvent)."""
        if self._matrix is None:
            self.setMinimumHeight(180)
            return
        fm = QFontMetrics(ui_font(17, mono=True))
        header_h = QFontMetrics(ui_font(15, italic=True)).height() + 8 if self._show_headers else 0
        row_h = max(44, int(fm.height() * 2.4))
        needed = header_h + self._matrix.rows * row_h + 2 * 10 + 16
        self.setMinimumHeight(max(180, needed))

    def matrix(self) -> Optional[Matrix]:
        return self._matrix

    def alert_rows(self) -> Tuple[int, ...]:
        return self._alert_rows

    def highlight_cells(self) -> Tuple[Tuple[int, int], ...]:
        return self._highlight_cells

    def header_roles(self) -> Dict[int, str]:
        return dict(self._header_roles)

    def contradiction_rows(self) -> Tuple[int, ...]:
        return self._contradiction_rows

    def set_empty_text(self, text: str) -> None:
        """Texto del estado vacío (por ejemplo «Pulsa Calcular para ver C = AB (A · B)»)."""
        self._empty_text = text
        self.update()

    def empty_text(self) -> str:
        """Retorna el texto actual del estado vacío."""
        return self._empty_text

    def clear(self) -> None:
        self.set_matrix(None)

    def sizeHint(self) -> QSize:
        return QSize(360, 240)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # La geometría se recalcula en el próximo pintado. Si el visor cambia de
        # alto porque la explicación ocupa otra línea, la coreografía sigue; un
        # redimensionamiento de la ventana la termina desde ``MainWindow``.
        self._geometry = None

    # ------------------------------------------------------------------
    # Geometría (cacheada: se calcula una vez por estado y tamaño)
    # ------------------------------------------------------------------

    def _layout(self) -> Optional[_Geometry]:
        matrix = self._matrix
        if matrix is None:
            return None
        key = (id(matrix), self._mode, self._show_headers, self._split_col, self.width(), self.height())
        cached = self._geometry
        if cached is not None and cached.key == key:
            return cached

        rows, cols = matrix.rows, matrix.cols
        split = self._split_col
        mono = ui_font(17, mono=True)
        header_font = ui_font(15, italic=True)
        fm = QFontMetrics(mono)
        header_fm = QFontMetrics(header_font)
        cell_pad_x = 14
        row_h = max(44, int(fm.height() * 2.4))
        header_h = header_fm.height() + 8 if self._show_headers else 0

        texts = [[format_scalar(matrix.get(r, c), mode=self._mode) for c in range(cols)] for r in range(rows)]
        col_widths: List[int] = []
        for c in range(cols):
            max_w = 36
            if self._show_headers:
                header = variable_symbol(c) if split is None or c < split else "b"
                max_w = max(max_w, header_fm.horizontalAdvance(header) + 8)
            for r in range(rows):
                max_w = max(max_w, _text_width(fm, texts[r][c]))
            col_widths.append(max(max_w + cell_pad_x, 48))

        gap_split = 18 if split is not None else 0
        inner_w = sum(col_widths) + gap_split
        inner_h = rows * row_h
        bracket_pad_x = 18
        bracket_pad_y = 10
        total_w = inner_w + 2 * bracket_pad_x
        total_h = header_h + inner_h + 2 * bracket_pad_y
        origin_x = max(8, (self.width() - total_w) // 2)
        origin_y = max(8, (self.height() - total_h) // 2)
        content_left = origin_x + bracket_pad_x
        content_top = origin_y + header_h + bracket_pad_y

        lefts: List[int] = []
        x = content_left
        for c in range(cols):
            lefts.append(x)
            x += col_widths[c]
            if split is not None and c + 1 == split:
                x += gap_split

        bracket_rect = QRect(origin_x, origin_y + header_h, total_w, inner_h + 2 * bracket_pad_y)
        bar_x = lefts[split] - gap_split // 2 if split is not None and 0 < split < cols else None
        cells = [[QRect(lefts[c], content_top + r * row_h, col_widths[c], row_h) for c in range(cols)] for r in range(rows)]
        bands = [QRect(bracket_rect.left() + 4, content_top + r * row_h, bracket_rect.width() - 8, row_h) for r in range(rows)]
        geometry = _Geometry(key, texts, col_widths, row_h, header_h, origin_x, origin_y, bracket_rect, bar_x, cells, bands)
        self._geometry = geometry
        self._cell_rects = cells
        return geometry

    def cell_rect(self, row: int, col: int) -> Optional[QRect]:
        """Rectángulo de la entrada (fila, columna) en coordenadas del widget."""
        geometry = self._layout()
        if geometry is None or not (0 <= row < len(geometry.cells) and 0 <= col < len(geometry.cells[0])):
            return None
        return QRect(geometry.cells[row][col])

    def cell_text(self, row: int, col: int) -> str:
        geometry = self._layout()
        if geometry is None:
            return ""
        return geometry.texts[row][col]

    def cell_color(self, row: int, col: int) -> str:
        """Color de tinta con que se pinta la entrada en reposo."""
        if self._pivot == (row, col):
            return COLOR_BG_BASE
        if self._split_col is not None and col >= self._split_col:
            return COLOR_INTERACTIVE_IDLE
        return COLOR_TEXT_PRIMARY

    # ------------------------------------------------------------------
    # Transiciones
    # ------------------------------------------------------------------

    def is_animating(self) -> bool:
        return self._transition is not None

    def transition_kind(self) -> str:
        return self._transition.kind if self._transition is not None else ""

    def transition_operation(self) -> Optional[step_diff.RowOperation]:
        return self._transition.op if self._transition is not None else None

    def _end_transition(self) -> None:
        tween = self._tween
        self._tween = None
        if tween is not None and motion.is_alive(tween):
            try:
                tween.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            tween.stop()
        motion._forget(tween)
        if self._transition is not None:
            self._transition = None
            self.update()

    def finish_transition(self) -> None:
        """Lleva la coreografía en curso a su estado final."""
        self._end_transition()

    def _start(self, transition: _Transition) -> int:
        self._end_transition()
        if transition.total <= 0:
            return 0
        self._transition = transition

        def step(t: float) -> None:
            if self._transition is transition:
                transition.now = t * transition.total
                self.update()

        def done() -> None:
            if self._transition is transition:
                self._transition = None
                self._tween = None
                self.update()

        self._tween = motion.run(self, int(transition.total), step, done)
        return int(transition.total)

    def animate_from(
        self,
        previous: Optional[Matrix],
        *,
        kind: str = TRANSITION_FORWARD,
        previous_pivot: Optional[Cell] = None,
        previous_alert_rows: Sequence[int] = (),
        alert_color: Optional[str] = None,
        base_matrix: Optional[Matrix] = None,
        lead_cells: Sequence[Cell] = (),
    ) -> int:
        """Anima el paso de ``previous`` al estado visible. Devuelve la duración en ms.

        - ``forward``: la coreografía completa de la operación del paso.
        - ``short``: navegación en ráfaga; solo un fundido breve de lo que cambió.
        - ``back``: se deshace un paso; fundido breve, sin repetir la operación.
        - ``jump``: salto de varios pasos; fundido breve si la forma coincide.

        ``base_matrix`` (la matriz inicial) permite reconocer una columna
        reemplazada; ``lead_cells`` son los pivotes que se encienden al llegar
        a la forma final.
        """
        matrix = self._matrix
        if matrix is None or not motion.motion_enabled():
            return 0
        changed = step_diff.changed_cells(previous, matrix)
        mode = self._mode
        new_alerts = tuple(r for r in self._alert_rows if r not in set(previous_alert_rows))

        if kind != TRANSITION_FORWARD:
            total = float(motion.ms(motion.FAST))
            transition = _Transition(kind, total)
            if changed:
                transition.old_text = {cell: format_scalar(previous.get(*cell), mode=mode) for cell in changed}
                transition.fade = (0.0, total)
            if kind == TRANSITION_JUMP and new_alerts:
                transition.total = float(motion.ms(motion.EMPHASIS))
                transition.alert_rows = new_alerts
                transition.alert_color = alert_color or COLOR_ACCENT_WARNING
                transition.alert_window = (0.0, transition.total)
            if kind == TRANSITION_SHORT and self._affected_rows:
                self._flash.stop()
                self._flash.start()
                motion.track(self._flash)
            if not transition.old_text and not transition.alert_rows:
                return 0
            return self._start(transition)

        total = float(motion.ms(motion.SIGNATURE))
        transition = _Transition(kind, total)
        op = step_diff.detect_step_operation(
            previous,
            matrix,
            split_col=self._split_col,
            actor_row=self._actor_row,
            affected_rows=self._affected_rows,
        )
        if op is not None and op.kind == step_diff.ADD and op.source is not None:
            transition.op = op
            transition.label = factor_label(op.factor, mode)
            transition.fade = (0.60 * total, 0.22 * total)
        elif op is not None and op.kind == step_diff.SWAP:
            transition.op = op
            transition.total = total = float(motion.ms(motion.SIGNATURE * 0.85))
            transition.fade = (0.80 * total, 0.15 * total)
        elif op is not None and op.kind == step_diff.SCALE:
            transition.op = op
            transition.label = factor_label(op.factor, mode)
            transition.fade = (0.28 * total, 0.27 * total)
        else:
            transition.fade = (0.08 * total, 0.40 * total)

        if changed:
            transition.old_text = {cell: format_scalar(previous.get(*cell), mode=mode) for cell in changed}
            if transition.op is not None and transition.op.kind == step_diff.SWAP:
                # Las filas que se cruzan llegan ya con su valor: no hay fundido encima.
                moving = set(transition.op.rows())
                lo, hi = transition.op.columns
                transition.old_text = {
                    cell: text for cell, text in transition.old_text.items()
                    if not (cell[0] in moving and lo <= cell[1] < hi)
                }

        column = step_diff.replaced_column(base_matrix, matrix, self._highlight_cells)
        if column is not None:
            transition.replaced_col = column
            source = previous if previous is not None and previous.shape == matrix.shape else base_matrix
            transition.replaced_old = {r: format_scalar(source.get(r, column), mode=mode) for r in range(matrix.rows)}
            for r in range(matrix.rows):
                transition.old_text.pop((r, column), None)

        if (
            previous_pivot is not None
            and self._pivot is not None
            and previous_pivot != self._pivot
            and previous is not None
            and previous.shape == matrix.shape
        ):
            transition.pivot_from = tuple(previous_pivot)
            transition.glide = (0.0, float(motion.ms(motion.SLOW)))

        if new_alerts:
            transition.alert_rows = new_alerts
            transition.alert_color = alert_color or COLOR_ACCENT_WARNING
            start = transition.fade[0] if transition.op is not None else 0.0
            transition.alert_window = (start, float(motion.ms(motion.EMPHASIS)))
            transition.total = max(transition.total, sum(transition.alert_window))

        if not lead_cells and transition.replaced_col is None and self._highlight_cells:
            # Las celdas que el paso señala (la diagonal de U, la columna nueva de
            # Aᵀ, la entrada cᵢⱼ) se encienden en orden de lectura.
            lead_cells = tuple(sorted(self._highlight_cells))
            transition.lead_color = COLOR_ACCENT_WARNING
        if lead_cells:
            transition.lead_cells = tuple(lead_cells)
            transition.lead_step = float(motion.ms(motion.stagger_step(len(lead_cells), 70, 420)))
            transition.lead_start = transition.fade[0] + transition.fade[1] * 0.5
            end = transition.lead_start + transition.lead_step * (len(lead_cells) - 1) + motion.ms(motion.SLOW + 60)
            transition.total = max(transition.total, end)

        if not (
            transition.old_text
            or transition.op
            or transition.replaced_col is not None
            or transition.pivot_from
            or transition.alert_rows
            or transition.lead_cells
        ):
            return 0
        return self._start(transition)

    def animate_arrival(self, delays: Dict[Cell, float], land_ms: float) -> int:
        """Las entradas aparecen al aterrizar (cada una tras su ``delay``) y los corchetes se asientan.

        Acompaña a los objetos que viajan desde la cuadrícula de entrada por la
        capa de coreografía: mientras viajan, su lugar aquí queda vacío.
        """
        if self._matrix is None or not motion.motion_enabled() or not delays:
            return 0
        arrival = {cell: float(delay) + float(land_ms) for cell, delay in delays.items()}
        end = max(arrival.values())
        settle = float(motion.ms(motion.BASE))
        transition = _Transition("arrival", end + settle)
        transition.arrival = arrival
        transition.arrival_end = end
        return self._start(transition)

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(COLOR_SURFACE_INNER))

        if self._matrix is None:
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.setFont(ui_font(16, italic=True))
            painter.drawText(
                self.rect().adjusted(12, 0, -12, 0), Qt.AlignCenter | Qt.TextWordWrap, self._empty_text
            )
            return

        g = self._layout()
        tx = self._transition
        now = tx.now if tx is not None else 0.0
        matrix = self._matrix
        rows, cols = matrix.rows, matrix.cols
        split = self._split_col
        mono = ui_font(17, mono=True)

        if self._show_headers:
            self._paint_headers(painter, g, cols, split)

        bracket_alpha = 1.0
        bracket_rect = QRect(g.bracket_rect)
        if tx is not None and tx.arrival:
            k = motion.ease(motion.CURVE_ENTER, motion.local(now, tx.arrival_end, tx.total - tx.arrival_end))
            bracket_alpha = 0.35 + 0.65 * k
            grow = int(round(6 * (1.0 - k)))
            bracket_rect = bracket_rect.adjusted(-grow, -grow, grow, grow)
        painter.setOpacity(bracket_alpha)
        draw_square_brackets(painter, bracket_rect, QColor(COLOR_TEXT_PRIMARY), thickness=2)
        if g.bar_x is not None:
            draw_split_bar(painter, g.bar_x, g.bracket_rect.top() + 6, g.bracket_rect.bottom() - 6, QColor(COLOR_INTERACTIVE_IDLE))
        painter.setOpacity(1.0)

        op = tx.op if tx is not None else None
        moving_rows: set = set()
        op_cols = range(0)
        if op is not None:
            op_cols = range(*op.columns)
            if op.kind == step_diff.SWAP and now < tx.fade[0]:
                moving_rows = set(op.rows())

        self._paint_row_bands(painter, g, rows, tx, now, op)

        pivot_r, pivot_c = self._pivot if self._pivot is not None else (-1, -1)
        glide_rect: Optional[QRectF] = None
        if tx is not None and tx.pivot_from is not None and self._pivot is not None:
            k = motion.ease(motion.CURVE_MOVE, motion.local(now, *tx.glide))
            if k < 1.0:
                src = QRectF(g.cells[tx.pivot_from[0]][tx.pivot_from[1]].adjusted(4, 6, -4, -6))
                dst = QRectF(g.cells[pivot_r][pivot_c].adjusted(4, 6, -4, -6))
                glide_rect = motion.lerp_rect(src, dst, k)

        for r in range(rows):
            for c in range(cols):
                cell = g.cells[r][c]
                if self._highlight_col is not None and c == self._highlight_col:
                    painter.fillRect(cell, motion.with_alpha(COLOR_INTERACTIVE_IDLE, 0.16))
                if (r, c) in self._highlight_cells and not (r == pivot_r and c == pivot_c):
                    ring_alpha = 1.0
                    if tx is not None and tx.replaced_col is not None and c == tx.replaced_col:
                        start = tx.total * (0.45 + 0.06 * r)
                        ring_alpha = motion.ease(motion.CURVE_ENTER, motion.local(now, start, tx.total * 0.14))
                    if ring_alpha > 0:
                        painter.save()
                        painter.setPen(QPen(motion.with_alpha(COLOR_ACCENT_WARNING, ring_alpha), 2))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawRoundedRect(cell.adjusted(5, 7, -5, -7), 4, 4)
                        painter.restore()

                is_pivot = r == pivot_r and c == pivot_c
                if is_pivot and glide_rect is None:
                    painter.save()
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(COLOR_FEEDBACK_SUCCESS))
                    painter.drawRoundedRect(cell.adjusted(4, 6, -4, -6), 4, 4)
                    painter.restore()

                if r in moving_rows and c in op_cols:
                    continue
                if tx is not None and tx.arrival and now < tx.arrival.get((r, c), 0.0):
                    continue
                if tx is not None and tx.replaced_col is not None and c == tx.replaced_col:
                    self._paint_replaced_cell(painter, g, tx, now, r, c, mono)
                    continue
                self._paint_cell_text(painter, g, tx, now, r, c, mono, is_pivot and glide_rect is None)

        if glide_rect is not None:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(motion.with_alpha(COLOR_FEEDBACK_SUCCESS, 0.92))
            painter.drawRoundedRect(glide_rect, 4, 4)
            # El número del pivote se ve oscuro solo donde ya llegó el rectángulo.
            painter.setClipRect(glide_rect)
            paint_book_scalar(painter, g.cells[pivot_r][pivot_c], g.texts[pivot_r][pivot_c], QColor(COLOR_BG_BASE), mono)
            painter.restore()

        if tx is not None:
            if op is not None and op.kind == step_diff.SWAP and moving_rows:
                self._paint_swap(painter, g, tx, now, op, mono)
            elif op is not None and op.kind == step_diff.ADD:
                self._paint_ghost(painter, g, tx, now, op, mono)
            elif op is not None and op.kind == step_diff.SCALE:
                self._paint_scale(painter, g, tx, now, op)
            if tx.lead_cells:
                self._paint_leads(painter, g, tx, now)
        painter.end()

    def _paint_headers(self, painter: QPainter, g: _Geometry, cols: int, split: Optional[int]) -> None:
        header_font = ui_font(15, italic=True)
        header_fm = QFontMetrics(header_font)
        sub_font = ui_font(max(9, int(header_font.pixelSize() * 0.68)))
        sub_fm = QFontMetrics(sub_font)
        header_h = g.header_h
        for c in range(cols):
            hx = g.cells[0][c].left() if g.cells else 0
            role = self._header_roles.get(c)
            color = (
                COLOR_FEEDBACK_SUCCESS
                if role == "basic"
                else COLOR_ACCENT_WARNING
                if role == "free"
                else COLOR_INTERACTIVE_IDLE
            )
            painter.setPen(QColor(color))
            if split is not None and c >= split:
                painter.setFont(header_font)
                painter.drawText(QRect(hx, g.origin_y, g.col_widths[c], header_h), Qt.AlignCenter, "b")
                continue
            sub_str = str(c + 1)
            w_x = header_fm.horizontalAdvance("x")
            w_sub = sub_fm.horizontalAdvance(sub_str)
            start_x = hx + (g.col_widths[c] - (w_x + 1 + w_sub)) // 2
            base_y = g.origin_y + (header_h + header_fm.ascent() - header_fm.descent()) // 2
            painter.setFont(header_font)
            painter.drawText(start_x, base_y, "x")
            painter.setFont(sub_font)
            painter.drawText(start_x + w_x + 1, base_y + max(2, int(header_fm.ascent() * 0.32)), sub_str)

    def _paint_row_bands(self, painter: QPainter, g: _Geometry, rows: int, tx: Optional[_Transition], now: float, op) -> None:
        for r in range(rows):
            band = g.bands[r]
            if self._highlight_row is not None and r == self._highlight_row:
                painter.fillRect(band, motion.with_alpha(COLOR_INTERACTIVE_IDLE, 0.18))
            if r in self._alert_rows:
                painter.fillRect(band, motion.with_alpha(COLOR_ACCENT_WARNING, 0.20))
                painter.fillRect(QRect(band.right() - 3, band.top(), 3, band.height()), QColor(COLOR_ACCENT_WARNING))
            if tx is not None and r in tx.alert_rows:
                k = motion.bell(motion.local(now, *tx.alert_window))
                if k > 0:
                    painter.fillRect(band, motion.with_alpha(tx.alert_color, 0.32 * k))

            if tx is not None and op is not None and op.kind == step_diff.ADD and r == op.source:
                t = now / tx.total if tx.total else 1.0
                glow = min(1.0, t / 0.15) * (1.0 - motion.local(t, 0.72, 0.25))
                if glow > 0:
                    painter.fillRect(band, motion.with_alpha(COLOR_INTERACTIVE_IDLE, _WASH * glow))

            if r in self._affected_rows:
                wash = self._flash_alpha
                if tx is not None and tx.kind == TRANSITION_FORWARD and op is not None:
                    start = tx.fade[0] - (0.04 * tx.total)
                    wash = max(wash, 0.15 * motion.bell(motion.local(now, start, tx.total - start)))
                if wash > 0:
                    painter.fillRect(band, motion.with_alpha(COLOR_FEEDBACK_SUCCESS, min(wash, 0.15) * (_WASH / 0.16)))
                painter.fillRect(QRect(band.left(), band.top(), 3, band.height()), QColor(COLOR_FEEDBACK_SUCCESS))
            elif self._actor_row is not None and r == self._actor_row:
                painter.fillRect(QRect(band.left(), band.top(), 3, band.height()), QColor(COLOR_INTERACTIVE_IDLE))

    def _ink(self, r: int, c: int, is_pivot: bool) -> QColor:
        if is_pivot:
            return QColor(COLOR_BG_BASE)
        if r in self._contradiction_rows and self._split_col is not None:
            if c < self._split_col:
                return motion.with_alpha(COLOR_TEXT_MUTED, 0.55)
            return QColor(COLOR_FEEDBACK_ERROR)
        if self._split_col is not None and c >= self._split_col:
            return QColor(COLOR_INTERACTIVE_IDLE)
        return QColor(COLOR_TEXT_PRIMARY)

    def _paint_cell_text(self, painter, g: _Geometry, tx, now: float, r: int, c: int, mono, is_pivot: bool) -> None:
        cell = g.cells[r][c]
        ink = self._ink(r, c, is_pivot)
        old = tx.old_text.get((r, c)) if tx is not None else None
        if old is None or old == g.texts[r][c]:
            paint_book_scalar(painter, cell, g.texts[r][c], ink, mono)
            return
        start, dur = tx.fade
        k = motion.ease(motion.CURVE_MOVE, motion.local(now, start, dur))
        if 0.0 < k < 1.0 and not is_pivot:
            painter.fillRect(cell.adjusted(2, 4, -2, -4), motion.with_alpha(COLOR_FEEDBACK_SUCCESS, 0.18 * motion.bell(k)))
        if k < 1.0:
            old_ink = QColor(ink)
            old_ink.setAlphaF(ink.alphaF() * (1.0 - k))
            paint_book_scalar(painter, cell, old, old_ink, mono)
        if k > 0.0:
            new_ink = QColor(ink)
            new_ink.setAlphaF(ink.alphaF() * k)
            paint_book_scalar(painter, cell, g.texts[r][c], new_ink, mono)

    def _paint_replaced_cell(self, painter, g: _Geometry, tx: _Transition, now: float, r: int, c: int, mono) -> None:
        """La columna vieja baja y se desvanece; la nueva (``b``) entra desde la derecha."""
        cell = g.cells[r][c]
        ink = self._ink(r, c, self._pivot == (r, c))
        out = motion.ease(motion.CURVE_EXIT, motion.local(now, 0.0, tx.total * 0.45))
        old = tx.replaced_old.get(r, "")
        if out < 1.0 and old:
            color = QColor(ink)
            color.setAlphaF(1.0 - out)
            paint_book_scalar(painter, cell.translated(0, int(g.row_h * 0.55 * out)), old, color, mono)
        enter = motion.ease(motion.CURVE_ENTER, motion.local(now, tx.total * 0.25, tx.total * 0.45))
        if enter > 0.0:
            color = QColor(COLOR_INTERACTIVE_IDLE)
            color.setAlphaF(enter if enter < 1.0 else 1.0)
            if enter >= 1.0:
                color = ink
            paint_book_scalar(painter, cell.translated(int(round(40 * (1.0 - enter))), 0), g.texts[r][c], color, mono)

    def _paint_ghost(self, painter, g: _Geometry, tx: _Transition, now: float, op, mono) -> None:
        """Copia de la fila que actúa: viaja hasta la fila que modifica y se funde con ella."""
        total = tx.total
        travel = motion.local(now, 0.12 * total, 0.48 * total)
        if travel <= 0.0:
            return
        merge = motion.local(now, 0.60 * total, 0.12 * total)
        if merge >= 1.0:
            return
        k = motion.ease(motion.CURVE_TRAVEL, travel)
        dy = (g.cells[op.target][0].top() - g.cells[op.source][0].top()) * k
        alpha = 0.72 * min(1.0, travel / 0.18) * (1.0 - merge)
        texts = [(c, g.texts[op.source][c]) for c in range(*op.columns)]
        band = QRectF(g.bands[op.source]).translated(0, dy)
        left = g.cells[op.source][op.columns[0]].left() - 4
        right = g.cells[op.source][op.columns[1] - 1].right() + 4
        ghost_band = QRectF(left, band.top() + 4, right - left, band.height() - 8)
        painter.save()
        body = min(1.0, travel / 0.18) * (1.0 - merge)
        painter.setPen(QPen(motion.with_alpha(COLOR_INTERACTIVE_IDLE, 0.6 * body), 1))
        painter.setBrush(motion.with_alpha(COLOR_SURFACE_ELEVATED, 0.97 * body))
        painter.drawRoundedRect(ghost_band, 6, 6)
        painter.restore()
        for c, text in texts:
            color = QColor(COLOR_INTERACTIVE_IDLE if (self._split_col is not None and c >= self._split_col) else COLOR_TEXT_PRIMARY)
            color.setAlphaF(alpha)
            paint_book_scalar(painter, g.cells[op.source][c].translated(0, int(round(dy))), text, color, mono)
        self._paint_label(painter, g, tx.label, ghost_band.center().y(), alpha / 0.72)

    def _paint_label(self, painter, g: _Geometry, text: str, center_y: float, alpha: float) -> None:
        """Etiqueta ``× k`` junto a la matriz (afuera de los corchetes si cabe)."""
        if not text or alpha <= 0:
            return
        font = ui_font(15, mono=True, weight=600)
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(text) + 18
        h = fm.height() + 8
        x = g.bracket_rect.right() + 10
        if x + w > self.width() - 4:
            x = g.bracket_rect.left() - 10 - w
        if x < 4:
            x = g.bracket_rect.left() + 6
        rect = QRectF(x, center_y - h / 2, w, h)
        painter.save()
        painter.setOpacity(min(1.0, alpha))
        painter.setPen(QPen(QColor(COLOR_INTERACTIVE_IDLE), 1.2))
        painter.setBrush(QColor(COLOR_SURFACE_ELEVATED))
        painter.drawRoundedRect(rect, h / 2, h / 2)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.restore()

    def _paint_swap(self, painter, g: _Geometry, tx: _Transition, now: float, op, mono) -> None:
        """Las dos filas se cruzan: una por delante (realzada) y otra por detrás (atenuada)."""
        travel = motion.local(now, 0.10 * tx.total, 0.70 * tx.total)
        k = motion.ease(motion.CURVE_MOVE, travel)
        arc = min(22.0, g.row_h * 0.5) * motion.bell(k)
        a, b = op.target, op.source
        cols = range(*op.columns)
        # Delante: el contenido que termina en la fila b viene de la fila a.
        for row_from, row_to, front in ((a, b, False), (b, a, True)):
            dy = (g.cells[row_to][0].top() - g.cells[row_from][0].top()) * k
            dx = arc if front else -arc
            alpha = 1.0 if front else 1.0 - 0.55 * motion.bell(k)
            if front and 0.0 < k < 1.0:
                left = g.cells[row_from][op.columns[0]].left() - 4 + dx
                right = g.cells[row_from][op.columns[1] - 1].right() + 4 + dx
                band = QRectF(left, g.bands[row_from].top() + 4 + dy, right - left, g.row_h - 8)
                painter.save()
                painter.setPen(QPen(motion.with_alpha(COLOR_FEEDBACK_SUCCESS, 0.7 * motion.bell(k)), 1.2))
                painter.setBrush(motion.with_alpha(COLOR_SURFACE_ELEVATED, 0.9 * motion.bell(k)))
                painter.drawRoundedRect(band, 6, 6)
                painter.restore()
            for c in cols:
                ink = self._ink(row_to, c, False)
                ink.setAlphaF(ink.alphaF() * alpha)
                rect = g.cells[row_from][c].translated(int(round(dx)), int(round(dy)))
                paint_book_scalar(painter, rect, g.texts[row_to][c], ink, mono)

    def _paint_scale(self, painter, g: _Geometry, tx: _Transition, now: float, op) -> None:
        """La etiqueta ``× k`` aterriza sobre la fila; el pivote pulsa al quedar en 1."""
        total = tx.total
        drop = motion.ease(motion.CURVE_ENTER, motion.local(now, 0.0, 0.30 * total))
        leave = motion.local(now, 0.72 * total, 0.26 * total)
        alpha = drop * (1.0 - leave)
        center_y = g.cells[op.target][0].center().y() - 12 * (1.0 - drop)
        self._paint_label(painter, g, tx.label, center_y, alpha)
        if self._pivot is not None and self._pivot[0] == op.target:
            k = motion.local(now, 0.50 * total, 0.45 * total)
            if 0.0 < k < 1.0:
                cell = QRectF(g.cells[self._pivot[0]][self._pivot[1]].adjusted(4, 6, -4, -6))
                grow = 5.0 * k
                painter.save()
                painter.setPen(QPen(motion.with_alpha(COLOR_FEEDBACK_SUCCESS, 0.9 * motion.bell(k)), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(cell.adjusted(-grow, -grow, grow, grow), 6, 6)
                painter.restore()

    def _paint_leads(self, painter, g: _Geometry, tx: _Transition, now: float) -> None:
        """Los pivotes de la forma final se encienden en secuencia."""
        span = float(motion.ms(motion.SLOW + 60))
        for index, (r, c) in enumerate(tx.lead_cells):
            if not (0 <= r < len(g.cells) and 0 <= c < len(g.cells[0])):
                continue
            k = motion.local(now, tx.lead_start + index * tx.lead_step, span)
            if not 0.0 < k < 1.0:
                continue
            cell = QRectF(g.cells[r][c].adjusted(3, 5, -3, -5))
            grow = 3.0 * k
            painter.save()
            painter.setPen(QPen(motion.with_alpha(tx.lead_color, 0.95 * motion.bell(k)), 2.2))
            painter.setBrush(motion.with_alpha(tx.lead_color, 0.18 * motion.bell(k)))
            painter.drawRoundedRect(cell.adjusted(-grow, -grow, grow, grow), 6, 6)
            painter.restore()

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._matrix is not None:
            self.setFocus()
            self._end_transition()
        if self._clickable and self._matrix is not None:
            self._layout()
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            for r, row_rects in enumerate(self._cell_rects):
                for c, rect in enumerate(row_rects):
                    if rect.contains(pos):
                        self.cellClicked.emit(r, c)
                        self._highlight_row = r
                        self._highlight_col = c
                        self.update()
                        return
        super().mousePressEvent(event)

    def copy_to_clipboard(self) -> bool:
        """Copia la matriz visualizada al portapapeles en formato TSV universal."""
        if self._matrix is None:
            return False
        return copy_matrix_to_clipboard(self._matrix, mode=self._mode)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self._matrix is None:
            return

        menu = QMenu(self)
        copy_action = menu.addAction("Copiar matriz")
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_to_clipboard)
        latex_action = menu.addAction("Copiar como LaTeX")
        latex_action.triggered.connect(self.copy_latex_to_clipboard)
        menu.exec(event.globalPos())

    def copy_latex_to_clipboard(self) -> bool:
        """Copia la matriz en notación LaTeX (bmatrix o arreglo aumentado)."""
        if self._matrix is None:
            return False
        try:
            from PySide6.QtGui import QGuiApplication

            clipboard = QGuiApplication.clipboard()
        except Exception:
            return False
        if clipboard is None:
            return False
        clipboard.setText(self._matrix.to_latex(split_col=self._split_col))
        return True

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._matrix is not None and (
            event.matches(QKeySequence.Copy)
            or (event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier)
        ):
            self.copy_to_clipboard()
            event.accept()
            return
        super().keyPressEvent(event)


def _text_width(fm: QFontMetrics, text: str) -> int:
    """Ancho que ocupa un escalar pintado con :func:`paint_book_scalar`."""
    if "/" in text:
        body = text[1:] if text.startswith("-") else text
        num, den = body.split("/", 1)
        width = max(fm.horizontalAdvance(num), fm.horizontalAdvance(den)) + 18
        if text.startswith("-"):
            width += fm.horizontalAdvance("−") + 6
        return width
    return fm.horizontalAdvance(text.replace("-", "−")) + 8
