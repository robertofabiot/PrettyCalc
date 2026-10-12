"""Barra de navegación segmentada entre los módulos de PrettyCalc."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

try:
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QFrame
    from PySide6.QtCore import Signal, Qt
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.ui.theme import apply_widget_class


# Marcas tipográficas (no emojis): los emojis se dibujan con Segoe UI Emoji en
# Windows y con Noto Color Emoji en Linux, y se veían distintos en cada sistema.
MODULE_TABS: Sequence[Tuple[str, str]] = (
    ("[A|b]", "Sistemas Lineales"),
    ("A·B", "Álgebra Matricial"),
    ("ℝⁿ", "Vectores en ℝⁿ"),
    ("Ax", "Ecuaciones Matriciales"),
    ("det", "Determinantes"),
    ("LU", "Factorización LU"),
)


#: Rótulos cortos para ventanas angostas (el rótulo completo queda en el tooltip).
SHORT_LABELS: Sequence[str] = ("Sistemas", "Matrices", "Vectores", "Ecuaciones", "Determinantes", "LU")


class ModularNavigationBar(QWidget):
    """Pestañas segmentadas superiores. Emite `module_changed(int)` al conmutar."""

    module_changed = Signal(int)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        tabs: Sequence[Tuple[str, str]] = MODULE_TABS,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("modularNavigationBar")
        self._buttons: List[QPushButton] = []
        self._full_texts: List[str] = []
        self._short_texts: List[str] = []
        self._compact = False
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._setup_ui(tabs)
        self._group.idClicked.connect(self._on_id_clicked)

    def _setup_ui(self, tabs: Sequence[Tuple[str, str]]) -> None:
        shell = QFrame(self)
        shell.setObjectName("navSegmentBar")
        apply_widget_class(shell, "nav-segment-bar")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(shell)

        row = QHBoxLayout(shell)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(2)

        for index, (icon, label) in enumerate(tabs):
            btn = QPushButton(f"{icon}  {label}")
            btn.setToolTip(f"{label}  (Ctrl+{index + 1})")
            btn.setAccessibleName(label)
            self._full_texts.append(btn.text())
            self._short_texts.append(SHORT_LABELS[index] if index < len(SHORT_LABELS) else label)
            btn.setObjectName("navSegment")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.TabFocus)
            self._group.addButton(btn, index)
            self._buttons.append(btn)
            row.addWidget(btn)

        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_id_clicked(self, index: int) -> None:
        self.module_changed.emit(index)

    def current_index(self) -> int:
        return self._group.checkedId()

    def set_current_index(self, index: int, emit: bool = True) -> None:
        """Selecciona el módulo `index` (0-based)."""
        if index < 0 or index >= len(self._buttons):
            return
        if self._buttons[index].isChecked() and not emit:
            return
        self._buttons[index].setChecked(True)
        if emit:
            self.module_changed.emit(index)

    def is_compact(self) -> bool:
        return self._compact

    def _needed_width(self, texts: Sequence[str]) -> int:
        if not self._buttons:
            return 0
        metrics = self._buttons[0].fontMetrics()
        return sum(metrics.horizontalAdvance(text) + 34 for text in texts) + 12

    def set_compact(self, compact: bool) -> None:
        """Rótulos cortos cuando el ancho no alcanza: evita textos recortados."""
        if compact == self._compact:
            return
        self._compact = compact
        texts = self._short_texts if compact else self._full_texts
        for button, text in zip(self._buttons, texts):
            button.setText(text)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.set_compact(self.width() < self._needed_width(self._full_texts))

    @property
    def buttons(self) -> List[QPushButton]:
        return list(self._buttons)
