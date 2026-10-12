"""Vista de álgebra matricial: A ± B, k·A, A·B, la transpuesta Aᵀ y la inversa A⁻¹.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.
Muestra el cambio de dimensión n×m y las propiedades que cumple la matriz.

Sprint 10 (auditoría UI/UX, Módulo 2):

- Un único botón «Calcular» en la barra (``Ctrl+Intro`` desde cualquier celda) y
  los ejemplos dentro de cada modo, no todos amontonados en la barra.
- Inspector de producto con insignia «Inspeccionando C₁,₂» sobre la matriz C.
- Botón «Ajustar B» cuando la operación elegida no es conformable.
- Escalar k validado en vivo (borde rojo) con atajos −1, 0, ½ y 2.
- La matriz B de (A+B)ᵀ y (AB)ᵀ se ve y se edita en la propia página.
- Distributivas y asociativa: ejemplo para cada propiedad y carrusel con las
  matrices intermedias (B + C, A·B, A·C, …).
- Inversa: la fila nula que prueba la singularidad se resalta y el carrusel salta
  a ese paso; «Usar A⁻¹ como A» comprueba (A⁻¹)⁻¹ = A en un clic.
- TMI: tarjeta con las caracterizaciones clave (*c, *e, *h, det) y filtro.
- Identidades: (AB)⁻¹ y B⁻¹A⁻¹ lado a lado, con A⁻¹B⁻¹ como contraejemplo.
- Las cadenas de matrices se apilan en pantallas angostas.
"""

from __future__ import annotations

import html
from typing import Any, List, Optional, Sequence, Tuple

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
        QButtonGroup,
        QSizePolicy,
        QMessageBox,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.theorems import (
    evaluate_invertible_matrix_theorem,
    verify_inverse_algebraic_identities,
)
from prettycalc.core.matrix_inversion import (
    NonSquareMatrixError,
    SingularMatrixError,
    matrix_inverse,
)
from prettycalc.core.matrix_ops import (
    MultiplicationStepDetail,
    matrix_add,
    matrix_multiply,
    matrix_multiply_with_details,
    matrix_scale,
    matrix_sub,
    matrix_transpose,
)
from prettycalc.core.matrix_properties import (
    PropertyCheck,
    analyze_matrix,
    verify_matrix_associative,
    verify_matrix_distributive_left,
    verify_matrix_distributive_right,
)
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import DimensionMismatchError, Matrix, format_scalar, parse_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.mathtext import format_comparison_row_html, prettify_math_text, to_subscript
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.responsive import CurrentPageStack, ResponsiveRow
from prettycalc.ui.scalar_field import CANONICAL_SCALARS, ScalarField, ScalarInput
from prettycalc.ui.stepper_carousel import ALERT_SINGULAR, AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_message_box_theme,
    apply_widget_class,
    badge_style,
    rgba,
)

#: Índices de las páginas del QStackedWidget.
PAGE_BINARY, PAGE_SCALAR, PAGE_TRANSPOSE, PAGE_DISTRIBUTIVE, PAGE_INVERSE, PAGE_TMI, PAGE_IDENTITIES = range(7)

#: Caracterizaciones del TMI que la cátedra marca con asterisco, más el determinante.
TMI_KEY_CODES = ("*c", "*e", "*h", "det")

_CONNECTOR_STYLE = f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"


def _badge_style(ok: bool) -> str:
    return badge_style(COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR, font_size=15)


def _check_style(status: str) -> Tuple[str, str, str]:
    """(color de texto, fondo, borde) de una tarjeta de propiedad."""
    if status == "cumple":
        return COLOR_FEEDBACK_SUCCESS, rgba(COLOR_FEEDBACK_SUCCESS, 0.08), f"1px solid {rgba(COLOR_FEEDBACK_SUCCESS, 0.35)}"
    if status == "no_cumple":
        return COLOR_FEEDBACK_ERROR, rgba(COLOR_FEEDBACK_ERROR, 0.08), f"1px solid {rgba(COLOR_FEEDBACK_ERROR, 0.35)}"
    if status == "no_aplica":
        return COLOR_TEXT_MUTED, "transparent", "1px solid transparent"
    return COLOR_TEXT_PRIMARY, "transparent", "1px solid transparent"


def _checks_to_html(checks: Sequence[PropertyCheck]) -> str:
    """Tarjetas en HTML con tamaño grande (22px): verde si cumple, coral si no, gris si no aplica."""
    marks = {"cumple": "✓", "no_cumple": "✗", "no_aplica": "—", "dato": "·"}
    rows = []
    for check in checks:
        text = html.escape(prettify_math_text(f"{check.name}: {check.detail}"))
        color, bg, border = _check_style(check.status)
        rows.append(
            f'<div style="background-color:{bg}; border:{border}; border-radius:6px; '
            f'padding:8px 12px; margin:6px 0; color:{color}; font-size:22px; font-weight:600;">'
            f'{marks[check.status]}&nbsp;&nbsp;{text}</div>'
        )
    return "".join(rows)


def _sample_button(text: str, tooltip: str, slot) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    button.setToolTip(tooltip)
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(slot)
    return button


class MatrixOperationsView(QWidget):
    """Disposición [A] [+|-|×] [B] = [C] con validación en tiempo real."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixOperationsView")
        self._op: str = "mul"
        self._details: List[MultiplicationStepDetail] = []
        self._result: Optional[Matrix] = None
        self._inspected: Optional[Tuple[int, int]] = None
        self._tmi_checks: list = []
        self._tmi_filter = "all"
        self._setup_ui()
        self._refresh_compatibility()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(4, 4, 10, 16)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        self.mode_group = mode_group
        specs = (
            ("binary_mode_btn", "A  ∘  B", "Suma, resta y producto de dos matrices"),
            ("scalar_mode_btn", "k  ·  A", "Multiplicación por escalar"),
            ("transpose_mode_btn", "Aᵀ", "Transpuesta e identidades de la transpuesta"),
            ("distrib_mode_btn", "A · (B + C)", "Propiedades distributivas y asociativa"),
            ("inverse_mode_btn", "A⁻¹ (Inversa)", "Inversa por Gauss-Jordan sobre [A | Iₙ]"),
            ("tmi_mode_btn", "TMI", "Teorema de la Matriz Invertible"),
            ("identities_mode_btn", "Identidades A⁻¹", "(A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹A⁻¹ y (Aᵀ)⁻¹ = (A⁻¹)ᵀ"),
        )
        for index, (attr, text, tooltip) in enumerate(specs):
            button = QPushButton(text)
            button.setObjectName("modeToggle")
            button.setCheckable(True)
            button.setToolTip(tooltip)
            mode_group.addButton(button, index)
            toolbar.addWidget(button)
            setattr(self, attr, button)
        self.binary_mode_btn.setChecked(True)
        mode_group.idClicked.connect(self._on_mode_changed)
        toolbar.addStretch(1)

        # Un solo botón de cálculo (antes había dos idénticos). El atributo
        # header_compute_btn se conserva como alias para no romper integraciones.
        self.compute_btn = QPushButton("▶ Calcular")
        self.compute_btn.setObjectName("primaryAction")
        self.compute_btn.setCursor(Qt.PointingHandCursor)
        self.compute_btn.clicked.connect(self.compute)
        self.header_compute_btn = self.compute_btn
        toolbar.addWidget(self.compute_btn)
        root.addLayout(toolbar)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        self.badge = QLabel("")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        badge_row.addWidget(self.badge, stretch=1)
        self.fix_dims_btn = QPushButton("")
        self.fix_dims_btn.setObjectName("secondaryAction")
        self.fix_dims_btn.setCursor(Qt.PointingHandCursor)
        self.fix_dims_btn.clicked.connect(self.fix_partner_dimensions)
        self.fix_dims_btn.setVisible(False)
        badge_row.addWidget(self.fix_dims_btn)
        root.addLayout(badge_row)

        self.pages = CurrentPageStack()
        self.pages.addWidget(self._build_binary_page())
        self.pages.addWidget(self._build_scalar_page())
        self.pages.addWidget(self._build_transpose_page())
        self.pages.addWidget(self._build_distributive_page())
        self.pages.addWidget(self._build_inverse_page())
        self.pages.addWidget(self._build_tmi_page())
        self.pages.addWidget(self._build_inverse_identities_page())
        root.addWidget(self.pages)

        root.addWidget(self._build_note_card(
            "Inspector de producto  Cᵢⱼ = Σ Aᵢₖ Bₖⱼ",
            "Calcula un producto A · B y pulsa una celda de C para ver la fila de A, "
            "la columna de B y la sumatoria de productos parciales.",
            rich=False,
            target="inspector_label",
        ))
        root.addWidget(self._build_note_card(
            "Propiedades de la matriz y de la transpuesta",
            "Calcula para ver qué tipo de matriz es, qué propiedades cumple "
            "y si se verifican las identidades de la transpuesta.",
            rich=True,
            target="properties_label",
        ))
        root.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

        for grid in self._all_grids():
            grid.submitRequested.connect(self.compute)

    def _all_grids(self) -> List[DynamicMatrixGrid]:
        return [
            self.grid_a, self.grid_b, self.grid_scalar, self.grid_transpose, self.grid_transpose_b,
            self.grid_dist_a, self.grid_dist_b, self.grid_dist_c, self.grid_inverse, self.grid_tmi,
            self.grid_id_a, self.grid_id_b,
        ]

    def _page(self) -> Tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        return page, layout

    def _sample_bar(self, *buttons: QPushButton) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)
        caption = QLabel("Ejemplos")
        caption.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 600;")
        bar.addWidget(caption)
        for button in buttons:
            bar.addWidget(button)
        bar.addStretch(1)
        return bar

    def _build_binary_page(self) -> QWidget:
        page, layout = self._page()
        layout.addLayout(self._sample_bar(
            _sample_button("2×3 · 3×2", "Producto compatible de la clase", self.load_compatible_product_sample),
            _sample_button("Incompatible", "Producto 2×3 · 2×2: no conformable", self.load_incompatible_sample),
        ))

        row = ResponsiveRow(breakpoint=980)
        self.binary_row = row
        self.grid_a = DynamicMatrixGrid(initial_rows=2, initial_cols=3, augmented=False)
        self.grid_a.matrixChanged.connect(self._on_operands_changed)
        row.add_widget(self._wrap_matrix_card("Matriz A", self.grid_a), 3)

        op_host = QWidget()
        op_col = QVBoxLayout(op_host)
        op_col.setContentsMargins(0, 0, 0, 0)
        op_col.setSpacing(8)
        op_col.addStretch(1)
        self.op_group = QButtonGroup(self)
        self.op_group.setExclusive(True)
        self.add_btn = QPushButton("+")
        self.sub_btn = QPushButton("−")
        self.mul_btn = QPushButton("×")
        for btn, op_id, tip in (
            (self.add_btn, 0, "Suma A + B"),
            (self.sub_btn, 1, "Resta A − B"),
            (self.mul_btn, 2, "Producto A · B"),
        ):
            btn.setObjectName("opSelect")
            btn.setCheckable(True)
            btn.setToolTip(tip)
            self.op_group.addButton(btn, op_id)
            op_col.addWidget(btn, 0, Qt.AlignCenter)
        self.mul_btn.setChecked(True)
        self.op_group.idClicked.connect(self._on_op_changed)
        op_col.addStretch(1)
        row.add_widget(op_host)

        self.grid_b = DynamicMatrixGrid(initial_rows=3, initial_cols=2, augmented=False)
        self.grid_b.matrixChanged.connect(self._on_operands_changed)
        row.add_widget(self._wrap_matrix_card("Matriz B", self.grid_b), 3)

        row.add_connector("=", "=", _CONNECTOR_STYLE)

        self.result_view = BookMatrixWidget()
        self.result_view.set_empty_text("Pulsa Calcular para ver C")
        self.result_view.cellClicked.connect(self._on_result_cell_clicked)
        self.inspect_badge = QLabel("")
        self.inspect_badge.setObjectName("inspectBadge")
        self.inspect_badge.setVisible(False)
        self.inspect_badge.setStyleSheet(badge_style(COLOR_INTERACTIVE_IDLE, font_size=13, padding="4px 10px"))
        result_card, self.result_title_lbl = self._create_titled_matrix_card(
            "Matriz C", self.result_view, header_extra=self.inspect_badge
        )
        row.add_widget(result_card, 3)
        layout.addWidget(row)
        layout.addStretch(1)
        return page

    def _build_scalar_page(self) -> QWidget:
        page, _layout = self._page()
        row = ResponsiveRow(breakpoint=900)

        k_card = QFrame()
        apply_widget_class(k_card, "elevated-card")
        k_layout = QVBoxLayout(k_card)
        k_title = QLabel("Escalar k")
        k_title.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        k_layout.addWidget(k_title)
        self.scalar_edit = ScalarField("2", base_tooltip="Escalar k: entero, fracción a/b o decimal")
        self.scalar_edit.textChanged.connect(self._on_operands_changed)
        self.scalar_input = ScalarInput(
            self.scalar_edit,
            presets=CANONICAL_SCALARS,
            help_text="Entero, fracción o decimal",
        )
        k_layout.addWidget(self.scalar_input)
        k_layout.addStretch(1)
        row.add_widget(k_card)

        row.add_connector("·", "·", f"font-size: 32px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;")

        self.grid_scalar = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_scalar.matrixChanged.connect(self._on_operands_changed)
        row.add_widget(self._wrap_matrix_card("Matriz A", self.grid_scalar), 3)

        row.add_connector("=", "=", _CONNECTOR_STYLE)

        self.scalar_result_view = BookMatrixWidget()
        self.scalar_result_view.set_empty_text("Pulsa Calcular para ver k · A")
        row.add_widget(self._wrap_matrix_card("k · A", self.scalar_result_view), 3)
        _layout.addWidget(row)
        _layout.addStretch(1)
        return page

    def _build_note_card(self, title: str, body: str, rich: bool, target: str) -> QFrame:
        """Tarjeta de texto. Guarda la etiqueta en el atributo `target`."""
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        heading = QLabel(title)
        heading.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        layout.addWidget(heading)
        label = QLabel(body)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if rich:
            label.setTextFormat(Qt.RichText)
        label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-family: {FONT_FAMILY_MONO};"
        )
        layout.addWidget(label)
        setattr(self, target, label)
        return card

    def _build_transpose_page(self) -> QWidget:
        """Página unaria: A → Aᵀ → (Aᵀ)ᵀ = A, el escalar k y la matriz B opcional."""
        page, outer = self._page()
        row = ResponsiveRow(breakpoint=1100)
        self.transpose_row = row
        self.grid_transpose = DynamicMatrixGrid(initial_rows=2, initial_cols=3, augmented=False)
        self.grid_transpose.matrixChanged.connect(self._on_operands_changed)
        row.add_widget(self._wrap_matrix_card("Matriz A", self.grid_transpose), 3)
        row.add_connector("→", "↓", _CONNECTOR_STYLE)
        self.transpose_result_view = BookMatrixWidget()
        self.transpose_result_view.set_empty_text("Pulsa Calcular para ver Aᵀ")
        row.add_widget(self._wrap_matrix_card("Aᵀ", self.transpose_result_view), 3)
        row.add_connector("→", "↓", _CONNECTOR_STYLE)
        self.double_transpose_result_view = BookMatrixWidget()
        self.double_transpose_result_view.set_empty_text("(Aᵀ)ᵀ aparecerá aquí")
        row.add_widget(self._wrap_matrix_card("(Aᵀ)ᵀ = A", self.double_transpose_result_view), 3)
        outer.addWidget(row)
        outer.addLayout(self._transpose_identity_bar())

        self.transpose_b_card = self._wrap_matrix_card("Matriz B para (A+B)ᵀ y (A·B)ᵀ", None)
        self.grid_transpose_b = DynamicMatrixGrid(initial_rows=2, initial_cols=3, augmented=False)
        self.grid_transpose_b.matrixChanged.connect(self._on_operands_changed)
        b_layout = self.transpose_b_card.layout()
        b_hint = QLabel(
            "B se edita aquí. Para (A+B)ᵀ debe tener el tamaño de A; para (A·B)ᵀ, tantas filas "
            "como columnas tiene A. Si no es conformable, la tarjeta lo dice como «No aplica»."
        )
        b_hint.setWordWrap(True)
        apply_widget_class(b_hint, "field-hint")
        b_layout.addWidget(b_hint)
        b_layout.addWidget(self.grid_transpose_b)
        copy_b = QPushButton("Traer B de la vista A ∘ B")
        apply_widget_class(copy_b, "link-action")
        copy_b.clicked.connect(self.copy_partner_from_binary)
        b_layout.addWidget(copy_b, 0, Qt.AlignLeft)
        self.transpose_b_card.setVisible(False)
        outer.addWidget(self.transpose_b_card)
        outer.addStretch(1)
        return page

    def _transpose_identity_bar(self) -> QHBoxLayout:
        """Escalar k y la opción de usar B en las identidades de la transpuesta."""
        extras = QHBoxLayout()
        extras.setSpacing(8)
        k_label = QLabel("k")
        k_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        extras.addWidget(k_label, 0, Qt.AlignTop)
        self.identity_scalar_edit = ScalarField(
            "1", allow_empty=True, base_tooltip="Escalar usado en la comprobación (k·A)ᵀ = k·Aᵀ"
        )
        self.identity_scalar_edit.setFixedWidth(110)
        self.identity_scalar_edit.textChanged.connect(self._on_operands_changed)
        self.identity_scalar_input = ScalarInput(self.identity_scalar_edit, help_text="(k·A)ᵀ = k·Aᵀ")
        extras.addWidget(self.identity_scalar_input, 0, Qt.AlignTop)
        self.include_b_btn = QPushButton("Incluir B en (A+B)ᵀ y (A·B)ᵀ")
        self.include_b_btn.setObjectName("modeToggle")
        self.include_b_btn.setCheckable(True)
        self.include_b_btn.setToolTip("Muestra una matriz B editable en esta misma página")
        self.include_b_btn.toggled.connect(self._on_include_b_toggled)
        extras.addWidget(self.include_b_btn, 0, Qt.AlignTop)
        extras.addStretch(1)
        return extras

    def _build_distributive_page(self) -> QWidget:
        """Página ternaria: A(B+C) = AB + AC, (A+B)C = AC + BC y A(BC) = (AB)C."""
        page, layout = self._page()

        prop_bar = QHBoxLayout()
        prop_bar.setSpacing(8)
        prop_title = QLabel("Propiedad:")
        prop_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        prop_bar.addWidget(prop_title)

        self.dist_prop_group = QButtonGroup(self)
        self.dist_prop_group.setExclusive(True)
        self.dist_left_btn = QPushButton("A · (B + C) = A·B + A·C")
        self.dist_right_btn = QPushButton("(A + B) · C = A·C + B·C")
        self.dist_assoc_btn = QPushButton("A · (B · C) = (A · B) · C")
        for index, button in enumerate((self.dist_left_btn, self.dist_right_btn, self.dist_assoc_btn)):
            button.setObjectName("modeToggle")
            button.setCheckable(True)
            self.dist_prop_group.addButton(button, index)
            prop_bar.addWidget(button)
        self.dist_left_btn.setChecked(True)
        self.dist_prop_group.idClicked.connect(self._on_dist_prop_changed)
        prop_bar.addStretch(1)
        self.dist_sample_btn = _sample_button(
            "Ejemplo de esta propiedad",
            "Carga matrices conformables para la propiedad elegida y calcula",
            self.load_current_property_sample,
        )
        prop_bar.addWidget(self.dist_sample_btn)
        layout.addLayout(prop_bar)

        grids_row = ResponsiveRow(breakpoint=900)
        self.grid_dist_a = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_dist_b = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_dist_c = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        for name, grid in (("Matriz A", self.grid_dist_a), ("Matriz B", self.grid_dist_b), ("Matriz C", self.grid_dist_c)):
            grid.matrixChanged.connect(self._on_operands_changed)
            grids_row.add_widget(self._wrap_matrix_card(name, grid), 1)
        layout.addWidget(grids_row)

        results_row = ResponsiveRow(breakpoint=900)
        self.dist_lhs_view = BookMatrixWidget()
        self.dist_rhs_view = BookMatrixWidget()
        self.dist_lhs_view.set_empty_text("Miembro izquierdo")
        self.dist_rhs_view.set_empty_text("Miembro derecho")
        lhs_card, self.dist_lhs_title_lbl = self._create_titled_matrix_card("LHS: A · (B + C)", self.dist_lhs_view)
        rhs_card, self.dist_rhs_title_lbl = self._create_titled_matrix_card("RHS: A·B + A·C", self.dist_rhs_view)
        results_row.add_widget(lhs_card, 1)
        self.dist_equals_lbl = results_row.add_connector("=", "=", f"font-size: 32px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;")
        results_row.add_widget(rhs_card, 1)
        layout.addWidget(results_row)

        self.dist_comparison_label = QLabel("")
        self.dist_comparison_label.setTextFormat(Qt.RichText)
        self.dist_comparison_label.setWordWrap(True)
        layout.addWidget(self.dist_comparison_label)

        steps_title = QLabel("Matrices intermedias")
        steps_title.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(steps_title)
        self.dist_stepper = AlgorithmStepperCarousel(variable_headers=False)
        self.dist_stepper.setObjectName("distributiveStepper")
        self.dist_stepper.set_export_title("Propiedades del producto de matrices")
        self.dist_stepper.set_empty_hint("Calcula para recorrer B + C, A·B, A·C y los dos miembros.")
        self.dist_stepper.setMinimumHeight(300)
        layout.addWidget(self.dist_stepper)
        layout.addStretch(1)
        return page

    def _build_inverse_page(self) -> QWidget:
        """Página unaria: A, su inversa y la reducción de [A | I_n]."""
        page, outer = self._page()
        outer.addLayout(self._sample_bar(
            _sample_button("Invertible 3×3 (S10)", "Sesión 10, diapositiva 11", self.load_inverse_sample),
            _sample_button("Singular 3×3", "Filas iguales: el rango colapsa", self.load_singular_inverse_sample),
        ))

        row = ResponsiveRow(breakpoint=820)
        self.grid_inverse = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_inverse.matrixChanged.connect(self._on_operands_changed)
        row.add_widget(self._wrap_matrix_card("Matriz A", self.grid_inverse), 3)
        row.add_connector("→", "↓", _CONNECTOR_STYLE)
        self.inverse_result_view = BookMatrixWidget()
        self.inverse_result_view.set_empty_text("Pulsa Calcular para ver A⁻¹")
        inverse_card, _title = self._create_titled_matrix_card("A⁻¹", self.inverse_result_view)
        self.reuse_inverse_btn = QPushButton("Usar A⁻¹ como A")
        apply_widget_class(self.reuse_inverse_btn, "link-action")
        self.reuse_inverse_btn.setToolTip("Carga A⁻¹ en la cuadrícula para comprobar (A⁻¹)⁻¹ = A")
        self.reuse_inverse_btn.setEnabled(False)
        self.reuse_inverse_btn.clicked.connect(self.use_inverse_as_input)
        inverse_card.layout().addWidget(self.reuse_inverse_btn, 0, Qt.AlignLeft)
        row.add_widget(inverse_card, 3)
        outer.addWidget(row)

        self.inverse_check_label = QLabel(
            "Calcula para comprobar A · A⁻¹ = Iₙ y ver la reducción de [A | Iₙ]."
        )
        self.inverse_check_label.setObjectName("inverseIdentityCheck")
        self.inverse_check_label.setWordWrap(True)
        self.inverse_check_label.setTextFormat(Qt.RichText)
        self.inverse_check_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.inverse_check_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 18px;")
        outer.addWidget(self.inverse_check_label)

        self.inverse_stepper = AlgorithmStepperCarousel(alert_mode=ALERT_SINGULAR, variable_headers=False)
        self.inverse_stepper.setObjectName("inverseStepper")
        self.inverse_stepper.set_export_title("Inversa por Gauss-Jordan")
        self.inverse_stepper.set_empty_hint("Calcula para recorrer la reducción de [A | Iₙ].")
        self.inverse_stepper.setMinimumHeight(280)
        outer.addWidget(self.inverse_stepper)
        outer.addStretch(1)
        return page

    def _build_tmi_page(self) -> QWidget:
        """Checklist del Teorema de la Matriz Invertible."""
        page, outer = self._page()
        outer.addLayout(self._sample_bar(
            _sample_button("Invertible (S10)", "Sesión 10, diapositiva 19", self.load_tmi_invertible_sample),
            _sample_button("Singular (S10)", "Sesión 10, diapositiva 20", self.load_tmi_singular_sample),
        ))

        self.grid_tmi = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
        self.grid_tmi.matrixChanged.connect(self._on_operands_changed)
        outer.addWidget(self._wrap_matrix_card("Matriz A", self.grid_tmi))

        self.tmi_key_card = QLabel("")
        self.tmi_key_card.setObjectName("tmiKeyCard")
        self.tmi_key_card.setWordWrap(True)
        self.tmi_key_card.setTextFormat(Qt.RichText)
        self.tmi_key_card.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.tmi_key_card.setVisible(False)
        outer.addWidget(self.tmi_key_card)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        filter_caption = QLabel("Mostrar")
        filter_caption.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 600;")
        filter_row.addWidget(filter_caption)
        self.tmi_filter_group = QButtonGroup(self)
        self.tmi_filter_group.setExclusive(True)
        self.tmi_filter_buttons = {}
        for index, (key, text) in enumerate((("all", "Todas"), ("key", "Clave (*c, *e, *h, det)"), ("failed", "Solo las que no cumplen"))):
            button = QPushButton(text)
            button.setObjectName("modeToggle")
            button.setCheckable(True)
            self.tmi_filter_group.addButton(button, index)
            self.tmi_filter_buttons[key] = button
            filter_row.addWidget(button)
        self.tmi_filter_buttons["all"].setChecked(True)
        self.tmi_filter_group.idClicked.connect(self._on_tmi_filter)
        filter_row.addStretch(1)
        outer.addLayout(filter_row)

        self.tmi_checklist = QLabel("Calcula para ver *c, *e, *h y det(A) ≠ 0.")
        self.tmi_checklist.setObjectName("tmiChecklist")
        self.tmi_checklist.setWordWrap(True)
        self.tmi_checklist.setTextFormat(Qt.RichText)
        self.tmi_checklist.setTextInteractionFlags(Qt.TextSelectableByMouse)
        outer.addWidget(self.tmi_checklist)

        self.tmi_stepper = AlgorithmStepperCarousel(alert_mode=ALERT_SINGULAR, variable_headers=False)
        self.tmi_stepper.setObjectName("tmiStepper")
        self.tmi_stepper.set_export_title("Teorema de la Matriz Invertible")
        self.tmi_stepper.set_empty_hint("Calcula para ver el escalonamiento que cuenta los pivotes.")
        self.tmi_stepper.setMinimumHeight(240)
        outer.addWidget(self.tmi_stepper)
        outer.addStretch(1)
        return page

    def _build_inverse_identities_page(self) -> QWidget:
        """(A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹A⁻¹ y (Aᵀ)⁻¹ = (A⁻¹)ᵀ, con las matrices a la vista."""
        page, outer = self._page()
        outer.addLayout(self._sample_bar(
            _sample_button("(AB)⁻¹ con matrices 3×3", "A de la sesión 10 y B triangular superior", self.load_inverse_identities_sample),
        ))

        row = ResponsiveRow(breakpoint=760)
        self.grid_id_a = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
        self.grid_id_b = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
        self.grid_id_a.matrixChanged.connect(self._on_operands_changed)
        self.grid_id_b.matrixChanged.connect(self._on_operands_changed)
        row.add_widget(self._wrap_matrix_card("Matriz A", self.grid_id_a), 1)
        row.add_widget(self._wrap_matrix_card("Matriz B", self.grid_id_b), 1)
        outer.addWidget(row)

        note = QLabel(
            "Atención al orden: (AB)⁻¹ = B⁻¹A⁻¹, no A⁻¹B⁻¹. El producto de matrices no es "
            "conmutativo, así que la inversa del producto invierte el orden de los factores."
        )
        note.setObjectName("orderNote")
        note.setWordWrap(True)
        note.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; background-color: {rgba(COLOR_ACCENT_WARNING, 0.12)}; "
            f"border-left: 4px solid {COLOR_ACCENT_WARNING}; border-radius: 4px; padding: 10px 12px;"
        )
        outer.addWidget(note)

        compare = ResponsiveRow(breakpoint=1000)
        self.id_ab_inverse_view = BookMatrixWidget()
        self.id_ba_product_view = BookMatrixWidget()
        self.id_wrong_order_view = BookMatrixWidget()
        for view, text in (
            (self.id_ab_inverse_view, "(AB)⁻¹"),
            (self.id_ba_product_view, "B⁻¹A⁻¹"),
            (self.id_wrong_order_view, "A⁻¹B⁻¹"),
        ):
            view.set_empty_text(f"{text} aparecerá aquí")
        compare.add_widget(self._wrap_matrix_card("(AB)⁻¹", self.id_ab_inverse_view), 1)
        compare.add_connector("=", "=", f"font-size: 30px; font-weight: 700; color: {COLOR_FEEDBACK_SUCCESS}; padding: 8px;")
        compare.add_widget(self._wrap_matrix_card("B⁻¹ A⁻¹  (orden correcto)", self.id_ba_product_view), 1)
        self.id_wrong_connector = compare.add_connector("≠", "≠", f"font-size: 30px; font-weight: 700; color: {COLOR_FEEDBACK_ERROR}; padding: 8px;")
        compare.add_widget(self._wrap_matrix_card("A⁻¹ B⁻¹  (orden incorrecto)", self.id_wrong_order_view), 1)
        self.identity_compare_row = compare
        compare.setVisible(False)
        outer.addWidget(compare)

        self.identity_checklist = QLabel("Calcula para contrastar las tres identidades celda a celda.")
        self.identity_checklist.setObjectName("inverseAlgebraChecklist")
        self.identity_checklist.setWordWrap(True)
        self.identity_checklist.setTextFormat(Qt.RichText)
        self.identity_checklist.setTextInteractionFlags(Qt.TextSelectableByMouse)
        outer.addWidget(self.identity_checklist)

        self.identity_stepper = AlgorithmStepperCarousel(variable_headers=False)
        self.identity_stepper.setObjectName("inverseAlgebraStepper")
        self.identity_stepper.set_export_title("Identidades de la inversa")
        self.identity_stepper.set_empty_hint("Calcula para ver A⁻¹, B⁻¹, AB y (AB)⁻¹.")
        self.identity_stepper.setMinimumHeight(220)
        outer.addWidget(self.identity_stepper)
        outer.addStretch(1)
        return page

    def _create_titled_matrix_card(
        self,
        title: str,
        body: Optional[QWidget],
        header_extra: Optional[QWidget] = None,
    ) -> Tuple[QFrame, QLabel]:
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        if header_extra is None:
            layout.addWidget(lbl)
        else:
            header = QHBoxLayout()
            header.addWidget(lbl)
            header.addStretch(1)
            header.addWidget(header_extra)
            layout.addLayout(header)
        if body is not None:
            body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            layout.addWidget(body, stretch=1)
        return card, lbl

    def _wrap_matrix_card(self, title: str, body: Optional[QWidget]) -> QFrame:
        card, _ = self._create_titled_matrix_card(title, body)
        return card

    # ------------------------------------------------------------------
    # Modos y validación
    # ------------------------------------------------------------------

    def _set_page(self, index: int) -> None:
        button = self.mode_group.button(index)
        if button is not None:
            button.setChecked(True)
        self.pages.setCurrentIndex(index)

    def _on_mode_changed(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        self._clear_result()
        self._refresh_compatibility()

    def _on_op_changed(self, op_id: int) -> None:
        self._op = {0: "add", 1: "sub", 2: "mul"}[op_id]
        self._clear_result()
        self._refresh_compatibility()

    def _on_operands_changed(self) -> None:
        self._clear_highlights()
        self._refresh_compatibility()

    def _on_include_b_toggled(self, checked: bool) -> None:
        if checked and self.grid_transpose_b.snapshot()[2] == tuple(tuple("0" for _ in range(3)) for _ in range(2)):
            self.copy_partner_from_binary(silent=True)
        self.transpose_b_card.setVisible(checked)
        self._on_operands_changed()

    def copy_partner_from_binary(self, silent: bool = False) -> None:
        """Copia la B de la vista A ∘ B a la tarjeta B de la transpuesta."""
        if not self.grid_b.is_all_valid():
            return
        self.grid_transpose_b.set_matrix(self.grid_b.get_matrix())
        if not silent:
            show_toast(self, "Se copió B de la vista A ∘ B.", kind="info", action_text="Deshacer", action=self.grid_transpose_b.undo)

    def _is_scalar_mode(self) -> bool:
        return self.pages.currentIndex() == PAGE_SCALAR

    def _is_transpose_mode(self) -> bool:
        return self.pages.currentIndex() == PAGE_TRANSPOSE

    def _is_distributive_mode(self) -> bool:
        return self.pages.currentIndex() == PAGE_DISTRIBUTIVE

    def _is_inverse_mode(self) -> bool:
        return self.pages.currentIndex() == PAGE_INVERSE

    def _is_tmi_mode(self) -> bool:
        return self.pages.currentIndex() == PAGE_TMI

    def _is_identities_mode(self) -> bool:
        return self.pages.currentIndex() == PAGE_IDENTITIES

    def _on_dist_prop_changed(self, prop_id: int) -> None:
        titles = (
            ("LHS: A · (B + C)", "RHS: A·B + A·C"),
            ("LHS: (A + B) · C", "RHS: A·C + B·C"),
            ("LHS: A · (B · C)", "RHS: (A · B) · C"),
        )[prop_id]
        self.dist_lhs_title_lbl.setText(titles[0])
        self.dist_rhs_title_lbl.setText(titles[1])
        self._clear_result()
        self._refresh_compatibility()

    def _refresh_compatibility(self) -> None:
        ok, message = self._compatibility_state()
        self.badge.setText(message)
        self.badge.setStyleSheet(_badge_style(ok))
        self.compute_btn.setEnabled(ok)
        self.compute_btn.setToolTip("Calcular (Ctrl+Intro desde cualquier celda)" if ok else message)
        fix = self._dimension_fix()
        if fix is None:
            self.fix_dims_btn.setVisible(False)
        else:
            self.fix_dims_btn.setText(fix[0])
            self.fix_dims_btn.setToolTip(fix[1])
            self.fix_dims_btn.setVisible(True)

    def _dimension_fix(self) -> Optional[Tuple[str, str]]:
        """Texto del atajo «Ajustar B» si la operación binaria no es conformable."""
        if self.pages.currentIndex() != PAGE_BINARY:
            return None
        if not self.grid_a.is_all_valid() or not self.grid_b.is_all_valid():
            return None
        ra, ca = self.grid_a.data_shape()
        rb, cb = self.grid_b.data_shape()
        if self._op in ("add", "sub") and (ra, ca) != (rb, cb):
            return (f"Ajustar B a {ra}×{ca}", "Agrega o recorta filas y columnas de B para igualar a A")
        if self._op == "mul" and ca != rb:
            return (f"Ajustar B a {ca} filas", "B necesita tantas filas como columnas tiene A")
        return None

    def fix_partner_dimensions(self) -> None:
        """Redimensiona B para que la operación elegida sea conformable (deshacible)."""
        ra, ca = self.grid_a.data_shape()
        rb, cb = self.grid_b.data_shape()
        if self._op in ("add", "sub"):
            self.grid_b.resize_to(ra, ca)
        else:
            self.grid_b.resize_to(ca, cb)
        rows, cols = self.grid_b.data_shape()
        show_toast(
            self,
            f"B ahora es {rows}×{cols}. Las entradas nuevas valen 0.",
            kind="info",
            action_text="Deshacer",
            action=self.grid_b.undo,
        )

    def _compatibility_state(self) -> Tuple[bool, str]:
        if self._is_tmi_mode():
            return self._square_grid_compatibility(self.grid_tmi, "el Teorema de la Matriz Invertible")
        if self._is_identities_mode():
            return self._identities_compatibility()
        if self._is_inverse_mode():
            return self._inverse_compatibility()
        if self._is_distributive_mode():
            return self._distributive_compatibility()
        if self._is_transpose_mode():
            return self._transpose_compatibility()
        if self._is_scalar_mode():
            if not self.scalar_edit.is_valid():
                return False, "✕ El escalar k no es un número válido (usa enteros, a/b o decimales)."
            if not self.grid_scalar.is_all_valid():
                return False, f"✕ Hay celdas no numéricas en A. {self.grid_scalar.validation_message()}"
            r, c = self.grid_scalar.data_shape()
            return True, f"✓ Multiplicación escalar definida: k · A ({r}×{c})"

        if not self.grid_a.is_all_valid() or not self.grid_b.is_all_valid():
            detail = self.grid_a.validation_message() or self.grid_b.validation_message()
            return False, f"✕ Hay celdas no numéricas. Corrige las entradas marcadas. {detail}"

        ra, ca = self.grid_a.data_shape()
        rb, cb = self.grid_b.data_shape()
        if self._op in ("add", "sub"):
            nombre = "suma" if self._op == "add" else "resta"
            if (ra, ca) == (rb, cb):
                return True, f"✓ Dimensiones compatibles para {nombre}: ({ra}×{ca}) = ({rb}×{cb})"
            return (
                False,
                f"✕ Dimensiones incompatibles: A es {ra}×{ca} y B es {rb}×{cb}. "
                f"La {nombre} exige matrices de idénticas dimensiones m×n.",
            )

        if ca == rb:
            return (
                True,
                f"✓ Dimensiones compatibles para producto: ({ra}×{ca}) · ({rb}×{cb}) = ({ra}×{cb})",
            )
        return (
            False,
            f"✕ Dimensiones incompatibles: Columnas de A ({ca}) ≠ Filas de B ({rb}). "
            "El producto A (m×n) · B (n×p) exige que las columnas de A igualen las filas de B.",
        )

    def _distributive_compatibility(self) -> Tuple[bool, str]:
        """Comprueba dimensiones de A, B y C para la propiedad seleccionada."""
        if (
            not self.grid_dist_a.is_all_valid()
            or not self.grid_dist_b.is_all_valid()
            or not self.grid_dist_c.is_all_valid()
        ):
            return False, "✕ Hay celdas no numéricas en A, B o C. Corrige las entradas marcadas."

        ra, ca = self.grid_dist_a.data_shape()
        rb, cb = self.grid_dist_b.data_shape()
        rc, cc = self.grid_dist_c.data_shape()
        prop_id = self.dist_prop_group.checkedId()

        if prop_id == 0:
            if (rb, cb) != (rc, cc):
                return (
                    False,
                    f"✕ Dimensiones incompatibles para B + C: B es {rb}×{cb} y C es {rc}×{cc}. "
                    "Para sumarse, B y C deben tener idénticas dimensiones.",
                )
            if ca != rb:
                return (
                    False,
                    f"✕ Dimensiones incompatibles para A · (B + C): Columnas de A ({ca}) ≠ Filas de (B+C) ({rb}). "
                    "El producto exige que las columnas de A igualen las filas de B.",
                )
            return (
                True,
                f"✓ Compatible para distributiva izquierda: A ({ra}×{ca}) · [B+C ({rb}×{cb})] = A·B + A·C ⇒ ({ra}×{cb})",
            )

        if prop_id == 1:
            if (ra, ca) != (rb, cb):
                return (
                    False,
                    f"✕ Dimensiones incompatibles para A + B: A es {ra}×{ca} y B es {rb}×{cb}. "
                    "Para sumarse, A y B deben tener idénticas dimensiones.",
                )
            if ca != rc:
                return (
                    False,
                    f"✕ Dimensiones incompatibles para (A + B) · C: Columnas de (A+B) ({ca}) ≠ Filas de C ({rc}). "
                    "El producto exige que las columnas de (A+B) igualen las filas de C.",
                )
            return (
                True,
                f"✓ Compatible para distributiva derecha: [A+B ({ra}×{ca})] · C ({rc}×{cc}) = A·C + B·C ⇒ ({ra}×{cc})",
            )

        if ca != rb:
            return False, f"✕ Incompatible para A · B: Columnas de A ({ca}) ≠ Filas de B ({rb})."
        if cb != rc:
            return False, f"✕ Incompatible para B · C: Columnas de B ({cb}) ≠ Filas de C ({rc})."
        return (
            True,
            f"✓ Compatible para asociatividad: A ({ra}×{ca}) · B ({rb}×{cb}) · C ({rc}×{cc}) ⇒ Resultado ({ra}×{cc})",
        )

    def _inverse_compatibility(self) -> Tuple[bool, str]:
        """La inversa exige una matriz cuadrada con entradas válidas."""
        if not self.grid_inverse.is_all_valid():
            return False, f"✕ Hay celdas no numéricas en A. {self.grid_inverse.validation_message()}"
        rows, cols = self.grid_inverse.data_shape()
        if rows != cols:
            return (
                False,
                "✕ La inversa solo está definida para matrices cuadradas (n×n). "
                f"A es {rows}×{cols}.",
            )
        return (
            True,
            f"✓ Inversa definida para A de orden {rows}×{rows}. "
            "Se reducirá [A | Iₙ] hasta [Iₙ | A⁻¹].",
        )

    def _transpose_compatibility(self) -> Tuple[bool, str]:
        """La transpuesta siempre existe; solo exige entradas válidas en A, en B y en k."""
        if not self.grid_transpose.is_all_valid():
            return False, f"✕ Hay celdas no numéricas en A. {self.grid_transpose.validation_message()}"
        if not self.identity_scalar_edit.is_valid():
            return False, "✕ El escalar k de la comprobación no es válido."
        if self.include_b_btn.isChecked() and not self.grid_transpose_b.is_all_valid():
            return False, f"✕ Hay celdas no numéricas en B. {self.grid_transpose_b.validation_message()}"
        rows, cols = self.grid_transpose.data_shape()
        return True, f"✓ Transpuesta definida: A es {rows}×{cols}  ⇒  Aᵀ es {cols}×{rows}"

    def _square_grid_compatibility(self, grid: DynamicMatrixGrid, operation: str) -> Tuple[bool, str]:
        if not grid.is_all_valid():
            return False, f"✕ Hay celdas no numéricas en A. {grid.validation_message()}"
        rows, cols = grid.data_shape()
        if rows != cols:
            return (
                False,
                f"✕ {operation[0].upper()}{operation[1:]} exige una matriz cuadrada (n×n). "
                f"A es {rows}×{cols}.",
            )
        return True, f"✓ A es {rows}×{rows}. Se puede evaluar {operation}."

    def _identities_compatibility(self) -> Tuple[bool, str]:
        if not self.grid_id_a.is_all_valid() or not self.grid_id_b.is_all_valid():
            return False, "✕ Hay celdas no numéricas en A o en B."
        rows_a, cols_a = self.grid_id_a.data_shape()
        rows_b, cols_b = self.grid_id_b.data_shape()
        if rows_a != cols_a or rows_b != cols_b or rows_a != rows_b:
            return (
                False,
                "✕ Las identidades piden dos matrices cuadradas del mismo orden. "
                f"A es {rows_a}×{cols_a} y B es {rows_b}×{cols_b}.",
            )
        return True, f"✓ A y B son {rows_a}×{rows_a}. Se contrastarán las tres identidades."

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------

    def compute(self) -> None:
        ok, message = self._compatibility_state()
        if not ok:
            self.compute_btn.setEnabled(False)
            self.badge.setText(message)
            self.badge.setStyleSheet(_badge_style(False))
            return

        try:
            if self._is_tmi_mode():
                self._compute_tmi()
            elif self._is_identities_mode():
                self._compute_identities()
            elif self._is_inverse_mode():
                self._compute_inverse()
            elif self._is_distributive_mode():
                self._compute_distributive()
            elif self._is_transpose_mode():
                self._compute_transpose()
            elif self._is_scalar_mode():
                self._compute_scalar()
            else:
                self._compute_binary()
        except DimensionMismatchError as exc:
            self.badge.setText(f"✕ {exc}")
            self.badge.setStyleSheet(_badge_style(False))
            self.compute_btn.setEnabled(False)
        except Exception as exc:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Error matemático")
            box.setText(str(exc))
            apply_message_box_theme(box)
            box.exec()

    def _compute_scalar(self) -> None:
        """Calcula k·A y comprueba (k·A)ᵀ = k·Aᵀ."""
        k = parse_scalar(self.scalar_edit.text())
        primary = self.grid_scalar.get_matrix()
        result = matrix_scale(primary, k)
        self.scalar_result_view.set_matrix(result, split_col=None, clickable=False, show_headers=False)
        self._result = result
        self._details = []
        special = ""
        if k == 0:
            special = " Con k = 0 el resultado es la matriz nula O."
        elif k == -1:
            special = " Con k = −1 el resultado es la matriz opuesta −A."
        self.inspector_label.setText(f"Cada celda se escala: Cᵢⱼ = ({format_scalar(k)}) · Aᵢⱼ.{special}")
        self._show_properties(primary, None, k)

    def _compute_binary(self) -> None:
        """Calcula A±B o A·B y contrasta las identidades de la transpuesta con B."""
        primary = self.grid_a.get_matrix()
        other = self.grid_b.get_matrix()
        if self._op == "add":
            result = matrix_add(primary, other)
            self._details = []
            self.inspector_label.setText("Suma elemento a elemento: Cᵢⱼ = Aᵢⱼ + Bᵢⱼ.")
        elif self._op == "sub":
            result = matrix_sub(primary, other)
            self._details = []
            self.inspector_label.setText("Resta elemento a elemento: Cᵢⱼ = Aᵢⱼ − Bᵢⱼ.")
        else:
            result, self._details = matrix_multiply_with_details(primary, other)
            self.inspector_label.setText(
                "Producto calculado con tres bucles anidados. "
                "Pulsa una celda de C para inspeccionar Cᵢⱼ = Σₖ Aᵢₖ · Bₖⱼ."
            )
        self._result = result
        self._set_inspected(None)
        self.result_view.set_matrix(result, split_col=None, clickable=self._op == "mul", show_headers=False)
        self._show_properties(primary, other, None)

    def _inverse_check_html(self, order: int, left_ok: bool, right_ok: bool) -> str:
        """Checklist visual de A · A⁻¹ = Iₙ y A⁻¹ · A = Iₙ."""

        def line(ok: bool, text: str) -> str:
            color = COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR
            mark = "✓" if ok else "✗"
            return (
                f'<div style="color:{color}; font-size:22px; font-weight:600; margin:4px 0;">'
                f"{mark}&nbsp;&nbsp;{html.escape(text)}</div>"
            )

        return line(left_ok, f"A · A⁻¹ = I_{order}") + line(right_ok, f"A⁻¹ · A = I_{order}")

    def _compute_inverse(self) -> None:
        """Calcula A⁻¹ por Gauss-Jordan y comprueba la identidad, o explica la singularidad."""
        primary = self.grid_inverse.get_matrix()
        try:
            result = matrix_inverse(primary)
        except SingularMatrixError as exc:
            self._result = None
            self._details = []
            self.inverse_result_view.clear()
            self.reuse_inverse_btn.setEnabled(False)
            self.badge.setText(f"✕ {prettify_math_text(str(exc))}")
            self.badge.setStyleSheet(_badge_style(False))
            steps = exc.tracer.get_steps() if exc.tracer is not None else []
            self.inverse_stepper.set_steps(steps)
            alert_index = self.inverse_stepper.first_alert_index()
            where = ""
            if alert_index is not None:
                self.inverse_stepper.go_to_step(alert_index)
                where = f" La fila de ceros aparece en el paso {alert_index + 1} (resaltada en el carrusel)."
            self.inverse_check_label.setText(
                f'<div style="color:{COLOR_FEEDBACK_ERROR}; font-size:22px; font-weight:600;">'
                "✗ A es singular: no existe A⁻¹ y A · A⁻¹ = Iₙ no se puede comprobar.</div>"
                f'<div style="color:{COLOR_TEXT_PRIMARY}; font-size:16px; margin-top:6px;">{html.escape(where.strip())}</div>'
            )
            self.inspector_label.setText(
                "La reducción de [A | Iₙ] no alcanzó [Iₙ | A⁻¹]. "
                "Recorre el carrusel: una fila de ceros en el bloque izquierdo prueba que A es singular."
                + where
            )
            self._show_properties(primary, None, None)
            return
        except NonSquareMatrixError as exc:
            self.badge.setText(f"✕ {exc}")
            self.badge.setStyleSheet(_badge_style(False))
            self.compute_btn.setEnabled(False)
            return

        order = primary.rows
        identity = Matrix.identity(order)
        left_ok = matrix_multiply(primary, result.inverse) == identity
        right_ok = matrix_multiply(result.inverse, primary) == identity
        self._result = result.inverse
        self._details = []
        self.inverse_result_view.set_matrix(result.inverse, split_col=None, clickable=False, show_headers=False)
        self.reuse_inverse_btn.setEnabled(True)
        self.inverse_check_label.setText(self._inverse_check_html(order, left_ok, right_ok))
        self.inverse_stepper.set_steps(result.tracer.get_steps())
        self.badge.setText(f"✓ Matriz invertible {order}×{order}. A · A⁻¹ = I_{order}.")
        self.badge.setStyleSheet(_badge_style(left_ok and right_ok))
        self.inspector_label.setText(
            "Inversión por Gauss-Jordan sobre [A | Iₙ]. "
            "El bloque derecho de la forma reducida es A⁻¹. "
            "Recorre el carrusel para ver cada operación elemental."
        )
        self._show_properties(primary, None, None)

    def use_inverse_as_input(self) -> None:
        """Pone A⁻¹ en la cuadrícula y calcula: el resultado debe ser la A original."""
        inverse = self.inverse_result_view.matrix()
        if inverse is None:
            return
        self.grid_inverse.set_matrix(inverse)
        self.compute()
        show_toast(
            self,
            "A⁻¹ ahora es la entrada: el resultado es (A⁻¹)⁻¹, que debe coincidir con la A original.",
            kind="info",
            action_text="Volver a A",
            action=self._restore_inverse_input,
        )

    def receive_inverse(self, matrix, source: str = "Determinantes") -> None:
        """Recibe A⁻¹ de otro módulo en la página de la inversa y la invierte de nuevo."""
        self._set_page(4)
        self._on_mode_changed(4)
        self.grid_inverse.set_matrix(matrix)
        self.compute()
        show_toast(
            self,
            f"A⁻¹ llegó desde {source}. Su inversa es la A original: (A⁻¹)⁻¹ = A.",
            kind="success",
            action_text="Deshacer",
            action=self._restore_inverse_input,
        )

    def _restore_inverse_input(self) -> None:
        if self.grid_inverse.undo():
            self.compute()

    def _compute_transpose(self) -> None:
        """Calcula Aᵀ, comprueba (Aᵀ)ᵀ = A y publica las propiedades estructurales."""
        primary = self.grid_transpose.get_matrix()
        result = matrix_transpose(primary)
        double_result = matrix_transpose(result)
        self.transpose_result_view.set_matrix(result, split_col=None, clickable=False, show_headers=False)
        self.double_transpose_result_view.set_matrix(double_result, split_col=None, clickable=False, show_headers=False)
        self._result = result
        self._details = []
        rows, cols = primary.shape
        self.inspector_label.setTextFormat(Qt.RichText)
        self.inspector_label.setText(
            f"<b>Transpuesta doble:</b> (Aᵀ)ᵀ = A.<br/>"
            f"A es {rows}×{cols}, Aᵀ es {cols}×{rows}, y (Aᵀ)ᵀ vuelve a ser {rows}×{cols} exactamente igual a A."
        )
        self._show_properties(primary, self._optional_partner(), self._optional_identity_scalar())

    def _compute_distributive(self) -> None:
        """Comprueba identidades algebraicas con tres matrices A, B, C y traza los intermedios."""
        A = self.grid_dist_a.get_matrix()
        B = self.grid_dist_b.get_matrix()
        C = self.grid_dist_c.get_matrix()
        prop_id = self.dist_prop_group.checkedId()
        tracer = StepTracer()

        if prop_id == 0:
            res = verify_matrix_distributive_left(A, B, C)
            label, lhs_expr, rhs_expr = "Distributiva izquierda", "A · (B + C)", "A·B + A·C"
            lhs_long, rhs_long = "A · (B + C)", "(A · B) + (A · C)"
            tracer.record_initial(res.intermediate_sum, "Primero se suma dentro del paréntesis.", r"B + C")
            tracer.record_step(res.lhs_result, r"A(B + C)", "Miembro izquierdo: A por la suma.")
            tracer.record_step(res.first_product, r"AB", "Miembro derecho, primer producto.")
            tracer.record_step(res.second_product, r"AC", "Miembro derecho, segundo producto.")
            tracer.record_step(res.rhs_result, r"AB + AC", "Miembro derecho: suma de los dos productos.")
        elif prop_id == 1:
            res = verify_matrix_distributive_right(A, B, C)
            label, lhs_expr, rhs_expr = "Distributiva derecha", "(A + B) · C", "A·C + B·C"
            lhs_long, rhs_long = "(A + B) · C", "(A · C) + (B · C)"
            tracer.record_initial(res.intermediate_sum, "Primero se suma dentro del paréntesis.", r"A + B")
            tracer.record_step(res.lhs_result, r"(A + B)C", "Miembro izquierdo: la suma por C.")
            tracer.record_step(res.first_product, r"AC", "Miembro derecho, primer producto.")
            tracer.record_step(res.second_product, r"BC", "Miembro derecho, segundo producto.")
            tracer.record_step(res.rhs_result, r"AC + BC", "Miembro derecho: suma de los dos productos.")
        else:
            res = verify_matrix_associative(A, B, C)
            label, lhs_expr, rhs_expr = "Asociativa", "A · (B · C)", "(A · B) · C"
            lhs_long, rhs_long = "A · (B · C)", "(A · B) · C"
            tracer.record_initial(res.intermediate_bc, "Miembro izquierdo: primero B·C.", r"BC")
            tracer.record_step(res.lhs_result, r"A(BC)", "A por el producto B·C.")
            tracer.record_step(res.intermediate_ab, r"AB", "Miembro derecho: primero A·B.")
            tracer.record_step(res.rhs_result, r"(AB)C", "El producto A·B por C.")

        self.dist_lhs_view.set_matrix(res.lhs_result, split_col=None, clickable=False, show_headers=False)
        self.dist_rhs_view.set_matrix(res.rhs_result, split_col=None, clickable=False, show_headers=False)
        self.dist_equals_lbl.setText("=" if res.is_equal else "≠")
        self.dist_stepper.set_steps(tracer.get_steps())
        self._result = res.lhs_result
        self._details = []
        dim_str = f"{res.lhs_result.shape[0]}×{res.lhs_result.shape[1]}"
        self.dist_comparison_label.setText(
            format_comparison_row_html(
                mark="✓" if res.is_equal else "✗",
                label=label,
                lhs_expr=lhs_expr,
                rhs_expr=rhs_expr,
                ok=res.is_equal,
                font_size_px=22,
            )
        )
        self.inspector_label.setTextFormat(Qt.RichText)
        self.inspector_label.setText(
            f"<b>Comprobación {label.lower()}:</b><br/>"
            f"LHS = {lhs_long}: Matriz {dim_str}<br/>"
            f"RHS = {rhs_long}: Matriz {dim_str}<br/>"
            f"¿Ambas matrices son idénticas elemento a elemento? "
            f"<b>{'✓ SÍ, coinciden exactamente' if res.is_equal else '✗ No coinciden'}</b>"
        )
        self.properties_label.setText(_checks_to_html(analyze_matrix(A, B, C=C)))

    def _optional_partner(self) -> Optional[Matrix]:
        """B de la propia página, solo si el usuario pidió las identidades binarias."""
        if not self.include_b_btn.isChecked() or not self.grid_transpose_b.is_all_valid():
            return None
        return self.grid_transpose_b.get_matrix()

    def _optional_identity_scalar(self) -> Any:
        """Escalar k de la página de transpuesta, o None si el campo está vacío."""
        text = self.identity_scalar_edit.text().strip()
        if not text:
            return None
        return parse_scalar(text)

    def _show_properties(self, primary: Matrix, other: Optional[Matrix], scalar: Any) -> None:
        """Pinta las tarjetas de propiedades a partir del motor compartido."""
        self.properties_label.setText(_checks_to_html(analyze_matrix(primary, other, scalar)))

    # ------------------------------------------------------------------
    # Inspector de producto
    # ------------------------------------------------------------------

    def _set_inspected(self, cell: Optional[Tuple[int, int]]) -> None:
        self._inspected = cell
        if cell is None:
            self.inspect_badge.setVisible(False)
            self.inspect_badge.setText("")
            return
        row, col = cell
        self.inspect_badge.setText(f"Inspeccionando C{to_subscript(f'{row + 1},{col + 1}')}")
        self.inspect_badge.setVisible(True)

    def inspected_cell(self) -> Optional[Tuple[int, int]]:
        return self._inspected

    def _on_result_cell_clicked(self, row: int, col: int) -> None:
        if not self._details:
            return
        detail = next((d for d in self._details if d.row == row and d.col == col), None)
        if detail is None:
            return
        self.grid_a.set_highlight(rows=[row])
        self.grid_b.set_highlight(cols=[col])
        self.result_view.set_matrix(
            self._result,
            split_col=None,
            clickable=True,
            show_headers=False,
            highlight_row=row,
            highlight_col=col,
        )
        self._set_inspected((row, col))
        terms = []
        for k, (a_ik, b_kj, prod) in enumerate(detail.products):
            terms.append(
                f"A_{row + 1}{k + 1}·B_{k + 1}{col + 1} = "
                f"({format_scalar(a_ik)})·({format_scalar(b_kj)}) = {format_scalar(prod)}"
            )
        self.inspector_label.setTextFormat(Qt.PlainText)
        self.inspector_label.setText(f"{detail.formula}\n\n" + "\n".join(terms))

    def _clear_highlights(self) -> None:
        self.grid_a.clear_highlight()
        self.grid_b.clear_highlight()
        if hasattr(self, "inspect_badge"):
            self._set_inspected(None)

    def _clear_result(self) -> None:
        self._result = None
        self._details = []
        for view in (
            self.result_view, self.scalar_result_view, self.transpose_result_view,
            self.double_transpose_result_view, self.dist_lhs_view, self.dist_rhs_view,
            self.inverse_result_view, self.id_ab_inverse_view, self.id_ba_product_view,
            self.id_wrong_order_view,
        ):
            view.clear()
        self.dist_comparison_label.clear()
        self.dist_equals_lbl.setText("=")
        self.dist_stepper.set_steps([])
        self.reuse_inverse_btn.setEnabled(False)
        self.inverse_stepper.set_steps([])
        self.inverse_check_label.setText("Calcula para comprobar A · A⁻¹ = Iₙ y ver la reducción de [A | Iₙ].")
        self._tmi_checks = []
        self.tmi_key_card.setVisible(False)
        self.tmi_checklist.setText("Calcula para ver *c, *e, *h y det(A) ≠ 0.")
        self.tmi_stepper.set_steps([])
        self.identity_compare_row.setVisible(False)
        self.identity_checklist.setText("Calcula para contrastar las tres identidades celda a celda.")
        self.identity_stepper.set_steps([])
        self._clear_highlights()
        self.inspector_label.setTextFormat(Qt.PlainText)
        self.inspector_label.setText(
            "Calcula un producto A · B y pulsa una celda de C para ver la fila de A, "
            "la columna de B y la sumatoria de productos parciales."
        )
        self.properties_label.setText(
            "Calcula para ver qué tipo de matriz es, qué propiedades cumple "
            "y si se verifican las identidades de la transpuesta."
        )

    # ------------------------------------------------------------------
    # TMI
    # ------------------------------------------------------------------

    @staticmethod
    def _tmi_row(item, size: int = 18) -> str:
        color = COLOR_FEEDBACK_SUCCESS if item.holds else COLOR_FEEDBACK_ERROR
        mark = "Cumple" if item.holds else "No cumple"
        body = prettify_math_text(f"{item.statement} {item.evidence}")
        text = html.escape(f"{mark}   {item.code}   {body}")
        return f'<div style="color:{color}; font-size:{size}px; font-weight:600; margin:4px 0;">{text}</div>'

    def _tmi_to_html(self, checks) -> str:
        if self._tmi_filter == "key":
            checks = [item for item in checks if item.code in TMI_KEY_CODES]
        elif self._tmi_filter == "failed":
            checks = [item for item in checks if not item.holds]
            if not checks:
                return (
                    f'<div style="color:{COLOR_FEEDBACK_SUCCESS}; font-size:18px; font-weight:600;">'
                    "Todas las caracterizaciones se cumplen: A es invertible.</div>"
                )
        return "".join(self._tmi_row(item) for item in checks)

    def _tmi_key_html(self, checks) -> str:
        key_items = [item for item in checks if item.code in TMI_KEY_CODES]
        all_hold = all(item.holds for item in key_items)
        border = COLOR_FEEDBACK_SUCCESS if all_hold else COLOR_FEEDBACK_ERROR
        self.tmi_key_card.setStyleSheet(
            f"QLabel#tmiKeyCard {{ background-color: {rgba(border, 0.10)}; border: 1px solid {rgba(border, 0.45)}; "
            f"border-radius: 8px; padding: 10px 14px; }}"
        )
        rows = []
        for item in key_items:
            color = COLOR_FEEDBACK_SUCCESS if item.holds else COLOR_FEEDBACK_ERROR
            mark = "✓" if item.holds else "✗"
            rows.append(
                f'<div style="color:{color}; font-size:20px; font-weight:700; margin:3px 0;">'
                f"{mark}&nbsp;&nbsp;{html.escape(item.code)}&nbsp;&nbsp;{html.escape(item.statement)}</div>"
            )
        return (
            f'<div style="color:{COLOR_TEXT_PRIMARY}; font-size:15px; font-weight:700; margin-bottom:4px;">'
            "Caracterizaciones clave de la sesión</div>"
            + "".join(rows)
        )

    def _on_tmi_filter(self, index: int) -> None:
        self._tmi_filter = ("all", "key", "failed")[index]
        if self._tmi_checks:
            self.tmi_checklist.setText(self._tmi_to_html(self._tmi_checks))

    def _compute_tmi(self) -> None:
        matrix = self.grid_tmi.get_matrix()
        result = evaluate_invertible_matrix_theorem(matrix)
        self._result = None
        self._details = []
        self._tmi_checks = list(result.checks)
        self.tmi_key_card.setText(self._tmi_key_html(result.checks))
        self.tmi_key_card.setVisible(True)
        self.tmi_checklist.setText(self._tmi_to_html(result.checks))
        self.tmi_stepper.set_steps(result.tracer.get_steps())
        if result.is_invertible:
            self.badge.setText(
                f"✓ A es invertible. det(A) = {format_scalar(result.determinant)}. "
                f"Cumple *c, *e y *h ({result.pivot_count} pivotes)."
            )
            self.badge.setStyleSheet(_badge_style(True))
        else:
            self.badge.setText(
                f"✕ A es singular. det(A) = {format_scalar(result.determinant)}. "
                "Alguna caracterización del TMI no se cumple."
            )
            self.badge.setStyleSheet(_badge_style(False))
            alert_index = self.tmi_stepper.first_alert_index()
            if alert_index is not None:
                self.tmi_stepper.go_to_step(alert_index)
        self.inspector_label.setText(
            "Teorema de la Matriz Invertible. Cada renglón es una caracterización equivalente. "
            "Las marcadas por la cátedra son *c (pivotes), *e (columnas independientes) y *h (generan ℝⁿ)."
        )

    # ------------------------------------------------------------------
    # Identidades de la inversa
    # ------------------------------------------------------------------

    def _compute_identities(self) -> None:
        primary = self.grid_id_a.get_matrix()
        other = self.grid_id_b.get_matrix()
        result = verify_inverse_algebraic_identities(primary, other)
        self._result = None
        self._details = []
        self.identity_checklist.setText(_checks_to_html(result.checks))
        self.identity_stepper.set_steps(result.tracer.get_steps())
        self._show_identity_matrices(primary, other)
        all_hold = all(check.status == "cumple" for check in result.checks)
        if all_hold:
            self.badge.setText("✓ Las tres identidades de la inversa se cumplen celda a celda.")
            self.badge.setStyleSheet(_badge_style(True))
        else:
            self.badge.setText("✕ Alguna identidad de la inversa no se cumple o no aplica.")
            self.badge.setStyleSheet(_badge_style(False))
        self.inspector_label.setText(
            "(A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹ A⁻¹ y (Aᵀ)⁻¹ = (A⁻¹)ᵀ. "
            "El checklist compara ambos lados celda a celda."
        )

    def _show_identity_matrices(self, primary: Matrix, other: Matrix) -> None:
        """(AB)⁻¹, B⁻¹A⁻¹ y el contraejemplo A⁻¹B⁻¹ lado a lado."""
        try:
            inv_a = matrix_inverse(primary).inverse
            inv_b = matrix_inverse(other).inverse
            inv_ab = matrix_inverse(matrix_multiply(primary, other)).inverse
        except (SingularMatrixError, NonSquareMatrixError):
            self.identity_compare_row.setVisible(False)
            return
        right_order = matrix_multiply(inv_b, inv_a)
        wrong_order = matrix_multiply(inv_a, inv_b)
        self.id_ab_inverse_view.set_matrix(inv_ab, show_headers=False)
        self.id_ba_product_view.set_matrix(right_order, show_headers=False)
        self.id_wrong_order_view.set_matrix(wrong_order, show_headers=False)
        self.id_wrong_connector.setText("≠" if wrong_order != inv_ab else "=")
        self.identity_compare_row.setVisible(True)

    # ------------------------------------------------------------------
    # Ejemplos
    # ------------------------------------------------------------------

    def load_tmi_invertible_sample(self) -> None:
        """Sesión 10, diapositiva 19."""
        self._set_page(PAGE_TMI)
        self.grid_tmi.set_matrix(Matrix([[1, 0, -2], [3, 1, -2], [-5, -1, 9]]))
        self._refresh_compatibility()
        self.compute()

    def load_tmi_singular_sample(self) -> None:
        """Sesión 10, diapositiva 20."""
        self._set_page(PAGE_TMI)
        self.grid_tmi.set_matrix(Matrix([[2, 3, 4], [2, 3, 4], [2, 3, 4]]))
        self._refresh_compatibility()
        self.compute()

    def load_inverse_identities_sample(self) -> None:
        """Identidades con la matriz invertible de la sesión 10 y una triangular superior."""
        self._set_page(PAGE_IDENTITIES)
        self.grid_id_a.set_matrix(Matrix([[1, 0, -2], [3, 1, -2], [-5, -1, 9]]))
        self.grid_id_b.set_matrix(Matrix([[1, 1, 0], [0, 1, 1], [0, 0, 1]]))
        self._refresh_compatibility()
        self.compute()

    def load_compatible_product_sample(self) -> None:
        self._set_page(PAGE_BINARY)
        self.mul_btn.setChecked(True)
        self._op = "mul"
        self.grid_a.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
        self.grid_b.set_matrix(Matrix([[7, 8], [9, 10], [11, 12]]))
        self.compute()

    def load_incompatible_sample(self) -> None:
        self._set_page(PAGE_BINARY)
        self.mul_btn.setChecked(True)
        self._op = "mul"
        self.grid_a.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
        self.grid_b.set_matrix(Matrix([[1, 2], [3, 4]]))
        self._clear_result()
        self._refresh_compatibility()

    def load_inverse_sample(self) -> None:
        """Sesión 10, diapositiva 11: inversa 3×3 por Gauss-Jordan."""
        self._set_page(PAGE_INVERSE)
        self.grid_inverse.set_matrix(Matrix([[0, 1, 2], [1, 0, 3], [4, -3, 8]]))
        self.compute()

    def load_singular_inverse_sample(self) -> None:
        """Matriz con la tercera fila igual a la suma de las dos primeras: no tiene inversa."""
        self._set_page(PAGE_INVERSE)
        self.grid_inverse.set_matrix(Matrix([[1, 2, 3], [0, 1, 4], [1, 3, 7]]))
        self.compute()

    def load_distributive_matrix_sample(self) -> None:
        """Distributiva por la izquierda con matrices 2×2."""
        self._set_page(PAGE_DISTRIBUTIVE)
        self.dist_left_btn.setChecked(True)
        self._on_dist_prop_changed(0)
        self.grid_dist_a.set_matrix(Matrix([[1, 2], [3, 4]]))
        self.grid_dist_b.set_matrix(Matrix([[5, 6], [7, 8]]))
        self.grid_dist_c.set_matrix(Matrix([[2, -1], [0, 3]]))
        self.compute()

    def load_distributive_right_sample(self) -> None:
        """Distributiva por la derecha: A y B 2×3, C 3×2."""
        self._set_page(PAGE_DISTRIBUTIVE)
        self.dist_right_btn.setChecked(True)
        self._on_dist_prop_changed(1)
        self.grid_dist_a.set_matrix(Matrix([[1, 0, 2], [-1, 3, 1]]))
        self.grid_dist_b.set_matrix(Matrix([[2, 1, 0], [0, -2, 4]]))
        self.grid_dist_c.set_matrix(Matrix([[1, 2], [0, 1], [3, -1]]))
        self.compute()

    def load_associative_sample(self) -> None:
        """Asociativa con una cadena conformable 2×3 · 3×2 · 2×2."""
        self._set_page(PAGE_DISTRIBUTIVE)
        self.dist_assoc_btn.setChecked(True)
        self._on_dist_prop_changed(2)
        self.grid_dist_a.set_matrix(Matrix([[1, 2, 0], [0, 1, -1]]))
        self.grid_dist_b.set_matrix(Matrix([[2, 1], [1, 0], [0, 3]]))
        self.grid_dist_c.set_matrix(Matrix([[1, -1], [2, 1]]))
        self.compute()

    def load_current_property_sample(self) -> None:
        loaders = (
            self.load_distributive_matrix_sample,
            self.load_distributive_right_sample,
            self.load_associative_sample,
        )
        loaders[max(0, self.dist_prop_group.checkedId())]()
