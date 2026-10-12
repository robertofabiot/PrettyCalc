"""Esquema gráfico de la regla de Sarrus.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (Nielsen #8): además de las fórmulas, la regla se dibuja como en
la pizarra: la matriz 3×3 con sus dos primeras columnas repetidas a la
derecha, las tres diagonales principales en trazo continuo (se suman) y las
tres secundarias en trazo discontinuo (se restan). La diagonal del paso
visible del carrusel se resalta.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import QSizePolicy, QWidget
    from PySide6.QtCore import QPointF, QRect, QSize, Qt
    from PySide6.QtGui import QColor, QPainter, QPen
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui.book_matrix import draw_square_brackets, paint_book_scalar
from prettycalc.ui.theme import (
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    ui_font,
)

_COLS = 5  # 3 columnas + 2 repetidas


class SarrusDiagram(QWidget):
    """Matriz extendida con las seis diagonales de Sarrus."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._matrix: Optional[Matrix] = None
        self._active: Optional[int] = None  # 0..2 principales, 3..5 secundarias
        self.setMinimumHeight(190)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAccessibleName("Esquema de la regla de Sarrus")

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(360, 200)

    def set_matrix(self, matrix: Optional[Matrix]) -> None:
        self._matrix = matrix if matrix is not None and matrix.shape == (3, 3) else None
        self._active = None
        self.update()

    def matrix(self) -> Optional[Matrix]:
        return self._matrix

    def set_active_diagonal(self, index: Optional[int]) -> None:
        self._active = index if index is not None and 0 <= index < 6 else None
        self.update()

    def active_diagonal(self) -> Optional[int]:
        return self._active

    @staticmethod
    def diagonal_lines() -> List[Tuple[bool, Tuple[int, int], Tuple[int, int]]]:
        """(es_principal, inicio, fin) de las seis diagonales en la matriz 3×5."""
        lines = []
        for col in range(3):
            lines.append((True, (0, col), (2, col + 2)))
        for col in range(3):
            lines.append((False, (0, col + 2), (2, col)))
        return lines

    @staticmethod
    def extended_cells(index: int) -> Tuple[Tuple[int, int], ...]:
        """Celdas de la diagonal ``index`` sobre la matriz extendida 3×5."""
        if index < 3:
            return tuple((row, index + row) for row in range(3))
        start = index - 3
        return tuple((row, start + 2 - row) for row in range(3))

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(COLOR_SURFACE_INNER))
        if self._matrix is None:
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.setFont(ui_font(14, italic=True))
            painter.drawText(self.rect(), Qt.AlignCenter, "El esquema aparece al calcular con Sarrus")
            painter.end()
            return

        cell_w = max(44, min(72, (self.width() - 40) // _COLS))
        cell_h = max(36, min(46, (self.height() - 56) // 3))
        grid_w = cell_w * _COLS
        left = (self.width() - grid_w) // 2
        top = 24

        def center(row: int, col: int) -> QPointF:
            return QPointF(left + col * cell_w + cell_w / 2, top + row * cell_h + cell_h / 2)

        # Diagonales (detrás de los números)
        for index, (principal, start, end) in enumerate(self.diagonal_lines()):
            active = self._active == index
            color = QColor(COLOR_FEEDBACK_SUCCESS if principal else COLOR_FEEDBACK_ERROR)
            if self._active is not None and not active:
                color.setAlphaF(0.22)
            pen = QPen(color, 3.2 if active else 1.8)
            pen.setStyle(Qt.SolidLine if principal else Qt.DashLine)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            a, b = center(*start), center(*end)
            painter.drawLine(a, b)
            painter.setFont(ui_font(15, weight=700))
            sign_point = b + QPointF(0, cell_h * 0.62) if principal else a - QPointF(0, cell_h * 0.62)
            painter.drawText(
                QRect(int(sign_point.x()) - 10, int(sign_point.y()) - 9, 20, 18),
                Qt.AlignCenter,
                "+" if principal else "−",
            )

        # Corchetes de la matriz original y separador de las columnas repetidas
        draw_square_brackets(
            painter,
            QRect(left - 4, top - 2, cell_w * 3 + 8, cell_h * 3 + 4),
            QColor(COLOR_TEXT_PRIMARY),
        )
        sep = QPen(QColor(COLOR_TEXT_MUTED), 1, Qt.DotLine)
        painter.setPen(sep)
        x = left + 3 * cell_w + 6
        painter.drawLine(x, top, x, top + 3 * cell_h)

        active_cells = set(self.extended_cells(self._active)) if self._active is not None else set()
        font = ui_font(16, mono=True)
        for row in range(3):
            for col in range(_COLS):
                source_col = col % 3
                repeated = col >= 3
                color = QColor(COLOR_TEXT_MUTED if repeated else COLOR_TEXT_PRIMARY)
                if (row, col) in active_cells:
                    color = QColor(COLOR_TEXT_PRIMARY)
                    painter.save()
                    painter.setPen(Qt.NoPen)
                    glow = QColor(COLOR_FEEDBACK_SUCCESS if self._active < 3 else COLOR_FEEDBACK_ERROR)
                    glow.setAlphaF(0.22)
                    painter.setBrush(glow)
                    painter.drawRoundedRect(QRect(left + col * cell_w + 4, top + row * cell_h + 3, cell_w - 8, cell_h - 6), 6, 6)
                    painter.restore()
                rect = QRect(left + col * cell_w, top + row * cell_h, cell_w, cell_h)
                paint_book_scalar(painter, rect, format_scalar(self._matrix.get(row, source_col)), color, font)
        painter.end()
