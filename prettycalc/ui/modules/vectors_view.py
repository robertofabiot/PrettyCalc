"""Módulo 3: vectores en ℝⁿ — operaciones, métricas, combinación e independencia lineal.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).

Sprint 10 (auditoría UI/UX, Módulo 3):

- u ± v y k · v muestran el operador entre los operandos, permiten
  intercambiar u ↔ v de un clic y explican cada componente en un carrusel.
- Las métricas se eligen con un selector segmentado y un único «Calcular»
  (Ley de Hick); el producto exterior u vᵀ tiene inspector celda a celda que
  resalta uᵢ y vⱼ en los editores.
- Combinación e independencia lineal: validación en línea (sin diálogos),
  conjuntos en varias filas, pegado de una matriz como columnas, aviso k > n
  antes de evaluar y la contradicción concreta del sistema inconsistente.
- El diálogo de teoremas pertenece al Módulo 3.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QButtonGroup,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSpinBox,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.classifier import SystemType
from prettycalc.core.linear_combination import evaluate_linear_combination, format_combination_equation
from prettycalc.core.linear_independence import (
    LinearIndependenceResult,
    evaluate_linear_independence,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.vector_ops import (
    trace_vector_distance,
    trace_vector_norm,
    trace_vector_outer_product,
    trace_vector_scale,
    trace_vector_sum,
    vector_sub,
)
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.clipboard import get_matrix_from_clipboard
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.mathtext import latex_to_book_html, to_subscript, to_superscript
from prettycalc.ui.scalar_field import CANONICAL_SCALARS, ScalarField, ScalarInput
from prettycalc.ui.stepper_carousel import ALERT_SYSTEM, AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_message_box_theme,
    apply_widget_class,
    badge_style,
    idle_badge_style,
)
from prettycalc.ui.vector_set_editor import VectorColumnEditor, VectorSetEditor

__all__ = ["VectorsView", "VectorColumnEditor"]

_OP_ADD, _OP_SUB, _OP_SCALE = 0, 1, 2
_METRIC_NORM_U, _METRIC_NORM_V, _METRIC_DISTANCE, _METRIC_OUTER = 0, 1, 2, 3


def _space(n: int) -> str:
    return f"ℝ{to_superscript(n)}"


def _error_badge() -> str:
    return badge_style(COLOR_FEEDBACK_ERROR)


def _ok_badge() -> str:
    return badge_style(COLOR_FEEDBACK_SUCCESS)


def _warn_badge() -> str:
    return badge_style(COLOR_ACCENT_WARNING)


def _operator_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setMinimumWidth(28)
    label.setStyleSheet(f"font-size: 30px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};")
    return label


def _scroll_page(parent: QWidget) -> Tuple[QWidget, QVBoxLayout, QScrollArea]:
    container = QWidget(parent)
    main_layout = QVBoxLayout(container)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    scroll = QScrollArea(container)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.viewport().setAutoFillBackground(False)
    page = QWidget()
    page.setAutoFillBackground(False)
    layout = QVBoxLayout(page)
    layout.setContentsMargins(4, 4, 10, 16)
    layout.setSpacing(10)
    scroll.setWidget(page)
    main_layout.addWidget(scroll)
    return container, layout, scroll


def _sample_button(text: str, tooltip: str, slot) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    button.setToolTip(tooltip)
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(slot)
    return button


def _spin_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;")
    return label


def _crowded_combination(k: int, n: int) -> str:
    if k > n:
        return (
            f"k = {k} > n = {n}: en {_space(n)} más de {n} vectores siempre son L.D.; "
            "si b es combinación lineal, no será única."
        )
    return ""


def _crowded_independence(k: int, n: int) -> str:
    if k > n:
        return f"k = {k} > n = {n}: por el teorema de la dimensión, el conjunto será L.D."
    return ""


class VectorsView(QWidget):
    """Subpestañas: operaciones, métricas, combinación lineal e independencia lineal."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("vectorsView")
        self._last_indep_result: Optional[LinearIndependenceResult] = None
        self._outer_matrix: Optional[Matrix] = None
        self._inspected: Optional[Tuple[int, int]] = None
        self._combo_contradiction_step: Optional[int] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        tabs.addTab(self._build_basic_tab(), "Operaciones básicas")
        tabs.addTab(self._build_metrics_tab(), "Norma y producto exterior")
        tabs.addTab(self._build_combination_tab(), "Combinación lineal")
        tabs.addTab(self._build_independence_tab(), "Independencia lineal")
        root.addWidget(tabs)
        self.tabs = tabs

    # ======================================================================
    # Subpestaña 1: u ± v y k · v
    # ======================================================================
    def _build_basic_tab(self) -> QWidget:
        container, layout, _ = _scroll_page(self)

        controls = QHBoxLayout()
        controls.addWidget(_spin_label("Dimensión n"))
        self.basic_dim = QSpinBox()
        self.basic_dim.setRange(2, 10)
        self.basic_dim.setValue(3)
        self.basic_dim.setAccessibleName("Dimensión de u y v")
        self.basic_dim.valueChanged.connect(self._on_basic_dimension)
        controls.addWidget(self.basic_dim)
        controls.addSpacing(12)

        self.basic_op_group = QButtonGroup(self)
        self.basic_op_group.setExclusive(True)
        self.basic_add_btn = QPushButton("u + v")
        self.basic_sub_btn = QPushButton("u − v")
        self.basic_scale_btn = QPushButton("k · v")
        for i, btn in enumerate((self.basic_add_btn, self.basic_sub_btn, self.basic_scale_btn)):
            btn.setCheckable(True)
            btn.setObjectName("modeToggle")
            btn.setCursor(Qt.PointingHandCursor)
            self.basic_op_group.addButton(btn, i)
            controls.addWidget(btn)
        self.basic_add_btn.setChecked(True)
        self.basic_op_group.idClicked.connect(self._on_basic_op)

        self.swap_btn = QPushButton("⇄  Intercambiar u y v")
        self.swap_btn.setObjectName("secondaryAction")
        self.swap_btn.setCursor(Qt.PointingHandCursor)
        self.swap_btn.setToolTip("Intercambia los valores de u y v (por ejemplo, para obtener v − u)")
        self.swap_btn.clicked.connect(self.swap_basic_operands)
        controls.addWidget(self.swap_btn)
        controls.addStretch(1)
        controls.addWidget(
            _sample_button("Ejemplo", "Carga u = (1, −2, 3) y v = (4, 0, −1)", self.load_basic_sample)
        )
        layout.addLayout(controls)

        self.basic_badge = QLabel("")
        self.basic_badge.setAlignment(Qt.AlignCenter)
        self.basic_badge.setWordWrap(True)
        layout.addWidget(self.basic_badge)

        body = QHBoxLayout()
        body.setSpacing(8)

        self.scale_card = QFrame()
        apply_widget_class(self.scale_card, "elevated-card")
        scale_layout = QVBoxLayout(self.scale_card)
        k_title = QLabel("Escalar k")
        k_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        scale_layout.addWidget(k_title)
        self.basic_k = ScalarField("2", base_tooltip="Escalar k: entero, fracción a/b o decimal")
        self.basic_k.setFixedWidth(130)
        self.basic_k.textChanged.connect(self._on_basic_inputs_changed)
        self.basic_k.returnPressed.connect(self._compute_basic)
        self.basic_k_input = ScalarInput(
            self.basic_k, presets=CANONICAL_SCALARS, help_text="Entero, fracción o decimal"
        )
        scale_layout.addWidget(self.basic_k_input)
        scale_layout.addStretch(1)
        self.scale_card.setVisible(False)
        body.addWidget(self.scale_card, 0, Qt.AlignTop)

        self.vec_u = VectorColumnEditor(3, "Vector u")
        self.vec_u.changed.connect(self._on_basic_inputs_changed)
        self.vec_u.dimensionChanged.connect(self._on_basic_editor_dimension_changed)
        self.vec_u.submitRequested.connect(self._compute_basic)
        body.addWidget(self.vec_u)

        self.basic_op_lbl = _operator_label("+")
        body.addWidget(self.basic_op_lbl, 0, Qt.AlignVCenter)

        self.vec_v = VectorColumnEditor(3, "Vector v")
        self.vec_v.changed.connect(self._on_basic_inputs_changed)
        self.vec_v.dimensionChanged.connect(self._on_basic_editor_dimension_changed)
        self.vec_v.submitRequested.connect(self._compute_basic)
        body.addWidget(self.vec_v)

        body.addWidget(_operator_label("="), 0, Qt.AlignVCenter)

        result_card = QFrame()
        apply_widget_class(result_card, "elevated-card")
        result_layout = QVBoxLayout(result_card)
        self.basic_result_title = QLabel("Resultado  u + v")
        self.basic_result_title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        result_layout.addWidget(self.basic_result_title)
        self.basic_result = BookMatrixWidget()
        self.basic_result.setMinimumHeight(160)
        self.basic_result.set_empty_text("Pulsa Calcular (Ctrl+Enter)")
        result_layout.addWidget(self.basic_result, stretch=1)
        body.addWidget(result_card, stretch=1)
        layout.addLayout(body)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.basic_compute_btn = QPushButton("▶ Calcular")
        self.basic_compute_btn.setObjectName("primaryAction")
        self.basic_compute_btn.setToolTip("Calcular (Ctrl+Enter desde cualquier celda)")
        self.basic_compute_btn.clicked.connect(self._compute_basic)
        actions.addWidget(self.basic_compute_btn)
        layout.addLayout(actions)

        self.basic_stepper = AlgorithmStepperCarousel(variable_headers=False)
        self.basic_stepper.setObjectName("basicStepper")
        self.basic_stepper.set_export_title("Operación vectorial componente a componente")
        self.basic_stepper.set_empty_hint("Calcula para ver el desglose entrada por entrada.")
        layout.addWidget(self.basic_stepper)
        layout.addStretch(1)

        self._refresh_basic_badge()
        return container

    def _basic_op(self) -> int:
        return self.basic_op_group.checkedId()

    def _basic_op_text(self) -> str:
        return {_OP_ADD: "u + v", _OP_SUB: "u − v", _OP_SCALE: "k · v"}[self._basic_op()]

    def _on_basic_dimension(self, n: int) -> None:
        self.vec_u.set_dimension(n)
        self.vec_v.set_dimension(n)
        self._on_basic_inputs_changed()

    def _on_basic_editor_dimension_changed(self, n: int) -> None:
        if 2 <= n <= 10 and self.basic_dim.value() != n:
            self.basic_dim.setValue(n)

    def _on_basic_op(self, op_id: int) -> None:
        scale = op_id == _OP_SCALE
        self.scale_card.setVisible(scale)
        self.vec_u.setVisible(not scale)
        self.swap_btn.setVisible(not scale)
        symbol = {_OP_ADD: "+", _OP_SUB: "−", _OP_SCALE: "·"}[op_id]
        self.basic_op_lbl.setText(symbol)
        size = 46 if symbol == "·" else 30
        self.basic_op_lbl.setStyleSheet(f"font-size: {size}px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};")
        self.basic_result_title.setText(f"Resultado  {self._basic_op_text()}")
        self._on_basic_inputs_changed()

    def _on_basic_inputs_changed(self, *_args) -> None:
        self.basic_result.clear()
        self.basic_stepper.set_steps([])
        self._refresh_basic_badge()

    def swap_basic_operands(self) -> None:
        """u ↔ v: con u − v da v − u sin reescribir nada (se puede deshacer)."""
        u_values, v_values = self.vec_u.raw_values(), self.vec_v.raw_values()
        self.vec_u.set_raw_values(v_values)
        self.vec_v.set_raw_values(u_values)
        self._on_basic_inputs_changed()
        show_toast(
            self,
            "Se intercambiaron u y v.",
            action_text="Deshacer",
            action=self.swap_basic_operands,
        )

    def _refresh_basic_badge(self) -> None:
        n = self.basic_dim.value()
        problem = ""
        if self._basic_op() == _OP_SCALE:
            if not self.basic_k.is_valid():
                problem = f"Escalar k: {self.basic_k.diagnosis().message}"
            elif not self.vec_v.is_valid():
                problem = self.vec_v.validation_message()
        else:
            problem = self.vec_u.validation_message() or self.vec_v.validation_message()
        if problem:
            self.basic_badge.setText(f"✕ {problem}")
            self.basic_badge.setStyleSheet(_error_badge())
            self.basic_compute_btn.setEnabled(False)
            return
        if self._basic_op() == _OP_SCALE:
            text = f"✓ Escalado definido en {_space(n)}: k · v ∈ {_space(n)}."
        else:
            text = f"✓ u, v ∈ {_space(n)} con la misma dimensión. La suma y la resta están definidas."
        self.basic_badge.setText(text)
        self.basic_badge.setStyleSheet(_ok_badge())
        self.basic_compute_btn.setEnabled(True)

    def _compute_basic(self) -> None:
        if not self.basic_compute_btn.isEnabled():
            for editor in (self.vec_u, self.vec_v):
                if editor.isVisible() and editor.focus_first_invalid():
                    return
            return
        try:
            if self._basic_op() == _OP_SCALE:
                result = trace_vector_scale(self.vec_v.get_vector(), self.basic_k.text())
            else:
                result = trace_vector_sum(
                    self.vec_u.get_vector(),
                    self.vec_v.get_vector(),
                    subtract=self._basic_op() == _OP_SUB,
                )
        except DimensionMismatchError as exc:
            self.basic_badge.setText(f"✕ {exc}")
            self.basic_badge.setStyleSheet(_error_badge())
            self.basic_compute_btn.setEnabled(False)
            return
        self.basic_result.set_matrix(result.vector.to_column_matrix(), split_col=None, show_headers=False)
        self.basic_stepper.set_steps(result.tracer.get_steps())

    def load_basic_sample(self) -> None:
        self.tabs.setCurrentIndex(0)
        self.basic_dim.setValue(3)
        self.vec_u.set_vector(Vector([1, -2, 3]))
        self.vec_v.set_vector(Vector([4, 0, -1]))
        self._compute_basic()

    # ======================================================================
    # Subpestaña 2: ‖u‖, ‖v‖, d(u, v), u vᵀ
    # ======================================================================
    def _build_metrics_tab(self) -> QWidget:
        container, layout, _ = _scroll_page(self)

        controls = QHBoxLayout()
        controls.addWidget(_spin_label("dim u"))
        self.metric_u_dim = QSpinBox()
        controls.addWidget(self.metric_u_dim)
        controls.addWidget(_spin_label("dim v"))
        self.metric_v_dim = QSpinBox()
        controls.addWidget(self.metric_v_dim)
        for spin, name in ((self.metric_u_dim, "u"), (self.metric_v_dim, "v")):
            spin.setRange(1, 10)
            spin.setValue(3)
            spin.setAccessibleName(f"Dimensión de {name}")
        self.metric_u_dim.valueChanged.connect(self._on_metric_u_dimension)
        self.metric_v_dim.valueChanged.connect(self._on_metric_v_dimension)
        self.metric_swap_btn = QPushButton("⇄  Intercambiar")
        self.metric_swap_btn.setObjectName("secondaryAction")
        self.metric_swap_btn.setToolTip("Intercambia u y v (por ejemplo, para comparar u vᵀ con v uᵀ)")
        self.metric_swap_btn.setCursor(Qt.PointingHandCursor)
        self.metric_swap_btn.clicked.connect(self.swap_metric_operands)
        controls.addWidget(self.metric_swap_btn)
        self.metric_fix_dims_btn = QPushButton("Igualar dim v a dim u")
        apply_widget_class(self.metric_fix_dims_btn, "link-action")
        self.metric_fix_dims_btn.setCursor(Qt.PointingHandCursor)
        self.metric_fix_dims_btn.clicked.connect(self.match_metric_dimensions)
        self.metric_fix_dims_btn.setVisible(False)
        controls.addWidget(self.metric_fix_dims_btn)
        controls.addStretch(1)
        controls.addWidget(_sample_button("Ejemplo ‖(3, 4)‖", "Sesión 5: ‖(3, 4)‖ = 5", self.load_norm_sample))
        controls.addWidget(
            _sample_button("Ejemplo distancia", "Sesión 5: d((1, 2), (4, 6)) = 5", self.load_distance_sample)
        )
        controls.addWidget(
            _sample_button("Ejemplo x xᵀ", "Sesión 9: x xᵀ con x = (1, −2, 3)", self.load_outer_product_sample)
        )
        layout.addLayout(controls)

        self.metric_badge = QLabel("")
        self.metric_badge.setObjectName("metricBadge")
        self.metric_badge.setAlignment(Qt.AlignCenter)
        self.metric_badge.setWordWrap(True)
        layout.addWidget(self.metric_badge)

        body = QHBoxLayout()
        self.metric_u = VectorColumnEditor(3, "Vector u")
        self.metric_v = VectorColumnEditor(3, "Vector v")
        for editor in (self.metric_u, self.metric_v):
            editor.changed.connect(self._on_metric_inputs_changed)
            editor.submitRequested.connect(self.compute_metric)
            body.addWidget(editor)
        self.metric_u.dimensionChanged.connect(self.metric_u_dim.setValue)
        self.metric_v.dimensionChanged.connect(self.metric_v_dim.setValue)
        body.addStretch(1)
        layout.addLayout(body)

        selector = QHBoxLayout()
        selector.addWidget(_spin_label("Operación"))
        self.metric_group = QButtonGroup(self)
        self.metric_group.setExclusive(True)
        self.norm_u_btn = QPushButton("Norma ‖u‖")
        self.norm_v_btn = QPushButton("Norma ‖v‖")
        self.distance_btn = QPushButton("Distancia d(u, v)")
        self.outer_btn = QPushButton("Producto exterior u vᵀ")
        tips = (
            "‖u‖ = √(u · u)",
            "‖v‖ = √(v · v)",
            "d(u, v) = ‖u − v‖ (misma dimensión)",
            "M = u vᵀ, con Mᵢⱼ = uᵢ · vⱼ (dimensiones libres)",
        )
        for index, (button, tip) in enumerate(
            zip((self.norm_u_btn, self.norm_v_btn, self.distance_btn, self.outer_btn), tips)
        ):
            button.setObjectName("modeToggle")
            button.setCheckable(True)
            button.setToolTip(tip)
            button.setCursor(Qt.PointingHandCursor)
            self.metric_group.addButton(button, index)
            selector.addWidget(button)
        self.norm_u_btn.setChecked(True)
        self.metric_group.idClicked.connect(lambda _id: self._on_metric_inputs_changed())
        selector.addStretch(1)
        self.metric_compute_btn = QPushButton("▶ Calcular")
        self.metric_compute_btn.setObjectName("primaryAction")
        self.metric_compute_btn.setToolTip("Calcular la operación elegida (Ctrl+Enter)")
        self.metric_compute_btn.clicked.connect(self.compute_metric)
        selector.addWidget(self.metric_compute_btn)
        layout.addLayout(selector)

        self.metric_summary = QLabel("")
        self.metric_summary.setObjectName("metricSummary")
        self.metric_summary.setTextFormat(Qt.RichText)
        self.metric_summary.setWordWrap(True)
        self.metric_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.metric_summary.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 600; "
            f"font-family: {FONT_FAMILY_MONO};"
        )
        layout.addWidget(self.metric_summary)

        inspector_row = QHBoxLayout()
        self.metric_inspect_badge = QLabel("")
        self.metric_inspect_badge.setObjectName("metricInspectBadge")
        self.metric_inspect_badge.setStyleSheet(
            badge_style(COLOR_INTERACTIVE_IDLE, font_size=13, padding="4px 10px")
        )
        self.metric_inspect_badge.setVisible(False)
        inspector_row.addWidget(self.metric_inspect_badge, 0, Qt.AlignTop)
        self.metric_inspector = QLabel("")
        self.metric_inspector.setObjectName("metricInspector")
        self.metric_inspector.setWordWrap(True)
        self.metric_inspector.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 18px; font-family: {FONT_FAMILY_MONO};"
        )
        inspector_row.addWidget(self.metric_inspector, 1)
        layout.addLayout(inspector_row)

        self.metric_result = BookMatrixWidget()
        self.metric_result.setObjectName("metricResult")
        self.metric_result.setMinimumHeight(180)
        self.metric_result.set_empty_text("Elige una operación y pulsa Calcular")
        self.metric_result.cellClicked.connect(self._on_outer_cell_clicked)
        layout.addWidget(self.metric_result)

        self.metric_stepper = AlgorithmStepperCarousel(variable_headers=False)
        self.metric_stepper.setObjectName("metricStepper")
        self.metric_stepper.setMinimumHeight(220)
        self.metric_stepper.set_export_title("Métricas vectoriales")
        layout.addWidget(self.metric_stepper)
        layout.addStretch(1)

        self._on_metric_inputs_changed()
        return container

    def _metric(self) -> int:
        return self.metric_group.checkedId()

    def _on_metric_u_dimension(self, dimension: int) -> None:
        self.metric_u.set_dimension(dimension)
        self._on_metric_inputs_changed()

    def _on_metric_v_dimension(self, dimension: int) -> None:
        self.metric_v.set_dimension(dimension)
        self._on_metric_inputs_changed()

    def _on_metric_inputs_changed(self, *_args) -> None:
        self._outer_matrix = None
        self._set_metric_inspected(None)
        self.metric_summary.clear()
        self.metric_result.clear()
        self.metric_stepper.set_steps([])
        self._refresh_metric_badge()

    def swap_metric_operands(self) -> None:
        u_values, v_values = self.metric_u.raw_values(), self.metric_v.raw_values()
        self.metric_u.set_raw_values(v_values)
        self.metric_v.set_raw_values(u_values)
        for spin, n in ((self.metric_u_dim, len(v_values)), (self.metric_v_dim, len(u_values))):
            spin.blockSignals(True)
            spin.setValue(n)
            spin.blockSignals(False)
        self._on_metric_inputs_changed()
        show_toast(self, "Se intercambiaron u y v.", action_text="Deshacer", action=self.swap_metric_operands)

    def match_metric_dimensions(self) -> None:
        self.metric_v_dim.setValue(self.metric_u_dim.value())

    def _metric_problem(self) -> str:
        op = self._metric()
        if op == _METRIC_NORM_U:
            return self.metric_u.validation_message()
        if op == _METRIC_NORM_V:
            return self.metric_v.validation_message()
        return self.metric_u.validation_message() or self.metric_v.validation_message()

    def _refresh_metric_badge(self) -> None:
        if not hasattr(self, "metric_compute_btn"):
            return
        n_u, n_v = self.metric_u_dim.value(), self.metric_v_dim.value()
        same_dimension = n_u == n_v
        self.metric_fix_dims_btn.setVisible(not same_dimension)
        self.distance_btn.setToolTip(
            "d(u, v) = ‖u − v‖ (misma dimensión)"
            if same_dimension
            else f"Pide la misma dimensión: dim u = {n_u} ≠ dim v = {n_v}"
        )
        problem = self._metric_problem()
        if problem:
            self.metric_badge.setText(f"✕ {problem}")
            self.metric_badge.setStyleSheet(_error_badge())
            self.metric_compute_btn.setEnabled(False)
            return
        op = self._metric()
        if op == _METRIC_DISTANCE and not same_dimension:
            self.metric_badge.setText(
                f"✕ La distancia pide la misma dimensión: dim u = {n_u} ≠ dim v = {n_v}. "
                "Iguala las dimensiones o elige el producto exterior."
            )
            self.metric_badge.setStyleSheet(_error_badge())
            self.metric_compute_btn.setEnabled(False)
            return
        if op == _METRIC_OUTER:
            text = f"✓ u vᵀ es {n_u}×{n_v}: cada entrada es uᵢ · vⱼ. Haz clic en una entrada para inspeccionarla."
        elif op == _METRIC_DISTANCE:
            text = f"✓ u y v están en {_space(n_u)}: d(u, v) = ‖u − v‖ está definida."
        elif same_dimension:
            text = (
                f"✓ u y v están en {_space(n_u)}. La norma, la distancia y el producto exterior están definidos."
            )
        else:
            text = f"✓ La norma está definida. La distancia pide la misma dimensión (u vᵀ es {n_u}×{n_v})."
        self.metric_badge.setText(text)
        self.metric_badge.setStyleSheet(_ok_badge())
        self.metric_compute_btn.setEnabled(True)

    def compute_metric(self) -> None:
        if not self.metric_compute_btn.isEnabled():
            for editor in (self.metric_u, self.metric_v):
                if editor.focus_first_invalid():
                    return
            return
        op = self._metric()
        if op == _METRIC_NORM_U:
            self._compute_norm(self.metric_u.get_vector(), "u")
        elif op == _METRIC_NORM_V:
            self._compute_norm(self.metric_v.get_vector(), "v")
        elif op == _METRIC_DISTANCE:
            self._compute_distance()
        else:
            self._compute_outer_product()

    def _publish_metric(self, summary: str, matrix: Matrix, tracer, *, clickable: bool = False) -> None:
        if "\\" in summary:
            summary = latex_to_book_html(summary)
        self.metric_summary.setText(summary)
        self.metric_result.set_matrix(matrix, split_col=None, show_headers=False, clickable=clickable)
        self.metric_stepper.set_steps(tracer.get_steps())
        self.metric_badge.setText(
            "✓ Cálculo exacto en fracciones."
            + ("  Haz clic en una entrada de u vᵀ para ver de dónde sale." if clickable else "")
        )
        self.metric_badge.setStyleSheet(_ok_badge())

    def _compute_norm(self, vector: Vector, name: str) -> None:
        editor = self.metric_u if name == "u" else self.metric_v
        if not editor.is_valid():
            return
        result = trace_vector_norm(vector)
        self._publish_metric(
            f"‖{name}‖² = {format_scalar(result.squared)}    ‖{name}‖ = {result.display}",
            vector.to_column_matrix(),
            result.tracer,
        )

    def _compute_distance(self) -> None:
        try:
            result = trace_vector_distance(self.metric_u.get_vector(), self.metric_v.get_vector())
        except DimensionMismatchError as exc:
            self.metric_badge.setText(f"✕ {exc}")
            self.metric_badge.setStyleSheet(_error_badge())
            return
        difference = vector_sub(self.metric_u.get_vector(), self.metric_v.get_vector())
        self._publish_metric(
            f"d(u, v)² = {format_scalar(result.squared)}    d(u, v) = {result.display}",
            difference.to_column_matrix(),
            result.tracer,
        )

    def _compute_outer_product(self) -> None:
        if not self.metric_u.is_valid() or not self.metric_v.is_valid():
            return
        result = trace_vector_outer_product(self.metric_u.get_vector(), self.metric_v.get_vector())
        self._publish_metric(
            f"u vᵀ es {result.matrix.rows}×{result.matrix.cols}. Cada entrada es uᵢ · vⱼ.",
            result.matrix,
            result.tracer,
            clickable=True,
        )
        self._outer_matrix = result.matrix

    def _set_metric_inspected(self, cell: Optional[Tuple[int, int]]) -> None:
        self._inspected = cell
        if cell is None:
            self.metric_inspect_badge.setVisible(False)
            self.metric_inspector.clear()
            self.metric_u.highlight_component(None)
            self.metric_v.highlight_component(None)
            return
        row, col = cell
        self.metric_inspect_badge.setText(f"Inspeccionando M{to_subscript(f'{row + 1},{col + 1}')}")
        self.metric_inspect_badge.setVisible(True)

    def inspected_cell(self) -> Optional[Tuple[int, int]]:
        return self._inspected

    def _on_outer_cell_clicked(self, row: int, col: int) -> None:
        """Inspector de u vᵀ: resalta uᵢ en u y vⱼ en v (como A · B en el Módulo 2)."""
        if self._outer_matrix is None:
            return
        u_i = self.metric_u.get_vector()[row]
        v_j = self.metric_v.get_vector()[col]
        self.metric_u.highlight_component(row)
        self.metric_v.highlight_component(col)
        self.metric_result.set_matrix(
            self._outer_matrix,
            split_col=None,
            show_headers=False,
            clickable=True,
            highlight_row=row,
            highlight_col=col,
        )
        self._set_metric_inspected((row, col))
        i, j = to_subscript(row + 1), to_subscript(col + 1)
        self.metric_inspector.setText(
            f"M{to_subscript(f'{row + 1},{col + 1}')} = u{i} · v{j} = "
            f"({format_scalar(u_i)}) · ({format_scalar(v_j)}) = {format_scalar(u_i * v_j)}"
        )

    def _select_metric(self, op: int) -> None:
        self.metric_group.button(op).setChecked(True)
        self._refresh_metric_badge()

    def load_norm_sample(self) -> None:
        """Sesión 5, diapositiva 7: ‖(3, 4)‖ = 5."""
        self.tabs.setCurrentIndex(1)
        self.metric_u_dim.setValue(2)
        self.metric_u.set_vector(Vector([3, 4]))
        self._select_metric(_METRIC_NORM_U)
        self.compute_metric()

    def load_distance_sample(self) -> None:
        """Sesión 5, diapositiva 7: d((1, 2), (4, 6)) = 5."""
        self.tabs.setCurrentIndex(1)
        self.metric_u_dim.setValue(2)
        self.metric_v_dim.setValue(2)
        self.metric_u.set_vector(Vector([1, 2]))
        self.metric_v.set_vector(Vector([4, 6]))
        self._select_metric(_METRIC_DISTANCE)
        self.compute_metric()

    def load_outer_product_sample(self) -> None:
        """Sesión 9, diapositiva 15: x xᵀ con x = (1, −2, 3)."""
        self.tabs.setCurrentIndex(1)
        self.metric_u_dim.setValue(3)
        self.metric_v_dim.setValue(3)
        self.metric_u.set_vector(Vector([1, -2, 3]))
        self.metric_v.set_vector(Vector([1, -2, 3]))
        self._select_metric(_METRIC_OUTER)
        self.compute_metric()

    # ======================================================================
    # Subpestaña 3: Σ cᵢ vᵢ = b
    # ======================================================================
    def _build_combination_tab(self) -> QWidget:
        container, layout, _ = _scroll_page(self)

        top = QHBoxLayout()
        top.addWidget(_spin_label("Espacio ℝⁿ   n ="))
        self.combo_dim = QSpinBox()
        self.combo_dim.setRange(2, 10)
        self.combo_dim.setValue(3)
        self.combo_dim.setAccessibleName("Dimensión del espacio")
        self.combo_dim.valueChanged.connect(self._on_combo_dimension)
        top.addWidget(self.combo_dim)
        top.addStretch(1)
        top.addWidget(_sample_button("Ejemplo SCD", "Combinación única: b = 2e₁ − ½e₂ + 3e₃", self.load_combination_scd_sample))
        top.addWidget(_sample_button("Ejemplo SCI", "Infinitas combinaciones: v₃ = v₁ + v₂", self.load_combination_sci_sample))
        top.addWidget(_sample_button("Ejemplo SI", "b = e₃ no está en el plano generado por e₁ y e₂", self.load_combination_si_sample))
        layout.addLayout(top)

        body = QHBoxLayout()
        self.combo_set = VectorSetEditor(
            "Conjunto {v₁, …, vₖ}",
            3,
            initial_count=2,
            min_dimension=2,
            crowded_hint=_crowded_combination,
            extra_paste_actions=(("[v₁ … vₖ | b]: la última columna es b", self.paste_augmented_combination),),
        )
        self.combo_set.changed.connect(self._on_combo_inputs_changed)
        self.combo_set.dimensionChanged.connect(self._on_combo_editor_dimension_changed)
        self.combo_set.submitRequested.connect(self._evaluate_combination)
        self._combo_editors = self.combo_set.editors
        body.addWidget(self.combo_set, stretch=3)

        self.target_editor = VectorColumnEditor(3, "Vector objetivo  b")
        self.target_editor.setObjectName("targetVector")
        self.target_editor.setStyleSheet(
            f"QFrame#targetVector {{ border: 2px solid {COLOR_INTERACTIVE_IDLE}; border-radius: 8px; }}"
        )
        self.target_editor.dimensionChanged.connect(self._on_combo_editor_dimension_changed)
        self.target_editor.changed.connect(self._on_combo_inputs_changed)
        self.target_editor.submitRequested.connect(self._evaluate_combination)
        body.addWidget(self.target_editor, 0, Qt.AlignTop)
        layout.addLayout(body)

        actions = QHBoxLayout()
        self.combo_input_hint = QLabel("")
        self.combo_input_hint.setObjectName("comboInputHint")
        self.combo_input_hint.setWordWrap(True)
        self.combo_input_hint.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 14px; font-weight: 600;")
        actions.addWidget(self.combo_input_hint, 1)
        self.combo_btn = QPushButton("▶ Evaluar combinación lineal")
        self.combo_btn.setObjectName("primaryAction")
        self.combo_btn.setToolTip("Evaluar (Ctrl+Enter desde cualquier celda)")
        self.combo_btn.clicked.connect(self._evaluate_combination)
        actions.addWidget(self.combo_btn)
        layout.addLayout(actions)

        results = QFrame()
        apply_widget_class(results, "elevated-card")
        res_layout = QVBoxLayout(results)
        self.combo_badge = QLabel("Esperando evaluación")
        self.combo_badge.setAlignment(Qt.AlignCenter)
        self.combo_badge.setWordWrap(True)
        self.combo_badge.setStyleSheet(idle_badge_style())
        res_layout.addWidget(self.combo_badge)

        self.combo_summary = QLabel("")
        self.combo_summary.setWordWrap(True)
        self.combo_summary.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 600; "
            f"font-family: {FONT_FAMILY_MONO}; padding: 8px 0;"
        )
        self.combo_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        res_layout.addWidget(self.combo_summary)

        self.combo_checklist = QVBoxLayout()
        self.combo_checklist.setSpacing(10)
        res_layout.addLayout(self.combo_checklist)

        steps_row = QHBoxLayout()
        self.show_steps_btn = QPushButton("Ver procedimiento de escalonamiento")
        self.show_steps_btn.setObjectName("secondaryAction")
        self.show_steps_btn.setCheckable(True)
        self.show_steps_btn.clicked.connect(self._toggle_combo_steps)
        self.show_steps_btn.setEnabled(False)
        steps_row.addWidget(self.show_steps_btn)
        self.combo_contradiction_btn = QPushButton("Ir a la fila contradictoria")
        apply_widget_class(self.combo_contradiction_btn, "link-action")
        self.combo_contradiction_btn.setCursor(Qt.PointingHandCursor)
        self.combo_contradiction_btn.clicked.connect(self.show_combination_contradiction)
        self.combo_contradiction_btn.setVisible(False)
        steps_row.addWidget(self.combo_contradiction_btn)
        steps_row.addStretch(1)
        res_layout.addLayout(steps_row)

        self.combo_stepper = AlgorithmStepperCarousel(alert_mode=ALERT_SYSTEM)
        self.combo_stepper.set_export_title("Combinación lineal: escalonamiento de [v₁ … vₖ | b]")
        self.combo_stepper.setVisible(False)
        res_layout.addWidget(self.combo_stepper)
        layout.addWidget(results)
        layout.addStretch(1)

        self._refresh_combo_inputs()
        return container

    def _on_combo_dimension(self, n: int) -> None:
        self.combo_set.set_dimension(n)
        self.target_editor.set_dimension(n)
        self._on_combo_inputs_changed()

    def _on_combo_editor_dimension_changed(self, n: int) -> None:
        if 2 <= n <= 10 and self.combo_dim.value() != n:
            self.combo_dim.setValue(n)

    def _on_combo_inputs_changed(self, *_args) -> None:
        self._refresh_combo_inputs()
        self._mark_stale(self.combo_badge, "combo")

    def _mark_stale(self, badge: QLabel, which: str) -> None:
        """Los datos cambiaron: el veredicto anterior ya no describe lo que se ve."""
        if not getattr(self, f"_{which}_has_result", False):
            return
        setattr(self, f"_{which}_has_result", False)
        badge.setText("Datos modificados: vuelve a evaluar para actualizar el resultado.")
        badge.setStyleSheet(idle_badge_style())
        if which == "combo":
            self.combo_summary.clear()
            self._clear_combo_checklist()
            self.combo_contradiction_btn.setVisible(False)
            self.combo_stepper.set_steps([])
            self.show_steps_btn.setEnabled(False)
        else:
            self.indep_summary.clear()
            self._clear_indep_checklist()
            self.indep_stepper.set_steps([])
            self.indep_show_steps_btn.setEnabled(False)

    def _combo_problem(self) -> str:
        return self.combo_set.validation_message() or self.target_editor.validation_message()

    def _refresh_combo_inputs(self) -> None:
        # Los errores del conjunto ya se explican dentro de su tarjeta; aquí solo los de b.
        target_problem = self.target_editor.validation_message()
        self.combo_input_hint.setText(f"✕  {target_problem}" if target_problem else "")
        self.combo_btn.setEnabled(not self._combo_problem())

    def _add_combo_vector(self) -> None:
        self.combo_set.add_vector()

    def _remove_combo_vector(self, editor: VectorColumnEditor) -> None:
        self.combo_set.remove_vector(editor, offer_undo=False)

    def paste_augmented_combination(self) -> bool:
        """Pega [v₁ … vₖ | b]: las primeras columnas son el conjunto y la última es b."""
        matrix = get_matrix_from_clipboard()
        if matrix is None or matrix.cols < 2:
            show_toast(
                self,
                "Copia una matriz con al menos dos columnas: los vectores v₁ … vₖ y, al final, b.",
                kind="error",
            )
            return False
        before_set = self.combo_set.snapshot()
        before_target = self.target_editor.raw_values()
        generators = Matrix([[matrix.get(r, c) for c in range(matrix.cols - 1)] for r in range(matrix.rows)])
        if not self.combo_set.paste_matrix(generators):
            return False
        self.target_editor.set_vector(Vector([matrix.get(r, matrix.cols - 1) for r in range(matrix.rows)]))

        def undo() -> None:
            self.combo_set.restore(before_set)
            self.target_editor.set_raw_values(before_target)

        show_toast(
            self,
            f"Se cargaron {matrix.cols - 1} vectores y b desde [v₁ … vₖ | b].",
            kind="success",
            action_text="Deshacer",
            action=undo,
        )
        return True

    def _clear_combo_checklist(self) -> None:
        while self.combo_checklist.count():
            item = self.combo_checklist.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _check_row(self, text: str, color: str) -> QLabel:
        row = QLabel(text)
        row.setWordWrap(True)
        row.setMinimumHeight(48)
        row.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        row.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: 600; "
            f"font-family: {FONT_FAMILY_MONO}; padding: 10px 12px; "
            f"background-color: {COLOR_SURFACE_INNER}; border-radius: 6px;"
        )
        return row

    def _evaluate_combination(self) -> None:
        problem = self._combo_problem()
        if problem:
            self._refresh_combo_inputs()
            if not self.combo_set.focus_first_invalid():
                self.target_editor.focus_first_invalid()
            return
        try:
            vectors = self.combo_set.vectors()
            target = self.target_editor.get_vector()
            result = evaluate_linear_combination(vectors, target)
        except (DimensionMismatchError, ValueError) as exc:
            self.combo_input_hint.setText(f"✕  {exc}")
            return

        self._clear_combo_checklist()
        self.show_steps_btn.setEnabled(True)
        self.combo_stepper.set_steps(result.tracer.get_steps())
        self._combo_contradiction_step = None
        self._combo_has_result = True

        if result.system_type == SystemType.CONSISTENT_DETERMINED:
            self.combo_badge.setText("SÍ ES COMBINACIÓN LINEAL ÚNICA  (SCD)")
            self.combo_badge.setStyleSheet(_ok_badge())
        elif result.system_type == SystemType.CONSISTENT_INDETERMINED:
            self.combo_badge.setText("SÍ ES COMBINACIÓN LINEAL  (infinitas combinaciones, SCI)")
            self.combo_badge.setStyleSheet(_warn_badge())
        else:
            self.combo_badge.setText("NO ES COMBINACIÓN LINEAL  (SI)")
            self.combo_badge.setStyleSheet(_error_badge())

        lines: List[str] = []
        if result.weights is not None:
            lines.append(f"b  =  {format_combination_equation(vectors, result.weights)}")
            weight_bits = [f"c{i + 1} = {format_scalar(c)}" for i, c in enumerate(result.weights)]
            lines.append("Pesos:  " + " ,  ".join(weight_bits))
        if result.parametric_solution:
            lines.append(f"Solución paramétrica:  {result.parametric_solution}")
        if result.system_type == SystemType.INCONSISTENT:
            k = len(vectors)
            names = (
                ", ".join(f"v{to_subscript(i + 1)}" for i in range(k))
                if k <= 3
                else f"v₁, …, v{to_subscript(k)}"
            )
            lines.append(f"b ∉ gen{{{names}}}: A c = b no tiene solución.")
        self.combo_summary.setText("\n".join(lines))

        for label, got, expected, ok in result.verification_checklist:
            mark = "✓" if ok else "✗"
            color = COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR
            self.combo_checklist.addWidget(
                self._check_row(f"{mark}    {label}:    {format_scalar(got)}  =  {format_scalar(expected)}", color)
            )

        inconsistent = result.system_type == SystemType.INCONSISTENT
        if inconsistent:
            self.combo_checklist.addWidget(
                self._check_row(self._contradiction_text(result, len(vectors)), COLOR_FEEDBACK_ERROR)
            )
            self._combo_contradiction_step = self.combo_stepper.first_alert_index()
        self.combo_contradiction_btn.setVisible(inconsistent and self._combo_contradiction_step is not None)

    @staticmethod
    def _contradiction_text(result, k: int) -> str:
        """«Fila 3: 0·c₁ + 0·c₂ = 1  ⇒  0 = 1, imposible» con los valores reales."""
        analysis = result.analysis
        value = analysis.inconsistent_value
        row = analysis.inconsistent_row
        if value is None or row is None:
            return "Contradicción: aparece una fila [0 … 0 | c ≠ 0]."
        lhs = " + ".join(f"0·c{to_subscript(j + 1)}" for j in range(k))
        shown = format_scalar(value)
        return f"Contradicción en la fila {row + 1} de la forma escalonada:  {lhs} = {shown}  ⇒  0 = {shown}, imposible."

    def show_combination_contradiction(self) -> None:
        if self._combo_contradiction_step is None:
            return
        self.show_steps_btn.setChecked(True)
        self.combo_stepper.setVisible(True)
        self.combo_stepper.go_to_step(self._combo_contradiction_step)

    def _toggle_combo_steps(self) -> None:
        self.combo_stepper.setVisible(self.show_steps_btn.isChecked())

    def _load_combination(self, vectors: List[Vector], target: Vector) -> None:
        self.tabs.setCurrentIndex(2)
        self.combo_dim.setValue(target.dimension)
        self.combo_set.set_vectors(vectors)
        self.target_editor.set_vector(target)
        self._evaluate_combination()

    def load_combination_scd_sample(self) -> None:
        self._load_combination(
            [Vector([1, 0, 0]), Vector([0, 1, 0]), Vector([0, 0, 1])],
            Vector([2, "-1/2", 3]),
        )

    def load_combination_sci_sample(self) -> None:
        self._load_combination(
            [Vector([1, 0, 1]), Vector([0, 1, 1]), Vector([1, 1, 2])],
            Vector([2, 3, 5]),
        )

    def load_combination_si_sample(self) -> None:
        self._load_combination([Vector([1, 0, 0]), Vector([0, 1, 0])], Vector([0, 0, 1]))

    # ======================================================================
    # Subpestaña 4: independencia lineal
    # ======================================================================
    def _build_independence_tab(self) -> QWidget:
        container, layout, _ = _scroll_page(self)

        top = QHBoxLayout()
        top.addWidget(_spin_label("Espacio ℝⁿ   n ="))
        self.indep_dim = QSpinBox()
        self.indep_dim.setRange(1, 10)
        self.indep_dim.setValue(3)
        self.indep_dim.setAccessibleName("Dimensión del espacio")
        self.indep_dim.valueChanged.connect(self._on_indep_dimension)
        top.addWidget(self.indep_dim)
        top.addStretch(1)
        top.addWidget(_sample_button("Ejemplo L.I.", "Base canónica de ℝ³", self.load_independence_li_sample))
        top.addWidget(_sample_button("Ejemplo L.D.", "v₃ = v₁ + v₂", self.load_independence_ld_sample))
        top.addWidget(_sample_button("Ejemplo k > n (L.D.)", "Cuatro vectores en ℝ³", self.load_independence_dim_sample))
        theorems_btn = QPushButton("Teoremas clave")
        theorems_btn.setObjectName("secondaryAction")
        theorems_btn.setCursor(Qt.PointingHandCursor)
        theorems_btn.clicked.connect(self.show_theorems_dialog)
        top.addWidget(theorems_btn)
        layout.addLayout(top)

        self.indep_set = VectorSetEditor(
            "Conjunto de vectores {v₁, …, vₖ}",
            3,
            initial_count=3,
            min_dimension=1,
            crowded_hint=_crowded_independence,
        )
        self.indep_set.changed.connect(self._on_indep_inputs_changed)
        self.indep_set.dimensionChanged.connect(self._on_indep_editor_dimension_changed)
        self.indep_set.submitRequested.connect(self._evaluate_independence)
        self._indep_editors = self.indep_set.editors
        layout.addWidget(self.indep_set)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.indep_btn = QPushButton("▶ Evaluar independencia lineal")
        self.indep_btn.setObjectName("primaryAction")
        self.indep_btn.setToolTip("Evaluar (Ctrl+Enter desde cualquier celda)")
        self.indep_btn.clicked.connect(self._evaluate_independence)
        actions.addWidget(self.indep_btn)
        layout.addLayout(actions)

        results = QFrame()
        apply_widget_class(results, "elevated-card")
        res_layout = QVBoxLayout(results)
        self.indep_badge = QLabel("Esperando evaluación")
        self.indep_badge.setAlignment(Qt.AlignCenter)
        self.indep_badge.setWordWrap(True)
        self.indep_badge.setStyleSheet(idle_badge_style())
        res_layout.addWidget(self.indep_badge)

        self.indep_summary = QLabel("")
        self.indep_summary.setWordWrap(True)
        self.indep_summary.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;")
        self.indep_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        res_layout.addWidget(self.indep_summary)

        self.indep_checklist = QVBoxLayout()
        res_layout.addLayout(self.indep_checklist)

        self.indep_show_steps_btn = QPushButton("Ver procedimiento de escalonamiento por filas")
        self.indep_show_steps_btn.setObjectName("secondaryAction")
        self.indep_show_steps_btn.setCheckable(True)
        self.indep_show_steps_btn.clicked.connect(self._toggle_indep_steps)
        self.indep_show_steps_btn.setEnabled(False)
        res_layout.addWidget(self.indep_show_steps_btn, 0, Qt.AlignLeft)

        self.indep_stepper = AlgorithmStepperCarousel()
        self.indep_stepper.set_export_title("Independencia lineal: escalonamiento de [v₁ … vₖ | 0]")
        self.indep_stepper.setVisible(False)
        res_layout.addWidget(self.indep_stepper)
        layout.addWidget(results)
        layout.addStretch(1)

        self._refresh_indep_inputs()
        return container

    def _add_indep_vector(self) -> None:
        self.indep_set.add_vector()

    def _remove_indep_vector(self, editor: VectorColumnEditor) -> None:
        self.indep_set.remove_vector(editor, offer_undo=False)

    def _on_indep_dimension(self, n: int) -> None:
        self.indep_set.set_dimension(n)

    def _on_indep_editor_dimension_changed(self, n: int) -> None:
        if 1 <= n <= 10 and self.indep_dim.value() != n:
            self.indep_dim.setValue(n)

    def _on_indep_inputs_changed(self) -> None:
        self._refresh_indep_inputs()
        self._mark_stale(self.indep_badge, "indep")

    def _clear_indep_checklist(self) -> None:
        while self.indep_checklist.count():
            item = self.indep_checklist.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _refresh_indep_inputs(self) -> None:
        self.indep_btn.setEnabled(self.indep_set.is_valid())

    def _toggle_indep_steps(self) -> None:
        self.indep_stepper.setVisible(self.indep_show_steps_btn.isChecked())

    @staticmethod
    def _names(indices: List[int]) -> str:
        return ", ".join(f"c{to_subscript(c + 1)}" for c in indices)

    def _evaluate_independence(self) -> None:
        if not self.indep_set.is_valid():
            self._refresh_indep_inputs()
            self.indep_set.focus_first_invalid()
            return

        vectors = self.indep_set.vectors()
        res = evaluate_linear_independence(vectors)
        self._last_indep_result = res

        if res.is_linearly_independent:
            self.indep_badge.setText("CONJUNTO LINEALMENTE INDEPENDIENTE (L.I.)")
            self.indep_badge.setStyleSheet(_ok_badge())
        else:
            self.indep_badge.setText("CONJUNTO LINEALMENTE DEPENDIENTE (L.D.)")
            self.indep_badge.setStyleSheet(_error_badge())

        summary_lines = [
            f"<b>• Vectores:</b> k = {res.k} en ℝ^{res.n}",
            f"<b>• Número de pivotes (rango de A):</b> {res.num_pivots}",
            f"<b>• Variables básicas:</b> {self._names(res.basic_variables) if res.basic_variables else 'ninguna'}",
            f"<b>• Variables libres:</b> {self._names(res.free_variables) if res.free_variables else 'ninguna (0)'}",
            "<br><b>Justificación teórica:</b>",
        ]
        if res.is_linearly_independent:
            summary_lines.append("• El número de pivotes coincide con la cantidad de vectores (r = k).")
            summary_lines.append("• El sistema homogéneo A·c = 0 no tiene variables libres.")
            summary_lines.append(
                "• La <b>única solución</b> de c₁·v₁ + … + cₖ·vₖ = 0 es la <b>solución trivial</b>: c₁ = … = cₖ = 0."
            )
        else:
            summary_lines.append(
                f"• El número de pivotes (r = {res.num_pivots}) es menor que la cantidad de vectores (k = {res.k})."
            )
            summary_lines.append(
                f"• Hay {len(res.free_variables)} variable(s) libre(s): existen "
                "<b>infinitas soluciones no triviales</b> (c ≠ 0)."
            )
            if res.theorem_k_greater_n:
                summary_lines.append(
                    f"• <b>Teorema de la dimensión:</b> k = {res.k} > n = {res.n}. En ℝ^{res.n} ningún "
                    f"conjunto de más de {res.n} vectores puede ser L.I."
                )
            if res.zero_vector_index is not None:
                summary_lines.append(
                    f"• <b>Teorema del vector nulo:</b> v{to_subscript(res.zero_vector_index + 1)} es el vector "
                    "cero. Todo conjunto que contiene a 0 es L.D."
                )
        self.indep_summary.setText("<br>".join(summary_lines))

        self._clear_indep_checklist()
        self._indep_has_result = True

        if not res.is_linearly_independent and res.nontrivial_weights:
            title_lbl = QLabel("<b>Combinación lineal no trivial que da el vector cero:</b>")
            title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; margin-top: 8px;")
            self.indep_checklist.addWidget(title_lbl)

            terms = [
                f"({format_scalar(w)})·v{to_subscript(i + 1)}"
                for i, w in enumerate(res.nontrivial_weights)
                if w != Fraction(0, 1)
            ]
            eq_lbl = QLabel(f"   {' + '.join(terms)} = 0")
            eq_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            eq_lbl.setWordWrap(True)
            eq_lbl.setStyleSheet(
                f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-family: {FONT_FAMILY_MONO}; "
                f"font-weight: 600; padding: 8px 12px; background-color: {COLOR_SURFACE_INNER}; border-radius: 4px;"
            )
            self.indep_checklist.addWidget(eq_lbl)

            for label, val, _matches in res.verification_checklist:
                row = QLabel(f"   ✓ {label}: Σ cᵢ·vᵢ = {format_scalar(val)} (coincide con 0)")
                row.setStyleSheet(
                    f"color: {COLOR_FEEDBACK_SUCCESS}; font-size: 22px; font-weight: 600; "
                    f"font-family: {FONT_FAMILY_MONO}; padding: 6px 10px; "
                    f"background-color: {COLOR_SURFACE_INNER}; border-radius: 4px;"
                )
                self.indep_checklist.addWidget(row)

        self.indep_stepper.set_steps(res.tracer.get_steps())
        self.indep_show_steps_btn.setEnabled(True)

    def _load_independence(self, vectors: List[Vector]) -> None:
        self.tabs.setCurrentIndex(3)
        self.indep_dim.setValue(vectors[0].dimension)
        self.indep_set.set_vectors(vectors)
        self._evaluate_independence()

    def load_independence_li_sample(self) -> None:
        self._load_independence([Vector([1, 0, 0]), Vector([0, 1, 0]), Vector([0, 0, 1])])

    def load_independence_ld_sample(self) -> None:
        self._load_independence([Vector([1, 2, 3]), Vector([4, 5, 6]), Vector([5, 7, 9])])

    def load_independence_dim_sample(self) -> None:
        self._load_independence(
            [Vector([1, 0, 0]), Vector([0, 1, 0]), Vector([0, 0, 1]), Vector([1, 1, 1])]
        )

    THEOREMS_TITLE = "Teoremas clave del Módulo 3"

    def theorems_html(self) -> str:
        return (
            "<h3>Teoremas clave — Módulo 3: vectores e independencia lineal</h3>"
            "<hr>"
            "<p><b>1. Independencia lineal:</b><br>"
            "k vectores de ℝⁿ son L.I. si y solo si la única solución de "
            "<i>c₁·v₁ + c₂·v₂ + … + cₖ·vₖ = 0</i> es la trivial (sin variables libres).</p>"
            "<p><b>2. Dependencia lineal:</b><br>"
            "El conjunto es L.D. si existen escalares no todos nulos cuya combinación da 0; "
            "equivale a que algún vector es combinación lineal de los demás.</p>"
            "<p><b>3. Conexión con la forma escalonada:</b><br>"
            "Si el número de pivotes es <i>r = k</i>, hay 0 variables libres → <b>L.I.</b><br>"
            "Si <i>r &lt; k</i>, hay <i>k − r</i> variables libres → <b>L.D.</b></p>"
            "<p><b>4. Teorema de la dimensión (k &gt; n):</b><br>"
            "Todo conjunto de <i>k &gt; n</i> vectores en ℝⁿ es <b>linealmente dependiente</b>.</p>"
            "<p><b>5. Teorema del vector nulo:</b><br>"
            "Todo conjunto que contiene al vector cero <b>0</b> es <b>linealmente dependiente</b>.</p>"
        )

    def show_theorems_dialog(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(self.THEOREMS_TITLE)
        box.setTextFormat(Qt.RichText)
        box.setText(self.theorems_html())
        box.setStandardButtons(QMessageBox.Ok)
        box.button(QMessageBox.Ok).setText("Entendido")
        apply_message_box_theme(box)
        box.exec()
