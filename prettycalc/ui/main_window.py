"""Ventana principal de PrettyCalc en PySide6."""

from __future__ import annotations
import sys

try:
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QMessageBox,
        QSplitter,
        QFrame,
        QApplication,
        QSpacerItem,
        QSizePolicy,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QMainWindow = object  # type: ignore

from prettycalc.core.types import Matrix
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.classifier import classify_system, SystemType
from prettycalc.core.verifier import SolutionVerifier
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
from prettycalc.ui.results_dashboard import ResultsDashboardCard
from prettycalc.ui.theme import (
    get_global_stylesheet,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
    apply_widget_class,
)


class MainWindow(QMainWindow):
    """Ventana principal: cuadrícula, carrusel de pasos y dashboard."""

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

        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setHandleWidth(10)
        body_splitter.setChildrenCollapsible(False)

        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        matrix_card = QFrame()
        apply_widget_class(matrix_card, "elevated-card")
        card_layout = QVBoxLayout(matrix_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        grid_title = QLabel("Matriz aumentada  [A | b]")
        grid_title.setStyleSheet(
            f"font-size: 19px; font-weight: 600; letter-spacing: 0.03em; color: {COLOR_TEXT_PRIMARY};"
        )
        card_layout.addWidget(grid_title)

        self.matrix_grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2)
        card_layout.addWidget(self.matrix_grid, stretch=1)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.reset_btn = QPushButton("Reiniciar")
        self.reset_btn.setObjectName("secondaryAction")
        self.reset_btn.clicked.connect(self.reset_matrix)
        actions.addWidget(self.reset_btn)

        self.solve_btn = QPushButton("Resolver sistema")
        self.solve_btn.setObjectName("primaryAction")
        self.solve_btn.clicked.connect(self.solve_system)
        actions.addWidget(self.solve_btn)

        card_layout.addLayout(actions)
        left_layout.addWidget(matrix_card, stretch=1)

        samples_box = QFrame()
        apply_widget_class(samples_box, "elevated-card")
        samples_layout = QVBoxLayout(samples_box)
        samples_layout.setContentsMargins(10, 10, 10, 10)
        samples_layout.setSpacing(6)

        samples_lbl = QLabel("Casos de prueba")
        samples_lbl.setStyleSheet(
            f"font-size: 16px; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.03em;"
        )
        samples_layout.addWidget(samples_lbl)

        btn_case1 = QPushButton("I  ·  Solución única")
        btn_case1.clicked.connect(self.load_sample_case1)
        samples_layout.addWidget(btn_case1)

        btn_case2 = QPushButton("II  ·  Infinitas soluciones")
        btn_case2.clicked.connect(self.load_sample_case2)
        samples_layout.addWidget(btn_case2)

        btn_case3 = QPushButton("III  ·  Sin solución")
        btn_case3.clicked.connect(self.load_sample_case3)
        samples_layout.addWidget(btn_case3)

        left_layout.addWidget(samples_box)
        body_splitter.addWidget(left_pane)

        center_pane = QWidget()
        center_layout = QVBoxLayout(center_pane)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        steps_title = QLabel("Procedimiento")
        steps_title.setStyleSheet(
            f"font-size: 19px; font-weight: 600; letter-spacing: 0.03em; color: {COLOR_TEXT_PRIMARY};"
        )
        center_layout.addWidget(steps_title)

        self.stepper_carousel = AlgorithmStepperCarousel()
        center_layout.addWidget(self.stepper_carousel, stretch=1)
        body_splitter.addWidget(center_pane)

        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.dashboard_card = ResultsDashboardCard()
        right_layout.addWidget(self.dashboard_card)
        body_splitter.addWidget(right_pane)

        body_splitter.setSizes([360, 540, 380])
        body_splitter.setStretchFactor(0, 2)
        body_splitter.setStretchFactor(1, 4)
        body_splitter.setStretchFactor(2, 2)
        main_layout.addWidget(body_splitter, stretch=1)

    def solve_system(self) -> None:
        """Ejecuta escalonamiento, clasificación y verificación."""
        if not self.matrix_grid.is_all_valid():
            QMessageBox.warning(
                self,
                "Entrada inválida",
                "Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales.",
            )
            return

        try:
            augmented_mat = self.matrix_grid.get_matrix()
            split_col = augmented_mat.cols - 1

            _, tracer = gauss_jordan_elimination(augmented_mat, split_col=split_col)
            self.stepper_carousel.set_steps(tracer.get_steps())

            analysis = classify_system(augmented_mat, split_col=split_col)

            verifications = None
            if analysis.unique_solution is not None:
                verifications = SolutionVerifier.verify(
                    augmented_mat, analysis.unique_solution, split_col=split_col
                )

            self.dashboard_card.display_results(analysis, verifications)

        except Exception as e:
            QMessageBox.critical(self, "Error matemático", f"No se pudo resolver el sistema:\n{e}")

    def reset_matrix(self) -> None:
        """Restablece la cuadrícula a un estado 2×2 inicial."""
        self.matrix_grid.set_matrix(Matrix.zeros(2, 3))
        self.stepper_carousel.set_steps([])
        self.dashboard_card.clear()

    def load_sample_case1(self) -> None:
        """Caso I: solución única."""
        mat = Matrix([
            [1, 1, 1, 4],
            [2, -1, 1, 4],
            [1, 2, -1, 3],
        ])
        self.matrix_grid.set_matrix(mat)
        self.solve_system()

    def load_sample_case2(self) -> None:
        """Caso II: infinitas soluciones."""
        mat = Matrix([
            [1, 2, 3, 6],
            [2, 4, 6, 12],
            [3, 6, 9, 18],
        ])
        self.matrix_grid.set_matrix(mat)
        self.solve_system()

    def load_sample_case3(self) -> None:
        """Caso III: sistema sin solución."""
        mat = Matrix([
            [1, 2, 4],
            [2, 4, 9],
        ])
        self.matrix_grid.set_matrix(mat)
        self.solve_system()


def run_app():
    """Arranque de la aplicación GUI."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
