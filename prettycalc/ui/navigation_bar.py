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


MODULE_TABS: Sequence[Tuple[str, str]] = (
    ("🧮", "Sistemas Lineales"),
    ("⊞", "Álgebra Matricial"),
    ("↗", "Vectores en ℝⁿ"),
    ("🔣", "Ecuaciones Matriciales"),
)


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

    @property
    def buttons(self) -> List[QPushButton]:
        return list(self._buttons)
