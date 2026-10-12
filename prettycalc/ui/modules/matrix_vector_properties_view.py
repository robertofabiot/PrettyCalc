"""Módulo 4: propiedades del producto matriz-vector, A(u + v) = Au + Av y A(c·u) = c(Au).

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).

Sprint 10 (auditoría UI/UX, Módulo 4, flujos 2 y 3):

- «Vincular u y v a n»: con la casilla activa, cambiar las columnas de A
  redimensiona los vectores sin clics extra (Nielsen #7).
- Los lados LHS y RHS se leen en una sola fila cada uno
  ([u+v] → [A(u+v)] y [Au] + [Av] = [Au+Av]); en pantallas angostas se apilan
  (Nielsen #8).
- El escalar c usa el campo común: borde rojo, pista «≈ 1.5» y chips.
- Con c = 0 se explica el caso del vector nulo antes y después de verificar.
- Un único botón «Verificar»; errores en línea con fila y componente.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QButtonGroup,
        QCheckBox,
        QFrame,
        QHBoxLayout,
        QLabel,
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

from prettycalc.core.matrix_vector_ops import (
    DistributivePropertyResult,
    HomogeneityPropertyResult,
    verify_distributive_property,
    verify_homogeneity_property,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.mathtext import format_comparison_row_html, format_steps_to_rich_html, to_superscript
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.responsive import CurrentPageStack, ResponsiveRow
from prettycalc.ui.scalar_field import CANONICAL_SCALARS, ScalarField, ScalarInput
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
from prettycalc.ui.vector_set_editor import VectorColumnEditor

_IDLE_BANNER = "Realiza la verificación para comparar ambos lados de la igualdad."
_IDLE_CHECKLIST = "Pulsa «Verificar» para ver la comparación componente a componente."
_IDLE_STEPS = "El procedimiento detallado aparecerá tras pulsar «Verificar»."


def _badge(ok: bool) -> str:
    return badge_style(COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR, font_size=15)


def _caption(text: str, *, strong: bool = False) -> QLabel:
    label = QLabel(text)
    weight = "600" if strong else "500"
    label.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE}; font-weight: {weight};")
    return label


def _symbol(text: str, size: int = 26) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(f"font-size: {size}px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};")
    return label


def _result_view(min_height: int = 120) -> BookMatrixWidget:
    view = BookMatrixWidget()
    view.setMinimumHeight(min_height)
    view.setMinimumWidth(90)
    view.set_empty_text("—")
    return view


def _labeled(caption: QLabel, view: QWidget) -> QWidget:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    layout.addWidget(caption)
    layout.addWidget(view, 1)
    return box


class MatrixVectorPropertiesView(QWidget):
    """Comprobación interactiva de las propiedades del producto matriz-vector A · x."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixVectorPropertiesView")
        self._mode: str = "distributive"  # "distributive" o "homogeneity"
        self._last_distributive_result: Optional[DistributivePropertyResult] = None
        self._last_homogeneity_result: Optional[HomogeneityPropertyResult] = None
        self._has_result = False
        self._syncing = False
        self._setup_ui()
        self._refresh_validation()

    # ======================================================================
    # Construcción
    # ======================================================================
    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.viewport().setAutoFillBackground(False)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(6, 6, 12, 18)
        root.setSpacing(12)

        # 1. Cabecera: título + acción primaria arriba, ejemplos debajo
        header_card = QFrame()
        apply_widget_class(header_card, "elevated-card")
        header_outer = QVBoxLayout(header_card)
        header_outer.setContentsMargins(14, 10, 14, 10)
        header_outer.setSpacing(8)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("Propiedades del producto matriz-vector  A · x")
        title_lbl.setStyleSheet(f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.formula_lbl = QLabel("A(u + v) = A·u + A·v")
        self.formula_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 500; color: {COLOR_INTERACTIVE_IDLE}; font-family: {FONT_FAMILY_MONO};"
        )
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.formula_lbl)
        header_layout.addLayout(title_box, stretch=1)
        self.verify_btn = QPushButton("▶  Verificar")
        self.verify_btn.setObjectName("primaryAction")
        self.verify_btn.setToolTip("Comprobar la propiedad elegida (Ctrl+Intro desde cualquier celda)")
        self.verify_btn.setCursor(Qt.PointingHandCursor)
        self.verify_btn.clicked.connect(self.verify_current_property)
        self.header_verify_btn = self.verify_btn
        header_layout.addWidget(self.verify_btn, 0, Qt.AlignVCenter)
        header_outer.addLayout(header_layout)

        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(8)
        examples_lbl = QLabel("Ejemplos")
        examples_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        presets_layout.addWidget(examples_lbl)
        for text, tip, slot in (
            ("Distributiva (2×3)", "Ejemplo de A(u + v) = Au + Av", self.load_distributive_sample),
            ("Homogeneidad (2×3)", "Ejemplo de A(c·u) = c(Au) con c = 3/2", self.load_homogeneity_sample),
            ("Caso c = 0", "A(0·u) = 0·(Au): ambos lados son el vector nulo", self.load_zero_scalar_sample),
            ("Incompatible", "Dimensiones que no encajan: muestra el mensaje de error", self.load_incompatible_sample),
        ):
            button = QPushButton(text)
            button.setObjectName("secondaryAction")
            button.setToolTip(tip)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(slot)
            presets_layout.addWidget(button)
        presets_layout.addStretch(1)
        self.reset_btn = QPushButton("Limpiar")
        self.reset_btn.setObjectName("secondaryAction")
        self.reset_btn.setToolTip("Restablece A, u, v y c (se puede deshacer)")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset)
        presets_layout.addWidget(self.reset_btn)
        header_outer.addLayout(presets_layout)
        root.addWidget(header_card)

        # 2. Selector de propiedad
        mode_bar = QHBoxLayout()
        mode_bar.setSpacing(10)
        mode_lbl = QLabel("Propiedad")
        mode_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        mode_bar.addWidget(mode_lbl)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.btn_mode_dist = QPushButton("Distributiva  A(u + v) = Au + Av")
        self.btn_mode_homo = QPushButton("Homogeneidad  A(c·u) = c(Au)")
        for index, button in enumerate((self.btn_mode_dist, self.btn_mode_homo)):
            button.setObjectName("modeToggle")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            self.mode_group.addButton(button, index)
            mode_bar.addWidget(button)
        self.btn_mode_dist.setChecked(True)
        mode_bar.addStretch(1)
        self.mode_group.idClicked.connect(self._on_mode_toggled)
        root.addLayout(mode_bar)

        # 3. Dimensiones
        dim_card = QFrame()
        apply_widget_class(dim_card, "elevated-card")
        dim_layout = QHBoxLayout(dim_card)
        dim_layout.setContentsMargins(12, 8, 12, 8)
        dim_layout.setSpacing(10)

        def spin(label: str, value: int, accessible: str) -> QSpinBox:
            caption = QLabel(label)
            caption.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px;")
            dim_layout.addWidget(caption)
            box = QSpinBox()
            box.setRange(1, 8)
            box.setValue(value)
            box.setAccessibleName(accessible)
            dim_layout.addWidget(box)
            return box

        self.spin_m = spin("A: m", 2, "Filas de A")
        times = QLabel("×")
        times.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 16px;")
        dim_layout.addWidget(times)
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 8)
        self.spin_n.setValue(3)
        self.spin_n.setAccessibleName("Columnas de A")
        dim_layout.addWidget(self.spin_n)
        dim_layout.addSpacing(12)
        self.spin_dim_u = spin("dim u", 3, "Dimensión de u")
        self.lbl_dim_v = QLabel("dim v")
        self.lbl_dim_v.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px;")
        dim_layout.addWidget(self.lbl_dim_v)
        self.spin_dim_v = QSpinBox()
        self.spin_dim_v.setRange(1, 8)
        self.spin_dim_v.setValue(3)
        self.spin_dim_v.setAccessibleName("Dimensión de v")
        dim_layout.addWidget(self.spin_dim_v)
        self.spin_m.valueChanged.connect(self._on_dimension_spinners_changed)
        self.spin_n.valueChanged.connect(self._on_dimension_spinners_changed)
        self.spin_dim_u.valueChanged.connect(self._on_u_dimension_changed)
        self.spin_dim_v.valueChanged.connect(self._on_v_dimension_changed)

        self.link_dims_chk = QCheckBox("Vincular u y v a las columnas de A")
        self.link_dims_chk.setChecked(True)
        self.link_dims_chk.setToolTip(
            "Activa: al cambiar n, u y v se redimensionan solos. Desactívala para explorar dimensiones incompatibles."
        )
        self.link_dims_chk.toggled.connect(self._on_link_toggled)
        dim_layout.addSpacing(12)
        dim_layout.addWidget(self.link_dims_chk)
        self.sync_btn = QPushButton("Igualar a n")
        apply_widget_class(self.sync_btn, "link-action")
        self.sync_btn.setCursor(Qt.PointingHandCursor)
        self.sync_btn.setToolTip("Ajusta dim u y dim v al número de columnas de A")
        self.sync_btn.clicked.connect(self.sync_dimensions)
        dim_layout.addWidget(self.sync_btn)
        dim_layout.addStretch(1)
        root.addWidget(dim_card)

        # 4. Badge de validación
        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setWordWrap(True)
        root.addWidget(self.badge)

        # 5. Entradas
        inputs_card = QFrame()
        apply_widget_class(inputs_card, "elevated-card")
        inputs_layout = QVBoxLayout(inputs_card)
        inputs_layout.setContentsMargins(14, 12, 14, 14)
        inputs_layout.setSpacing(10)
        self.inputs_title = QLabel("")
        self.inputs_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        inputs_layout.addWidget(self.inputs_title)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)
        self.grid_a = DynamicMatrixGrid(initial_rows=2, initial_cols=3, augmented=False)
        self.grid_a.matrixChanged.connect(self._on_matrix_grid_changed)
        self.grid_a.submitRequested.connect(self.verify_current_property)
        body_layout.addWidget(self._wrap_card("Matriz de coeficientes  A", self.grid_a), stretch=4)
        body_layout.addWidget(_symbol("·", 40), 0, Qt.AlignCenter)
        self.vector_controls_stack = CurrentPageStack()
        self.vector_controls_stack.addWidget(self._build_distributive_inputs())
        self.vector_controls_stack.addWidget(self._build_homogeneity_inputs())
        body_layout.addWidget(self.vector_controls_stack, stretch=5)
        inputs_layout.addLayout(body_layout)
        root.addWidget(inputs_card)

        # 6. Resultados
        self.results_tabs = QTabWidget()
        self.results_tabs.addTab(self._build_comparison_tab(), "Comprobación de la igualdad")
        self.results_tabs.addTab(self._build_steps_tab(), "Desglose paso a paso")
        root.addWidget(self.results_tabs)
        root.addStretch(1)

        self.scroll_area.setWidget(content)
        content.setAutoFillBackground(False)
        main_layout.addWidget(self.scroll_area)
        self._apply_mode_texts()

    def _wrap_card(self, title: str, body: QWidget) -> QFrame:
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl)
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(body, stretch=1)
        return card

    def _vector_editor(self, title: str) -> VectorColumnEditor:
        editor = VectorColumnEditor(3, title)
        editor.changed.connect(self._on_inputs_changed)
        editor.submitRequested.connect(self.verify_current_property)
        return editor

    def _build_distributive_inputs(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(_symbol("(", 40), 0, Qt.AlignCenter)
        self.vec_u_dist = self._vector_editor("Vector u")
        layout.addWidget(self.vec_u_dist, stretch=1)
        layout.addWidget(_symbol("+"), 0, Qt.AlignCenter)
        self.vec_v_dist = self._vector_editor("Vector v")
        layout.addWidget(self.vec_v_dist, stretch=1)
        layout.addWidget(_symbol(")", 40), 0, Qt.AlignCenter)
        return container

    def _build_homogeneity_inputs(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(_symbol("(", 40), 0, Qt.AlignCenter)

        scalar_card = QFrame()
        apply_widget_class(scalar_card, "elevated-card")
        scalar_layout = QVBoxLayout(scalar_card)
        scalar_layout.setContentsMargins(10, 8, 10, 8)
        scalar_layout.setSpacing(4)
        c_title = QLabel("Escalar c")
        c_title.setStyleSheet(f"font-weight: 600; color: {COLOR_TEXT_PRIMARY}; font-size: 15px;")
        scalar_layout.addWidget(c_title)
        self.input_c = ScalarField("3", base_tooltip="Escalar c: entero, fracción a/b o decimal")
        self.input_c.setFixedWidth(130)
        self.input_c.textChanged.connect(self._on_inputs_changed)
        self.input_c.returnPressed.connect(self.verify_current_property)
        self.input_c_widget = ScalarInput(self.input_c, presets=CANONICAL_SCALARS, help_text="c ∈ ℝ (ej. 3, −1/2)")
        scalar_layout.addWidget(self.input_c_widget)
        self.c_zero_note = QLabel("c = 0: ambos lados serán el vector nulo de ℝᵐ.")
        self.c_zero_note.setObjectName("cZeroNote")
        self.c_zero_note.setWordWrap(True)
        self.c_zero_note.setStyleSheet(f"color: {COLOR_ACCENT_WARNING}; font-size: 13px; font-weight: 600;")
        self.c_zero_note.setVisible(False)
        scalar_layout.addWidget(self.c_zero_note)
        scalar_layout.addStretch(1)
        layout.addWidget(scalar_card, stretch=1)

        layout.addWidget(_symbol("·", 36), 0, Qt.AlignCenter)
        self.vec_u_homo = self._vector_editor("Vector u")
        layout.addWidget(self.vec_u_homo, stretch=1)
        layout.addWidget(_symbol(")", 40), 0, Qt.AlignCenter)
        return container

    def _build_comparison_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.equality_banner = QLabel(_IDLE_BANNER)
        self.equality_banner.setAlignment(Qt.AlignCenter)
        self.equality_banner.setWordWrap(True)
        self.equality_banner.setStyleSheet(idle_badge_style())
        layout.addWidget(self.equality_banner)

        self.zero_note = QLabel("")
        self.zero_note.setObjectName("zeroScalarNote")
        self.zero_note.setWordWrap(True)
        self.zero_note.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; padding: 10px 12px; "
            f"border-left: 4px solid {COLOR_ACCENT_WARNING}; background: transparent;"
        )
        self.zero_note.setVisible(False)
        layout.addWidget(self.zero_note)

        self.sides_row = ResponsiveRow(breakpoint=1050, spacing=14)

        lhs_card = QFrame()
        apply_widget_class(lhs_card, "elevated-card")
        lhs_layout = QVBoxLayout(lhs_card)
        lhs_layout.setContentsMargins(12, 10, 12, 10)
        lhs_layout.setSpacing(8)
        self.lhs_title = QLabel("Lado izquierdo")
        self.lhs_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        lhs_layout.addWidget(self.lhs_title)
        lhs_row = QHBoxLayout()
        self.lhs_intermediate_lbl = _caption("1. Operación intermedia")
        self.lhs_intermediate_view = _result_view()
        lhs_row.addWidget(_labeled(self.lhs_intermediate_lbl, self.lhs_intermediate_view), 1)
        lhs_row.addWidget(_symbol("→", 22), 0, Qt.AlignCenter)
        self.lhs_final_lbl = _caption("2. Resultado", strong=True)
        self.lhs_final_view = _result_view()
        lhs_row.addWidget(_labeled(self.lhs_final_lbl, self.lhs_final_view), 1)
        lhs_layout.addLayout(lhs_row)
        self.sides_row.add_widget(lhs_card, 1)

        center = QWidget()
        center_box = QVBoxLayout(center)
        center_box.setContentsMargins(0, 0, 0, 0)
        center_box.addStretch(1)
        center_box.addWidget(_symbol("=", 42))
        self.equals_check_lbl = QLabel("≟")
        self.equals_check_lbl.setAlignment(Qt.AlignCenter)
        self.equals_check_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLOR_TEXT_MUTED};")
        center_box.addWidget(self.equals_check_lbl)
        center_box.addStretch(1)
        self.sides_row.add_widget(center)

        rhs_card = QFrame()
        apply_widget_class(rhs_card, "elevated-card")
        rhs_layout = QVBoxLayout(rhs_card)
        rhs_layout.setContentsMargins(12, 10, 12, 10)
        rhs_layout.setSpacing(8)
        self.rhs_title = QLabel("Lado derecho")
        self.rhs_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        rhs_layout.addWidget(self.rhs_title)
        self.rhs_intermediate_lbl = _caption("1. Productos parciales")
        rhs_layout.addWidget(self.rhs_intermediate_lbl)
        rhs_row = QHBoxLayout()
        self.rhs_view1 = _result_view()
        self.rhs_view1_lbl = _caption("A·u")
        rhs_row.addWidget(_labeled(self.rhs_view1_lbl, self.rhs_view1), 1)
        self.rhs_plus_lbl = _symbol("+", 22)
        rhs_row.addWidget(self.rhs_plus_lbl, 0, Qt.AlignCenter)
        self.rhs_view2 = _result_view()
        self.rhs_view2_lbl = _caption("A·v")
        self.rhs_view2_box = _labeled(self.rhs_view2_lbl, self.rhs_view2)
        rhs_row.addWidget(self.rhs_view2_box, 1)
        self.rhs_arrow_lbl = _symbol("=", 22)
        rhs_row.addWidget(self.rhs_arrow_lbl, 0, Qt.AlignCenter)
        self.rhs_final_lbl = _caption("2. Resultado", strong=True)
        self.rhs_final_view = _result_view()
        rhs_row.addWidget(_labeled(self.rhs_final_lbl, self.rhs_final_view), 1)
        rhs_layout.addLayout(rhs_row)
        self.sides_row.add_widget(rhs_card, 1)
        layout.addWidget(self.sides_row)

        checklist_card = QFrame()
        apply_widget_class(checklist_card, "elevated-card")
        chk_layout = QVBoxLayout(checklist_card)
        chk_layout.setContentsMargins(12, 8, 12, 8)
        chk_layout.setSpacing(4)
        chk_title = QLabel("Comprobación componente a componente")
        chk_title.setStyleSheet(f"font-weight: 600; color: {COLOR_INTERACTIVE_IDLE}; font-size: 16px;")
        chk_layout.addWidget(chk_title)
        self.checklist_label = QLabel(_IDLE_CHECKLIST)
        self.checklist_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.checklist_label.setWordWrap(True)
        self.checklist_label.setStyleSheet(
            f"font-family: {FONT_FAMILY_MONO}; font-size: 22px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        chk_layout.addWidget(self.checklist_label)
        layout.addWidget(checklist_card)
        layout.addStretch(1)
        return tab

    def _build_steps_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        header_lbl = QLabel("Desglose de las transformaciones algebraicas")
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(header_lbl)
        self.steps_text = QLabel(_IDLE_STEPS)
        self.steps_text.setWordWrap(True)
        self.steps_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.steps_text.setObjectName("propertySteps")
        self.steps_text.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO}; font-size: 15px; padding: 14px;"
        )
        layout.addWidget(self.steps_text, stretch=1)
        return tab

    # ======================================================================
    # Sincronización
    # ======================================================================
    def _apply_mode_texts(self) -> None:
        if self._mode == "distributive":
            self.formula_lbl.setText("A(u + v) = A·u + A·v")
            self.inputs_title.setText("Datos:  A de tamaño m×n,  u, v ∈ ℝⁿ")
            self.verify_btn.setToolTip("Comprobar A(u + v) = A·u + A·v (Ctrl+Intro)")
        else:
            self.formula_lbl.setText("A(c·u) = c·(A·u)")
            self.inputs_title.setText("Datos:  A de tamaño m×n,  u ∈ ℝⁿ,  c ∈ ℝ")
            self.verify_btn.setToolTip("Comprobar A(c·u) = c·(A·u) (Ctrl+Intro)")
        distributive = self._mode == "distributive"
        self.lbl_dim_v.setVisible(distributive)
        self.spin_dim_v.setVisible(distributive)
        self.rhs_view2_box.setVisible(distributive)
        self.rhs_plus_lbl.setVisible(distributive)

    def _on_mode_toggled(self, btn_id: int) -> None:
        self._mode = "distributive" if btn_id == 0 else "homogeneity"
        self.vector_controls_stack.setCurrentIndex(btn_id)
        self._apply_mode_texts()
        self._clear_results()
        self._refresh_validation()

    def _set_spin(self, spin: QSpinBox, value: int) -> None:
        spin.blockSignals(True)
        spin.setValue(value)
        spin.blockSignals(False)

    def _on_matrix_grid_changed(self) -> None:
        rows, cols = self.grid_a.data_shape()
        self._set_spin(self.spin_m, rows)
        self._set_spin(self.spin_n, cols)
        if self.link_dims_chk.isChecked():
            self._resize_vectors(cols)
        self._on_inputs_changed()

    def _on_dimension_spinners_changed(self) -> None:
        m, n = self.spin_m.value(), self.spin_n.value()
        if self.grid_a.data_shape() != (m, n):
            self.grid_a.resize_to(m, n)
        elif self.link_dims_chk.isChecked():
            self._resize_vectors(n)
        self._on_inputs_changed()

    def _resize_vectors(self, n: int) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            for spin in (self.spin_dim_u, self.spin_dim_v):
                self._set_spin(spin, n)
            for editor in (self.vec_u_dist, self.vec_v_dist, self.vec_u_homo):
                editor.set_dimension(n)
        finally:
            self._syncing = False

    def _on_u_dimension_changed(self) -> None:
        dim = self.spin_dim_u.value()
        self.vec_u_dist.set_dimension(dim)
        self.vec_u_homo.set_dimension(dim)
        self._on_inputs_changed()

    def _on_v_dimension_changed(self) -> None:
        self.vec_v_dist.set_dimension(self.spin_dim_v.value())
        self._on_inputs_changed()

    def _on_link_toggled(self, checked: bool) -> None:
        if checked:
            self.sync_dimensions()
        else:
            self._refresh_validation()

    def sync_dimensions(self) -> None:
        """Ajusta dim(u) y dim(v) para que coincidan con las columnas n de A."""
        _, cols = self.grid_a.data_shape()
        self._resize_vectors(cols)
        self._on_inputs_changed()

    def _on_inputs_changed(self, *_args) -> None:
        self._refresh_validation()
        if self._has_result:
            self._clear_results(stale=True)

    def _first_problem(self) -> str:
        message = self.grid_a.validation_message()
        if message:
            return f"A, {message[0].lower()}{message[1:]}"
        if self._mode == "distributive":
            return self.vec_u_dist.validation_message() or self.vec_v_dist.validation_message()
        if not self.input_c.is_valid():
            return f"Escalar c: {self.input_c.diagnosis().message}"
        return self.vec_u_homo.validation_message()

    def _set_state(self, text: str, ok: bool) -> None:
        self.badge.setText(text)
        self.badge.setStyleSheet(_badge(ok))
        self._enable_action_buttons(ok)

    def _refresh_validation(self) -> None:
        if not hasattr(self, "c_zero_note"):
            return
        m, n = self.grid_a.data_shape()
        c_value = self.input_c.value()
        self.c_zero_note.setVisible(self._mode == "homogeneity" and c_value == 0 and self.input_c.text().strip() != "")
        mismatch = False

        problem = self._first_problem()
        if problem:
            self.sync_btn.setVisible(False)
            self._set_state(f"✕ {problem}", False)
            return

        if self._mode == "distributive":
            dim_u = self.vec_u_dist.grid.num_rows
            dim_v = self.vec_v_dist.grid.num_rows
            mismatch = dim_u != n or dim_v != n
            self.sync_btn.setVisible(mismatch)
            if dim_u != dim_v:
                self._set_state(
                    f"✕ Vectores no conformables: dim(u) = {dim_u} ≠ dim(v) = {dim_v}. "
                    "La suma (u + v) requiere vectores de la misma dimensión.",
                    False,
                )
                return
            if n != dim_u:
                self._set_state(
                    f"✕ Producto no conformable: A tiene {n} columnas pero u y v tienen dimensión {dim_u}. "
                    f"Se requiere que dim(u) = dim(v) = {n} (número de columnas de A).",
                    False,
                )
                return
            self._set_state(
                f"✓ Conformable: A ({m}×{n}) · (u + v) ({n}×1) = A·u ({m}×1) + A·v ({m}×1). "
                f"Ambos lados dan un vector en ℝ{to_superscript(m)}.",
                True,
            )
            return

        dim_u = self.vec_u_homo.grid.num_rows
        self.sync_btn.setVisible(dim_u != n)
        if n != dim_u:
            self._set_state(
                f"✕ Producto no conformable: A tiene {n} columnas pero u tiene dimensión {dim_u}. "
                f"Se requiere que dim(u) = {n} (número de columnas de A).",
                False,
            )
            return
        c_text = format_scalar(c_value) if c_value is not None else self.input_c.text().strip()
        self._set_state(
            f"✓ Conformable: A ({m}×{n}) · ({c_text}·u) ({n}×1) = ({c_text}) · (A·u) ({m}×1). "
            f"Ambos lados dan un vector en ℝ{to_superscript(m)}.",
            True,
        )

    def _enable_action_buttons(self, enabled: bool) -> None:
        self.verify_btn.setEnabled(enabled)

    # ======================================================================
    # Verificación
    # ======================================================================
    def verify_current_property(self) -> None:
        if not self.verify_btn.isEnabled():
            self._focus_first_invalid()
            return
        if self._mode == "distributive":
            self._verify_distributive()
        else:
            self._verify_homogeneity()
        self.scroll_area.ensureWidgetVisible(self.results_tabs)

    def _focus_first_invalid(self) -> None:
        editors = (
            (self.vec_u_dist, self.vec_v_dist) if self._mode == "distributive" else (self.vec_u_homo,)
        )
        if self.grid_a.focus_first_invalid():
            return
        if self._mode == "homogeneity" and not self.input_c.is_valid():
            self.input_c.setFocus()
            return
        for editor in editors:
            if editor.focus_first_invalid():
                return

    def _show_equality(self, ok: bool, success_text: str) -> None:
        if ok:
            self.equality_banner.setText(success_text)
            self.equality_banner.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS))
            self.equals_check_lbl.setText("✓ =")
            self.equals_check_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_FEEDBACK_SUCCESS};")
        else:
            self.equality_banner.setText("✕ Discrepancia encontrada en la comprobación.")
            self.equality_banner.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
            self.equals_check_lbl.setText("≠")
            self.equals_check_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_FEEDBACK_ERROR};")

    @staticmethod
    def _column(vector: Vector) -> Matrix:
        return vector.to_column_matrix()

    def _verify_distributive(self) -> None:
        try:
            A = self.grid_a.get_matrix()
            u = self.vec_u_dist.get_vector()
            v = self.vec_v_dist.get_vector()
            result = verify_distributive_property(A, u, v)
        except DimensionMismatchError as exc:
            self._set_state(f"✕ {exc}", False)
            return

        self._last_distributive_result = result
        self._has_result = True
        self.zero_note.setVisible(False)
        self._show_equality(
            result.is_equal,
            "✓ ¡PROPIEDAD DISTRIBUTIVA DEMOSTRADA!  A(u + v) = A·u + A·v\n"
            f"Ambos miembros coinciden exactamente en cada componente de ℝ{to_superscript(A.rows)}.",
        )

        self.lhs_title.setText("Lado izquierdo:  A · (u + v)")
        self.lhs_intermediate_lbl.setText(f"1. u + v ∈ ℝ{to_superscript(u.dimension)}")
        self.lhs_intermediate_view.set_matrix(self._column(result.u_plus_v), show_headers=False)
        self.lhs_final_lbl.setText(f"2. A · (u + v) ∈ ℝ{to_superscript(A.rows)}")
        self.lhs_final_view.set_matrix(self._column(result.lhs_result), show_headers=False)

        self.rhs_title.setText("Lado derecho:  A·u + A·v")
        self.rhs_intermediate_lbl.setText("1. Productos parciales A·u y A·v; 2. su suma")
        self.rhs_view1_lbl.setText("A·u")
        self.rhs_view1.set_matrix(self._column(result.Au), show_headers=False)
        self.rhs_view2_lbl.setText("A·v")
        self.rhs_view2.set_matrix(self._column(result.Av), show_headers=False)
        self.rhs_final_lbl.setText("A·u + A·v")
        self.rhs_final_view.set_matrix(self._column(result.rhs_result), show_headers=False)

        rows = []
        for label, lhs_val, rhs_val, ok in result.verification_checklist:
            comp_idx = label.split()[-1] if " " in label else label
            rows.append(
                format_comparison_row_html(
                    "✓" if ok else "✗",
                    label,
                    f"(A·(u + v))_{comp_idx} = {format_scalar(lhs_val)}",
                    f"(A·u + A·v)_{comp_idx} = {format_scalar(rhs_val)}",
                    ok,
                    font_size_px=22,
                )
            )
        self.checklist_label.setTextFormat(Qt.RichText)
        self.checklist_label.setText("".join(rows))

        self.steps_text.setTextFormat(Qt.RichText)
        self.steps_text.setText(
            format_steps_to_rich_html(
                "DEMOSTRACIÓN PASO A PASO: PROPIEDAD DISTRIBUTIVA DEL PRODUCTO MATRIZ-VECTOR: A(u + v) = A·u + A·v",
                [
                    "--- LADO IZQUIERDO (LHS) ---",
                    *result.lhs_steps,
                    "--- LADO DERECHO (RHS) ---",
                    *result.rhs_steps,
                    "--- CONCLUSIÓN FORMAL ---",
                    f"Para toda componente i = 1, ..., {A.rows}:",
                    "  (A(u + v))_i = Σ_j A_ij (u_j + v_j) = Σ_j (A_ij u_j + A_ij v_j) = Σ_j A_ij u_j + Σ_j A_ij v_j = (Au)_i + (Av)_i",
                    "Por lo tanto, la igualdad se cumple en todo ℝᵐ.",
                ],
            )
        )

    def _verify_homogeneity(self) -> None:
        try:
            A = self.grid_a.get_matrix()
            u = self.vec_u_homo.get_vector()
            result = verify_homogeneity_property(A, u, self.input_c.text().strip())
        except DimensionMismatchError as exc:
            self._set_state(f"✕ {exc}", False)
            return

        self._last_homogeneity_result = result
        self._has_result = True
        c_fmt = format_scalar(result.c)
        self._show_equality(
            result.is_equal,
            "✓ ¡PROPIEDAD DE HOMOGENEIDAD DEMOSTRADA!  A(c·u) = c·(A·u)\n"
            f"Con c = {c_fmt}, ambos miembros coinciden en cada componente de ℝ{to_superscript(A.rows)}.",
        )
        if result.c == 0:
            self.zero_note.setText(
                "Caso particular c = 0: 0·u es el vector nulo de ℝⁿ y A·0 = 0; por el otro lado, "
                f"0·(A·u) también es el vector nulo de ℝ{to_superscript(A.rows)}. La propiedad se cumple "
                "trivialmente: cualquier transformación lineal envía 0 a 0."
            )
            self.zero_note.setVisible(True)
        else:
            self.zero_note.setVisible(False)

        self.lhs_title.setText(f"Lado izquierdo:  A · ({c_fmt} · u)")
        self.lhs_intermediate_lbl.setText(f"1. c · u ∈ ℝ{to_superscript(u.dimension)}")
        self.lhs_intermediate_view.set_matrix(self._column(result.cu), show_headers=False)
        self.lhs_final_lbl.setText(f"2. A · (c·u) ∈ ℝ{to_superscript(A.rows)}")
        self.lhs_final_view.set_matrix(self._column(result.lhs_result), show_headers=False)

        self.rhs_title.setText(f"Lado derecho:  {c_fmt} · (A · u)")
        self.rhs_intermediate_lbl.setText("1. Producto A·u; 2. escalado por c")
        self.rhs_view1_lbl.setText("A·u")
        self.rhs_view1.set_matrix(self._column(result.Au), show_headers=False)
        self.rhs_final_lbl.setText(f"{c_fmt} · (A·u)")
        self.rhs_final_view.set_matrix(self._column(result.rhs_result), show_headers=False)

        rows = []
        for label, lhs_val, rhs_val, ok in result.verification_checklist:
            comp_idx = label.split()[-1] if " " in label else label
            rows.append(
                format_comparison_row_html(
                    "✓" if ok else "✗",
                    label,
                    f"(A·(c·u))_{comp_idx} = {format_scalar(lhs_val)}",
                    f"(c·(A·u))_{comp_idx} = {format_scalar(rhs_val)}",
                    ok,
                    font_size_px=22,
                )
            )
        self.checklist_label.setTextFormat(Qt.RichText)
        self.checklist_label.setText("".join(rows))

        self.steps_text.setTextFormat(Qt.RichText)
        self.steps_text.setText(
            format_steps_to_rich_html(
                f"DEMOSTRACIÓN PASO A PASO: PROPIEDAD DE HOMOGENEIDAD: A(c·u) = c·(A·u) (c = {c_fmt})",
                [
                    "--- LADO IZQUIERDO (LHS) ---",
                    *result.lhs_steps,
                    "--- LADO DERECHO (RHS) ---",
                    *result.rhs_steps,
                    "--- CONCLUSIÓN FORMAL ---",
                    f"Para toda componente i = 1, ..., {A.rows}:",
                    "  (A(c u))_i = Σ_j A_ij (c u_j) = c Σ_j A_ij u_j = c (Au)_i = (c (Au))_i",
                    "Por lo tanto, la multiplicación por escalar conmuta con el producto matriz-vector.",
                ],
            )
        )

    def _clear_results(self, *, stale: bool = False) -> None:
        self._has_result = False
        for view in (
            self.lhs_intermediate_view,
            self.lhs_final_view,
            self.rhs_view1,
            self.rhs_view2,
            self.rhs_final_view,
        ):
            view.clear()
        self.equality_banner.setText(
            "Datos modificados: vuelve a verificar para actualizar la comparación." if stale else _IDLE_BANNER
        )
        self.equality_banner.setStyleSheet(idle_badge_style())
        self.equals_check_lbl.setText("≟")
        self.equals_check_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLOR_TEXT_MUTED};")
        self.zero_note.setVisible(False)
        self.checklist_label.setTextFormat(Qt.PlainText)
        self.checklist_label.setText(_IDLE_CHECKLIST)
        self.steps_text.setTextFormat(Qt.PlainText)
        self.steps_text.setText(_IDLE_STEPS)

    # ======================================================================
    # Ejemplos
    # ======================================================================
    def _select_mode(self, index: int) -> None:
        self.mode_group.button(index).setChecked(True)
        self._on_mode_toggled(index)

    def load_distributive_sample(self) -> None:
        """Caso canónico 2×3 para la propiedad distributiva."""
        self._select_mode(0)
        self.link_dims_chk.setChecked(True)
        self.grid_a.set_matrix(Matrix([[2, -1, 3], [1, 0, -2]]))
        self.vec_u_dist.set_vector(Vector([1, 2, -1]))
        self.vec_v_dist.set_vector(Vector([3, -1, 4]))
        self._refresh_validation()
        self.verify_current_property()

    def load_homogeneity_sample(self) -> None:
        """Caso canónico 2×3 con escalar fraccionario."""
        self._select_mode(1)
        self.link_dims_chk.setChecked(True)
        self.grid_a.set_matrix(Matrix([[1, 2, -1], [-3, 4, 2]]))
        self.vec_u_homo.set_vector(Vector([2, -1, 3]))
        self.input_c.setText("3/2")
        self._refresh_validation()
        self.verify_current_property()

    def load_zero_scalar_sample(self) -> None:
        """c = 0: ambos lados son el vector nulo."""
        self.load_homogeneity_sample()
        self.input_c.setText("0")
        self.verify_current_property()

    def load_incompatible_sample(self) -> None:
        """Dimensiones incompatibles a propósito (desvincula u y v de n)."""
        self._select_mode(0)
        self.link_dims_chk.setChecked(False)
        self.grid_a.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
        self.spin_dim_u.setValue(2)
        self.spin_dim_v.setValue(2)
        self.vec_u_dist.set_vector(Vector([1, 2]))
        self.vec_v_dist.set_vector(Vector([3, 4]))
        self._refresh_validation()

    def reset(self) -> None:
        """Restablece A, u, v y c; un aviso permite deshacerlo."""
        before = (
            self.grid_a.snapshot(),
            self.vec_u_dist.raw_values(),
            self.vec_v_dist.raw_values(),
            self.vec_u_homo.raw_values(),
            self.input_c.text(),
            self.link_dims_chk.isChecked(),
        )
        self.link_dims_chk.setChecked(True)
        self.grid_a.set_matrix(Matrix.zeros(2, 3))
        self._resize_vectors(3)
        for editor in (self.vec_u_dist, self.vec_v_dist, self.vec_u_homo):
            editor.set_vector(Vector([0, 0, 0]))
        self.input_c.setText("1")
        self._clear_results()
        self.results_tabs.setCurrentIndex(0)
        self._refresh_validation()

        def undo() -> None:
            _grid, u_dist, v_dist, u_homo, c_text, linked = before
            self.link_dims_chk.blockSignals(True)
            self.link_dims_chk.setChecked(linked)
            self.link_dims_chk.blockSignals(False)
            self.grid_a.undo()
            self.vec_u_dist.set_raw_values(u_dist)
            self.vec_v_dist.set_raw_values(v_dist)
            self.vec_u_homo.set_raw_values(u_homo)
            self._set_spin(self.spin_dim_u, len(u_dist))
            self._set_spin(self.spin_dim_v, len(v_dist))
            self.input_c.setText(c_text)
            self._refresh_validation()

        show_toast(self, "Se restablecieron A, u, v y c.", action_text="Deshacer", action=undo)
