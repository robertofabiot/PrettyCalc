"""Vista de álgebra matricial: A ± B, k·A, A·B y la transpuesta Aᵀ.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.
Muestra el cambio de dimensión n×m y las propiedades que cumple la matriz.
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
        QStackedWidget,
        QLineEdit,
        QSizePolicy,
        QMessageBox,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.matrix_ops import (
    MultiplicationStepDetail,
    matrix_add,
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
from prettycalc.core.types import DimensionMismatchError, Matrix, format_scalar, parse_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.mathtext import format_comparison_row_html, format_steps_to_rich_html
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
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


def _checks_to_html(checks: Sequence[PropertyCheck]) -> str:
    """Tarjetas en HTML con tamaño grande (22px): verde si cumple, coral si no, gris si no aplica."""
    colors = {
        "cumple": COLOR_FEEDBACK_SUCCESS,
        "no_cumple": COLOR_FEEDBACK_ERROR,
        "no_aplica": COLOR_TEXT_MUTED,
        "dato": COLOR_TEXT_PRIMARY,
    }
    marks = {"cumple": "✓", "no_cumple": "✗", "no_aplica": "—", "dato": "·"}
    rows = []
    for check in checks:
        text = html.escape(f"{check.name}: {check.detail}")
        color = colors[check.status]
        bg = "rgba(129, 178, 154, 0.08)" if check.status == "cumple" else ("rgba(238, 108, 77, 0.08)" if check.status == "no_cumple" else "transparent")
        border = "1px solid rgba(129, 178, 154, 0.35)" if check.status == "cumple" else ("1px solid rgba(238, 108, 77, 0.35)" if check.status == "no_cumple" else "1px solid transparent")
        rows.append(
            f'<div style="background-color:{bg}; border:{border}; border-radius:6px; '
            f'padding:8px 12px; margin:6px 0; color:{color}; font-size:22px; font-weight:600;">'
            f'{marks[check.status]}&nbsp;&nbsp;{text}</div>'
        )
    return "".join(rows)


class MatrixOperationsView(QWidget):
    """Disposición [A] [+|-|×] [B] = [C] con validación en tiempo real."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixOperationsView")
        self._op: str = "mul"
        self._details: List[MultiplicationStepDetail] = []
        self._result: Optional[Matrix] = None
        self._setup_ui()
        self._refresh_compatibility()

    def _setup_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(4, 4, 10, 16)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        self.binary_mode_btn = QPushButton("A  ∘  B")
        self.binary_mode_btn.setObjectName("modeToggle")
        self.binary_mode_btn.setCheckable(True)
        self.binary_mode_btn.setChecked(True)
        self.scalar_mode_btn = QPushButton("k  ·  A")
        self.scalar_mode_btn.setObjectName("modeToggle")
        self.scalar_mode_btn.setCheckable(True)
        self.transpose_mode_btn = QPushButton("Aᵀ")
        self.transpose_mode_btn.setObjectName("modeToggle")
        self.transpose_mode_btn.setCheckable(True)
        self.distrib_mode_btn = QPushButton("A · (B + C)")
        self.distrib_mode_btn.setObjectName("modeToggle")
        self.distrib_mode_btn.setCheckable(True)
        mode_group.addButton(self.binary_mode_btn, 0)
        mode_group.addButton(self.scalar_mode_btn, 1)
        mode_group.addButton(self.transpose_mode_btn, 2)
        mode_group.addButton(self.distrib_mode_btn, 3)
        mode_group.idClicked.connect(self._on_mode_changed)
        toolbar.addWidget(self.binary_mode_btn)
        toolbar.addWidget(self.scalar_mode_btn)
        toolbar.addWidget(self.transpose_mode_btn)
        toolbar.addWidget(self.distrib_mode_btn)
        toolbar.addStretch(1)

        sample_ok = QPushButton("Ejemplo 2×3 · 3×2")
        sample_ok.setObjectName("secondaryAction")
        sample_ok.clicked.connect(self.load_compatible_product_sample)
        sample_bad = QPushButton("Ejemplo incompatible")
        sample_bad.setObjectName("secondaryAction")
        sample_bad.clicked.connect(self.load_incompatible_sample)
        sample_dist = QPushButton("Ejemplo A(B+C)")
        sample_dist.setObjectName("secondaryAction")
        sample_dist.clicked.connect(self.load_distributive_matrix_sample)
        toolbar.addWidget(sample_ok)
        toolbar.addWidget(sample_bad)
        toolbar.addWidget(sample_dist)

        self.header_compute_btn = QPushButton("▶ Calcular")
        self.header_compute_btn.setObjectName("primaryAction")
        self.header_compute_btn.clicked.connect(self.compute)
        toolbar.addWidget(self.header_compute_btn)
        root.addLayout(toolbar)

        self.badge = QLabel("")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        root.addWidget(self.badge)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_binary_page())
        self.pages.addWidget(self._build_scalar_page())
        self.pages.addWidget(self._build_transpose_page())
        self.pages.addWidget(self._build_distributive_page())
        root.addWidget(self.pages, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.compute_btn = QPushButton("▶ Calcular")
        self.compute_btn.setObjectName("primaryAction")
        self.compute_btn.clicked.connect(self.compute)
        actions.addWidget(self.compute_btn)
        root.addLayout(actions)
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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    def _build_binary_page(self) -> QWidget:
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self.grid_a = DynamicMatrixGrid(
            initial_rows=2, initial_cols=3, augmented=False
        )
        self.grid_a.matrixChanged.connect(self._on_operands_changed)
        row.addWidget(self._wrap_matrix_card("Matriz A", self.grid_a), stretch=3)

        op_col = QVBoxLayout()
        op_col.setSpacing(8)
        op_col.addStretch(1)
        self.op_group = QButtonGroup(self)
        self.op_group.setExclusive(True)
        self.add_btn = QPushButton("+")
        self.sub_btn = QPushButton("−")
        self.mul_btn = QPushButton("×")
        for btn, op_id in ((self.add_btn, 0), (self.sub_btn, 1), (self.mul_btn, 2)):
            btn.setObjectName("opSelect")
            btn.setCheckable(True)
            self.op_group.addButton(btn, op_id)
            op_col.addWidget(btn, 0, Qt.AlignCenter)
        self.mul_btn.setChecked(True)
        self.op_group.idClicked.connect(self._on_op_changed)
        op_col.addStretch(1)
        row.addLayout(op_col)

        self.grid_b = DynamicMatrixGrid(
            initial_rows=3, initial_cols=2, augmented=False
        )
        self.grid_b.matrixChanged.connect(self._on_operands_changed)
        row.addWidget(self._wrap_matrix_card("Matriz B", self.grid_b), stretch=3)

        eq = QLabel("=")
        eq.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        row.addWidget(eq, 0, Qt.AlignCenter)

        self.result_view = BookMatrixWidget()
        self.result_view.cellClicked.connect(self._on_result_cell_clicked)
        row.addWidget(self._wrap_matrix_card("Matriz C", self.result_view), stretch=3)
        return page

    def _build_scalar_page(self) -> QWidget:
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        k_card = QFrame()
        apply_widget_class(k_card, "elevated-card")
        k_layout = QVBoxLayout(k_card)
        k_title = QLabel("Escalar k")
        k_title.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        k_layout.addWidget(k_title)
        self.scalar_edit = QLineEdit("2")
        self.scalar_edit.setObjectName("scalarField")
        self.scalar_edit.setFont(QFont("Fira Code", 14))
        self.scalar_edit.setAlignment(Qt.AlignCenter)
        self.scalar_edit.textChanged.connect(self._on_operands_changed)
        k_layout.addWidget(self.scalar_edit)
        hint = QLabel("Entero, fracción o decimal")
        hint.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 13px;")
        k_layout.addWidget(hint)
        k_layout.addStretch(1)
        row.addWidget(k_card)

        dot = QLabel("·")
        dot.setStyleSheet(
            f"font-size: 32px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        row.addWidget(dot, 0, Qt.AlignCenter)

        self.grid_scalar = DynamicMatrixGrid(
            initial_rows=2, initial_cols=2, augmented=False
        )
        self.grid_scalar.matrixChanged.connect(self._on_operands_changed)
        row.addWidget(self._wrap_matrix_card("Matriz A", self.grid_scalar), stretch=3)

        eq = QLabel("=")
        eq.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        row.addWidget(eq, 0, Qt.AlignCenter)

        self.scalar_result_view = BookMatrixWidget()
        row.addWidget(self._wrap_matrix_card("k · A", self.scalar_result_view), stretch=3)
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
        """Página unaria: A a la izquierda, Aᵀ al centro, (Aᵀ)ᵀ = A a la derecha y el escalar k."""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)
        outer.addLayout(self._transpose_matrix_row(), stretch=1)
        outer.addLayout(self._transpose_identity_bar())
        return page

    def _transpose_matrix_row(self) -> QHBoxLayout:
        """Fila visual A → Aᵀ → (Aᵀ)ᵀ = A. El resultado cambia de m×n a n×m y vuelve a m×n."""
        row = QHBoxLayout()
        row.setSpacing(10)
        self.grid_transpose = DynamicMatrixGrid(
            initial_rows=2, initial_cols=3, augmented=False
        )
        self.grid_transpose.matrixChanged.connect(self._on_operands_changed)
        row.addWidget(self._wrap_matrix_card("Matriz A", self.grid_transpose), stretch=3)
        arrow1 = QLabel("→")
        arrow1.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        row.addWidget(arrow1, 0, Qt.AlignCenter)
        self.transpose_result_view = BookMatrixWidget()
        row.addWidget(self._wrap_matrix_card("Aᵀ", self.transpose_result_view), stretch=3)

        arrow2 = QLabel("→")
        arrow2.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        row.addWidget(arrow2, 0, Qt.AlignCenter)
        self.double_transpose_result_view = BookMatrixWidget()
        row.addWidget(self._wrap_matrix_card("(Aᵀ)ᵀ = A", self.double_transpose_result_view), stretch=3)
        return row

    def _transpose_identity_bar(self) -> QHBoxLayout:
        """Escalar k y la opción de usar B en las identidades de la transpuesta."""
        extras = QHBoxLayout()
        extras.setSpacing(8)
        k_label = QLabel("k")
        k_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        extras.addWidget(k_label)
        self.identity_scalar_edit = QLineEdit("1")
        self.identity_scalar_edit.setObjectName("scalarField")
        self.identity_scalar_edit.setFont(QFont("Fira Code", 14))
        self.identity_scalar_edit.setFixedWidth(88)
        self.identity_scalar_edit.setAlignment(Qt.AlignCenter)
        self.identity_scalar_edit.setToolTip("Escalar usado en la comprobación (k·A)ᵀ = k·Aᵀ")
        self.identity_scalar_edit.textChanged.connect(self._on_operands_changed)
        extras.addWidget(self.identity_scalar_edit)
        self.include_b_btn = QPushButton("Incluir B en (A+B)ᵀ y (A·B)ᵀ")
        self.include_b_btn.setObjectName("modeToggle")
        self.include_b_btn.setCheckable(True)
        self.include_b_btn.setToolTip("Usa la matriz B de la vista A ∘ B")
        self.include_b_btn.toggled.connect(self._on_operands_changed)
        extras.addWidget(self.include_b_btn)
        extras.addStretch(1)
        return extras

    def _build_distributive_page(self) -> QWidget:
        """Página ternaria: Propiedad distributiva A(B+C) = AB + AC, (A+B)C = AC + BC y asociativa A(BC) = (AB)C."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Barra de selección de propiedad
        prop_bar = QHBoxLayout()
        prop_bar.setSpacing(8)
        prop_title = QLabel("Propiedad a comprobar:")
        prop_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        prop_bar.addWidget(prop_title)

        self.dist_prop_group = QButtonGroup(self)
        self.dist_prop_group.setExclusive(True)
        self.dist_left_btn = QPushButton("A · (B + C) = A·B + A·C")
        self.dist_left_btn.setObjectName("modeToggle")
        self.dist_left_btn.setCheckable(True)
        self.dist_left_btn.setChecked(True)
        self.dist_right_btn = QPushButton("(A + B) · C = A·C + B·C")
        self.dist_right_btn.setObjectName("modeToggle")
        self.dist_right_btn.setCheckable(True)
        self.dist_assoc_btn = QPushButton("A · (B · C) = (A · B) · C")
        self.dist_assoc_btn.setObjectName("modeToggle")
        self.dist_assoc_btn.setCheckable(True)

        self.dist_prop_group.addButton(self.dist_left_btn, 0)
        self.dist_prop_group.addButton(self.dist_right_btn, 1)
        self.dist_prop_group.addButton(self.dist_assoc_btn, 2)
        self.dist_prop_group.idClicked.connect(self._on_dist_prop_changed)

        prop_bar.addWidget(self.dist_left_btn)
        prop_bar.addWidget(self.dist_right_btn)
        prop_bar.addWidget(self.dist_assoc_btn)
        prop_bar.addStretch(1)
        layout.addLayout(prop_bar)

        # Fila de 3 matrices de entrada: A, B, C
        grids_row = QHBoxLayout()
        grids_row.setSpacing(10)
        self.grid_dist_a = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_dist_a.matrixChanged.connect(self._on_operands_changed)
        grids_row.addWidget(self._wrap_matrix_card("Matriz A", self.grid_dist_a), stretch=1)

        self.grid_dist_b = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_dist_b.matrixChanged.connect(self._on_operands_changed)
        grids_row.addWidget(self._wrap_matrix_card("Matriz B", self.grid_dist_b), stretch=1)

        self.grid_dist_c = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
        self.grid_dist_c.matrixChanged.connect(self._on_operands_changed)
        grids_row.addWidget(self._wrap_matrix_card("Matriz C", self.grid_dist_c), stretch=1)
        layout.addLayout(grids_row)

        # Fila de resultados: Miembro Izquierdo (LHS) = Miembro Derecho (RHS)
        results_row = QHBoxLayout()
        results_row.setSpacing(10)

        self.dist_lhs_view = BookMatrixWidget()
        self.dist_rhs_view = BookMatrixWidget()

        lhs_card, self.dist_lhs_title_lbl = self._create_titled_matrix_card("Miembro izquierdo: A · (B + C)", self.dist_lhs_view)
        rhs_card, self.dist_rhs_title_lbl = self._create_titled_matrix_card("Miembro derecho: A·B + A·C", self.dist_rhs_view)

        results_row.addWidget(lhs_card, stretch=1)
        eq_lbl = QLabel("=")
        eq_lbl.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;")
        results_row.addWidget(eq_lbl, 0, Qt.AlignCenter)
        results_row.addWidget(rhs_card, stretch=1)
        layout.addLayout(results_row)

        # Tarjeta destacada de comprobación grande (≥22px)
        self.dist_comparison_label = QLabel("")
        self.dist_comparison_label.setTextFormat(Qt.RichText)
        self.dist_comparison_label.setWordWrap(True)
        layout.addWidget(self.dist_comparison_label)

        return page

    def _create_titled_matrix_card(self, title: str, body: QWidget) -> Tuple[QFrame, QLabel]:
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        layout.addWidget(lbl)
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(body, stretch=1)
        return card, lbl

    def _wrap_matrix_card(self, title: str, body: QWidget) -> QFrame:
        card, _ = self._create_titled_matrix_card(title, body)
        return card

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

    def _is_scalar_mode(self) -> bool:
        return self.pages.currentIndex() == 1

    def _is_transpose_mode(self) -> bool:
        return self.pages.currentIndex() == 2

    def _is_distributive_mode(self) -> bool:
        return self.pages.currentIndex() == 3

    def _on_dist_prop_changed(self, prop_id: int) -> None:
        self._clear_result()
        self._refresh_compatibility()

    def _refresh_compatibility(self) -> None:
        ok, message = self._compatibility_state()
        self.badge.setText(message)
        self.badge.setStyleSheet(_badge_style(ok))
        self.compute_btn.setEnabled(ok)
        self.compute_btn.setToolTip("" if ok else message)
        if hasattr(self, "header_compute_btn"):
            self.header_compute_btn.setEnabled(ok)
            self.header_compute_btn.setToolTip("" if ok else message)

    def _compatibility_state(self) -> Tuple[bool, str]:
        if self._is_distributive_mode():
            return self._distributive_compatibility()
        if self._is_transpose_mode():
            return self._transpose_compatibility()
        if self._is_scalar_mode():
            text = self.scalar_edit.text().strip()
            try:
                parse_scalar(text)
            except Exception:
                return False, "✕ El escalar k no es un número válido (usa enteros, a/b o decimales)."
            if not self.grid_scalar.is_all_valid():
                return False, "✕ Hay celdas no numéricas en A."
            r, c = self.grid_scalar.data_shape()
            return True, f"✓ Multiplicación escalar definida: k · A ({r}×{c})"

        if not self.grid_a.is_all_valid() or not self.grid_b.is_all_valid():
            return False, "✕ Hay celdas no numéricas. Corrige las entradas marcadas."

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

        if prop_id == 0:  # A · (B + C) = A·B + A·C
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
                    f"El producto exige que las columnas de A igualen las filas de B.",
                )
            return (
                True,
                f"✓ Compatible para distributiva izquierda: A ({ra}×{ca}) · [B+C ({rb}×{cb})] = A·B + A·C ⇒ ({ra}×{cb})",
            )

        if prop_id == 1:  # (A + B) · C = A·C + B·C
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
                    f"El producto exige que las columnas de (A+B) igualen las filas de C.",
                )
            return (
                True,
                f"✓ Compatible para distributiva derecha: [A+B ({ra}×{ca})] · C ({rc}×{cc}) = A·C + B·C ⇒ ({ra}×{cc})",
            )

        # prop_id == 2: A · (B · C) = (A · B) · C
        if ca != rb:
            return (
                False,
                f"✕ Incompatible para A · B: Columnas de A ({ca}) ≠ Filas de B ({rb}).",
            )
        if cb != rc:
            return (
                False,
                f"✕ Incompatible para B · C: Columnas de B ({cb}) ≠ Filas de C ({rc}).",
            )
        return (
            True,
            f"✓ Compatible para asociatividad: A ({ra}×{ca}) · B ({rb}×{cb}) · C ({rc}×{cc}) ⇒ Resultado ({ra}×{cc})",
        )

    def _transpose_compatibility(self) -> Tuple[bool, str]:
        """La transpuesta siempre existe; solo exige entradas válidas en A y en k."""
        if not self.grid_transpose.is_all_valid():
            return False, "✕ Hay celdas no numéricas en A."
        k_text = self.identity_scalar_edit.text().strip()
        if k_text:
            try:
                parse_scalar(k_text)
            except Exception:
                return False, "✕ El escalar k de la comprobación no es válido."
        rows, cols = self.grid_transpose.data_shape()
        return True, f"✓ Transpuesta definida: A es {rows}×{cols}  ⇒  Aᵀ es {cols}×{rows}"

    def compute(self) -> None:
        ok, message = self._compatibility_state()
        if not ok:
            self.compute_btn.setEnabled(False)
            if hasattr(self, "header_compute_btn"):
                self.header_compute_btn.setEnabled(False)
            self.badge.setText(message)
            return

        try:
            if self._is_distributive_mode():
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
            if hasattr(self, "header_compute_btn"):
                self.header_compute_btn.setEnabled(False)
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
        self.scalar_result_view.set_matrix(
            result, split_col=None, clickable=False, show_headers=False
        )
        self._result = result
        self._details = []
        self.inspector_label.setText(
            f"Cada celda se escala: Cᵢⱼ = ({format_scalar(k)}) · Aᵢⱼ."
        )
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
        self.result_view.set_matrix(
            result,
            split_col=None,
            clickable=self._op == "mul",
            show_headers=False,
        )
        self._show_properties(primary, other, None)

    def _compute_transpose(self) -> None:
        """Calcula Aᵀ, comprueba (Aᵀ)ᵀ = A y publica las propiedades estructurales."""
        primary = self.grid_transpose.get_matrix()
        result = matrix_transpose(primary)
        double_result = matrix_transpose(result)
        self.transpose_result_view.set_matrix(
            result, split_col=None, clickable=False, show_headers=False
        )
        self.double_transpose_result_view.set_matrix(
            double_result, split_col=None, clickable=False, show_headers=False
        )
        self._result = result
        self._details = []
        rows, cols = primary.shape
        self.inspector_label.setText(
            f"<b>Transpuesta doble:</b> (Aᵀ)ᵀ = A.<br/>"
            f"A es {rows}×{cols}, Aᵀ es {cols}×{rows}, y (Aᵀ)ᵀ vuelve a ser {rows}×{cols} exactamente igual a A."
        )
        self.inspector_label.setTextFormat(Qt.RichText)
        other = self._optional_partner()
        scalar = self._optional_identity_scalar()
        self._show_properties(primary, other, scalar)

    def _compute_distributive(self) -> None:
        """Comprueba identidades algebraicas con tres matrices A, B, C."""
        A = self.grid_dist_a.get_matrix()
        B = self.grid_dist_b.get_matrix()
        C = self.grid_dist_c.get_matrix()
        prop_id = self.dist_prop_group.checkedId()

        if prop_id == 0:  # A · (B + C) = A·B + A·C
            res = verify_matrix_distributive_left(A, B, C)
            self.dist_lhs_title_lbl.setText("LHS: A · (B + C)")
            self.dist_rhs_title_lbl.setText("RHS: A·B + A·C")
            self.dist_lhs_view.set_matrix(res.lhs_result, split_col=None, clickable=False, show_headers=False)
            self.dist_rhs_view.set_matrix(res.rhs_result, split_col=None, clickable=False, show_headers=False)
            self._result = res.lhs_result
            self._details = []
            dim_str = f"{res.lhs_result.shape[0]}×{res.lhs_result.shape[1]}"
            self.dist_comparison_label.setText(
                format_comparison_row_html(
                    mark="✓" if res.is_equal else "✗",
                    label="Distributiva izquierda",
                    lhs_expr="A · (B + C)",
                    rhs_expr="A·B + A·C",
                    ok=res.is_equal,
                    font_size_px=22,
                )
            )
            self.inspector_label.setText(
                f"<b>Comprobación distributiva por la izquierda:</b><br/>"
                f"LHS = A · (B + C): Matriz {dim_str}<br/>"
                f"RHS = (A · B) + (A · C): Matriz {dim_str}<br/>"
                f"¿Ambas matrices son idénticas elemento a elemento? <b>{'✓ SÍ, coinciden exactamente' if res.is_equal else '✗ No coinciden'}</b>"
            )
            self.inspector_label.setTextFormat(Qt.RichText)

        elif prop_id == 1:  # (A + B) · C = A·C + B·C
            res = verify_matrix_distributive_right(A, B, C)
            self.dist_lhs_title_lbl.setText("LHS: (A + B) · C")
            self.dist_rhs_title_lbl.setText("RHS: A·C + B·C")
            self.dist_lhs_view.set_matrix(res.lhs_result, split_col=None, clickable=False, show_headers=False)
            self.dist_rhs_view.set_matrix(res.rhs_result, split_col=None, clickable=False, show_headers=False)
            self._result = res.lhs_result
            self._details = []
            dim_str = f"{res.lhs_result.shape[0]}×{res.lhs_result.shape[1]}"
            self.dist_comparison_label.setText(
                format_comparison_row_html(
                    mark="✓" if res.is_equal else "✗",
                    label="Distributiva derecha",
                    lhs_expr="(A + B) · C",
                    rhs_expr="A·C + B·C",
                    ok=res.is_equal,
                    font_size_px=22,
                )
            )
            self.inspector_label.setText(
                f"<b>Comprobación distributiva por la derecha:</b><br/>"
                f"LHS = (A + B) · C: Matriz {dim_str}<br/>"
                f"RHS = (A · C) + (B · C): Matriz {dim_str}<br/>"
                f"¿Ambas matrices son idénticas elemento a elemento? <b>{'✓ SÍ, coinciden exactamente' if res.is_equal else '✗ No coinciden'}</b>"
            )
            self.inspector_label.setTextFormat(Qt.RichText)

        else:  # A · (B · C) = (A · B) · C
            res = verify_matrix_associative(A, B, C)
            self.dist_lhs_title_lbl.setText("LHS: A · (B · C)")
            self.dist_rhs_title_lbl.setText("RHS: (A · B) · C")
            self.dist_lhs_view.set_matrix(res.lhs_result, split_col=None, clickable=False, show_headers=False)
            self.dist_rhs_view.set_matrix(res.rhs_result, split_col=None, clickable=False, show_headers=False)
            self._result = res.lhs_result
            self._details = []
            dim_str = f"{res.lhs_result.shape[0]}×{res.lhs_result.shape[1]}"
            self.dist_comparison_label.setText(
                format_comparison_row_html(
                    mark="✓" if res.is_equal else "✗",
                    label="Asociativa",
                    lhs_expr="A · (B · C)",
                    rhs_expr="(A · B) · C",
                    ok=res.is_equal,
                    font_size_px=22,
                )
            )
            self.inspector_label.setText(
                f"<b>Comprobación asociativa:</b><br/>"
                f"LHS = A · (B · C): Matriz {dim_str}<br/>"
                f"RHS = (A · B) · C: Matriz {dim_str}<br/>"
                f"¿Ambas matrices son idénticas elemento a elemento? <b>{'✓ SÍ, coinciden exactamente' if res.is_equal else '✗ No coinciden'}</b>"
            )
            self.inspector_label.setTextFormat(Qt.RichText)

        checks = analyze_matrix(A, B, C=C)
        self.properties_label.setText(_checks_to_html(checks))

    def _optional_partner(self) -> Optional[Matrix]:
        """Devuelve B solo si el usuario pidió comprobar las identidades binarias."""
        if not self.include_b_btn.isChecked() or not self.grid_b.is_all_valid():
            return None
        return self.grid_b.get_matrix()

    def _optional_identity_scalar(self) -> Any:
        """Escalar k de la página de transpuesta, o None si el campo está vacío."""
        text = self.identity_scalar_edit.text().strip()
        if not text:
            return None
        return parse_scalar(text)

    def _show_properties(
        self,
        primary: Matrix,
        other: Optional[Matrix],
        scalar: Any,
    ) -> None:
        """Pinta las tarjetas de propiedades a partir del motor compartido."""
        checks = analyze_matrix(primary, other, scalar)
        self.properties_label.setText(_checks_to_html(checks))

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
        terms = []
        for k, (a_ik, b_kj, prod) in enumerate(detail.products):
            terms.append(
                f"A_{row + 1}{k + 1}·B_{k + 1}{col + 1} = "
                f"({format_scalar(a_ik)})·({format_scalar(b_kj)}) = {format_scalar(prod)}"
            )
        body = "\n".join(terms)
        self.inspector_label.setText(
            f"{detail.formula}\n\n{body}"
        )

    def _clear_highlights(self) -> None:
        self.grid_a.clear_highlight()
        self.grid_b.clear_highlight()

    def _clear_result(self) -> None:
        self._result = None
        self._details = []
        self.result_view.clear()
        self.scalar_result_view.clear()
        self.transpose_result_view.clear()
        if hasattr(self, "double_transpose_result_view"):
            self.double_transpose_result_view.clear()
        if hasattr(self, "dist_lhs_view"):
            self.dist_lhs_view.clear()
        if hasattr(self, "dist_rhs_view"):
            self.dist_rhs_view.clear()
        if hasattr(self, "dist_comparison_label"):
            self.dist_comparison_label.clear()
        self._clear_highlights()
        self.inspector_label.setText(
            "Calcula un producto A · B y pulsa una celda de C para ver la fila de A, "
            "la columna de B y la sumatoria de productos parciales."
        )
        self.properties_label.setText(
            "Calcula para ver qué tipo de matriz es, qué propiedades cumple "
            "y si se verifican las identidades de la transpuesta."
        )

    def load_compatible_product_sample(self) -> None:
        self.binary_mode_btn.setChecked(True)
        self.pages.setCurrentIndex(0)
        self.mul_btn.setChecked(True)
        self._op = "mul"
        self.grid_a.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
        self.grid_b.set_matrix(Matrix([[7, 8], [9, 10], [11, 12]]))
        self.compute()

    def load_incompatible_sample(self) -> None:
        self.binary_mode_btn.setChecked(True)
        self.pages.setCurrentIndex(0)
        self.mul_btn.setChecked(True)
        self._op = "mul"
        self.grid_a.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
        self.grid_b.set_matrix(Matrix([[1, 2], [3, 4]]))
        self._clear_result()
        self._refresh_compatibility()

    def load_distributive_matrix_sample(self) -> None:
        self.distrib_mode_btn.setChecked(True)
        self.pages.setCurrentIndex(3)
        self.dist_left_btn.setChecked(True)
        self.grid_dist_a.set_matrix(Matrix([[1, 2], [3, 4]]))
        self.grid_dist_b.set_matrix(Matrix([[5, 6], [7, 8]]))
        self.grid_dist_c.set_matrix(Matrix([[2, -1], [0, 3]]))
        self.compute()

