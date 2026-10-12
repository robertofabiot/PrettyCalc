"""Filas adaptables: una cadena horizontal que pasa a columna en pantallas angostas.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (Nielsen #8): la cadena A → Aᵀ → (Aᵀ)ᵀ, las tres matrices de las
propiedades ternarias o los resultados LHS = RHS dejan de comprimirse en
pantallas de 1366 px: bajo el umbral se apilan y las flechas giran (→ pasa a ↓).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import QBoxLayout, QLabel, QVBoxLayout, QWidget
    from PySide6.QtCore import Qt, Signal
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore


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


class CurrentPageStack(QWidget):
    """Páginas apiladas que miden lo que mide la página visible.

    Misma API que ``QStackedWidget`` (``addWidget``, ``setCurrentIndex``,
    ``currentIndex``, ``currentWidget``, ``widget``, ``count`` y la señal
    ``currentChanged``), pero las páginas ocultas no reservan espacio: con
    ``QStackedWidget`` una página corta heredaba la altura de la más alta y
    empujaba fuera de la vista lo que venía después.
    """

    currentChanged = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._pages: List[QWidget] = []
        self._current = -1
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def addWidget(self, page: QWidget) -> int:  # noqa: N802
        self._pages.append(page)
        self._layout.addWidget(page)
        index = len(self._pages) - 1
        if self._current < 0:
            self._current = index
            page.setVisible(True)
        else:
            page.setVisible(False)
        return index

    def count(self) -> int:
        return len(self._pages)

    def widget(self, index: int) -> Optional[QWidget]:
        return self._pages[index] if 0 <= index < len(self._pages) else None

    def currentIndex(self) -> int:  # noqa: N802
        return self._current

    def currentWidget(self) -> Optional[QWidget]:  # noqa: N802
        return self.widget(self._current)

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        if not 0 <= index < len(self._pages) or index == self._current:
            return
        for page_index, page in enumerate(self._pages):
            page.setVisible(page_index == index)
        self._current = index
        self.updateGeometry()
        self.currentChanged.emit(index)
