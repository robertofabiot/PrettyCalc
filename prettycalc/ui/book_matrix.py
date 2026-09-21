"""Visor de matriz con notación de libro: corchetes, barra [A | b] y fracciones apiladas."""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import QWidget, QSizePolicy
    from PySide6.QtCore import Qt, Signal, QRect, QSize, Property, QPropertyAnimation, QEasingCurve
    from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics, QPaintEvent, QMouseEvent
except ImportError:
    QWidget = object  # type: ignore
    Property = lambda *args, **kwargs: None  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui.mathtext import variable_symbol
from prettycalc.ui.theme import (
    COLOR_BG_BASE,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
)


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
        self._cell_rects: List[List[QRect]] = []
        self._clickable: bool = False
        self._flash = QPropertyAnimation(self, b"flashAlpha", self)
        self._flash.setDuration(600)
        self._flash.setStartValue(0.0)
        self._flash.setKeyValueAt(0.28, 0.15)
        self._flash.setEndValue(0.0)
        self._flash.setEasingCurve(QEasingCurve.InOutCubic)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def _get_flash_alpha(self) -> float:
        return self._flash_alpha

    def _set_flash_alpha(self, value: float) -> None:
        self._flash_alpha = float(value)
        self.update()

    flashAlpha = Property(float, _get_flash_alpha, _set_flash_alpha)

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
    ) -> None:
        self._matrix = matrix
        self._split_col = split_col
        self._pivot = pivot
        self._mode = mode
        self._actor_row = actor_row
        self._affected_rows = affected_rows
        self._highlight_row = highlight_row
        self._highlight_col = highlight_col
        if clickable is not None:
            self._clickable = clickable
        if show_headers is not None:
            self._show_headers = show_headers
        self.setCursor(Qt.PointingHandCursor if self._clickable and matrix is not None else Qt.ArrowCursor)
        self.update()
        self.updateGeometry()
        if animate and affected_rows:
            self._flash.stop()
            self._flash.start()
        elif not animate:
            self._flash.stop()
            self._flash_alpha = 0.0

    def clear(self) -> None:
        self.set_matrix(None)

    def sizeHint(self) -> QSize:
        return QSize(360, 240)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(COLOR_SURFACE_INNER))

        if self._matrix is None:
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            font = QFont()
            font.setFamily(FONT_FAMILY_SANS.split(",")[0].strip())
            font.setItalic(True)
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "Sin matriz para mostrar")
            return

        matrix = self._matrix
        rows, cols = matrix.rows, matrix.cols
        split = self._split_col

        mono = QFont()
        mono.setFamily(FONT_FAMILY_MONO.split(",")[0].strip())
        mono.setPointSize(13)
        header_font = QFont()
        header_font.setFamily(FONT_FAMILY_SANS.split(",")[0].strip())
        header_font.setPointSize(11)
        header_font.setItalic(True)

        fm = QFontMetrics(mono)
        header_fm = QFontMetrics(header_font)

        cell_pad_x = 14
        row_h = max(44, int(fm.height() * 2.4))
        header_h = header_fm.height() + 8 if self._show_headers else 0

        texts: List[List[str]] = [
            [format_scalar(matrix.get(r, c), mode=self._mode) for c in range(cols)]
            for r in range(rows)
        ]

        col_widths: List[int] = []
        for c in range(cols):
            max_w = 36
            if self._show_headers:
                header = variable_symbol(c) if split is None or c < split else "b"
                max_w = max(max_w, header_fm.horizontalAdvance(header) + 8)
            for r in range(rows):
                t = texts[r][c]
                if "/" in t:
                    body = t[1:] if t.startswith("-") else t
                    num, den = body.split("/", 1)
                    frac_w = max(fm.horizontalAdvance(num), fm.horizontalAdvance(den)) + 18
                    if t.startswith("-"):
                        frac_w += fm.horizontalAdvance("−") + 6
                    max_w = max(max_w, frac_w)
                else:
                    max_w = max(max_w, fm.horizontalAdvance(t.replace("-", "−")) + 8)
            col_widths.append(max(max_w + cell_pad_x, 48))

        gap_split = 18 if split is not None else 0
        inner_w = sum(col_widths) + gap_split
        inner_h = rows * row_h
        bracket_pad_x = 18
        bracket_pad_y = 10

        total_w = inner_w + 2 * bracket_pad_x
        total_h = header_h + inner_h + 2 * bracket_pad_y

        origin_x = (self.width() - total_w) // 2
        origin_y = (self.height() - total_h) // 2
        origin_x = max(8, origin_x)
        origin_y = max(8, origin_y)

        content_left = origin_x + bracket_pad_x
        content_top = origin_y + header_h + bracket_pad_y

        def col_left(c: int) -> int:
            x = content_left
            for i in range(c):
                x += col_widths[i]
                if split is not None and i + 1 == split:
                    x += gap_split
            return x

        # Encabezados
        if self._show_headers:
            sub_font = QFont(header_font)
            sub_font.setPointSize(max(7, int(header_font.pointSize() * 0.68)))
            sub_font.setItalic(False)
            sub_fm = QFontMetrics(sub_font)
            painter.setPen(QColor(COLOR_INTERACTIVE_IDLE))

            for c in range(cols):
                hx = col_left(c)
                if split is not None and c >= split:
                    painter.setFont(header_font)
                    painter.drawText(
                        QRect(hx, origin_y, col_widths[c], header_h),
                        Qt.AlignCenter,
                        "b",
                    )
                else:
                    sub_str = str(c + 1)
                    w_x = header_fm.horizontalAdvance("x")
                    w_sub = sub_fm.horizontalAdvance(sub_str)
                    gap = 1
                    total_hdr_w = w_x + gap + w_sub
                    start_x = hx + (col_widths[c] - total_hdr_w) // 2

                    base_y = origin_y + (header_h + header_fm.ascent() - header_fm.descent()) // 2
                    painter.setFont(header_font)
                    painter.drawText(start_x, base_y, "x")

                    painter.setFont(sub_font)
                    sub_y = base_y + max(2, int(header_fm.ascent() * 0.32))
                    painter.drawText(start_x + w_x + gap, sub_y, sub_str)

        bracket_rect = QRect(
            origin_x,
            origin_y + header_h,
            total_w,
            inner_h + 2 * bracket_pad_y,
        )
        draw_square_brackets(painter, bracket_rect, QColor(COLOR_TEXT_PRIMARY), thickness=2)

        if split is not None and 0 < split < cols:
            bar_x = col_left(split) - gap_split // 2
            draw_split_bar(
                painter,
                bar_x,
                bracket_rect.top() + 6,
                bracket_rect.bottom() - 6,
                QColor(COLOR_INTERACTIVE_IDLE),
            )

        pivot_r, pivot_c = self._pivot if self._pivot is not None else (-1, -1)
        painter.setFont(mono)
        self._cell_rects = []

        for r in range(rows):
            y = content_top + r * row_h
            row_band = QRect(bracket_rect.left() + 4, y, bracket_rect.width() - 8, row_h)
            is_actor = self._actor_row is not None and r == self._actor_row
            is_affected = r in self._affected_rows
            is_hl_row = self._highlight_row is not None and r == self._highlight_row

            if is_hl_row:
                wash = QColor(COLOR_INTERACTIVE_IDLE)
                wash.setAlphaF(0.18)
                painter.fillRect(row_band, wash)

            if is_affected:
                if self._flash_alpha > 0:
                    wash = QColor(COLOR_FEEDBACK_SUCCESS)
                    wash.setAlphaF(min(self._flash_alpha, 0.15))
                    painter.fillRect(row_band, wash)
                painter.fillRect(
                    QRect(row_band.left(), row_band.top(), 3, row_band.height()),
                    QColor(COLOR_FEEDBACK_SUCCESS),
                )
            elif is_actor:
                painter.fillRect(
                    QRect(row_band.left(), row_band.top(), 3, row_band.height()),
                    QColor(COLOR_INTERACTIVE_IDLE),
                )

            row_rects: List[QRect] = []
            for c in range(cols):
                x = col_left(c)
                cell = QRect(x, y, col_widths[c], row_h)
                row_rects.append(cell)

                if self._highlight_col is not None and c == self._highlight_col:
                    col_wash = QColor(COLOR_INTERACTIVE_IDLE)
                    col_wash.setAlphaF(0.16)
                    painter.fillRect(cell, col_wash)

                if r == pivot_r and c == pivot_c:
                    painter.save()
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(COLOR_FEEDBACK_SUCCESS))
                    painter.drawRoundedRect(cell.adjusted(4, 6, -4, -6), 4, 4)
                    painter.restore()
                    fg = QColor(COLOR_BG_BASE)
                elif split is not None and c >= split:
                    fg = QColor(COLOR_INTERACTIVE_IDLE)
                else:
                    fg = QColor(COLOR_TEXT_PRIMARY)

                paint_book_scalar(painter, cell, texts[r][c], fg, mono)
            self._cell_rects.append(row_rects)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._clickable and self._matrix is not None:
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
