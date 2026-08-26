"""Ventana principal de PrettyCalc en PySide6."""

from __future__ import annotations
import sys
from typing import Optional

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
    COLOR_FEEDBACK_SUCCESS,
    COLOR_SURFACE_ELEVATED,
)


class MainWindow(QMainWindow):
    """Ventana principal que integra la cuadrícula dinámica, carrusel de pasos y dashboard."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrettyCalc - Calculadora de Álgebra Lineal")
        self.resize(1200, 720)
        self.setStyleSheet(get_global_stylesheet())

        self._setup_ui()

    def _setup_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("rootWidget")
        self.setCentralWidget(root_widget)

        main_layout = QVBoxLayout(root_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Barra de Encabezado y Acciones
        header_layout = QHBoxLayout()

        title_box = QVBoxLayout()
        title_lbl = QLabel("✨ PrettyCalc")
        title_lbl.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        sub_lbl = QLabel("Resolución de Sistemas de Ecuaciones Lineales con Eliminación por Filas")
        sub_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box, stretch=1)

        # Botones de Acción
        self.solve_btn = QPushButton("⚡ Resolver Sistema")
        self.solve_btn.setStyleSheet(f"""
            background-color: {COLOR_FEEDBACK_SUCCESS};
            color: #1A181B;
            font-size: 14px;
            font-weight: bold;
            padding: 8px 18px;
            border: none;
            border-radius: 6px;
        """)
        self.solve_btn.clicked.connect(self.solve_system)
        header_layout.addWidget(self.solve_btn)

        self.reset_btn = QPushButton("🧹 Reiniciar Matriz")
        self.reset_btn.clicked.connect(self.reset_matrix)
        header_layout.addWidget(self.reset_btn)

        main_layout.addLayout(header_layout)

        # 2. Contenedor Principal Dividido en 3 Columnas (Entrada | Carrusel de Pasos | Dashboard)
        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setHandleWidth(8)

        # Columna Izquierda: Entrada de Datos con Crecimiento Dinámico (Ghosting)
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        grid_title = QLabel("📝 Matriz Aumentada [A | b]")
        grid_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        left_layout.addWidget(grid_title)

        self.matrix_grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2)
        left_layout.addWidget(self.matrix_grid, stretch=1)

        # Botones de Carga Rápida de Casos de Prueba Universitarios
        samples_box = QFrame()
        samples_box.setProperty("class", "elevated-card")
        samples_layout = QVBoxLayout(samples_box)
        samples_layout.setContentsMargins(8, 8, 8, 8)
        samples_layout.setSpacing(6)

        samples_lbl = QLabel("📚 Cargar Casos Académicos de Prueba:")
        samples_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_INTERACTIVE_IDLE}; font-weight: bold;")
        samples_layout.addWidget(samples_lbl)

        btn_case1 = QPushButton("Caso 1: Solución Única (SCD)")
        btn_case1.clicked.connect(self.load_sample_case1)
        samples_layout.addWidget(btn_case1)

        btn_case2 = QPushButton("Caso 2: Infinitas Soluciones (SCI)")
        btn_case2.clicked.connect(self.load_sample_case2)
        samples_layout.addWidget(btn_case2)

        btn_case3 = QPushButton("Caso 3: Sin Solución (SI)")
        btn_case3.clicked.connect(self.load_sample_case3)
        samples_layout.addWidget(btn_case3)

        left_layout.addWidget(samples_box)
        body_splitter.addWidget(left_pane)

        # Columna Central: Carrusel / Stepper de Pasos con Pivotes Resaltados
        center_pane = QWidget()
        center_layout = QVBoxLayout(center_pane)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        steps_title = QLabel("🔍 Procedimiento Paso a Paso")
        steps_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        center_layout.addWidget(steps_title)

        self.stepper_carousel = AlgorithmStepperCarousel()
        center_layout.addWidget(self.stepper_carousel, stretch=1)
        body_splitter.addWidget(center_pane)

        # Columna Derecha: Dashboard de Resultados y Checklist de Verificación
        self.dashboard_card = ResultsDashboardCard()
        body_splitter.addWidget(self.dashboard_card)

        # Proporciones iniciales: 30% Entrada, 45% Pasos, 25% Resultados
        body_splitter.setSizes([340, 520, 340])
        main_layout.addWidget(body_splitter, stretch=1)

    def solve_system(self) -> None:
        """Ejecuta el cálculo algebraico, escalonamiento, clasificación y verificación."""
        if not self.matrix_grid.is_all_valid():
            QMessageBox.warning(
                self,
                "Error de Entrada",
                "Por favor corrige los campos en rojo antes de resolver. Solo se admiten enteros, fracciones o decimales.",
            )
            return

        try:
            augmented_mat = self.matrix_grid.get_matrix()
            split_col = augmented_mat.cols - 1

            # 1. Eliminación de Gauss-Jordan con registro de pasos
            _, tracer = gauss_jordan_elimination(augmented_mat, split_col=split_col)
            self.stepper_carousel.set_steps(tracer.get_steps())

            # 2. Clasificación formal del sistema
            analysis = classify_system(augmented_mat, split_col=split_col)

            # 3. Verificación automática por sustitución
            verifications = None
            if analysis.system_type == SystemType.CONSISTENT_DETERMINED and analysis.unique_solution:
                verifications = SolutionVerifier.verify(augmented_mat, analysis.unique_solution, split_col=split_col)
            elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED and analysis.unique_solution:
                verifications = SolutionVerifier.verify(augmented_mat, analysis.unique_solution, split_col=split_col)

            # 4. Desplegar resultados en Dashboard
            self.dashboard_card.display_results(analysis, verifications)

        except Exception as e:
            QMessageBox.critical(self, "Error Matemático", f"Ocurrió un error durante la resolución:\n{str(e)}")

    def reset_matrix(self) -> None:
        """Restablece la cuadrícula a un estado 2x2 inicial limpio."""
        self.matrix_grid.set_matrix(Matrix.zeros(2, 3))
        self.stepper_carousel.set_steps([])
        self.dashboard_card.status_badge.setText("Esperando cálculo...")
        self.dashboard_card.summary_label.setText("")
        while self.dashboard_card.var_container.count():
            w = self.dashboard_card.var_container.takeAt(0).widget()
            if w:
                w.deleteLater()
        while self.dashboard_card.checklist_container.count():
            w = self.dashboard_card.checklist_container.takeAt(0).widget()
            if w:
                w.deleteLater()

    def load_sample_case1(self) -> None:
        """Carga el Caso 1: Solución Única."""
        mat = Matrix([
            [1, 1, 1, 4],
            [2, -1, 1, 4],
            [1, 2, -1, 3],
        ])
        self.matrix_grid.set_matrix(mat)
        self.solve_system()

    def load_sample_case2(self) -> None:
        """Carga el Caso 2: Infinitas Soluciones."""
        mat = Matrix([
            [1, 2, 3, 6],
            [2, 4, 6, 12],
            [3, 6, 9, 18],
        ])
        self.matrix_grid.set_matrix(mat)
        self.solve_system()

    def load_sample_case3(self) -> None:
        """Carga el Caso 3: Sistema Sin Solución."""
        mat = Matrix([
            [1, 2, 4],
            [2, 4, 9],
        ])
        self.matrix_grid.set_matrix(mat)
        self.solve_system()


def run_app():
    """Función de arranque de la aplicación GUI."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
