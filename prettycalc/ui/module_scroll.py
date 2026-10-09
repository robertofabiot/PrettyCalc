"""Scroll de módulo: el panel conserva su tamaño y el usuario se desplaza.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.
Evita que el layout de Linux encoja las tarjetas cuando el contenido no cabe.
"""

from __future__ import annotations

try:
    from PySide6.QtWidgets import QFrame, QLayout, QScrollArea, QSizePolicy, QWidget
    from PySide6.QtCore import QEvent, QTimer, Qt
except ImportError:
    QScrollArea = object  # type: ignore
    QWidget = object  # type: ignore
    QEvent = None  # type: ignore

from prettycalc.ui.theme import COLOR_BG_BASE


class ModuleScroll(QScrollArea):
    """Viewport fijo. El contenido no baja de su alto natural: aparece la barra."""

    def __init__(self, content: QWidget) -> None:
        super().__init__()
        self.setObjectName("moduleScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            f"QScrollArea#moduleScroll {{ background: transparent; border: none; }} "
            f"QScrollArea#moduleScroll > QWidget#qt_scrollarea_viewport {{ background-color: {COLOR_BG_BASE}; }}"
        )
        self.viewport().setAutoFillBackground(False)
        layout = content.layout()
        if layout is not None:
            layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self._syncing = False
        self.setWidget(content)
        content.setAutoFillBackground(False)
        self._watch(content)
        self._sync_natural_height()

    def _watch(self, widget: QWidget) -> None:
        """Sigue el árbol de widgets para enterarse cuando crece el contenido."""
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        """Recalcula el alto cuando aparecen más comprobaciones u otros bloques."""
        if QEvent is None:
            return super().eventFilter(watched, event)
        if event.type() == QEvent.Type.ChildAdded:
            child = event.child()
            if isinstance(child, QWidget):
                self._watch(child)
                QTimer.singleShot(0, self._sync_natural_height)
        elif event.type() == QEvent.Type.LayoutRequest:
            QTimer.singleShot(0, self._sync_natural_height)
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:
        """Al cambiar la ventana, conserva el alto del contenido y desplaza el resto."""
        super().resizeEvent(event)
        self._sync_natural_height()

    def _sync_natural_height(self) -> None:
        """Fija el mínimo al alto que el contenido pide, para que no se aplaste."""
        content = self.widget()
        if content is None or self._syncing:
            return
        layout = content.layout()
        natural = layout.sizeHint().height() if layout is not None else content.sizeHint().height()
        if natural <= 0 or content.minimumHeight() == natural:
            return
        self._syncing = True
        content.setMinimumHeight(natural)
        content.updateGeometry()
        self._syncing = False


def make_module_scroll(content: QWidget) -> ModuleScroll:
    """Envuelve el contenido de un módulo. Devuelve el área que se desplaza."""
    return ModuleScroll(content)
