"""Vista de sistemas de ecuaciones lineales (módulo Sprint 1, pulido en Sprint 10).

Sprint 10 (auditoría UI/UX, Módulo 1):

- Dimensiones directas «ecuaciones × incógnitas» además de las celdas fantasma.
- Estado de carga visible al resolver y ``Ctrl+Intro`` desde cualquier celda.
- Reiniciar y cargar un caso de prueba se pueden deshacer (aviso + ``Ctrl+Z``).
- El caso cargado queda marcado hasta que el usuario edita la matriz.
- Cramer se deshabilita con explicación cuando el sistema no es n×n y, si
  det(A) = 0, el aviso ofrece pasar a Gauss-Jordan en un clic.
- Las aplicaciones cargan la matriz y llevan la vista hasta ella.
"""

from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QGridLayout,
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
    from PySide6.QtCore import Qt, QTimer
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.classifier import classify_system
from prettycalc.core.cramer import format_cramer_component, solve_cramer
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.matrix_inversion import NonSquareMatrixError, SingularMatrixError
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.verifier import SolutionVerifier
from prettycalc.ui.feedback import busy, show_toast
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.modules.applied_models_panel import AppliedModelsPanel
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.stepper_carousel import ALERT_SYSTEM, AlgorithmStepperCarousel
from prettycalc.ui.results_dashboard import ResultsDashboardCard
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.theme import (
    apply_message_box_theme,
    COLOR_ACCENT_WARNING,
    COLOR_TEXT_PRIMARY,
    apply_widget_class,
)

#: Casos de prueba de la cátedra: (identificador, rótulo, ayuda).
_PRESETS = (
    ("case1", "I  ·  Solución única", "Sistema 3×3 compatible determinado"),
    ("case2", "II  ·  Infinitas soluciones", "Filas dependientes: compatible indeterminado"),
    ("case3", "III  ·  Sin solución", "Sistema 2×2 inconsistente"),
    ("cramer", "IV  ·  Cramer 3×3", "Solución por determinantes: x = (4, −2, 3)"),
)


class LinearSystemsView(QWidget):
    """Cuadrícula aumentada, carrusel de pasos y dashboard de clasificación."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("linearSystemsView")
        self._solver = "gauss"
        self.last_cramer = None
        self.last_applied = None
        self.active_preset: str | None = None
        self._loading_preset = False
        self._user_dirty = False
        self._setup_ui()
        self._refresh_method_state()

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

        self.matrix_card = QFrame()
        matrix_card = self.matrix_card
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
        self.size_control = MatrixSizeControl(
            self.matrix_grid,
            rows_label="Ecuaciones m",
            cols_label="Incógnitas n",
            caption="Ecuaciones × incógnitas",
            minimum=1,
            maximum=10,
        )
        card_layout.addWidget(self.size_control)
        card_layout.addWidget(self.matrix_grid, stretch=1)
        self.matrix_grid.matrixChanged.connect(self._on_grid_changed)
        self.matrix_grid.submitRequested.connect(self.solve_system)

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
        self.gauss_method_btn.setToolTip("Clasifica cualquier sistema m×n: SCD, SCI o SI")
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

        self.method_hint = QWidget()
        hint_row = QHBoxLayout(self.method_hint)
        hint_row.setContentsMargins(0, 0, 0, 0)
        hint_row.setSpacing(8)
        self.method_hint_label = QLabel("")
        self.method_hint_label.setObjectName("methodHint")
        self.method_hint_label.setWordWrap(True)
        self.method_hint_label.setStyleSheet(
            f"color: {COLOR_ACCENT_WARNING}; font-size: 13px; font-weight: 600;"
        )
        hint_row.addWidget(self.method_hint_label, stretch=1)
        self.make_square_btn = QPushButton("Igualar a n×n")
        apply_widget_class(self.make_square_btn, "link-action")
        self.make_square_btn.setToolTip("Agrega o quita ecuaciones para que haya tantas como incógnitas")
        self.make_square_btn.clicked.connect(self.make_system_square)
        hint_row.addWidget(self.make_square_btn)
        self.use_gauss_btn = QPushButton("Usar Gauss-Jordan")
        apply_widget_class(self.use_gauss_btn, "link-action")
        self.use_gauss_btn.clicked.connect(lambda: self._select_solver("gauss"))
        hint_row.addWidget(self.use_gauss_btn)
        self.method_hint.setVisible(False)
        card_layout.addWidget(self.method_hint)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.reset_btn = QPushButton("Reiniciar")
        self.reset_btn.setObjectName("secondaryAction")
        self.reset_btn.setToolTip("Vuelve a un sistema 2×2 en ceros (se puede deshacer con Ctrl+Z)")
        self.reset_btn.clicked.connect(self.reset_matrix)
        actions.addWidget(self.reset_btn)

        self.solve_btn = QPushButton("Resolver sistema")
        self.solve_btn.setObjectName("primaryAction")
        self.solve_btn.setToolTip("Resolver (Ctrl+Intro desde cualquier celda)")
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

        presets_grid = QGridLayout()
        presets_grid.setHorizontalSpacing(6)
        presets_grid.setVerticalSpacing(6)
        self.preset_group = QButtonGroup(self)
        self.preset_group.setExclusive(True)
        self.preset_buttons: dict[str, QPushButton] = {}
        loaders = {
            "case1": self.load_sample_case1,
            "case2": self.load_sample_case2,
            "case3": self.load_sample_case3,
            "cramer": self.load_cramer_sample,
        }
        for index, (key, text, tooltip) in enumerate(_PRESETS):
            button = QPushButton(text)
            button.setObjectName("secondaryAction")
            button.setCheckable(True)
            button.setToolTip(f"{tooltip}. Reemplaza la matriz actual (Ctrl+Z la recupera).")
            button.clicked.connect(loaders[key])
            self.preset_group.addButton(button, index)
            self.preset_buttons[key] = button
            presets_grid.addWidget(button, index // 2, index % 2)
        samples_layout.addLayout(presets_grid)

        self.applications_toggle = QPushButton("V  ·  Aplicaciones")
        self.applications_toggle.setObjectName("secondaryAction")
        self.applications_toggle.setCheckable(True)
        self.applications_toggle.setToolTip(
            "Química, Leontief, dieta y redes de tráfico: arman la matriz aumentada por ti"
        )
        self.applications_toggle.clicked.connect(self.toggle_applications)
        samples_layout.addWidget(self.applications_toggle)

        left_layout.addWidget(samples_box)

        self.applications_panel = AppliedModelsPanel()
        self.applications_panel.model_ready.connect(self._present_applied_model)
        self.applications_panel.setVisible(False)
        left_layout.addWidget(self.applications_panel)
        left_layout.addStretch(1)

        left_scroll = QScrollArea()
        self.left_scroll = left_scroll
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setWidget(left_pane)
        left_pane.setAutoFillBackground(False)
        left_scroll.setMinimumWidth(left_pane.minimumSizeHint().width() + 18)
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

        self.stepper_carousel = AlgorithmStepperCarousel(alert_mode=ALERT_SYSTEM)
        self.stepper_carousel.set_export_title("Sistema de ecuaciones lineales")
        self.stepper_carousel.set_empty_hint("Ingresa el sistema y pulsa Resolver.")
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

        body_splitter.setSizes([400, 520, 390])
        body_splitter.setStretchFactor(0, 2)
        body_splitter.setStretchFactor(1, 4)
        body_splitter.setStretchFactor(2, 2)
        main_layout.addWidget(body_splitter, stretch=1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    # ------------------------------------------------------------------
    # Estado de controles
    # ------------------------------------------------------------------

    def _show_alert(self, icon: QMessageBox.Icon, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Ok)
        apply_message_box_theme(box)
        box.exec()

    def _is_square_system(self) -> bool:
        rows, data_cols = self.matrix_grid.data_shape()
        return rows == data_cols - 1

    def _on_grid_changed(self) -> None:
        if not self._loading_preset:
            self._user_dirty = True
            self._clear_preset_marker()
        self._refresh_method_state()

    def _refresh_method_state(self) -> None:
        rows, data_cols = self.matrix_grid.data_shape()
        unknowns = data_cols - 1
        square = rows == unknowns
        cramer_selected = self._solver == "cramer"
        self.cramer_method_btn.setEnabled(square or cramer_selected)
        self.cramer_method_btn.setToolTip(
            "Resuelve por cocientes de determinantes x_i = det(A_i(b)) / det(A)"
            if square
            else f"Requiere matriz cuadrada n×n: ahora hay {rows} ecuaciones y {unknowns} incógnitas"
        )
        show_hint = cramer_selected and not square
        if show_hint:
            self.method_hint_label.setText(
                f"Cramer exige un sistema n×n: A es {rows}×{unknowns}."
            )
            self.make_square_btn.setText(f"Igualar a {unknowns}×{unknowns}")
        self.method_hint.setVisible(show_hint)

        valid = self.matrix_grid.is_all_valid()
        ready = valid and not show_hint
        self.solve_btn.setEnabled(ready)
        if not valid:
            self.solve_btn.setToolTip(self.matrix_grid.validation_message())
        elif show_hint:
            self.solve_btn.setToolTip("Cramer necesita tantas ecuaciones como incógnitas")
        else:
            self.solve_btn.setToolTip("Resolver (Ctrl+Intro desde cualquier celda)")

    def _on_solver_changed(self, solver_id: int) -> None:
        self._solver = "cramer" if solver_id == 1 else "gauss"
        self._refresh_method_state()

    def _select_solver(self, solver: str) -> None:
        button = self.cramer_method_btn if solver == "cramer" else self.gauss_method_btn
        button.setEnabled(True)
        button.setChecked(True)
        self._solver = solver
        self._refresh_method_state()

    def make_system_square(self) -> None:
        """Ajusta el número de ecuaciones al de incógnitas (n×n)."""
        _rows, data_cols = self.matrix_grid.data_shape()
        unknowns = data_cols - 1
        self.matrix_grid.resize_to(unknowns, data_cols)
        show_toast(
            self,
            f"El sistema ahora es {unknowns}×{unknowns}. Completa las ecuaciones nuevas.",
            kind="info",
            action_text="Deshacer",
            action=self.matrix_grid.undo,
        )

    def _clear_preset_marker(self) -> None:
        if self.active_preset is None:
            return
        self.active_preset = None
        self.preset_group.setExclusive(False)
        for button in self.preset_buttons.values():
            button.setChecked(False)
        self.preset_group.setExclusive(True)

    def _mark_preset(self, key: str) -> None:
        self.active_preset = key
        button = self.preset_buttons.get(key)
        if button is not None:
            button.setChecked(True)

    def toggle_applications(self) -> None:
        """Muestra u oculta el asistente de química, Leontief, dieta y tráfico."""
        visible = not self.applications_panel.isVisible()
        self.applications_panel.setVisible(visible)
        self.applications_toggle.setChecked(visible)
        if visible:
            QTimer.singleShot(0, lambda: self.left_scroll.ensureWidgetVisible(self.applications_panel, 0, 0))

    def _present_applied_model(self, result) -> None:
        """Carga la matriz que armó el asistente y conserva su explicación en el carrusel."""
        self.last_applied = result
        self._select_solver("gauss")
        self._load_matrix(result.augmented_matrix, preset=None, label="la matriz del modelo aplicado")
        self.solve_system()
        self.stepper_carousel.set_steps(result.tracer.get_steps())
        self.reveal_matrix()

    def reveal_matrix(self) -> None:
        """Lleva la vista a la matriz aumentada y la destaca con un destello."""
        self.left_scroll.ensureWidgetVisible(self.matrix_card, 0, 0)
        self.left_scroll.verticalScrollBar().setValue(0)
        self.matrix_grid.flash()

    # ------------------------------------------------------------------
    # Resolución
    # ------------------------------------------------------------------

    def solve_system(self) -> None:
        """Ejecuta el método seleccionado: Gauss-Jordan o la Regla de Cramer."""
        if not self.matrix_grid.is_all_valid():
            self.matrix_grid.focus_first_invalid()
            self._show_alert(
                QMessageBox.Warning,
                "Entrada inválida",
                "Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales.\n\n"
                + self.matrix_grid.validation_message(),
            )
            return

        with busy(self.solve_btn, "Resolviendo…"):
            self._solve_now()
        self._refresh_method_state()

    def _solve_now(self) -> None:
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

    def _switch_to_gauss_and_solve(self) -> None:
        self._select_solver("gauss")
        self.solve_system()

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
                action_text="Cambiar a Gauss-Jordan para clasificar",
                action=self._switch_to_gauss_and_solve,
            )
            return
        coefficients, constants_matrix = augmented.split_augmented(split_col)
        constants = Vector.from_column_matrix(constants_matrix)
        try:
            result = solve_cramer(coefficients, constants)
        except SingularMatrixError as exc:
            self.last_cramer = None
            self.stepper_carousel.set_steps([])
            self.dashboard_card.display_notice(
                "Regla de Cramer",
                f"{exc} Gauss-Jordan dirá si el sistema es indeterminado (SCI) o inconsistente (SI).",
                action_text="Cambiar a Gauss-Jordan para clasificar",
                action=self._switch_to_gauss_and_solve,
            )
            return
        except (NonSquareMatrixError, DimensionMismatchError) as exc:
            self.last_cramer = None
            self.stepper_carousel.set_steps([])
            self.dashboard_card.display_notice(
                "Regla de Cramer",
                str(exc),
                action_text="Cambiar a Gauss-Jordan para clasificar",
                action=self._switch_to_gauss_and_solve,
            )
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
                highlight_cells=tuple((row, index) for row in range(replaced.rows)),
            )
        self.stepper_carousel.set_steps(tracer.get_steps())
        verifications = SolutionVerifier.verify(
            augmented, result.solution, split_col=split_col
        )
        self.last_cramer = result
        self.dashboard_card.display_cramer(result, verifications)

    # ------------------------------------------------------------------
    # Reinicio y casos de prueba (deshacibles)
    # ------------------------------------------------------------------

    def _load_matrix(self, matrix: Matrix, *, preset: str | None, label: str) -> None:
        """Carga una matriz programáticamente y ofrece deshacer si pisó datos del usuario."""
        had_user_data = self._user_dirty and any(
            text.strip() not in ("", "0") for row in self.matrix_grid.get_raw_strings() for text in row
        )
        self._loading_preset = True
        try:
            self.matrix_grid.set_matrix(matrix)
        finally:
            self._loading_preset = False
        self._user_dirty = False
        if preset is not None:
            self._mark_preset(preset)
        else:
            self._clear_preset_marker()
        if had_user_data:
            show_toast(
                self,
                f"Se cargó {label}. Tu matriz anterior se puede recuperar.",
                kind="info",
                action_text="Deshacer",
                action=self.undo_last_load,
            )
        self._refresh_method_state()

    def undo_last_load(self) -> None:
        """Recupera la matriz previa a un reinicio o a un caso cargado."""
        if self.matrix_grid.undo():
            self._clear_preset_marker()
            self.last_cramer = None
            self.stepper_carousel.set_steps([])
            self.dashboard_card.clear()
            self._user_dirty = True

    def reset_matrix(self) -> None:
        """Restablece la cuadrícula a un estado 2×2 inicial (deshacible con Ctrl+Z)."""
        before = self.matrix_grid.snapshot()
        self.last_cramer = None
        self._loading_preset = True
        try:
            self.matrix_grid.set_matrix(Matrix.zeros(2, 3))
        finally:
            self._loading_preset = False
        self._user_dirty = False
        self._clear_preset_marker()
        self.stepper_carousel.set_steps([])
        self.dashboard_card.clear()
        self._refresh_method_state()
        if before != self.matrix_grid.snapshot():
            rows, cols, _ = before
            show_toast(
                self,
                f"Matriz reiniciada a 2×2. El sistema {rows}×{cols} anterior se puede recuperar.",
                kind="info",
                action_text="Deshacer",
                action=self.undo_last_load,
            )

    def load_sample_case1(self) -> None:
        """Caso I: solución única."""
        self._select_solver("gauss")
        self._load_matrix(Matrix([
            [1, 1, 1, 4],
            [2, -1, 1, 4],
            [1, 2, -1, 3],
        ]), preset="case1", label="el caso I")
        self.solve_system()

    def load_sample_case2(self) -> None:
        """Caso II: infinitas soluciones."""
        self._select_solver("gauss")
        self._load_matrix(Matrix([
            [1, 2, 3, 6],
            [2, 4, 6, 12],
            [3, 6, 9, 18],
        ]), preset="case2", label="el caso II")
        self.solve_system()

    def load_sample_case3(self) -> None:
        """Caso III: sistema sin solución."""
        self._select_solver("gauss")
        self._load_matrix(Matrix([
            [1, 2, 4],
            [2, 4, 9],
        ]), preset="case3", label="el caso III")
        self.solve_system()

    def load_cramer_sample(self) -> None:
        """Sesión 11, diapositivas 32 a 36: solución única por Cramer, x = (4, −2, 3)."""
        self._load_matrix(Matrix([
            [2, 4, 6, 18],
            [4, 5, 6, 24],
            [3, 1, -2, 4],
        ]), preset="cramer", label="el caso IV (Cramer)")
        self._select_solver("cramer")
        self.solve_system()
