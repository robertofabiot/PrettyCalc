"""Filas adaptables: una cadena horizontal que pasa a columna en pantallas angostas.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (Nielsen #8): la cadena A → Aᵀ → (Aᵀ)ᵀ, las tres matrices de las
propiedades ternarias o los resultados LHS = RHS dejan de comprimirse en
pantallas de 1366 px: bajo el umbral se apilan y las flechas giran (→ pasa a ↓).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import QBoxLayout, QLabel, QWidget
    from PySide6.QtCore import Qt
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore


class ResponsiveRow(QWidget):
    """Contenedor horizontal que se vuelve vertical bajo ``breakpoint`` píxeles."""

    def __init__(self, breakpoint: int = 1100, spacing: int = 10, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._breakpoint = breakpoint
        self._layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(spacing)
        self._connectors: List[Tuple[QLabel, str, str]] = []
        self._vertical = False

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self._layout.addWidget(widget, stretch)

    def add_connector(self, horizontal: str, vertical: Optional[str] = None, style: str = "") -> QLabel:
        """Símbolo entre tarjetas (``→``, ``=``, ``·``); en vertical usa ``vertical``."""
        label = QLabel(horizontal)
        label.setAlignment(Qt.AlignCenter)
        if style:
            label.setStyleSheet(style)
        self._layout.addWidget(label, 0, Qt.AlignCenter)
        self._connectors.append((label, horizontal, vertical if vertical is not None else horizontal))
        return label

    def is_vertical(self) -> bool:
        return self._vertical

    def set_vertical(self, vertical: bool) -> None:
        if vertical == self._vertical:
            return
        self._vertical = vertical
        self._layout.setDirection(QBoxLayout.TopToBottom if vertical else QBoxLayout.LeftToRight)
        for label, horizontal, vertical_text in self._connectors:
            label.setText(vertical_text if vertical else horizontal)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.set_vertical(self.width() < self._breakpoint)
