"""Delegado de PySide6 para la partición vertical de la matriz aumentada [A | b]."""

from __future__ import annotations
from typing import Optional

try:
    from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
    from PySide6.QtGui import QPainter, QColor, QFont
    from PySide6.QtCore import QModelIndex, Qt, QSize
except ImportError:
    QStyledItemDelegate = object  # type: ignore

from prettycalc.ui.theme import COLOR_INTERACTIVE_IDLE, COLOR_TEXT_PRIMARY, FONT_FAMILY_MONO
from prettycalc.ui.book_matrix import draw_split_bar, paint_book_scalar


class AugmentedMatrixDelegate(QStyledItemDelegate):
    """Pinta fracciones apiladas y la línea divisoria en la columna b."""

    def __init__(self, split_col: int, parent: Optional[object] = None):
        super().__init__(parent)
        self.split_col = split_col

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: ARG002
        base = super().sizeHint(option, index)
        return QSize(max(base.width(), 52), max(base.height(), 48))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()

        bg = index.data(Qt.BackgroundRole)
        if bg is not None:
            color = bg if isinstance(bg, QColor) else bg.color()
            painter.fillRect(option.rect.adjusted(2, 2, -2, -2), color)

        fg_role = index.data(Qt.ForegroundRole)
        if fg_role is None:
            fg = QColor(COLOR_TEXT_PRIMARY)
        else:
            fg = fg_role if isinstance(fg_role, QColor) else fg_role.color()

        font_role = index.data(Qt.FontRole)
        if isinstance(font_role, QFont):
            font = font_role
        else:
            font = QFont()
            font.setFamily(FONT_FAMILY_MONO.split(",")[0].strip())
            font.setPointSize(12)

        text = str(index.data(Qt.DisplayRole) or "")
        paint_book_scalar(painter, option.rect, text, fg, font)

        if index.column() == self.split_col:
            draw_split_bar(
                painter,
                option.rect.left() + 1,
                option.rect.top(),
                option.rect.bottom(),
                QColor(COLOR_INTERACTIVE_IDLE),
            )

        painter.restore()
