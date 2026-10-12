"""Filas adaptables: una cadena horizontal que pasa a columna en pantallas angostas.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (Nielsen #8): la cadena A → Aᵀ → (Aᵀ)ᵀ, las tres matrices de las
propiedades ternarias o los resultados LHS = RHS dejan de comprimirse en
pantallas de 1366 px: bajo el umbral se apilan y las flechas giran (→ pasa a ↓).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import QBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget
    from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore
    QLayout = object  # type: ignore
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


class FlowLayout(QLayout):
    """Distribuye los widgets en filas y salta de línea cuando no caben.

    Sprint 10 (Nielsen #8): los conjuntos {v₁, …, vₖ} ya no se apilan en una
    fila con barra de desplazamiento horizontal; con k ≥ 5 los vectores pasan a
    una segunda fila y todos quedan a la vista a la vez.
    """

    def __init__(self, parent: Optional[QWidget] = None, spacing: int = 10, *, center: bool = False) -> None:
        super().__init__(parent)
        self._items = []
        self._spacing = spacing
        self._center = center
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item) -> None:  # noqa: N802
        self._items.append(item)

    def insertWidget(self, index: int, widget: QWidget) -> None:  # noqa: N802
        self.addChildWidget(widget)
        from PySide6.QtWidgets import QWidgetItem

        self._items.insert(max(0, min(index, len(self._items))), QWidgetItem(widget))
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):  # noqa: N802
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int):  # noqa: N802
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):  # noqa: N802
        return Qt.Orientations(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._do_layout(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._do_layout(rect, apply=True)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _do_layout(self, rect: QRect, *, apply: bool) -> int:
        """Reparte en líneas; dentro de cada línea los widgets quedan centrados en vertical."""
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        lines = []
        current = []
        width = 0
        for item in self._items:
            widget = item.widget()
            if widget is not None and widget.isHidden():
                continue
            hint = item.sizeHint()
            needed = hint.width() if not current else width + self._spacing + hint.width()
            if current and needed > area.width():
                lines.append(current)
                current, width = [], 0
                needed = hint.width()
            current.append((item, hint))
            width = needed
        if current:
            lines.append(current)
        y = area.y()
        for index, line in enumerate(lines):
            line_height = max(hint.height() for _item, hint in line)
            if apply:
                x = area.x()
                for item, hint in line:
                    offset = (line_height - hint.height()) // 2 if self._center else 0
                    item.setGeometry(QRect(QPoint(x, y + offset), hint))
                    x += hint.width() + self._spacing
            y += line_height + (self._spacing if index < len(lines) - 1 else 0)
        return y - rect.y() + margins.bottom()
