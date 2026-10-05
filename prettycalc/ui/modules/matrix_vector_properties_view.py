"""Vista de propiedades del producto matriz-vector: A(u + v) = Au + Av y A(c·u) = c(Au)."""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
        QButtonGroup,
        QStackedWidget,
        QLineEdit,
        QSpinBox,
        QScrollArea,
        QSizePolicy,
        QTabWidget,
        QMessageBox,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.matrix_vector_ops import (
    DistributivePropertyResult,
    HomogeneityPropertyResult,
    verify_distributive_property,
    verify_homogeneity_property,
)
from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    Vector,
    format_scalar,
    parse_scalar,
)
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.mathtext import to_superscript
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.modules.vectors_view import VectorColumnEditor
from prettycalc.ui.theme import (
    COLOR_BG_BASE,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
    apply_message_box_theme,
    apply_widget_class,
)


def _badge_style(ok: bool) -> str:
    bg = COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR
    fg = COLOR_BG_BASE if ok else COLOR_TEXT_PRIMARY
    return (
        f"background-color: {bg}; color: {fg}; font-weight: 600; font-size: 15px; "
        f"padding: 10px 14px; border-radius: 6px; font-family: {FONT_FAMILY_SANS};"
    )


class MatrixVectorPropertiesView(QWidget):
    """Vista interactiva para comprobar las propiedades del producto matriz-vector A · x."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixVectorPropertiesView")
        self._mode: str = "distributive"  # "distributive" o "homogeneity"
        self._last_distributive_result: Optional[DistributivePropertyResult] = None
        self._last_homogeneity_result: Optional[HomogeneityPropertyResult] = None
        self._setup_ui()
        self._refresh_validation()

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

        # 1. Cabecera con título y presets
        header_card = QFrame()
        apply_widget_class(header_card, "elevated-card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("Propiedades del Producto Matriz-Vector  A · x")
        title_lbl.setStyleSheet(
            f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        self.formula_lbl = QLabel("A(u + v) = A·u + A·v")
        self.formula_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 500; color: {COLOR_INTERACTIVE_IDLE}; "
            f"font-family: {FONT_FAMILY_MONO};"
        )
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.formula_lbl)
        header_layout.addLayout(title_box, stretch=1)

        # Botones de presets
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(8)

        sample_dist = QPushButton("Ejemplo Distributiva (2×3)")
        sample_dist.setToolTip("Cargar ejemplo de A(u + v) = Au + Av")
        sample_dist.setCursor(Qt.PointingHandCursor)
        sample_dist.clicked.connect(self.load_distributive_sample)
        presets_layout.addWidget(sample_dist)

        sample_homo = QPushButton("Ejemplo Homogeneidad (2×3)")
        sample_homo.setToolTip("Cargar ejemplo de A(c·u) = c·(Au)")
        sample_homo.setCursor(Qt.PointingHandCursor)
        sample_homo.clicked.connect(self.load_homogeneity_sample)
        presets_layout.addWidget(sample_homo)

        sample_incomp = QPushButton("Ejemplo Incompatible")
        sample_incomp.setToolTip("Cargar dimensiones incompatibles para verificar validación de error")
        sample_incomp.setCursor(Qt.PointingHandCursor)
        sample_incomp.clicked.connect(self.load_incompatible_sample)
        presets_layout.addWidget(sample_incomp)

        reset_btn = QPushButton("Limpiar")
        reset_btn.setObjectName("secondaryAction")
        reset_btn.setToolTip("Restablecer matriz y vectores a cero")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.reset)
        presets_layout.addWidget(reset_btn)

        self.header_verify_btn = QPushButton("▶  Verificar Propiedad")
        self.header_verify_btn.setObjectName("primaryAction")
        self.header_verify_btn.setToolTip("Ejecutar la comprobación algebraica paso a paso")
        self.header_verify_btn.setCursor(Qt.PointingHandCursor)
        self.header_verify_btn.clicked.connect(self.verify_current_property)
        presets_layout.addWidget(self.header_verify_btn)

        header_layout.addLayout(presets_layout)
        root.addWidget(header_card)

        # 2. Selector de propiedad (Modo Distributiva vs Homogeneidad)
        mode_bar = QHBoxLayout()
        mode_bar.setSpacing(10)

        mode_lbl = QLabel("Propiedad a comprobar:")
        mode_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        mode_bar.addWidget(mode_lbl)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        self.btn_mode_dist = QPushButton("1. Propiedad Distributiva:  A(u + v) = A·u + A·v")
        self.btn_mode_dist.setObjectName("modeToggle")
        self.btn_mode_dist.setCheckable(True)
        self.btn_mode_dist.setChecked(True)
        self.mode_group.addButton(self.btn_mode_dist, 0)
        mode_bar.addWidget(self.btn_mode_dist)

        self.btn_mode_homo = QPushButton("2. Homogeneidad / Escalar:  A(c·u) = c·(A·u)")
        self.btn_mode_homo.setObjectName("modeToggle")
        self.btn_mode_homo.setCheckable(True)
        self.mode_group.addButton(self.btn_mode_homo, 1)
        mode_bar.addWidget(self.btn_mode_homo)

        mode_bar.addStretch(1)
        self.mode_group.idClicked.connect(self._on_mode_toggled)
        root.addLayout(mode_bar)

        # 3. Barra de control de dimensiones
        dim_card = QFrame()
        apply_widget_class(dim_card, "elevated-card")
        dim_layout = QHBoxLayout(dim_card)
        dim_layout.setContentsMargins(12, 8, 12, 8)
        dim_layout.setSpacing(14)

        dim_title = QLabel("Dimensiones:")
        dim_title.setStyleSheet(f"font-weight: 600; color: {COLOR_INTERACTIVE_IDLE};")
        dim_layout.addWidget(dim_title)

        # Filas de A (m)
        dim_layout.addWidget(QLabel("Filas A (m):"))
        self.spin_m = QSpinBox()
        self.spin_m.setRange(1, 8)
        self.spin_m.setValue(2)
        self.spin_m.valueChanged.connect(self._on_dimension_spinners_changed)
        dim_layout.addWidget(self.spin_m)

        # Columnas de A (n)
        dim_layout.addWidget(QLabel("Columnas A (n):"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 8)
        self.spin_n.setValue(3)
        self.spin_n.valueChanged.connect(self._on_dimension_spinners_changed)
        dim_layout.addWidget(self.spin_n)

        # Dimensión de u
        dim_layout.addWidget(QLabel("dim(u):"))
        self.spin_dim_u = QSpinBox()
        self.spin_dim_u.setRange(1, 8)
        self.spin_dim_u.setValue(3)
        self.spin_dim_u.valueChanged.connect(self._on_u_dimension_changed)
        dim_layout.addWidget(self.spin_dim_u)

        # Dimensión de v (visible en distributiva)
        self.lbl_dim_v = QLabel("dim(v):")
        self.spin_dim_v = QSpinBox()
        self.spin_dim_v.setRange(1, 8)
        self.spin_dim_v.setValue(3)
        self.spin_dim_v.valueChanged.connect(self._on_v_dimension_changed)
        dim_layout.addWidget(self.lbl_dim_v)
        dim_layout.addWidget(self.spin_dim_v)

        sync_btn = QPushButton("⟳ Sincronizar dimensiones")
        sync_btn.setObjectName("secondaryAction")
        sync_btn.setToolTip("Ajusta la dimensión de los vectores para que coincida con las columnas de A")
        sync_btn.setCursor(Qt.PointingHandCursor)
        sync_btn.clicked.connect(self.sync_dimensions)
        dim_layout.addWidget(sync_btn)

        dim_layout.addStretch(1)
        root.addWidget(dim_card)

        # 4. Badge de validación y compatibilidad dimensional
        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setWordWrap(True)
        root.addWidget(self.badge)

        # 5. Entrada interactiva de Matriz A, Vectores u, v y Escalar c
        inputs_card = QFrame()
        apply_widget_class(inputs_card, "elevated-card")
        inputs_layout = QVBoxLayout(inputs_card)
        inputs_layout.setContentsMargins(14, 12, 14, 14)
        inputs_layout.setSpacing(12)

        self.inputs_title = QLabel("Entrada de Datos:  A ∈ M_{m×n},  u ∈ ℝⁿ,  v ∈ ℝⁿ")
        self.inputs_title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        inputs_layout.addWidget(self.inputs_title)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)

        # Matriz A
        self.grid_a = DynamicMatrixGrid(initial_rows=2, initial_cols=3, augmented=False)
        self.grid_a.matrixChanged.connect(self._on_matrix_grid_changed)
        body_layout.addWidget(self._wrap_card("Matriz de Coeficientes  A", self.grid_a), stretch=4)

        # Operador ·
        dot_lbl = QLabel("·")
        dot_lbl.setAlignment(Qt.AlignCenter)
        dot_lbl.setStyleSheet(
            f"font-size: 34px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 4px;"
        )
        body_layout.addWidget(dot_lbl, 0, Qt.AlignCenter)

        # Stack central para Distributiva (u + v) o Homogeneidad (c · u)
        self.vector_controls_stack = QStackedWidget()
        self.vector_controls_stack.addWidget(self._build_distributive_inputs())
        self.vector_controls_stack.addWidget(self._build_homogeneity_inputs())
        body_layout.addWidget(self.vector_controls_stack, stretch=5)

        inputs_layout.addLayout(body_layout)

        # Botón de verificación principal
        action_bar = QHBoxLayout()
        action_bar.addStretch(1)
        self.verify_btn = QPushButton("Verificar Propiedad Distributiva  A(u + v) = A·u + A·v")
        self.verify_btn.setObjectName("primaryAction")
        self.verify_btn.setMinimumHeight(44)
        self.verify_btn.setCursor(Qt.PointingHandCursor)
        self.verify_btn.clicked.connect(self.verify_current_property)
        action_bar.addWidget(self.verify_btn)
        action_bar.addStretch(1)
        inputs_layout.addLayout(action_bar)

        root.addWidget(inputs_card)

        # 6. Pestañas de Resultados y Demostración
        self.results_tabs = QTabWidget()
        self.results_tabs.setMinimumHeight(420)

        # Pestaña 1: Comparación visual y demostración
        self.results_tabs.addTab(self._build_comparison_tab(), "✓  Demostración y Comprobación")

        # Pestaña 2: Desglose algebraico paso a paso
        self.results_tabs.addTab(self._build_steps_tab(), "📋  Desglose Matemático Paso a Paso")

        root.addWidget(self.results_tabs)

        self.scroll_area.setWidget(content)
        main_layout.addWidget(self.scroll_area)

    def _wrap_card(self, title: str, body: QWidget) -> QFrame:
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(body)
        layout.addWidget(scroll, stretch=1)
        return card

    def _build_distributive_inputs(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        bracket_open = QLabel("(")
        bracket_open.setStyleSheet(
            f"font-size: 40px; font-weight: 300; color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(bracket_open, 0, Qt.AlignCenter)

        # Vector u
        self.vec_u_dist = VectorColumnEditor(3, "Vector u")
        self.vec_u_dist.changed.connect(self._refresh_validation)
        layout.addWidget(self.vec_u_dist, stretch=1)

        plus_lbl = QLabel("+")
        plus_lbl.setAlignment(Qt.AlignCenter)
        plus_lbl.setStyleSheet(
            f"font-size: 26px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(plus_lbl, 0, Qt.AlignCenter)

        # Vector v
        self.vec_v_dist = VectorColumnEditor(3, "Vector v")
        self.vec_v_dist.changed.connect(self._refresh_validation)
        layout.addWidget(self.vec_v_dist, stretch=1)

        bracket_close = QLabel(")")
        bracket_close.setStyleSheet(
            f"font-size: 40px; font-weight: 300; color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(bracket_close, 0, Qt.AlignCenter)

        return container

    def _build_homogeneity_inputs(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        bracket_open = QLabel("(")
        bracket_open.setStyleSheet(
            f"font-size: 40px; font-weight: 300; color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(bracket_open, 0, Qt.AlignCenter)

        # Escalar c
        scalar_card = QFrame()
        apply_widget_class(scalar_card, "elevated-card")
        scalar_layout = QVBoxLayout(scalar_card)
        scalar_layout.setContentsMargins(8, 8, 8, 8)
        scalar_layout.setSpacing(4)
        c_title = QLabel("Escalar c")
        c_title.setStyleSheet(f"font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        c_sub = QLabel("c ∈ ℝ (ej. 3, -1/2)")
        c_sub.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        scalar_layout.addWidget(c_title)
        scalar_layout.addWidget(c_sub)

        self.input_c = QLineEdit("3")
        self.input_c.setObjectName("scalarField")
        self.input_c.setAlignment(Qt.AlignCenter)
        self.input_c.setFont(QFont("Fira Code", 14))
        self.input_c.setMinimumHeight(38)
        self.input_c.textChanged.connect(self._refresh_validation)
        scalar_layout.addWidget(self.input_c)
        scalar_layout.addStretch(1)
        layout.addWidget(scalar_card, stretch=1)

        dot_lbl = QLabel("·")
        dot_lbl.setAlignment(Qt.AlignCenter)
        dot_lbl.setStyleSheet(
            f"font-size: 30px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(dot_lbl, 0, Qt.AlignCenter)

        # Vector u (para homogeneidad)
        self.vec_u_homo = VectorColumnEditor(3, "Vector u")
        self.vec_u_homo.changed.connect(self._refresh_validation)
        layout.addWidget(self.vec_u_homo, stretch=1)

        bracket_close = QLabel(")")
        bracket_close.setStyleSheet(
            f"font-size: 40px; font-weight: 300; color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(bracket_close, 0, Qt.AlignCenter)

        return container

    def _build_comparison_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Banner de estado de igualdad
        self.equality_banner = QLabel("Realiza la verificación para comparar ambos lados de la igualdad.")
        self.equality_banner.setAlignment(Qt.AlignCenter)
        self.equality_banner.setStyleSheet(
            f"background-color: {COLOR_SURFACE_INNER}; color: {COLOR_TEXT_PRIMARY}; "
            f"font-size: 16px; font-weight: 600; padding: 10px; border-radius: 6px;"
        )
        layout.addWidget(self.equality_banner)

        # Comparación lado a lado
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(14)

        # Columna Izquierda: LHS
        lhs_card = QFrame()
        apply_widget_class(lhs_card, "elevated-card")
        lhs_layout = QVBoxLayout(lhs_card)
        lhs_layout.setContentsMargins(12, 10, 12, 10)
        lhs_layout.setSpacing(8)

        self.lhs_title = QLabel("Lado Izquierdo (LHS)")
        self.lhs_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        lhs_layout.addWidget(self.lhs_title)

        self.lhs_intermediate_lbl = QLabel("Paso 1: Operación intermedia")
        self.lhs_intermediate_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE};")
        lhs_layout.addWidget(self.lhs_intermediate_lbl)

        self.lhs_intermediate_view = BookMatrixWidget()
        self.lhs_intermediate_view.setMinimumHeight(110)
        lhs_layout.addWidget(self.lhs_intermediate_view)

        self.lhs_final_lbl = QLabel("Paso 2: Resultado final LHS")
        self.lhs_final_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE}; font-weight: 600;")
        lhs_layout.addWidget(self.lhs_final_lbl)

        self.lhs_final_view = BookMatrixWidget()
        self.lhs_final_view.setMinimumHeight(130)
        lhs_layout.addWidget(self.lhs_final_view, stretch=1)

        columns_layout.addWidget(lhs_card, stretch=1)

        # Símbolo central de igualdad
        center_box = QVBoxLayout()
        center_box.setSpacing(6)
        center_box.addStretch(1)
        eq_big = QLabel("=")
        eq_big.setAlignment(Qt.AlignCenter)
        eq_big.setStyleSheet(f"font-size: 42px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};")
        center_box.addWidget(eq_big)
        self.equals_check_lbl = QLabel("≟")
        self.equals_check_lbl.setAlignment(Qt.AlignCenter)
        self.equals_check_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLOR_TEXT_MUTED};")
        center_box.addWidget(self.equals_check_lbl)
        center_box.addStretch(1)
        columns_layout.addLayout(center_box)

        # Columna Derecha: RHS
        rhs_card = QFrame()
        apply_widget_class(rhs_card, "elevated-card")
        rhs_layout = QVBoxLayout(rhs_card)
        rhs_layout.setContentsMargins(12, 10, 12, 10)
        rhs_layout.setSpacing(8)

        self.rhs_title = QLabel("Lado Derecho (RHS)")
        self.rhs_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        rhs_layout.addWidget(self.rhs_title)

        self.rhs_intermediate_lbl = QLabel("Paso 1: Operaciones parciales")
        self.rhs_intermediate_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE};")
        rhs_layout.addWidget(self.rhs_intermediate_lbl)

        # Para distributiva tenemos Au y Av; para homogeneidad tenemos Au
        self.rhs_intermediate_container = QHBoxLayout()
        self.rhs_view1 = BookMatrixWidget()
        self.rhs_view1.setMinimumHeight(110)
        self.rhs_view2 = BookMatrixWidget()
        self.rhs_view2.setMinimumHeight(110)
        self.rhs_intermediate_container.addWidget(self.rhs_view1)
        self.rhs_intermediate_container.addWidget(self.rhs_view2)
        rhs_layout.addLayout(self.rhs_intermediate_container)

        self.rhs_final_lbl = QLabel("Paso final: Resultado RHS")
        self.rhs_final_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE}; font-weight: 600;")
        rhs_layout.addWidget(self.rhs_final_lbl)

        self.rhs_final_view = BookMatrixWidget()
        self.rhs_final_view.setMinimumHeight(130)
        rhs_layout.addWidget(self.rhs_final_view, stretch=1)

        columns_layout.addWidget(rhs_card, stretch=1)

        layout.addLayout(columns_layout, stretch=1)

        # Tarjeta de Checklist de verificación componente a componente
        checklist_card = QFrame()
        apply_widget_class(checklist_card, "elevated-card")
        chk_layout = QVBoxLayout(checklist_card)
        chk_layout.setContentsMargins(12, 8, 12, 8)
        chk_layout.setSpacing(4)
        chk_title = QLabel("Comprobación rigurosa componente a componente:")
        chk_title.setStyleSheet(f"font-weight: 600; color: {COLOR_INTERACTIVE_IDLE}; font-size: 14px;")
        chk_layout.addWidget(chk_title)

        self.checklist_label = QLabel("Presione 'Verificar Propiedad' para ver la comparación fila a fila.")
        self.checklist_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.checklist_label.setStyleSheet(
            f"font-family: {FONT_FAMILY_MONO}; font-size: 14px; color: {COLOR_TEXT_PRIMARY};"
        )
        chk_layout.addWidget(self.checklist_label)
        layout.addWidget(checklist_card)

        return tab

    def _build_steps_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_lbl = QLabel("Desglose analítico de las transformaciones algebraicas:")
        header_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(header_lbl)

        self.steps_text = QLabel("El procedimiento detallado aparecerá tras pulsar 'Verificar Propiedad'.")
        self.steps_text.setWordWrap(True)
        self.steps_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.steps_text.setStyleSheet(
            f"background-color: {COLOR_SURFACE_INNER}; color: {COLOR_TEXT_PRIMARY}; "
            f"font-family: {FONT_FAMILY_MONO}; font-size: 14px; padding: 14px; border-radius: 6px;"
        )
        scroll_steps = QScrollArea()
        scroll_steps.setWidgetResizable(True)
        scroll_steps.setFrameShape(QFrame.NoFrame)
        scroll_steps.setWidget(self.steps_text)
        layout.addWidget(scroll_steps, stretch=1)

        return tab

    # --------------------------------------------------------------------------
    # Sincronización y lógica de interfaz
    # --------------------------------------------------------------------------

    def _on_mode_toggled(self, btn_id: int) -> None:
        if btn_id == 0:
            self._mode = "distributive"
            self.vector_controls_stack.setCurrentIndex(0)
            self.formula_lbl.setText("A(u + v) = A·u + A·v")
            self.inputs_title.setText("Entrada de Datos:  A ∈ M_{m×n},  u ∈ ℝⁿ,  v ∈ ℝⁿ")
            self.verify_btn.setText("Verificar Propiedad Distributiva  A(u + v) = A·u + A·v")
            self.lbl_dim_v.setVisible(True)
            self.spin_dim_v.setVisible(True)
            self.rhs_view2.setVisible(True)
        else:
            self._mode = "homogeneity"
            self.vector_controls_stack.setCurrentIndex(1)
            self.formula_lbl.setText("A(c·u) = c·(A·u)")
            self.inputs_title.setText("Entrada de Datos:  A ∈ M_{m×n},  u ∈ ℝⁿ,  c ∈ ℝ")
            self.verify_btn.setText("Verificar Propiedad de Homogeneidad  A(c·u) = c·(A·u)")
            self.lbl_dim_v.setVisible(False)
            self.spin_dim_v.setVisible(False)
            self.rhs_view2.setVisible(False)

        self._refresh_validation()

    def _on_matrix_grid_changed(self) -> None:
        rows, cols = self.grid_a.data_shape()
        self.spin_m.blockSignals(True)
        self.spin_n.blockSignals(True)
        self.spin_m.setValue(rows)
        self.spin_n.setValue(cols)
        self.spin_m.blockSignals(False)
        self.spin_n.blockSignals(False)
        self._refresh_validation()

    def _on_dimension_spinners_changed(self) -> None:
        m = self.spin_m.value()
        n = self.spin_n.value()
        current_rows, current_cols = self.grid_a.data_shape()
        if current_rows != m or current_cols != n:
            # Reajustar matriz conservando datos existentes
            current_raw = self.grid_a.get_raw_strings()
            new_data: List[List[str]] = []
            for r in range(m):
                row: List[str] = []
                for c in range(n):
                    if r < len(current_raw) and c < len(current_raw[r]):
                        row.append(current_raw[r][c] or "0")
                    else:
                        row.append("0")
                new_data.append(row)
            self.grid_a.set_matrix(Matrix(new_data))
        self._refresh_validation()

    def _on_u_dimension_changed(self) -> None:
        dim = self.spin_dim_u.value()
        self.vec_u_dist.set_dimension(dim)
        self.vec_u_homo.set_dimension(dim)
        self._refresh_validation()

    def _on_v_dimension_changed(self) -> None:
        dim = self.spin_dim_v.value()
        self.vec_v_dist.set_dimension(dim)
        self._refresh_validation()

    def sync_dimensions(self) -> None:
        """Ajusta dim(u) y dim(v) para que coincidan con las columnas n de A."""
        _, cols = self.grid_a.data_shape()
        self.spin_dim_u.setValue(cols)
        self.spin_dim_v.setValue(cols)
        self.vec_u_dist.set_dimension(cols)
        self.vec_v_dist.set_dimension(cols)
        self.vec_u_homo.set_dimension(cols)
        self._refresh_validation()

    def _refresh_validation(self) -> None:
        m, n = self.grid_a.data_shape()
        valid_cells = self.grid_a.is_all_valid()

        if self._mode == "distributive":
            dim_u = self.vec_u_dist.grid.num_rows
            dim_v = self.vec_v_dist.grid.num_rows
            valid_cells = valid_cells and self.vec_u_dist.is_valid() and self.vec_v_dist.is_valid()

            if not valid_cells:
                self.badge.setText("✕ Hay celdas con valores no numéricos en la matriz o los vectores.")
                self.badge.setStyleSheet(_badge_style(False))
                self._enable_action_buttons(False)
                return

            if dim_u != dim_v:
                self.badge.setText(
                    f"✕ Vectores no conformables: dim(u) = {dim_u} ≠ dim(v) = {dim_v}. "
                    "La suma (u + v) requiere vectores de la misma dimensión."
                )
                self.badge.setStyleSheet(_badge_style(False))
                self._enable_action_buttons(False)
                return

            if n != dim_u:
                self.badge.setText(
                    f"✕ Producto no conformable: A tiene {n} columnas pero u y v tienen dimensión {dim_u}. "
                    f"Se requiere que dim(u) = dim(v) = {n} (número de columnas de A)."
                )
                self.badge.setStyleSheet(_badge_style(False))
                self._enable_action_buttons(False)
                return

            self.badge.setText(
                f"✓ Conformable: A ({m}×{n}) · (u + v) ({n}×1) = A·u ({m}×1) + A·v ({m}×1). "
                f"Ambos lados dan un vector en ℝ{to_superscript(m)}."
            )
            self.badge.setStyleSheet(_badge_style(True))
            self._enable_action_buttons(True)

        else:
            dim_u = self.vec_u_homo.grid.num_rows
            valid_cells = valid_cells and self.vec_u_homo.is_valid()
            c_text = self.input_c.text().strip()

            c_valid = True
            try:
                parse_scalar(c_text)
            except Exception:
                c_valid = False

            if not valid_cells or not c_valid:
                msg = "✕ Hay celdas inválidas."
                if not c_valid:
                    msg = "✕ Escalar c inválido: ingrese un número entero, fracción (a/b) o decimal."
                self.badge.setText(msg)
                self.badge.setStyleSheet(_badge_style(False))
                self._enable_action_buttons(False)
                return

            if n != dim_u:
                self.badge.setText(
                    f"✕ Producto no conformable: A tiene {n} columnas pero u tiene dimensión {dim_u}. "
                    f"Se requiere que dim(u) = {n} (número de columnas de A)."
                )
                self.badge.setStyleSheet(_badge_style(False))
                self._enable_action_buttons(False)
                return

            self.badge.setText(
                f"✓ Conformable: A ({m}×{n}) · ({c_text}·u) ({n}×1) = ({c_text}) · (A·u) ({m}×1). "
                f"Ambos lados dan un vector en ℝ{to_superscript(m)}."
            )
            self.badge.setStyleSheet(_badge_style(True))
            self._enable_action_buttons(True)

    def _enable_action_buttons(self, enabled: bool) -> None:
        self.verify_btn.setEnabled(enabled)
        if hasattr(self, "header_verify_btn"):
            self.header_verify_btn.setEnabled(enabled)

    # --------------------------------------------------------------------------
    # Verificación algebraica y presentación de resultados
    # --------------------------------------------------------------------------

    def verify_current_property(self) -> None:
        if self._mode == "distributive":
            self._verify_distributive()
        else:
            self._verify_homogeneity()

    def _verify_distributive(self) -> None:
        try:
            A = self.grid_a.get_matrix()
            u = self.vec_u_dist.get_vector()
            v = self.vec_v_dist.get_vector()
            result = verify_distributive_property(A, u, v)
        except DimensionMismatchError as exc:
            self.badge.setText(f"✕ {exc}")
            self.badge.setStyleSheet(_badge_style(False))
            self._enable_action_buttons(False)
            return
        except Exception as exc:
            self._show_alert("Error de cálculo", str(exc))
            return

        self._last_distributive_result = result

        # Actualizar banner de igualdad
        if result.is_equal:
            self.equality_banner.setText(
                f"✓ ¡PROPIEDAD DISTRIBUTIVA DEMOSTRADA RIGUROSAMENTE!  A(u + v) = A·u + A·v\n"
                f"Ambos miembros de la ecuación coinciden exactamente en cada componente de ℝ{to_superscript(A.rows)}."
            )
            self.equality_banner.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_SUCCESS}; color: {COLOR_BG_BASE}; "
                f"font-size: 16px; font-weight: 700; padding: 12px; border-radius: 6px;"
            )
            self.equals_check_lbl.setText("✓ =")
            self.equals_check_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_FEEDBACK_SUCCESS};")
        else:
            self.equality_banner.setText("✕ Discrepancia encontrada en la comprobación.")
            self.equality_banner.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_ERROR}; color: {COLOR_TEXT_PRIMARY}; "
                f"font-size: 16px; font-weight: 700; padding: 12px; border-radius: 6px;"
            )
            self.equals_check_lbl.setText("≠")
            self.equals_check_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_FEEDBACK_ERROR};")

        # Configurar Lado Izquierdo (LHS)
        self.lhs_title.setText("Lado Izquierdo:  A · (u + v)")
        self.lhs_intermediate_lbl.setText(f"1. Suma intermedia (u + v) ∈ ℝ{to_superscript(u.dimension)}:")
        self.lhs_intermediate_view.set_matrix(result.u_plus_v.to_column_matrix())
        self.lhs_final_lbl.setText(f"2. Resultado A · (u + v) ∈ ℝ{to_superscript(A.rows)}:")
        self.lhs_final_view.set_matrix(result.lhs_result.to_column_matrix())

        # Configurar Lado Derecho (RHS)
        self.rhs_title.setText("Lado Derecho:  (A · u) + (A · v)")
        self.rhs_intermediate_lbl.setText("1. Productos parciales  A·u  y  A·v:")
        self.rhs_view1.set_matrix(result.Au.to_column_matrix())
        self.rhs_view2.set_matrix(result.Av.to_column_matrix())
        self.rhs_view2.setVisible(True)
        self.rhs_final_lbl.setText(f"2. Suma (A·u) + (A·v) ∈ ℝ{to_superscript(A.rows)}:")
        self.rhs_final_view.set_matrix(result.rhs_result.to_column_matrix())

        # Checklist de verificación
        chk_lines = []
        for label, lhs_val, rhs_val, ok in result.verification_checklist:
            mark = "✓" if ok else "✗"
            chk_lines.append(
                f"  {mark}  {label}:  A(u + v) = {format_scalar(lhs_val)}  |  Au + Av = {format_scalar(rhs_val)}  (Coinciden exactamente)"
            )
        self.checklist_label.setText("\n".join(chk_lines))

        # Pasos detallados
        steps_full = [
            "================================================================================",
            "DEMOSTRACIÓN PASO A PASO: PROPIEDAD DISTRIBUTIVA DEL PRODUCTO MATRIZ-VECTOR",
            "Identidad: A · (u + v) = A · u + A · v",
            "================================================================================",
            "",
            "--- LADO IZQUIERDO (LHS) ---",
            *result.lhs_steps,
            "",
            "--- LADO DERECHO (RHS) ---",
            *result.rhs_steps,
            "",
            "--- CONCLUSIÓN FORMAL ---",
            f"Para toda componente i = 1, ..., {A.rows}:",
            "  (A(u + v))_i = Σ_j A_ij (u_j + v_j) = Σ_j (A_ij u_j + A_ij v_j) = Σ_j A_ij u_j + Σ_j A_ij v_j = (Au)_i + (Av)_i",
            "Por lo tanto, se verifica rigurosamente la igualdad matricial en todo ℝᵐ.",
        ]
        self.steps_text.setText("\n".join(steps_full))

    def _verify_homogeneity(self) -> None:
        try:
            A = self.grid_a.get_matrix()
            u = self.vec_u_homo.get_vector()
            c_val = self.input_c.text().strip()
            result = verify_homogeneity_property(A, u, c_val)
        except DimensionMismatchError as exc:
            self.badge.setText(f"✕ {exc}")
            self.badge.setStyleSheet(_badge_style(False))
            self._enable_action_buttons(False)
            return
        except Exception as exc:
            self._show_alert("Error de cálculo", str(exc))
            return

        self._last_homogeneity_result = result
        c_fmt = format_scalar(result.c)

        # Actualizar banner de igualdad
        if result.is_equal:
            self.equality_banner.setText(
                f"✓ ¡PROPIEDAD DE HOMOGENEIDAD DEMOSTRADA RIGUROSAMENTE!  A(c·u) = c·(A·u)\n"
                f"Con escalar c = {c_fmt}, ambos miembros coinciden en cada componente de ℝ{to_superscript(A.rows)}."
            )
            self.equality_banner.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_SUCCESS}; color: {COLOR_BG_BASE}; "
                f"font-size: 16px; font-weight: 700; padding: 12px; border-radius: 6px;"
            )
            self.equals_check_lbl.setText("✓ =")
            self.equals_check_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_FEEDBACK_SUCCESS};")
        else:
            self.equality_banner.setText("✕ Discrepancia encontrada en la comprobación.")
            self.equality_banner.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_ERROR}; color: {COLOR_TEXT_PRIMARY}; "
                f"font-size: 16px; font-weight: 700; padding: 12px; border-radius: 6px;"
            )
            self.equals_check_lbl.setText("≠")
            self.equals_check_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_FEEDBACK_ERROR};")

        # Configurar Lado Izquierdo (LHS)
        self.lhs_title.setText(f"Lado Izquierdo:  A · ({c_fmt} · u)")
        self.lhs_intermediate_lbl.setText(f"1. Vector escalado (c · u) ∈ ℝ{to_superscript(u.dimension)}:")
        self.lhs_intermediate_view.set_matrix(result.cu.to_column_matrix())
        self.lhs_final_lbl.setText(f"2. Resultado A · (c·u) ∈ ℝ{to_superscript(A.rows)}:")
        self.lhs_final_view.set_matrix(result.lhs_result.to_column_matrix())

        # Configurar Lado Derecho (RHS)
        self.rhs_title.setText(f"Lado Derecho:  {c_fmt} · (A · u)")
        self.rhs_intermediate_lbl.setText("1. Producto intermedio A · u:")
        self.rhs_view1.set_matrix(result.Au.to_column_matrix())
        self.rhs_view2.setVisible(False)
        self.rhs_final_lbl.setText(f"2. Escalado final c · (A·u) ∈ ℝ{to_superscript(A.rows)}:")
        self.rhs_final_view.set_matrix(result.rhs_result.to_column_matrix())

        # Checklist de verificación
        chk_lines = []
        for label, lhs_val, rhs_val, ok in result.verification_checklist:
            mark = "✓" if ok else "✗"
            chk_lines.append(
                f"  {mark}  {label}:  A(c·u) = {format_scalar(lhs_val)}  |  c(Au) = {format_scalar(rhs_val)}  (Coinciden exactamente)"
            )
        self.checklist_label.setText("\n".join(chk_lines))

        # Pasos detallados
        steps_full = [
            "================================================================================",
            "DEMOSTRACIÓN PASO A PASO: PROPIEDAD DE HOMOGENEIDAD (MULTIPLICACIÓN POR ESCALAR)",
            f"Identidad: A · (c · u) = c · (A · u)   con escalar c = {c_fmt}",
            "================================================================================",
            "",
            "--- LADO IZQUIERDO (LHS) ---",
            *result.lhs_steps,
            "",
            "--- LADO DERECHO (RHS) ---",
            *result.rhs_steps,
            "",
            "--- CONCLUSIÓN FORMAL ---",
            f"Para toda componente i = 1, ..., {A.rows}:",
            "  (A(c u))_i = Σ_j A_ij (c u_j) = c Σ_j A_ij u_j = c (Au)_i = (c (Au))_i",
            "Por lo tanto, la multiplicación por escalar conmuta con el producto matriz-vector en todo ℝᵐ.",
        ]
        self.steps_text.setText("\n".join(steps_full))

    # --------------------------------------------------------------------------
    # Presets y ejemplos académicos
    # --------------------------------------------------------------------------

    def load_distributive_sample(self) -> None:
        """Carga un caso canónico 2×3 para la propiedad distributiva."""
        self.btn_mode_dist.setChecked(True)
        self._on_mode_toggled(0)

        self.spin_m.setValue(2)
        self.spin_n.setValue(3)
        self.spin_dim_u.setValue(3)
        self.spin_dim_v.setValue(3)

        self.grid_a.set_matrix(Matrix([
            [2, -1, 3],
            [1, 0, -2],
        ]))
        self.vec_u_dist.set_vector(Vector([1, 2, -1]))
        self.vec_v_dist.set_vector(Vector([3, -1, 4]))

        self._refresh_validation()
        self.verify_current_property()

    def load_homogeneity_sample(self) -> None:
        """Carga un caso canónico 2×3 con escalar fraccionario para homogeneidad."""
        self.btn_mode_homo.setChecked(True)
        self._on_mode_toggled(1)

        self.spin_m.setValue(2)
        self.spin_n.setValue(3)
        self.spin_dim_u.setValue(3)

        self.grid_a.set_matrix(Matrix([
            [1, 2, -1],
            [-3, 4, 2],
        ]))
        self.vec_u_homo.set_vector(Vector([2, -1, 3]))
        self.input_c.setText("3/2")

        self._refresh_validation()
        self.verify_current_property()

    def load_incompatible_sample(self) -> None:
        """Carga dimensiones incompatibles intencionadamente para demostrar el mensaje de error."""
        self.btn_mode_dist.setChecked(True)
        self._on_mode_toggled(0)

        self.spin_m.setValue(2)
        self.spin_n.setValue(3)
        self.grid_a.set_matrix(Matrix([
            [1, 2, 3],
            [4, 5, 6],
        ]))
        # u y v tienen dimensión 2 pero A tiene 3 columnas
        self.spin_dim_u.setValue(2)
        self.spin_dim_v.setValue(2)
        self.vec_u_dist.set_vector(Vector([1, 2]))
        self.vec_v_dist.set_vector(Vector([3, 4]))

        self._refresh_validation()

    def reset(self) -> None:
        """Restablece los campos a ceros."""
        self.grid_a.set_matrix(Matrix.zeros(2, 3))
        self.spin_m.setValue(2)
        self.spin_n.setValue(3)
        self.spin_dim_u.setValue(3)
        self.spin_dim_v.setValue(3)
        self.vec_u_dist.set_vector(Vector([0, 0, 0]))
        self.vec_v_dist.set_vector(Vector([0, 0, 0]))
        self.vec_u_homo.set_vector(Vector([0, 0, 0]))
        self.input_c.setText("1")

        self.lhs_intermediate_view.clear()
        self.lhs_final_view.clear()
        self.rhs_view1.clear()
        self.rhs_view2.clear()
        self.rhs_final_view.clear()
        self.equality_banner.setText("Realiza la verificación para comparar ambos lados de la igualdad.")
        self.equality_banner.setStyleSheet(
            f"background-color: {COLOR_SURFACE_INNER}; color: {COLOR_TEXT_PRIMARY}; "
            f"font-size: 16px; font-weight: 600; padding: 10px; border-radius: 6px;"
        )
        self.checklist_label.setText("Presione 'Verificar Propiedad' para ver la comparación fila a fila.")
        self.steps_text.setText("El procedimiento detallado aparecerá tras pulsar 'Verificar Propiedad'.")
        self.results_tabs.setCurrentIndex(0)
        self._refresh_validation()

    def _show_alert(self, title: str, message: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setIcon(QMessageBox.Warning)
        apply_message_box_theme(box)
        box.exec()
