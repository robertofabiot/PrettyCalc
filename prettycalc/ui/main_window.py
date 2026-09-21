"""Ventana principal de PrettyCalc en PySide6."""

from __future__ import annotations
import sys

try:
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QApplication,
        QStackedWidget,
    )
    from PySide6.QtGui import QAction, QKeySequence
    from PySide6.QtCore import Qt
except ImportError:
    QMainWindow = object  # type: ignore

from prettycalc.ui.modules.linear_systems_view import LinearSystemsView
from prettycalc.ui.modules.matrix_operations_view import MatrixOperationsView
from prettycalc.ui.modules.vectors_view import VectorsView
from prettycalc.ui.modules.matrix_equations_view import MatrixEquationsView
from prettycalc.ui.navigation_bar import ModularNavigationBar
from prettycalc.ui.theme import (
    get_global_stylesheet,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
)

_MODULE_SUBTITLES = (
    "Sistemas de ecuaciones lineales  ·  eliminación por filas",
    "Álgebra matricial  ·  suma, escala y producto A · B",
    "Vectores en ℝⁿ  ·  operaciones y combinación lineal",
    "Ecuaciones matriciales  ·  A x = b",
)


class MainWindow(QMainWindow):
    """Shell multi-módulo: navegación segmentada y cuatro vistas persistentes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrettyCalc — Álgebra lineal")
        self.setMinimumSize(1080, 680)
        self.resize(1380, 800)
        self.setStyleSheet(get_global_stylesheet())
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("rootWidget")
        self.setCentralWidget(root_widget)

        main_layout = QVBoxLayout(root_widget)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("PrettyCalc")
        title_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: 600; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.02em;"
        )
        self.subtitle_lbl = QLabel(_MODULE_SUBTITLES[0])
        self.subtitle_lbl.setStyleSheet(f"font-size: 15px; color: {COLOR_INTERACTIVE_IDLE};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        header_layout.addLayout(title_box)

        self.nav_bar = ModularNavigationBar()
        self.nav_bar.module_changed.connect(self._on_module_changed)
        header_layout.addWidget(self.nav_bar, stretch=1, alignment=Qt.AlignVCenter)
        main_layout.addLayout(header_layout)

        self.module_stack = QStackedWidget()
        self.linear_systems_view = LinearSystemsView()
        self.matrix_operations_view = MatrixOperationsView()
        self.vectors_view = VectorsView()
        self.matrix_equations_view = MatrixEquationsView()
        self.module_stack.addWidget(self.linear_systems_view)
        self.module_stack.addWidget(self.matrix_operations_view)
        self.module_stack.addWidget(self.vectors_view)
        self.module_stack.addWidget(self.matrix_equations_view)
        main_layout.addWidget(self.module_stack, stretch=1)

    def _setup_shortcuts(self) -> None:
        for index in range(4):
            action = QAction(self)
            action.setShortcut(QKeySequence(f"Ctrl+{index + 1}"))
            action.triggered.connect(lambda _checked=False, i=index: self.set_module(i))
            self.addAction(action)

    def set_module(self, index: int) -> None:
        """Conmuta el módulo visible y sincroniza la barra de navegación."""
        self.nav_bar.set_current_index(index, emit=False)
        self._on_module_changed(index)

    def _on_module_changed(self, index: int) -> None:
        if index < 0 or index >= self.module_stack.count():
            return
        self.module_stack.setCurrentIndex(index)
        if 0 <= index < len(_MODULE_SUBTITLES):
            self.subtitle_lbl.setText(_MODULE_SUBTITLES[index])

    @property
    def matrix_grid(self):
        return self.linear_systems_view.matrix_grid

    @property
    def solve_btn(self):
        return self.linear_systems_view.solve_btn

    @property
    def reset_btn(self):
        return self.linear_systems_view.reset_btn

    @property
    def dashboard_card(self):
        return self.linear_systems_view.dashboard_card

    @property
    def stepper_carousel(self):
        return self.linear_systems_view.stepper_carousel

    def solve_system(self) -> None:
        self.linear_systems_view.solve_system()

    def reset_matrix(self) -> None:
        self.linear_systems_view.reset_matrix()

    def load_sample_case1(self) -> None:
        self.set_module(0)
        self.linear_systems_view.load_sample_case1()

    def load_sample_case2(self) -> None:
        self.set_module(0)
        self.linear_systems_view.load_sample_case2()

    def load_sample_case3(self) -> None:
        self.set_module(0)
        self.linear_systems_view.load_sample_case3()


def run_app():
    """Arranque de la aplicación GUI."""
    app = QApplication(sys.argv)
    app.setStyleSheet(get_global_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
