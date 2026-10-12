"""Módulo 5: determinantes, Sarrus, cofactores de Laplace, adjunta y propiedades.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).

Sprint 10 (auditoría UI/UX, Módulo 5):

- Orden n con un spinbox directo (2 → 7 en un paso) y sin diálogos modales.
- Sarrus en una matriz que no es 3×3 ofrece «Ajustar a 3×3» (badge y aviso)
  y, al calcular, dibuja el esquema de diagonales que sigue al carrusel.
- Laplace resalta en A la fila o columna de expansión y sugiere la que tiene
  más ceros.
- Menores, cofactores, adjunta e inversa en pestañas, con «Usar A⁻¹ como A»
  y «Enviar A⁻¹ a Matrices».
- Propiedades: B al lado de A, escalar k con el campo común y el desglose
  kⁿ = 2² = 4 ⇒ 4 · 9 = 36.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QButtonGroup,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.adjugate import AdjugateResult, calculate_adjugate_and_inverse
from prettycalc.core.determinants import (
    DeterminantMethod,
    DeterminantPropertiesResult,
    DeterminantResult,
    best_expansion_line,
    matrix_determinant,
    scaling_breakdown,
    singularity_diagnosis,
    verify_determinant_properties,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.responsive import ResponsiveRow
from prettycalc.ui.sarrus_diagram import SarrusDiagram
from prettycalc.ui.scalar_field import CANONICAL_SCALARS, ScalarField, ScalarInput
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.stepper_carousel import ALERT_SINGULAR, AlgorithmStepperCarousel
from prettycalc.ui.theme import (
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

MAX_DETERMINANT_ORDER = 8

_SESSION11_MATRIX = Matrix([
    [1, 3, -3],
    [2, 0, 1],
    [-1, 4, -2],
])

_SARRUS_SLIDE26 = Matrix([
    [2, -1, 0],
    [-2, 3, 4],
    [-5, 1, 6],
])

_METHODS = ("triangulation", "sarrus", "laplace", "adjugate", "properties")


def _matrix_inline(matrix: Matrix) -> str:
    rows = matrix.to_str_list(mode="fraction")
    return "  |  ".join("  ".join(row) for row in rows)


def _title(text: str, size: int = 19) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size: {size}px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
    return label


class DeterminantsView(QWidget):
    """Matriz cuadrada, selector de método y desglose de det(A), cofactores y adjunta."""

    #: A⁻¹ lista para llevarse al Módulo 2 (la ventana principal decide cómo).
    inverseExported = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("determinantsView")
        self._method = "triangulation"
        self.last_determinant: Optional[DeterminantResult] = None
        self.last_adjugate: Optional[AdjugateResult] = None
        self.last_properties: Optional[DeterminantPropertiesResult] = None
        self._setup_ui()
        self._sync_controls()

    # ======================================================================
    # Construcción
    # ======================================================================
    def _setup_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        method_row = QHBoxLayout()
        method_row.setSpacing(8)
        self.method_group = QButtonGroup(self)
        self.method_group.setExclusive(True)
        self.triangulation_mode_btn = self._mode_button(
            "Triangulación", 0, "det(A) = (−1)ˢ · producto de la diagonal de U", checked=True
        )
        self.sarrus_mode_btn = self._mode_button("Sarrus (3×3)", 1, "Diagonales principales menos secundarias")
        self.laplace_mode_btn = self._mode_button("Cofactores de Laplace", 2, "Desarrollo por una fila o columna")
        self.adjugate_mode_btn = self._mode_button("Matriz adjunta", 3, "Menores, cofactores, adj(A) y A⁻¹")
        self.properties_mode_btn = self._mode_button("Propiedades", 4, "det(AB), det(Aᵀ), det(A⁻¹), det(kA)")
        self.method_group.idClicked.connect(self._on_method_changed)
        for button in self.method_group.buttons():
            method_row.addWidget(button)
        method_row.addStretch(1)
        root.addLayout(method_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.grid = DynamicMatrixGrid(
            initial_rows=2,
            initial_cols=2,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.size_control = MatrixSizeControl(
            self.grid, square=True, order_label="Orden n", minimum=1, maximum=MAX_DETERMINANT_ORDER
        )
        self.size_control.sizeChanged.connect(self._on_order_changed)
        action_row.addWidget(self.size_control)

        self.laplace_box = QWidget()
        laplace_row = QHBoxLayout(self.laplace_box)
        laplace_row.setContentsMargins(12, 0, 0, 0)
        laplace_row.setSpacing(6)
        axis_group = QButtonGroup(self)
        axis_group.setExclusive(True)
        self.laplace_row_btn = QPushButton("Fila")
        self.laplace_row_btn.setObjectName("modeToggle")
        self.laplace_row_btn.setCheckable(True)
        self.laplace_row_btn.setChecked(True)
        self.laplace_col_btn = QPushButton("Columna")
        self.laplace_col_btn.setObjectName("modeToggle")
        self.laplace_col_btn.setCheckable(True)
        for button in (self.laplace_row_btn, self.laplace_col_btn):
            button.setCursor(Qt.PointingHandCursor)
            axis_group.addButton(button)
            laplace_row.addWidget(button)
        axis_group.buttonClicked.connect(lambda _b: self._on_expansion_changed())
        self.expansion_index = QSpinBox()
        self.expansion_index.setObjectName("expansionIndexSpin")
        self.expansion_index.setRange(1, MAX_DETERMINANT_ORDER)
        self.expansion_index.setValue(1)
        self.expansion_index.setPrefix("índice ")
        self.expansion_index.setAccessibleName("Fila o columna de expansión")
        self.expansion_index.valueChanged.connect(lambda _v: self._on_expansion_changed())
        laplace_row.addWidget(self.expansion_index)
        self.laplace_suggest_btn = QPushButton("")
        apply_widget_class(self.laplace_suggest_btn, "link-action")
        self.laplace_suggest_btn.setCursor(Qt.PointingHandCursor)
        self.laplace_suggest_btn.setToolTip(
            "Desarrollar por la línea con más ceros: cada cero anula un término y ahorra un menor"
        )
        self.laplace_suggest_btn.clicked.connect(self.apply_expansion_suggestion)
        laplace_row.addWidget(self.laplace_suggest_btn)
        self.laplace_box.setVisible(False)
        action_row.addWidget(self.laplace_box)
        action_row.addStretch(1)

        for text, tip, slot in (
            ("Ejemplo Sesión 11", "Diapositiva 40: det(A) = −19, cofactores y adjunta", self.load_session11_example),
            ("Ejemplo Sarrus", "Diapositiva 26: det(B) = 36", self.load_sarrus_example),
            ("Ejemplo det(AB)", "Diapositiva 24: det(A) = 9, det(B) = 5", self.load_properties_example),
        ):
            button = QPushButton(text)
            button.setObjectName("secondaryAction")
            button.setToolTip(tip)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(slot)
            action_row.addWidget(button)
        self.compute_btn = QPushButton("▶ Calcular")
        self.compute_btn.setObjectName("primaryAction")
        self.compute_btn.setToolTip("Calcular con el método elegido (Ctrl+Intro desde cualquier celda)")
        self.compute_btn.setCursor(Qt.PointingHandCursor)
        self.compute_btn.clicked.connect(self.compute)
        action_row.addWidget(self.compute_btn)
        root.addLayout(action_row)

        badge_row = QHBoxLayout()
        self.badge = QLabel("")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        badge_row.addWidget(self.badge, 1)
        self.sarrus_fix_btn = QPushButton("Ajustar a 3×3")
        apply_widget_class(self.sarrus_fix_btn, "link-action")
        self.sarrus_fix_btn.setCursor(Qt.PointingHandCursor)
        self.sarrus_fix_btn.setToolTip("Cambia el orden a 3 conservando las entradas que caben (se puede deshacer)")
        self.sarrus_fix_btn.clicked.connect(self.adjust_to_sarrus)
        self.sarrus_fix_btn.setVisible(False)
        badge_row.addWidget(self.sarrus_fix_btn)
        root.addLayout(badge_row)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self._build_input_panel())
        self.splitter.addWidget(self._build_steps_panel())
        self.splitter.addWidget(self._build_result_panel())
        self.splitter.setSizes([380, 520, 420])
        root.addWidget(self.splitter, stretch=1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    def _build_input_panel(self) -> QWidget:
        left_card = QFrame()
        apply_widget_class(left_card, "elevated-card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        self.inputs_row = ResponsiveRow(breakpoint=470, spacing=14)
        a_box = QWidget()
        a_layout = QVBoxLayout(a_box)
        a_layout.setContentsMargins(0, 0, 0, 0)
        a_layout.addWidget(_title("Matriz A"))
        self.grid.matrixChanged.connect(self._on_matrix_changed)
        self.grid.submitRequested.connect(self.compute)
        a_layout.addWidget(self.grid, stretch=1)
        self.inputs_row.add_widget(a_box, 1)

        self.properties_box = QWidget()
        self.properties_box.setObjectName("detPropertiesBox")
        properties_layout = QVBoxLayout(self.properties_box)
        properties_layout.setContentsMargins(0, 0, 0, 0)
        properties_layout.setSpacing(8)
        properties_layout.addWidget(_title("Matriz B", 19))
        self.grid_b = DynamicMatrixGrid(
            initial_rows=2,
            initial_cols=2,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.grid_b.matrixChanged.connect(self._on_matrix_changed)
        self.grid_b.submitRequested.connect(self.compute)
        properties_layout.addWidget(self.grid_b, stretch=1)
        self.properties_box.setVisible(False)
        self.inputs_row.add_widget(self.properties_box, 1)
        left_layout.addWidget(self.inputs_row, stretch=1)

        self.scalar_box = QWidget()
        k_layout = QHBoxLayout(self.scalar_box)
        k_layout.setContentsMargins(0, 0, 0, 0)
        k_label = QLabel("Escalar k para det(kA)")
        k_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;")
        k_layout.addWidget(k_label, 0, Qt.AlignTop)
        self.scalar_k = ScalarField(
            "2", object_name="detScalarField", base_tooltip="Escalar k: entero, fracción a/b o decimal"
        )
        self.scalar_k.setFixedWidth(120)
        self.scalar_k.textChanged.connect(self._on_matrix_changed)
        self.scalar_k.returnPressed.connect(self.compute)
        self.scalar_k_input = ScalarInput(self.scalar_k, presets=CANONICAL_SCALARS, help_text="Entero, fracción o decimal")
        k_layout.addWidget(self.scalar_k_input, 1)
        self.scalar_box.setVisible(False)
        left_layout.addWidget(self.scalar_box)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setWidget(left_card)
        return left_scroll

    def _build_steps_panel(self) -> QWidget:
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        center_layout.addWidget(_title("Procedimiento"))
        self.stepper = AlgorithmStepperCarousel(alert_mode=ALERT_SINGULAR, variable_headers=False)
        self.stepper.set_export_title("Determinante")
        self.stepper.set_empty_hint("Elige un método y pulsa Calcular.")
        self.stepper.stepChanged.connect(self._on_step_changed)
        center_layout.addWidget(self.stepper, stretch=1)
        return center

    def _build_result_panel(self) -> QWidget:
        right_card = QFrame()
        apply_widget_class(right_card, "elevated-card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(10)
        right_layout.addWidget(_title("Resultado"))
        self.det_value_label = QLabel("det(A) = —")
        self.det_value_label.setObjectName("detValueLabel")
        self.det_value_label.setWordWrap(True)
        self.det_value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.det_value_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 28px; font-weight: 700; font-family: {FONT_FAMILY_MONO};"
        )
        right_layout.addWidget(self.det_value_label)
        self.diagnosis_label = QLabel("")
        self.diagnosis_label.setObjectName("detDiagnosisLabel")
        self.diagnosis_label.setWordWrap(True)
        self.diagnosis_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;")
        right_layout.addWidget(self.diagnosis_label)

        self.sarrus_diagram = SarrusDiagram()
        self.sarrus_diagram.setVisible(False)
        right_layout.addWidget(self.sarrus_diagram)

        self.properties_checklist = QLabel("")
        self.properties_checklist.setObjectName("detPropertiesChecklist")
        self.properties_checklist.setWordWrap(True)
        self.properties_checklist.setTextFormat(Qt.RichText)
        self.properties_checklist.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.properties_checklist.setVisible(False)
        right_layout.addWidget(self.properties_checklist)

        self.adjugate_section = QWidget()
        self.adjugate_section.setObjectName("adjugateSection")
        adjugate_layout = QVBoxLayout(self.adjugate_section)
        adjugate_layout.setContentsMargins(0, 4, 0, 0)
        adjugate_layout.setSpacing(8)
        self.adjugate_tabs = QTabWidget()
        self.adjugate_tabs.setObjectName("adjugateTabs")
        self.minors_view, self.minors_readout = self._matrix_tab("Mᵢⱼ", "Matriz de menores Mᵢⱼ", "minorsReadout", "Menores")
        self.cofactors_view, self.cofactors_readout = self._matrix_tab(
            "Cᵢⱼ", "Cofactores  Cᵢⱼ = (−1)ⁱ⁺ʲ Mᵢⱼ", "cofactorReadout", "Cofactores"
        )
        self.adjugate_view, self.adjugate_readout = self._matrix_tab("adj(A)", "Adjunta  adj(A) = Cᵀ", "adjugateReadout", "Matriz adjunta")
        self.inverse_view, self.inverse_readout = self._matrix_tab(
            "A⁻¹", "Inversa  A⁻¹ = (1/det A) · adj(A)", "inverseReadout", "Inversa por adjunta"
        )
        adjugate_layout.addWidget(self.adjugate_tabs)
        inverse_actions = QHBoxLayout()
        self.use_inverse_btn = QPushButton("Usar A⁻¹ como A")
        self.use_inverse_btn.setObjectName("secondaryAction")
        self.use_inverse_btn.setToolTip("Carga A⁻¹ en la cuadrícula A (por ejemplo, para comprobar (A⁻¹)⁻¹ = A)")
        self.use_inverse_btn.clicked.connect(self.use_inverse_as_input)
        self.send_inverse_btn = QPushButton("Enviar A⁻¹ a Matrices")
        self.send_inverse_btn.setObjectName("secondaryAction")
        self.send_inverse_btn.setToolTip("Abre el Módulo 2 con A⁻¹ en la matriz A")
        self.send_inverse_btn.clicked.connect(self.export_inverse)
        for button in (self.use_inverse_btn, self.send_inverse_btn):
            button.setCursor(Qt.PointingHandCursor)
            button.setEnabled(False)
            inverse_actions.addWidget(button)
        inverse_actions.addStretch(1)
        adjugate_layout.addLayout(inverse_actions)
        self.adjugate_section.setVisible(False)
        right_layout.addWidget(self.adjugate_section)
        right_layout.addStretch(1)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setWidget(right_card)
        return right_scroll

    def _mode_button(self, text: str, method_id: int, tooltip: str, checked: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("modeToggle")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setToolTip(tooltip)
        button.setCursor(Qt.PointingHandCursor)
        self.method_group.addButton(button, method_id)
        return button

    def _matrix_tab(self, tab: str, caption_text: str, readout_name: str, tooltip: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        caption = QLabel(caption_text)
        caption.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        layout.addWidget(caption)
        view = BookMatrixWidget()
        view.setMinimumHeight(180)
        layout.addWidget(view)
        readout = QLabel("")
        readout.setObjectName(readout_name)
        readout.setWordWrap(True)
        readout.setTextInteractionFlags(Qt.TextSelectableByMouse)
        readout.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 14px; font-family: {FONT_FAMILY_MONO};")
        layout.addWidget(readout)
        index = self.adjugate_tabs.addTab(page, tab)
        self.adjugate_tabs.setTabToolTip(index, tooltip)
        return view, readout

    # ======================================================================
    # Estado
    # ======================================================================
    def _apply_method_visibility(self) -> None:
        method = self._method
        self.laplace_box.setVisible(method == "laplace")
        properties = method == "properties"
        self.properties_box.setVisible(properties)
        self.scalar_box.setVisible(properties)
        self.properties_checklist.setVisible(properties)
        self.splitter.setSizes([700, 486, 300] if properties else [380, 520, 420])
        self._refresh_expansion_highlight()

    def _on_method_changed(self, method_id: int) -> None:
        self._method = _METHODS[method_id]
        self._apply_method_visibility()
        if self._method == "properties":
            self._match_partner_order()
        self._clear_results()
        self._sync_controls()
        if self._method == "sarrus" and self._order() not in (None, 3):
            show_toast(
                self,
                f"La regla de Sarrus solo vale para 3×3 y A es {self._order()}×{self._order()}.",
                kind="warning",
                action_text="Ajustar a 3×3",
                action=self.adjust_to_sarrus,
            )

    def _on_matrix_changed(self) -> None:
        self._clear_results()
        self._sync_controls()

    def _on_order_changed(self, _rows: int, _cols: int) -> None:
        if self._method == "properties":
            self._match_partner_order()

    def _order(self) -> Optional[int]:
        rows, cols = self.grid.data_shape()
        return rows if rows == cols else None

    def _clear_results(self) -> None:
        self.last_determinant = None
        self.last_adjugate = None
        self.last_properties = None
        self.det_value_label.setText("det(A) = —")
        self.diagnosis_label.setText("")
        self.properties_checklist.setText("")
        self.adjugate_section.setVisible(False)
        self.sarrus_diagram.setVisible(False)
        self.sarrus_diagram.set_matrix(None)
        self.stepper.set_steps([])
        for view in (self.minors_view, self.cofactors_view, self.adjugate_view, self.inverse_view):
            view.clear()
        for readout in (self.minors_readout, self.cofactors_readout, self.adjugate_readout, self.inverse_readout):
            readout.setText("")
        self.use_inverse_btn.setEnabled(False)
        self.send_inverse_btn.setEnabled(False)

    def _blocking_reason(self) -> Optional[str]:
        message = self.grid.validation_message()
        if message:
            return f"A, {message[0].lower()}{message[1:]}"
        rows, cols = self.grid.data_shape()
        if rows != cols:
            return f"El determinante solo está definido para matrices cuadradas (n×n). A es {rows}×{cols}."
        if rows > MAX_DETERMINANT_ORDER:
            return f"El orden n debe estar entre 1 y {MAX_DETERMINANT_ORDER}."
        if self._method == "sarrus" and rows != 3:
            return f"La regla de Sarrus solo está definida para matrices 3×3. A es {rows}×{rows}."
        if self._method == "properties":
            if not self.scalar_k.is_valid():
                return f"Escalar k: {self.scalar_k.diagnosis().message}"
            message_b = self.grid_b.validation_message()
            if message_b:
                return f"B, {message_b[0].lower()}{message_b[1:]}"
            if self.grid_b.data_shape() != (rows, cols):
                b_rows, b_cols = self.grid_b.data_shape()
                return (
                    "A y B deben ser cuadradas del mismo orden para det(AB). "
                    f"A es {rows}×{cols} y B es {b_rows}×{b_cols}."
                )
        return None

    def _sync_controls(self) -> None:
        order = self._order()
        if order is not None:
            self.expansion_index.setMaximum(max(1, order))
        self._refresh_expansion_suggestion()
        self._refresh_expansion_highlight()
        reason = self._blocking_reason()
        self.compute_btn.setEnabled(reason is None)
        self.sarrus_fix_btn.setVisible(self._method == "sarrus" and order != 3)
        if reason is not None:
            self.badge.setText(reason)
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
        elif self.last_determinant is None and self.last_adjugate is None and self.last_properties is None:
            self.badge.setText("Matriz cuadrada lista para calcular.")
            self.badge.setStyleSheet(idle_badge_style())

    def adjust_to_sarrus(self) -> None:
        """Lleva A a 3×3 (rellena con ceros o recorta) y deja Sarrus listo."""
        if self._order() == 3:
            return
        self.size_control.set_size(3, 3)
        if self._method != "sarrus":
            self._set_method("sarrus")
            self._sync_controls()
        show_toast(self, "A ahora es 3×3. Revisa las entradas nuevas.", action_text="Deshacer", action=self.grid.undo)

    # -------------------------------------------------------------- Laplace
    def _expansion(self) -> tuple[str, int]:
        return ("row" if self.laplace_row_btn.isChecked() else "col", self.expansion_index.value() - 1)

    def _on_expansion_changed(self) -> None:
        self._refresh_expansion_highlight()
        if self.last_determinant is not None and self._method == "laplace":
            self._clear_results()
            self._sync_controls()

    def _refresh_expansion_highlight(self) -> None:
        if self._method != "laplace":
            self.grid.clear_highlight()
            return
        along, index = self._expansion()
        if along == "row":
            self.grid.set_highlight(rows=[index])
        else:
            self.grid.set_highlight(cols=[index])

    def expansion_suggestion(self) -> Optional[tuple[str, int, int]]:
        if self._order() is None or not self.grid.is_all_valid():
            return None
        return best_expansion_line(self.grid.get_matrix())

    def _refresh_expansion_suggestion(self) -> None:
        suggestion = self.expansion_suggestion()
        if suggestion is None or suggestion[2] == 0:
            self.laplace_suggest_btn.setVisible(False)
            return
        along, index, zeros = suggestion
        name = "fila" if along == "row" else "columna"
        self.laplace_suggest_btn.setText(f"Sugerencia: {name} {index + 1} ({zeros} cero{'s' if zeros > 1 else ''})")
        self.laplace_suggest_btn.setVisible(self._expansion() != (along, index))

    def apply_expansion_suggestion(self) -> None:
        suggestion = self.expansion_suggestion()
        if suggestion is None:
            return
        along, index, _zeros = suggestion
        (self.laplace_row_btn if along == "row" else self.laplace_col_btn).setChecked(True)
        self.expansion_index.setValue(index + 1)
        self._on_expansion_changed()
        self._refresh_expansion_suggestion()

    # ======================================================================
    # Ejemplos
    # ======================================================================
    def _set_method(self, method: str) -> None:
        self.method_group.button(_METHODS.index(method)).setChecked(True)
        self._method = method
        self._apply_method_visibility()

    def load_session11_example(self) -> None:
        """Diapositiva 40: det(A) = −19, cofactores y adjunta."""
        self._set_method("adjugate")
        self.grid.set_matrix(_SESSION11_MATRIX)
        self.compute()

    def load_sarrus_example(self) -> None:
        """Diapositiva 26: det(B) = 36 por la regla de Sarrus."""
        self._set_method("sarrus")
        self.grid.set_matrix(_SARRUS_SLIDE26)
        self.compute()

    def _match_partner_order(self) -> None:
        order = self._order()
        if order is None or self.grid_b.data_shape() == (order, order):
            return
        self.grid_b.resize_to(order, order)

    def load_properties_example(self) -> None:
        """Sesión 11, diapositiva 24: det(A) = 9, det(B) = 5 y det(AB) = 45."""
        self._set_method("properties")
        self.grid.set_matrix(Matrix([[6, 1], [3, 2]]))
        self.grid_b.set_matrix(Matrix([[4, 3], [1, 2]]))
        self.scalar_k.setText("2")
        self.compute()

    # ======================================================================
    # Cálculo
    # ======================================================================
    def compute(self) -> None:
        """Evalúa el método activo y publica el determinante o la adjunta."""
        reason = self._blocking_reason()
        if reason is not None:
            self.badge.setText(reason)
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
            self.compute_btn.setEnabled(False)
            if not self.grid.focus_first_invalid() and self._method == "properties":
                self.grid_b.focus_first_invalid()
            return
        matrix = self.grid.get_matrix()
        try:
            if self._method == "properties":
                properties = verify_determinant_properties(matrix, self.grid_b.get_matrix(), self.scalar_k.value())
                self._publish_properties(properties)
                return
            adjugate = None
            if self._method == "adjugate":
                determinant = matrix_determinant(matrix, DeterminantMethod.TRIANGULATION)
                adjugate = calculate_adjugate_and_inverse(matrix)
            elif self._method == "sarrus":
                determinant = matrix_determinant(matrix, DeterminantMethod.SARRUS_3X3)
            elif self._method == "laplace":
                along, index = self._expansion()
                method = DeterminantMethod.LAPLACE_ROW if along == "row" else DeterminantMethod.LAPLACE_COL
                determinant = matrix_determinant(matrix, method, expansion_index=index)
            else:
                determinant = matrix_determinant(matrix, DeterminantMethod.TRIANGULATION)
        except (NonSquareMatrixError, ValueError, IndexError) as exc:
            self._clear_results()
            self.badge.setText(str(exc))
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
            return

        self.last_determinant = determinant
        self.last_adjugate = adjugate
        self._publish(determinant, adjugate)

    def _on_step_changed(self, index: int) -> None:
        """En Sarrus, el esquema resalta la diagonal del paso visible (pasos 1–6)."""
        if not self.sarrus_diagram.isVisibleTo(self) or self.sarrus_diagram.matrix() is None:
            return
        self.sarrus_diagram.set_active_diagonal(index - 1 if 1 <= index <= 6 else None)

    def _publish_properties(self, result: DeterminantPropertiesResult) -> None:
        self.last_properties = result
        self.last_determinant = None
        self.last_adjugate = None
        self.adjugate_section.setVisible(False)
        self.properties_checklist.setVisible(True)
        self.det_value_label.setText(f"det(A) = {format_scalar(result.det_A)}")
        self.diagnosis_label.setText(
            "Se contrastan det(AB), det(Aᵀ), det(A⁻¹) y det(kA) con el lado derecho de cada ley."
        )
        self.stepper.set_steps(result.tracer.get_steps())

        def row(ok: bool, text: str, detail: str = "") -> str:
            color = COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR
            mark = "✓" if ok else "✗"
            extra = (
                f'<div style="color:{COLOR_TEXT_PRIMARY}; font-size:16px; font-weight:500; '
                f'margin:2px 0 0 26px; font-family:{FONT_FAMILY_MONO};">{detail}</div>'
                if detail
                else ""
            )
            return (
                f'<div style="color:{color}; font-size:18px; font-weight:600; margin:6px 0;">'
                f"{mark}&nbsp;&nbsp;{text}{extra}</div>"
            )

        lines = []
        if result.det_B is not None and result.det_AB is not None and result.is_multiplicative_valid is not None:
            product = result.det_A * result.det_B
            lines.append(row(
                result.is_multiplicative_valid,
                f"det(AB) = {format_scalar(result.det_AB)} y det(A)·det(B) = {format_scalar(product)}",
                f"det(A)·det(B) = {format_scalar(result.det_A)} · {format_scalar(result.det_B)} = {format_scalar(product)}",
            ))
        lines.append(row(
            result.is_transpose_valid,
            f"det(Aᵀ) = {format_scalar(result.det_transpose)} y det(A) = {format_scalar(result.det_A)}",
        ))
        if result.is_inverse_valid is None:
            lines.append(
                f'<div style="color:{COLOR_TEXT_MUTED}; font-size:18px; font-weight:600; margin:6px 0;">'
                "—&nbsp;&nbsp;det(A⁻¹) no aplica porque det(A) = 0.</div>"
            )
        else:
            lines.append(row(
                result.is_inverse_valid,
                f"det(A⁻¹) = {format_scalar(result.det_inverse)} y 1/det(A) = {format_scalar(result.inverse_reciprocal)}",
            ))
        if result.k is not None and result.det_scaled is not None and result.is_scaling_valid is not None:
            order = self.grid.data_shape()[0]
            lines.append(row(
                result.is_scaling_valid,
                f"det(kA) = {format_scalar(result.det_scaled)} = kⁿ det(A), con k = {format_scalar(result.k)} y n = {order}",
                scaling_breakdown(result.k, order, result.det_A),
            ))
        self.properties_checklist.setText("".join(lines))
        checks = [
            result.is_multiplicative_valid,
            result.is_transpose_valid,
            result.is_inverse_valid,
            result.is_scaling_valid,
        ]
        if all(item is not False for item in checks) and any(item is True for item in checks):
            self.badge.setText("✓ Las propiedades del determinante se cumplen.")
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS))
        else:
            self.badge.setText("✕ Alguna propiedad del determinante no se cumple.")
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
        self.compute_btn.setEnabled(True)

    def _publish(self, determinant: DeterminantResult, adjugate: Optional[AdjugateResult]) -> None:
        shown = format_scalar(determinant.value, mode="fraction")
        self.det_value_label.setText(f"det(A) = {shown}")
        diagnosis = singularity_diagnosis(determinant.value, determinant.matrix.rows)
        if adjugate is not None:
            diagnosis = (
                f"{diagnosis} La inversa analítica es (1/det A) · adj(A)."
                if adjugate.inverse_via_adjugate is not None
                else f"{diagnosis} La adjunta está definida, pero no existe A⁻¹."
            )
        self.diagnosis_label.setText(diagnosis)
        sarrus = determinant.method is DeterminantMethod.SARRUS_3X3
        self.sarrus_diagram.set_matrix(determinant.matrix if sarrus else None)
        self.sarrus_diagram.setVisible(sarrus)
        self.stepper.set_steps(determinant.tracer.get_steps())
        if determinant.is_singular:
            self.badge.setText(f"det(A) = {shown}. Matriz singular.")
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
        else:
            self.badge.setText(f"det(A) = {shown}. Matriz no singular.")
            self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS))
        self.compute_btn.setEnabled(True)

        if adjugate is None:
            self.adjugate_section.setVisible(False)
            return
        self.adjugate_section.setVisible(True)
        self._show_matrix(self.minors_view, self.minors_readout, adjugate.minors_matrix)
        self._show_matrix(self.cofactors_view, self.cofactors_readout, adjugate.cofactors_matrix)
        self._show_matrix(self.adjugate_view, self.adjugate_readout, adjugate.adjugate_matrix)
        invertible = adjugate.inverse_via_adjugate is not None
        if not invertible:
            self.inverse_view.clear()
            self.inverse_view.set_empty_text("No existe A⁻¹")
            self.inverse_readout.setText("No existe A⁻¹ porque det(A) = 0.")
        else:
            self._show_matrix(self.inverse_view, self.inverse_readout, adjugate.inverse_via_adjugate)
        self.use_inverse_btn.setEnabled(invertible)
        self.send_inverse_btn.setEnabled(invertible)
        reason = "" if invertible else "No hay inversa: det(A) = 0"
        for button in (self.use_inverse_btn, self.send_inverse_btn):
            if reason:
                button.setToolTip(reason)

    @staticmethod
    def _show_matrix(view: BookMatrixWidget, readout: QLabel, matrix: Matrix) -> None:
        view.set_matrix(matrix, show_headers=False)
        readout.setText(_matrix_inline(matrix))

    # ------------------------------------------------------------ inversa
    def use_inverse_as_input(self) -> None:
        if self.last_adjugate is None or self.last_adjugate.inverse_via_adjugate is None:
            return
        self.grid.set_matrix(self.last_adjugate.inverse_via_adjugate)
        self.compute()
        show_toast(
            self,
            "A⁻¹ ahora es la matriz A. Su adjunta lleva de vuelta a la matriz original.",
            action_text="Deshacer",
            action=self._undo_use_inverse,
        )

    def _undo_use_inverse(self) -> None:
        if self.grid.undo():
            self.compute()

    def export_inverse(self) -> None:
        if self.last_adjugate is None or self.last_adjugate.inverse_via_adjugate is None:
            return
        self.inverseExported.emit(self.last_adjugate.inverse_via_adjugate)
