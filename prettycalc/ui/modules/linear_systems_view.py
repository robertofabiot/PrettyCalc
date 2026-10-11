"""Vista de sistemas de ecuaciones lineales (módulo Sprint 1)."""

from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QMessageBox,
        QSplitter,
        QFrame,
        QSpacerItem,
        QSizePolicy,
        QScrollArea,
        QButtonGroup,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.classifier import classify_system
from prettycalc.core.cramer import format_cramer_component, solve_cramer
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.matrix_inversion import NonSquareMatrixError, SingularMatrixError
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.verifier import SolutionVerifier
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.modules.applied_models_panel import AppliedModelsPanel
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
from prettycalc.ui.results_dashboard import ResultsDashboardCard
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.theme import (
    apply_message_box_theme,
    COLOR_TEXT_PRIMARY,
    apply_widget_class,
)


class LinearSystemsView(QWidget):
    """Cuadrícula aumentada, carrusel de pasos y dashboard de clasificación."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("linearSystemsView")
        self._solver = "gauss"
        self.last_cramer = None
        self.last_applied = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

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

        method_row = QHBoxLayout()
        method_row.setSpacing(8)
        method_label = QLabel("Método")
        method_label.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        method_row.addWidget(method_label)
        self.solver_group = QButtonGroup(self)
        self.solver_group.setExclusive(True)
        self.gauss_method_btn = QPushButton("Gauss-Jordan")
        self.gauss_method_btn.setObjectName("modeToggle")
        self.gauss_method_btn.setCheckable(True)
        self.gauss_method_btn.setChecked(True)
        self.cramer_method_btn = QPushButton("Regla de Cramer")
        self.cramer_method_btn.setObjectName("modeToggle")
        self.cramer_method_btn.setCheckable(True)
        self.solver_group.addButton(self.gauss_method_btn, 0)
        self.solver_group.addButton(self.cramer_method_btn, 1)
        self.solver_group.idClicked.connect(self._on_solver_changed)
        method_row.addWidget(self.gauss_method_btn)
        method_row.addWidget(self.cramer_method_btn)
        method_row.addStretch(1)
        card_layout.addLayout(method_row)

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
        btn_case1.setObjectName("secondaryAction")
        btn_case1.clicked.connect(self.load_sample_case1)
        samples_layout.addWidget(btn_case1)

        btn_case2 = QPushButton("II  ·  Infinitas soluciones")
        btn_case2.setObjectName("secondaryAction")
        btn_case2.clicked.connect(self.load_sample_case2)
        samples_layout.addWidget(btn_case2)

        btn_case3 = QPushButton("III  ·  Sin solución")
        btn_case3.setObjectName("secondaryAction")
        btn_case3.clicked.connect(self.load_sample_case3)
        samples_layout.addWidget(btn_case3)

        btn_cramer = QPushButton("IV  ·  Cramer 3×3")
        btn_cramer.setObjectName("secondaryAction")
        btn_cramer.clicked.connect(self.load_cramer_sample)
        samples_layout.addWidget(btn_cramer)

        self.applications_toggle = QPushButton("V  ·  Aplicaciones")
        self.applications_toggle.setObjectName("secondaryAction")
        self.applications_toggle.clicked.connect(self.toggle_applications)
        samples_layout.addWidget(self.applications_toggle)

        left_layout.addWidget(samples_box)

        self.applications_panel = AppliedModelsPanel()
        self.applications_panel.model_ready.connect(self._present_applied_model)
        self.applications_panel.setVisible(False)
        left_layout.addWidget(self.applications_panel)
        left_layout.addStretch(1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setWidget(left_pane)
        left_pane.setAutoFillBackground(False)
        body_splitter.addWidget(left_scroll)

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

        self.dashboard_card = ResultsDashboardCard()
        right_scroll = QScrollArea()
        right_scroll.setObjectName("resultsScroll")
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setWidget(self.dashboard_card)
        body_splitter.addWidget(right_scroll)

        body_splitter.setSizes([360, 540, 380])
        body_splitter.setStretchFactor(0, 2)
        body_splitter.setStretchFactor(1, 4)
        body_splitter.setStretchFactor(2, 2)
        main_layout.addWidget(body_splitter, stretch=1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    def _show_alert(self, icon: QMessageBox.Icon, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Ok)
        apply_message_box_theme(box)
        box.exec()

    def _on_solver_changed(self, solver_id: int) -> None:
        self._solver = "cramer" if solver_id == 1 else "gauss"

    def toggle_applications(self) -> None:
        """Muestra u oculta el asistente de química, Leontief, dieta y tráfico."""
        self.applications_panel.setVisible(not self.applications_panel.isVisible())

    def _present_applied_model(self, result) -> None:
        """Carga la matriz que armó el asistente y conserva su explicación en el carrusel."""
        self.last_applied = result
        self.gauss_method_btn.setChecked(True)
        self._solver = "gauss"
        self.matrix_grid.set_matrix(result.augmented_matrix)
        self.solve_system()
        self.stepper_carousel.set_steps(result.tracer.get_steps())

    def solve_system(self) -> None:
        """Ejecuta el método seleccionado: Gauss-Jordan o la Regla de Cramer."""
        if not self.matrix_grid.is_all_valid():
            self._show_alert(
                QMessageBox.Warning,
                "Entrada inválida",
                "Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales.",
            )
            return

        try:
            augmented_mat = self.matrix_grid.get_matrix()
            if self._solver == "cramer":
                self._solve_with_cramer(augmented_mat)
                return
            split_col = augmented_mat.cols - 1

            _, tracer = gauss_jordan_elimination(augmented_mat, split_col=split_col)
            self.stepper_carousel.set_steps(tracer.get_steps())

            analysis = classify_system(augmented_mat, split_col=split_col)

            verifications = None
            if analysis.unique_solution is not None:
                verifications = SolutionVerifier.verify(
                    augmented_mat, analysis.unique_solution, split_col=split_col
                )

            self.last_cramer = None
            self.dashboard_card.display_results(analysis, verifications)

        except Exception as e:
            self._show_alert(
                QMessageBox.Critical,
                "Error matemático",
                f"No se pudo resolver el sistema:\n{e}",
            )

    def _solve_with_cramer(self, augmented: Matrix) -> None:
        """Resuelve un sistema n×n por cocientes de determinantes."""
        split_col = augmented.cols - 1
        if augmented.rows != split_col:
            self.last_cramer = None
            self.stepper_carousel.set_steps([])
            self.dashboard_card.display_notice(
                "Regla de Cramer",
                "La Regla de Cramer exige un sistema n×n: la matriz de coeficientes "
                f"A es {augmented.rows}×{split_col}. Hace falta el mismo número de "
                "ecuaciones y de incógnitas.",
            )
            return
        coefficients, constants_matrix = augmented.split_augmented(split_col)
        constants = Vector.from_column_matrix(constants_matrix)
        try:
            result = solve_cramer(coefficients, constants)
        except SingularMatrixError as exc:
            self.last_cramer = None
            self.stepper_carousel.set_steps([])
            self.dashboard_card.display_notice("Regla de Cramer", str(exc))
            return
        except (NonSquareMatrixError, DimensionMismatchError) as exc:
            self.last_cramer = None
            self.stepper_carousel.set_steps([])
            self.dashboard_card.display_notice("Regla de Cramer", str(exc))
            return

        tracer = StepTracer()
        tracer.record_initial(
            coefficients,
            description=(
                f"Matriz de coeficientes A. det(A) = {format_scalar(result.det_A)}. "
                "Como el determinante no es cero, existe una única solución."
            ),
            latex_title=r"\det(A)",
        )
        for index, replaced, column_det in result.column_determinants:
            tracer.record_step(
                matrix=replaced,
                latex_formula=rf"\det(A_{{{index + 1}}}(b))",
                heuristic_text=format_cramer_component(
                    index, column_det, result.det_A, result.solution[index]
                ),
            )
        self.stepper_carousel.set_steps(tracer.get_steps())
        verifications = SolutionVerifier.verify(
            augmented, result.solution, split_col=split_col
        )
        self.last_cramer = result
        self.dashboard_card.display_cramer(result, verifications)

    def reset_matrix(self) -> None:
        """Restablece la cuadrícula a un estado 2×2 inicial."""
        self.last_cramer = None
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

    def load_cramer_sample(self) -> None:
        """Sesión 11, diapositivas 32 a 36: solución única por Cramer, x = (4, −2, 3)."""
        self.cramer_method_btn.setChecked(True)
        self._solver = "cramer"
        self.matrix_grid.set_matrix(Matrix([
            [2, 4, 6, 18],
            [4, 5, 6, 24],
            [3, 1, -2, 4],
        ]))
        self.solve_system()
