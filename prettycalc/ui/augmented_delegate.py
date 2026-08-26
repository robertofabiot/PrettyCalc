"""Delegado personalizado de PySide6 para dibujar la partición vertical de la matriz aumentada [A | b]."""

from __future__ import annotations
from typing import Optional

try:
    from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
    from PySide6.QtGui import QPainter, QPen, QColor
    from PySide6.QtCore import QModelIndex
except ImportError:
    # Soporte para entornos donde PySide6 está terminando de instalarse
    QStyledItemDelegate = object  # type: ignore

from prettycalc.ui.theme import COLOR_INTERACTIVE_IDLE


class AugmentedMatrixDelegate(QStyledItemDelegate):
    """Dibuja una línea divisoria vertical continua en el borde izquierdo de la columna b."""

    def __init__(self, split_col: int, parent: Optional[object] = None):
        super().__init__(parent)
        self.split_col = split_col

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)
        # Si la celda corresponde a la columna de términos independientes, pintar la línea vertical a la izquierda
        if index.column() == self.split_col:
            painter.save()
            pen = QPen(QColor(COLOR_INTERACTIVE_IDLE))
            pen.setWidth(2)
            painter.setPen(pen)
            # Dibujar línea vertical de arriba a abajo del rectángulo de la celda
            x = option.rect.left()
            painter.drawLine(x, option.rect.top(), x, option.rect.bottom())
            painter.restore()
