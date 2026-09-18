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
    )
except ImportError:
    QMainWindow = object  # type: ignore

from prettycalc.ui.modules.linear_systems_view import LinearSystemsView
from prettycalc.ui.theme import (
    get_global_stylesheet,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
)


class MainWindow(QMainWindow):
    """Ventana principal: encabezado y módulo de sistemas lineales."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrettyCalc — Álgebra lineal")
        self.resize(1320, 780)
        self.setStyleSheet(get_global_stylesheet())
        self._setup_ui()

    def _setup_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("rootWidget")
        self.setCentralWidget(root_widget)

        main_layout = QVBoxLayout(root_widget)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("PrettyCalc")
        title_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: 600; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.02em;"
        )
        sub_lbl = QLabel("Sistemas de ecuaciones lineales  ·  eliminación por filas")
        sub_lbl.setStyleSheet(f"font-size: 17px; color: {COLOR_INTERACTIVE_IDLE};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box, stretch=1)
        main_layout.addLayout(header_layout)

        self.linear_systems_view = LinearSystemsView()
        main_layout.addWidget(self.linear_systems_view, stretch=1)

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
        self.linear_systems_view.load_sample_case1()

    def load_sample_case2(self) -> None:
        self.linear_systems_view.load_sample_case2()

    def load_sample_case3(self) -> None:
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
