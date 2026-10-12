"""Módulo 6: factorización LU (PA = LU) y resolución en dos etapas.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).

Sprint 10 (auditoría UI/UX, Módulo 6):

- Tamaño de A con spinboxes directos m × n (sin modales al redimensionar).
- Las filas que la permutación P movió se marcan en ocre sobre A.
- Etapa 1, etapa 2 y clasificación en pestañas: los carruseles ya no se
  comprimen en cuatro columnas a 1366 px.
- Si U tiene un pivote nulo (o A no es cuadrada), «Clasificar A x = b»
  muestra el tablero de resultados de los Módulos 1 y 4 con las variables
  libres y la solución paramétrica.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
        QSplitter,
        QScrollArea,
        QTabWidget,
    )
    from PySide6.QtCore import Qt, QTimer
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.classifier import SystemType, classify_system
from prettycalc.core.lu_decomposition import (
    LUPivotZeroError,
    LUSingularError,
    PLUFactorizationResult,
    PLUSystemSolutionResult,
    plu_decompose,
    solve_from_plu_factorization,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.mathtext import plain_formula_to_html
from prettycalc.ui.results_dashboard import ResultsDashboardCard
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_widget_class,
    badge_style,
    idle_badge_style,
)

MAX_LU_DIMENSION = 8

_EXAMPLE1_A = Matrix([
    [3, -7, -2],
    [-3, 5, 1],
    [6, -4, 0],
])
_EXAMPLE1_B = Matrix([[-7], [5], [2]])

_EXAMPLE2_A = Matrix([
    [3, -7, -2, 2],
    [-3, 5, 1, 0],
    [6, -4, 0, -5],
    [-9, 5, -5, 12],
])
_EXAMPLE2_B = Matrix([[-9], [5], [7], [11]])

_EXAMPLE3_A = Matrix([
    [2, 4, -1, 5, -2],
    [-4, -5, 3, -8, 1],
    [2, -5, -4, 1, 8],
    [-6, 0, 7, -3, 1],
])


def _badge_style(background: str, _foreground: str = "") -> str:
    """Badge con el texto de mejor contraste (tokens del tema)."""
    return badge_style(background)


def permuted_rows(P: Matrix) -> list[int]:
    """Filas de A que la permutación P movió de lugar (índices 0-based)."""
    moved = []
    for row in range(P.rows):
        source = next((col for col in range(P.cols) if P.get(row, col) == 1), row)
        if source != row:
            moved.append(source)
    return sorted(moved)


def _matrix_inline(matrix: Matrix) -> str:
    rows = matrix.to_str_list(mode="fraction")
    return "  |  ".join("  ".join(row) for row in rows)


def _vector_inline(vector: Vector) -> str:
    shown = ", ".join(format_scalar(component, mode="fraction") for component in vector)
    return f"[{shown}]ᵀ"


def _book_step_lines(lines: list[str]) -> str:
    """Sustituciones y_1, b_1, x_1 en HTML de libro, una etapa por renglón."""
    return "<br>".join(plain_formula_to_html(line) for line in lines)


class LUFactorizationView(QWidget):
    """Entrada de A, factores L y U en paralelo, y las dos sustituciones."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("luFactorizationView")
        self._syncing_b = False
        self.last_factorization: Optional[PLUFactorizationResult] = None
        self.last_solution: Optional[PLUSystemSolutionResult] = None
        self._setup_ui()
        self.grid.matrixChanged.connect(self._on_a_changed)
        self.b_grid.matrixChanged.connect(self._on_b_changed)
        self._sync_b()
        self._sync_controls(refresh_badge=True)

    def _setup_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.grid = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.size_control = MatrixSizeControl(
            self.grid,
            rows_label="Filas m",
            cols_label="Columnas n",
            caption="Tamaño de A",
            minimum=1,
            maximum=MAX_LU_DIMENSION,
        )
        controls.addWidget(self.size_control)
        self.shape_label = QLabel("3 × 3")
        self.shape_label.setObjectName("luShapeLabel")
        self.shape_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        controls.addWidget(self.shape_label)
        controls.addStretch(1)

        self.example1_btn = QPushButton("Ejemplo 1 (3×3)")
        self.example1_btn.setObjectName("secondaryAction")
        self.example1_btn.clicked.connect(self.load_example_1)
        self.example2_btn = QPushButton("Ejemplo 2 (4×4)")
        self.example2_btn.setObjectName("secondaryAction")
        self.example2_btn.clicked.connect(self.load_example_2)
        self.example3_btn = QPushButton("Ejemplo 3 (4×5)")
        self.example3_btn.setObjectName("secondaryAction")
        self.example3_btn.clicked.connect(self.load_example_3)
        for button, tip in (
            (self.example1_btn, "Sesión 12: x = [3, 4, −6]ᵀ"),
            (self.example2_btn, "Sesión 12: matriz 4×4"),
            (self.example3_btn, "Sesión 12: A rectangular 4×5 (una columna sin pivote)"),
        ):
            button.setToolTip(tip)
            button.setCursor(Qt.PointingHandCursor)
        self.decompose_btn = QPushButton("Descomponer A = LU")
        self.decompose_btn.setObjectName("primaryAction")
        self.decompose_btn.setToolTip("Calcula P, L y U (Ctrl+Enter desde A)")
        self.decompose_btn.clicked.connect(self.decompose)
        self.solve_btn = QPushButton("Resolver Ly = b y Ux = y")
        self.solve_btn.setObjectName("primaryAction")
        self.solve_btn.setToolTip("Reutiliza L y U para resolver con el b actual (Ctrl+Enter desde b)")
        self.solve_btn.clicked.connect(self.solve)
        controls.addWidget(self.decompose_btn)
        controls.addWidget(self.solve_btn)
        root.addLayout(controls)

        examples_row = QHBoxLayout()
        examples_row.setSpacing(8)
        examples_caption = QLabel("Ejemplos de la Sesión 12")
        examples_caption.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        examples_row.addWidget(examples_caption)
        for button in (self.example1_btn, self.example2_btn, self.example3_btn):
            examples_row.addWidget(button)
        examples_row.addStretch(1)
        root.addLayout(examples_row)

        self.badge = QLabel("")
        self.badge.setObjectName("luBadge")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        root.addWidget(self.badge)

        upper = QSplitter(Qt.Horizontal)
        upper.setHandleWidth(10)
        upper.setChildrenCollapsible(False)
        upper.setMinimumHeight(380)

        left_card = QFrame()
        apply_widget_class(left_card, "elevated-card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._section_title("Matriz A"))
        self.grid.submitRequested.connect(self.decompose)
        left_layout.addWidget(self.grid, stretch=1)
        self.swap_legend = QLabel("")
        self.swap_legend.setObjectName("luSwapLegend")
        self.swap_legend.setWordWrap(True)
        self.swap_legend.setStyleSheet(f"color: {COLOR_ACCENT_WARNING}; font-size: 14px; font-weight: 600;")
        self.swap_legend.setVisible(False)
        left_layout.addWidget(self.swap_legend)
        upper.addWidget(self._scroll(left_card))

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        center_layout.addWidget(self._section_title("Construcción de L y U"))
        self.factor_stepper = AlgorithmStepperCarousel(variable_headers=False)
        self.factor_stepper.setObjectName("luFactorStepper")
        center_layout.addWidget(self.factor_stepper, stretch=1)
        upper.addWidget(center)

        right_card = QFrame()
        apply_widget_class(right_card, "elevated-card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(8)
        right_layout.addWidget(self._section_title("Factores"))
        self.p_view, self.p_readout = self._matrix_block(right_layout, "P  matriz de permutación", "pReadout")
        self.permutation_note = QLabel("")
        self.permutation_note.setObjectName("luPermutationNote")
        self.permutation_note.setWordWrap(True)
        self.permutation_note.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )
        right_layout.addWidget(self.permutation_note)
        self.l_view, self.l_readout = self._matrix_block(right_layout, "L  triangular inferior unitaria", "lReadout")
        self.u_view, self.u_readout = self._matrix_block(right_layout, "U  forma escalonada", "uReadout")
        self.checklist_label = QLabel("L · U = A")
        self.checklist_label.setObjectName("luChecklist")
        self.checklist_label.setWordWrap(True)
        self.checklist_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 16px; font-weight: 600;"
        )
        right_layout.addWidget(self.checklist_label)
        self.multiplier_label = QLabel("")
        self.multiplier_label.setObjectName("luMultiplierLabel")
        self.multiplier_label.setWordWrap(True)
        self.multiplier_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px;")
        right_layout.addWidget(self.multiplier_label)
        right_layout.addStretch(1)
        upper.addWidget(self._scroll(right_card))
        upper.setSizes([360, 520, 420])
        self.upper_splitter = upper
        root.addWidget(upper)

        root.addWidget(self._section_title("Solución en dos etapas"))
        lower = QSplitter(Qt.Horizontal)
        lower.setHandleWidth(10)
        lower.setChildrenCollapsible(False)
        lower.setMinimumHeight(420)

        b_card = QFrame()
        apply_widget_class(b_card, "elevated-card")
        b_layout = QVBoxLayout(b_card)
        b_layout.setContentsMargins(16, 14, 16, 14)
        b_layout.setSpacing(8)
        b_layout.addWidget(self._section_title("Vector b"))
        self.b_grid = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=1,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.b_grid.submitRequested.connect(self.solve)
        b_layout.addWidget(self.b_grid, 0, Qt.AlignTop)
        b_layout.addStretch(1)
        lower.addWidget(self._scroll(b_card))

        self.stage_tabs = QTabWidget()
        self.stage_tabs.setObjectName("luStageTabs")
        forward_box = QWidget()
        forward_layout = QVBoxLayout(forward_box)
        forward_layout.setContentsMargins(8, 8, 8, 8)
        forward_layout.setSpacing(8)
        self.forward_title = self._section_title("Etapa 1 · Ly = b")
        forward_layout.addWidget(self.forward_title)
        self.forward_stepper = AlgorithmStepperCarousel()
        self.forward_stepper.setObjectName("luForwardStepper")
        self.forward_stepper.set_export_title("LU · etapa 1 (sustitución hacia adelante)")
        self.forward_stepper.set_empty_hint("Descompón A y pulsa Resolver.")
        forward_layout.addWidget(self.forward_stepper, stretch=1)
        self.forward_steps_label = self._steps_label("forwardStepsLabel")
        forward_layout.addWidget(self.forward_steps_label)
        self.stage_tabs.addTab(forward_box, "Etapa 1 · Ly = b")

        backward_box = QWidget()
        backward_layout = QVBoxLayout(backward_box)
        backward_layout.setContentsMargins(8, 8, 8, 8)
        backward_layout.setSpacing(8)
        backward_layout.addWidget(self._section_title("Etapa 2 · Ux = y"))
        self.backward_stepper = AlgorithmStepperCarousel()
        self.backward_stepper.setObjectName("luBackwardStepper")
        self.backward_stepper.set_export_title("LU · etapa 2 (sustitución hacia atrás)")
        self.backward_stepper.set_empty_hint("Descompón A y pulsa Resolver.")
        backward_layout.addWidget(self.backward_stepper, stretch=1)
        self.backward_steps_label = self._steps_label("backwardStepsLabel")
        backward_layout.addWidget(self.backward_steps_label)
        self.stage_tabs.addTab(backward_box, "Etapa 2 · Ux = y")

        classify_box = QWidget()
        classify_layout = QVBoxLayout(classify_box)
        classify_layout.setContentsMargins(8, 8, 8, 8)
        classify_layout.setSpacing(8)
        self.classify_hint = QLabel(
            "Si U tiene un pivote nulo o A no es cuadrada, no hay solución única por sustitución. "
            "Clasifica A x = b para ver si es inconsistente o tiene infinitas soluciones."
        )
        self.classify_hint.setWordWrap(True)
        self.classify_hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        classify_layout.addWidget(self.classify_hint)
        self.classify_btn = QPushButton("Clasificar A x = b")
        self.classify_btn.setObjectName("secondaryAction")
        self.classify_btn.setCursor(Qt.PointingHandCursor)
        self.classify_btn.clicked.connect(self.classify)
        self.classify_btn.setEnabled(False)
        classify_layout.addWidget(self.classify_btn, 0, Qt.AlignLeft)
        self.dashboard = ResultsDashboardCard()
        classify_layout.addWidget(self.dashboard, stretch=1)
        self.stage_tabs.addTab(classify_box, "Clasificación")
        lower.addWidget(self.stage_tabs)

        answer_card = QFrame()
        apply_widget_class(answer_card, "elevated-card")
        answer_layout = QVBoxLayout(answer_card)
        answer_layout.setContentsMargins(16, 14, 16, 14)
        answer_layout.setSpacing(8)
        answer_layout.addWidget(self._section_title("Solución"))
        self.pb_label = QLabel("")
        self.pb_label.setObjectName("luPermutedLoad")
        self.pb_label.setWordWrap(True)
        self.pb_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-family: {FONT_FAMILY_MONO};"
        )
        answer_layout.addWidget(self.pb_label)
        self.y_view, self.y_label = self._matrix_block(answer_layout, "Vector intermedio y", "yReadout")
        self.x_view, self.x_label = self._matrix_block(answer_layout, "Solución x", "xReadout")
        self.ax_label = QLabel("A · x = b")
        self.ax_label.setObjectName("luAxChecklist")
        self.ax_label.setWordWrap(True)
        self.ax_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 16px; font-weight: 600;"
        )
        answer_layout.addWidget(self.ax_label)
        answer_layout.addStretch(1)
        lower.addWidget(self._scroll(answer_card))
        lower.setSizes([220, 760, 320])
        root.addWidget(lower)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;")
        return label

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        return label

    def _steps_label(self, name: str) -> QLabel:
        label = QLabel("")
        label.setObjectName(name)
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-family: {FONT_FAMILY_MONO};"
        )
        return label

    def _matrix_block(self, layout: QVBoxLayout, title: str, readout_name: str):
        caption = QLabel(title)
        caption.setWordWrap(True)
        caption.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 600; margin-top: 6px;"
        )
        layout.addWidget(caption)
        view = BookMatrixWidget()
        view.setMinimumHeight(140)
        layout.addWidget(view)
        readout = QLabel("")
        readout.setObjectName(readout_name)
        readout.setWordWrap(True)
        readout.setTextInteractionFlags(Qt.TextSelectableByMouse)
        readout.setStyleSheet(
            f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 14px; font-family: {FONT_FAMILY_MONO};"
        )
        layout.addWidget(readout)
        return view, readout

    @staticmethod
    def _scroll(card: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(card)
        return scroll

    def _fit_matrix_panel(self) -> None:
        """Ensancha el panel de A si la matriz no cabe (p. ej. 4×5), a costa del panel de factores."""
        sizes = self.upper_splitter.sizes()
        if len(sizes) != 3 or sum(sizes) == 0:
            return
        panel = self.upper_splitter.widget(0)
        card = panel.widget() if isinstance(panel, QScrollArea) else panel
        need = max(self.grid.sizeHint().width() + 48, card.minimumSizeHint().width() + 4)
        if sizes[0] >= need:
            return
        extra = need - sizes[0]
        take_right = min(extra, max(0, sizes[2] - 260))
        take_center = extra - take_right
        self.upper_splitter.setSizes([need, max(300, sizes[1] - take_center), sizes[2] - take_right])

    def _on_a_changed(self) -> None:
        # El tamaño de la cuadrícula se conoce cuando su layout se activa.
        QTimer.singleShot(0, self, self._fit_matrix_panel)
        self._clear_results()
        self._sync_b()
        self._sync_controls(refresh_badge=True)

    def _on_b_changed(self) -> None:
        if self._syncing_b:
            return
        had_solution = self.last_solution is not None
        self._clear_solution()
        self._sync_controls()
        if had_solution and self.last_factorization is not None:
            self.badge.setText("b cambió. L y U se reutilizan: vuelve a resolver las dos etapas.")
            self.badge.setStyleSheet(idle_badge_style())

    def _clear_solution(self) -> None:
        self.last_solution = None
        self.forward_stepper.set_steps([])
        self.backward_stepper.set_steps([])
        self.forward_steps_label.setText("")
        self.backward_steps_label.setText("")
        self.y_view.clear()
        self.x_view.clear()
        self.y_label.setText("")
        self.x_label.setText("")
        self.pb_label.setText("")
        self.forward_title.setText("Etapa 1 · Ly = b")
        self.stage_tabs.setTabText(0, "Etapa 1 · Ly = b")
        self.ax_label.setText("A · x = b")
        self.ax_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 16px; font-weight: 600;"
        )
        self.dashboard.clear()

    def _clear_results(self) -> None:
        self.last_factorization = None
        self.factor_stepper.set_steps([])
        self.l_view.clear()
        self.u_view.clear()
        self.p_view.clear()
        self.l_readout.setText("")
        self.u_readout.setText("")
        self.p_readout.setText("")
        self.permutation_note.setText("")
        self.checklist_label.setText("L · U = A")
        self.checklist_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 16px; font-weight: 600;"
        )
        self.multiplier_label.setText("")
        self.grid.set_alert_rows([])
        self.swap_legend.setVisible(False)
        self._clear_solution()

    def _blocking_reason(self) -> Optional[str]:
        message = self.grid.validation_message()
        if message:
            return f"A, {message[0].lower()}{message[1:]}"
        matrix = self.grid.get_matrix()
        if matrix.rows > MAX_LU_DIMENSION or matrix.cols > MAX_LU_DIMENSION:
            return f"Cada dimensión debe estar entre 1 y {MAX_LU_DIMENSION}."
        return None

    def _can_classify(self) -> bool:
        """Hay factores, b es válido y la sustitución no da solución única."""
        factorization = self.last_factorization
        if factorization is None or not self.b_grid.is_all_valid():
            return False
        if self.b_grid.data_shape()[0] != factorization.original.rows:
            return False
        return not self._can_solve()

    def _can_solve(self) -> bool:
        factorization = self.last_factorization
        if factorization is None or not self.b_grid.is_all_valid():
            return False
        original = factorization.original
        if original.rows != original.cols:
            return False
        if any(factorization.U.get(index, index) == 0 for index in range(original.rows)):
            return False
        load = self.b_grid.get_matrix()
        return load.rows == original.rows and load.cols == 1

    def _sync_b(self) -> None:
        if not self.grid.is_all_valid():
            return
        rows = self.grid.get_matrix().rows
        if (
            self.b_grid.is_all_valid()
            and self.b_grid.get_matrix().shape == (rows, 1)
        ):
            return
        values = []
        if self.b_grid.is_all_valid():
            current = self.b_grid.get_matrix()
            for row_index in range(rows):
                if row_index < current.rows and current.cols >= 1:
                    values.append([current.get(row_index, 0)])
                else:
                    values.append([0])
        else:
            values = [[0] for _ in range(rows)]
        self._syncing_b = True
        try:
            self.b_grid.set_matrix(Matrix(values))
        finally:
            self._syncing_b = False

    def _sync_controls(self, refresh_badge: bool = False) -> None:
        rows, cols = self.grid.data_shape()
        kind = "cuadrada" if rows == cols else "rectangular"
        self.shape_label.setText(f"A es {rows} × {cols} ({kind})")
        reason = self._blocking_reason()
        self.decompose_btn.setEnabled(reason is None)
        self.solve_btn.setEnabled(reason is None and self._can_solve())
        self.classify_btn.setEnabled(reason is None and self._can_classify())
        if reason is not None:
            self.badge.setText(reason)
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))
        elif refresh_badge and self.last_factorization is None and self.last_solution is None:
            self.badge.setText("Matriz lista para descomponer A = LU.")
            self.badge.setStyleSheet(idle_badge_style())

    def load_example_1(self) -> None:
        """Sesión 12, diapositivas 6 a 10. x = [3, 4, −6]ᵀ."""
        self.grid.set_matrix(_EXAMPLE1_A)
        self.b_grid.set_matrix(_EXAMPLE1_B)
        self.decompose()
        self.solve()

    def load_example_2(self) -> None:
        """Sesión 12, diapositivas 11 a 15. x = [3, 4, −6, −1]ᵀ."""
        self.grid.set_matrix(_EXAMPLE2_A)
        self.b_grid.set_matrix(_EXAMPLE2_B)
        self.decompose()
        self.solve()

    def load_example_3(self) -> None:
        """Sesión 12, diapositivas 17 a 22. A es 4×5 y una columna no tiene pivote."""
        self.grid.set_matrix(_EXAMPLE3_A)
        self.decompose()

    def decompose(self) -> None:
        """Calcula P, L y U y comprueba P · A = L · U. Si P = I, eso es A = L U."""
        reason = self._blocking_reason()
        if reason is not None:
            self.badge.setText(reason)
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))
            self.decompose_btn.setEnabled(False)
            return
        matrix = self.grid.get_matrix()
        factorization = plu_decompose(matrix)
        self.last_factorization = factorization
        self._publish_factors(factorization)
        self._sync_controls()

    def solve(self) -> None:
        """Reutiliza L y U para resolver Ly = b y después Ux = y."""
        if self.last_factorization is None:
            self.decompose()
        if self.last_factorization is None:
            return
        if not self.b_grid.is_all_valid():
            cell = self.b_grid.first_invalid_cell()
            detail = f" (componente {cell.row + 1}: {cell.error_message})" if cell is not None else ""
            self.badge.setText(f"Corrige las celdas del vector b{detail}.")
            self.b_grid.focus_first_invalid()
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))
            return
        load = Vector.from_column_matrix(self.b_grid.get_matrix())
        try:
            solution = solve_from_plu_factorization(self.last_factorization, load)
        except (LUSingularError, LUPivotZeroError, NonSquareMatrixError, DimensionMismatchError, ValueError) as exc:
            self._clear_solution()
            tracer = getattr(exc, "tracer", None)
            if tracer is not None:
                target = self.backward_stepper if "x_" in str(exc) else self.forward_stepper
                target.set_steps(tracer.get_steps())
            self.badge.setText(str(exc))
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))
            self._sync_controls()
            return
        self.last_solution = solution
        self._publish_solution(solution)
        self._sync_controls()

    def _publish_factors(self, factorization: PLUFactorizationResult) -> None:
        self._show_matrix(self.p_view, self.p_readout, factorization.P)
        self._show_matrix(self.l_view, self.l_readout, factorization.L)
        self._show_matrix(self.u_view, self.u_readout, factorization.U)
        self.factor_stepper.set_steps(factorization.tracer.get_steps())
        count = len(factorization.multipliers_table)
        self.multiplier_label.setText(
            f"{count} multiplicador{'es' if count != 1 else ''} guardado{'s' if count != 1 else ''} en L."
        )
        swapped = factorization.permutation_count > 0
        moved = permuted_rows(factorization.P) if swapped else []
        self.grid.set_alert_rows(moved)
        if moved:
            self.swap_legend.setText(
                "Filas de A que P cambió de lugar: "
                + ", ".join(str(row + 1) for row in moved)
                + " (resaltadas en ocre)."
            )
        self.swap_legend.setVisible(bool(moved))
        if swapped:
            self.permutation_note.setText(
                f"Se intercambiaron filas {factorization.permutation_count} "
                f"{'vez' if factorization.permutation_count == 1 else 'veces'}. "
                "La identidad es P · A = L · U. Al resolver se usa el vector Pb."
            )
            identity_text = "✓  P · A = L · U" if factorization.is_valid else "P · A no coincide con L · U"
        else:
            self.permutation_note.setText("No se requirieron permutaciones de fila (A = LU).")
            identity_text = "✓  L · U = A" if factorization.is_valid else "L · U no coincide con A"
        if factorization.is_valid:
            self.checklist_label.setText(identity_text)
            self.checklist_label.setStyleSheet(
                f"color: {COLOR_FEEDBACK_SUCCESS}; font-size: 16px; font-weight: 600;"
            )
        else:
            self.checklist_label.setText(identity_text)
            self.checklist_label.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-size: 16px; font-weight: 600;"
            )

        original = factorization.original
        singular = (
            original.rows == original.cols
            and any(factorization.U.get(index, index) == 0 for index in range(original.rows))
        )
        if not factorization.is_valid:
            self.badge.setText("La comprobación P · A = L · U no cerró.")
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))
        elif factorization.permutation_count > 0 and original.rows == original.cols and not singular:
            self.badge.setText(
                "P · A = L · U verificada. Hay permutación de filas: la primera etapa resuelve L y = P b."
            )
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS))
        elif original.rows != original.cols:
            self.badge.setText(
                f"A = LU verificada. A es {original.rows}×{original.cols}: "
                "la solución única en dos etapas pide una matriz cuadrada."
            )
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS))
        elif singular:
            self.badge.setText(
                "A = LU verificada, pero U tiene un pivote diagonal nulo. "
                "Ax = b no tiene solución única por sustitución hacia atrás: usa «Clasificar A x = b»."
            )
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))
        else:
            self.badge.setText("A = LU verificada. Ya se puede resolver Ly = b y Ux = y.")
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS))

    def _publish_solution(self, solution: PLUSystemSolutionResult) -> None:
        self.y_view.set_matrix(solution.y_intermediate.to_column_matrix(), show_headers=False)
        self.x_view.set_matrix(solution.x_solution.to_column_matrix(), show_headers=False)
        self.y_label.setText(f"y = {_vector_inline(solution.y_intermediate)}")
        self.x_label.setText(f"x = {_vector_inline(solution.x_solution)}")
        self.forward_steps_label.setText(_book_step_lines(solution.forward_steps))
        self.backward_steps_label.setText(_book_step_lines(solution.backward_steps))
        self.forward_stepper.set_steps(solution.forward_tracer.get_steps())
        self.backward_stepper.set_steps(solution.backward_tracer.get_steps())
        swapped = solution.factorization.permutation_count > 0
        self.forward_title.setText("Etapa 1 · Ly = Pb" if swapped else "Etapa 1 · Ly = b")
        self.stage_tabs.setTabText(0, "Etapa 1 · Ly = Pb" if swapped else "Etapa 1 · Ly = b")
        if swapped:
            self.pb_label.setText(f"Pb = {_vector_inline(solution.permuted_b)}")
        else:
            self.pb_label.setText("P = I, así que Pb = b.")
        if solution.verification_passed:
            self.ax_label.setText("✓  A · x = b")
            self.ax_label.setStyleSheet(
                f"color: {COLOR_FEEDBACK_SUCCESS}; font-size: 16px; font-weight: 600;"
            )
            stage = "L y = P b" if swapped else "L y = b"
            self.badge.setText(
                f"x = {_vector_inline(solution.x_solution)}. "
                f"Se comprobó {stage}, U x = y y A x = b."
            )
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS))
        else:
            self.ax_label.setText("A · x no coincide con b")
            self.ax_label.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-size: 16px; font-weight: 600;"
            )
            self.badge.setText("La sustitución terminó, pero la comprobación A · x = b no cerró.")
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR))

    @staticmethod
    def _show_matrix(view: BookMatrixWidget, readout: QLabel, matrix: Matrix) -> None:
        view.set_matrix(matrix, show_headers=False)
        readout.setText(_matrix_inline(matrix))

    def classify(self) -> None:
        """Clasifica [A | b] cuando la sustitución no da solución única (SCI o SI)."""
        if not self._can_classify():
            return
        a = self.grid.get_matrix()
        b = self.b_grid.get_matrix()
        augmented = Matrix([[*(a.get(r, c) for c in range(a.cols)), b.get(r, 0)] for r in range(a.rows)])
        analysis = classify_system(augmented, split_col=a.cols)
        self.dashboard.display_results(analysis)
        self.stage_tabs.setCurrentIndex(2)
        names = {
            SystemType.CONSISTENT_DETERMINED: "solución única",
            SystemType.CONSISTENT_INDETERMINED: "infinitas soluciones",
            SystemType.INCONSISTENT: "sin solución",
        }
        show_toast(self, f"A x = b: {names.get(analysis.system_type, 'clasificado')}.", kind="info")
