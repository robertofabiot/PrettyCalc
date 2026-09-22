"""Vista de ecuaciones matriciales A x = b con comprobación por producto y navegación fluida."""

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
        QMessageBox,
        QScrollArea,
        QSizePolicy,
        QTabWidget,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.classifier import SystemType
from prettycalc.core.matrix_equations import solve_matrix_equation
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.verifier import SolutionVerifier
from prettycalc.ui.mathtext import to_superscript
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.modules.vectors_view import VectorColumnEditor
from prettycalc.ui.results_dashboard import ResultsDashboardCard
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_BG_BASE,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
    apply_message_box_theme,
    apply_widget_class,
)


class MatrixEquationsView(QWidget):
    """Entrada de A y b, resolución por filas y verificación de A · x = b con scroll y pestañas."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixEquationsView")
        self._setup_ui()
        self._refresh_formula()

    def _setup_ui(self) -> None:
        # Layout principal del widget: contiene un QScrollArea que evita cualquier corte de pantalla
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.viewport().setAutoFillBackground(False)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(4, 4, 10, 16)
        root.setSpacing(14)

        # 1. Cabecera y Presets de prueba
        header_card = QFrame()
        apply_widget_class(header_card, "elevated-card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        main_title = QLabel("Ecuación Matricial  A · x = b")
        main_title.setStyleSheet(
            f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        self.formula_lbl = QLabel("A (3×3)  ·  x (3×1)  =  b (3×1)")
        self.formula_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 500; color: {COLOR_INTERACTIVE_IDLE}; "
            f"font-family: {FONT_FAMILY_MONO};"
        )
        title_col.addWidget(main_title)
        title_col.addWidget(self.formula_lbl)
        header_layout.addLayout(title_col, stretch=1)

        # Barra de ejemplos académicos y reinicio
        samples_row = QHBoxLayout()
        samples_row.setSpacing(8)

        sample_scd = QPushButton("Ejemplo SCD (3×3)")
        sample_scd.setToolTip("Cargar sistema con solución única: x = (2, 1, 1)")
        sample_scd.setCursor(Qt.PointingHandCursor)
        sample_scd.clicked.connect(self.load_sample)
        samples_row.addWidget(sample_scd)

        sample_sci = QPushButton("Ejemplo SCI (2×3)")
        sample_sci.setToolTip("Cargar sistema con infinitas soluciones y variables libres")
        sample_sci.setCursor(Qt.PointingHandCursor)
        sample_sci.clicked.connect(self.load_sample_sci)
        samples_row.addWidget(sample_sci)

        sample_si = QPushButton("Ejemplo SI (3×2)")
        sample_si.setToolTip("Cargar sistema incompatible sin solución")
        sample_si.setCursor(Qt.PointingHandCursor)
        sample_si.clicked.connect(self.load_sample_si)
        samples_row.addWidget(sample_si)

        reset_btn = QPushButton("Limpiar")
        reset_btn.setObjectName("secondaryAction")
        reset_btn.setToolTip("Restablecer matriz y vector a ceros")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.reset)
        samples_row.addWidget(reset_btn)

        self.header_solve_btn = QPushButton("▶  Resolver A · x = b")
        self.header_solve_btn.setObjectName("primaryAction")
        self.header_solve_btn.setToolTip("Resolver la ecuación matricial actual")
        self.header_solve_btn.setCursor(Qt.PointingHandCursor)
        self.header_solve_btn.clicked.connect(self.solve)
        samples_row.addWidget(self.header_solve_btn)

        header_layout.addLayout(samples_row)
        root.addWidget(header_card)

        # 2. Badge de conformabilidad dimensional
        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setWordWrap(True)
        root.addWidget(self.badge)

        # 3. Tarjeta de Planteamiento: A · x = b
        equation_card = QFrame()
        apply_widget_class(equation_card, "elevated-card")
        eq_card_layout = QVBoxLayout(equation_card)
        eq_card_layout.setContentsMargins(14, 12, 14, 14)
        eq_card_layout.setSpacing(12)

        eq_title = QLabel("Planteamiento de la Ecuación")
        eq_title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.02em;"
        )
        eq_card_layout.addWidget(eq_title)

        body = QHBoxLayout()
        body.setSpacing(10)

        # Matriz A
        self.grid_a = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
        self.grid_a.matrixChanged.connect(self._on_a_changed)
        body.addWidget(self._card("Matriz de Coeficientes  A", self.grid_a), stretch=4)

        # Operador ·
        dot = QLabel("·")
        dot.setAlignment(Qt.AlignCenter)
        dot.setStyleSheet(
            f"font-size: 34px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 4px;"
        )
        body.addWidget(dot, 0, Qt.AlignCenter)

        # Vector x (incógnita / solución)
        x_card = QFrame()
        x_card.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_SURFACE_INNER}; border-radius: 6px; padding: 6px; }}"
        )
        x_layout = QVBoxLayout(x_card)
        x_layout.setContentsMargins(8, 8, 8, 8)
        x_layout.setSpacing(4)
        self.x_title = QLabel("x ∈ ℝ³")
        self.x_title.setAlignment(Qt.AlignCenter)
        self.x_title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        self.x_subtitle = QLabel("Incógnita a resolver")
        self.x_subtitle.setAlignment(Qt.AlignCenter)
        self.x_subtitle.setStyleSheet(
            f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE}; font-style: italic;"
        )
        x_layout.addWidget(self.x_title)
        x_layout.addWidget(self.x_subtitle)

        self.x_view = BookMatrixWidget()
        self.x_view.setMinimumSize(90, 160)
        x_layout.addWidget(self.x_view, stretch=1)
        body.addWidget(x_card, stretch=2)

        # Operador =
        eq = QLabel("=")
        eq.setAlignment(Qt.AlignCenter)
        eq.setStyleSheet(
            f"font-size: 30px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 4px;"
        )
        body.addWidget(eq, 0, Qt.AlignCenter)

        # Vector b
        self.vec_b = VectorColumnEditor(3, "Vector Términos  b")
        self.vec_b.changed.connect(self._refresh_formula)
        body.addWidget(self.vec_b, stretch=2)
        eq_card_layout.addLayout(body)

        # Botón de resolución
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.solve_btn = QPushButton("Resolver ecuación matricial  A · x = b")
        self.solve_btn.setObjectName("primaryAction")
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        self.solve_btn.setMinimumHeight(44)
        self.solve_btn.clicked.connect(self.solve)
        actions.addWidget(self.solve_btn)
        actions.addStretch(1)
        eq_card_layout.addLayout(actions)

        root.addWidget(equation_card)

        # 4. Sección de Resultados y Procedimiento organizada con Pestañas
        self.results_tabs = QTabWidget()
        self.results_tabs.setMinimumHeight(440)

        # --- Pestaña 1: Comprobación y Resultados ---
        tab_results = QWidget()
        tab_results_layout = QHBoxLayout(tab_results)
        tab_results_layout.setContentsMargins(10, 12, 10, 12)
        tab_results_layout.setSpacing(14)

        # Panel izquierdo: Dashboard formal de clasificación
        self.dashboard = ResultsDashboardCard()
        self.dashboard.setMinimumWidth(340)
        tab_results_layout.addWidget(self.dashboard, stretch=3)

        # Panel derecho: Tarjeta de verificación del producto A · x = b
        self.product_card = QFrame()
        apply_widget_class(self.product_card, "elevated-card")
        prod_layout = QVBoxLayout(self.product_card)
        prod_layout.setContentsMargins(14, 14, 14, 14)
        prod_layout.setSpacing(10)

        prod_title = QLabel("Comprobación  A · x = b")
        prod_title.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        prod_layout.addWidget(prod_title)

        prod_desc = QLabel(
            "Multiplicación fila por vector para verificar la igualdad exacta componente a componente:"
        )
        prod_desc.setWordWrap(True)
        prod_desc.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MUTED};")
        prod_layout.addWidget(prod_desc)

        self.product_label = QLabel("Resuelve para verificar el producto matricial.")
        self.product_label.setWordWrap(True)
        self.product_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.product_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-family: {FONT_FAMILY_MONO}; "
            f"background-color: {COLOR_SURFACE_INNER}; border-radius: 6px; padding: 12px;"
        )
        prod_layout.addWidget(self.product_label)
        prod_layout.addStretch(1)
        tab_results_layout.addWidget(self.product_card, stretch=2)

        self.results_tabs.addTab(tab_results, "✓  Comprobación y Solución")

        # --- Pestaña 2: Procedimiento de Eliminación por Filas ---
        tab_stepper = QWidget()
        tab_stepper_layout = QVBoxLayout(tab_stepper)
        tab_stepper_layout.setContentsMargins(10, 12, 10, 12)
        tab_stepper_layout.setSpacing(10)

        steps_title = QLabel("Procedimiento de Gauss-Jordan sobre la Matriz Aumentada [A | b]")
        steps_title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        tab_stepper_layout.addWidget(steps_title)

        self.stepper = AlgorithmStepperCarousel()
        self.stepper.setMinimumHeight(340)
        tab_stepper_layout.addWidget(self.stepper, stretch=1)

        self.results_tabs.addTab(tab_stepper, "📋  Procedimiento Paso a Paso [A | b]")

        root.addWidget(self.results_tabs)

        self.scroll_area.setWidget(content)
        main_layout.addWidget(self.scroll_area)

    def _card(self, title: str, body: QWidget) -> QFrame:
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(body)
        layout.addWidget(scroll, stretch=1)
        return card

    def _on_a_changed(self) -> None:
        rows, _cols = self.grid_a.data_shape()
        if self.vec_b.grid.num_rows != rows:
            self.vec_b.set_dimension(rows)
        self._refresh_formula()

    def _refresh_formula(self) -> None:
        m, n = self.grid_a.data_shape()
        b_dim = self.vec_b.grid.num_rows
        self.formula_lbl.setText(f"A ({m}×{n})  ·  x ({n}×1)  =  b ({b_dim}×1)")
        self.x_title.setText(f"x ∈ ℝ{to_superscript(n)}")
        ok = m == b_dim and self.grid_a.is_all_valid() and self.vec_b.is_valid()
        if not self.grid_a.is_all_valid() or not self.vec_b.is_valid():
            self.badge.setText("✕ Hay entradas no numéricas en A o en b.")
            self.badge.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_ERROR}; color: {COLOR_TEXT_PRIMARY}; "
                "font-weight: 600; padding: 10px 14px; border-radius: 6px;"
            )
            self.solve_btn.setEnabled(False)
            if hasattr(self, "header_solve_btn"):
                self.header_solve_btn.setEnabled(False)
            return
        if m != b_dim:
            self.badge.setText(
                f"✕ La ecuación no es conformable: A tiene {m} filas y b ∈ ℝ{to_superscript(b_dim)}. "
                "Se requiere dim(b) = filas de A."
            )
            self.badge.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_ERROR}; color: {COLOR_TEXT_PRIMARY}; "
                "font-weight: 600; padding: 10px 14px; border-radius: 6px;"
            )
            self.solve_btn.setEnabled(False)
            if hasattr(self, "header_solve_btn"):
                self.header_solve_btn.setEnabled(False)
            return
        self.badge.setText(
            f"✓ Ecuación conformable: A ({m}×{n}) · x ({n}×1) = b ({m}×1)"
        )
        self.badge.setStyleSheet(
            f"background-color: {COLOR_FEEDBACK_SUCCESS}; color: {COLOR_BG_BASE}; "
            "font-weight: 600; padding: 10px 14px; border-radius: 6px;"
        )
        self.solve_btn.setEnabled(ok)
        if hasattr(self, "header_solve_btn"):
            self.header_solve_btn.setEnabled(ok)

    def solve(self) -> None:
        if not self.grid_a.is_all_valid() or not self.vec_b.is_valid():
            self._show_alert("Entrada inválida", "Corrige las celdas no numéricas.")
            return
        try:
            a = self.grid_a.get_matrix()
            b = self.vec_b.get_vector()
            result = solve_matrix_equation(a, b)
        except DimensionMismatchError as exc:
            self.badge.setText(f"✕ {exc}")
            self.solve_btn.setEnabled(False)
            return
        except Exception as exc:
            self._show_alert("Error matemático", str(exc))
            return

        self.stepper.set_steps(result.tracer.get_steps())
        verifications = None
        if result.solution is not None:
            verifications = SolutionVerifier.verify(
                result.augmented_matrix,
                result.solution.to_list(),
                split_col=a.cols,
            )
            self.x_view.set_matrix(
                result.solution.to_column_matrix(),
                split_col=None,
                show_headers=False,
            )
            self.x_subtitle.setText(f"Solución x ({result.solution.dimension}×1)")
        else:
            self.x_view.clear()
            self.x_subtitle.setText("Sin solución")

        self.dashboard.display_results(result.analysis, verifications)

        if result.product_Ax is not None and result.solution is not None:
            lines = ["A · x  ≟  b", ""]
            all_ok = result.product_matches
            for label, got, expected, ok in result.verification_checklist:
                mark = "✓" if ok else "✗"
                lines.append(
                    f"{mark}  {label}:  (A x) = {format_scalar(got)}  |  b = {format_scalar(expected)}"
                )
            if result.analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
                lines.append("")
                lines.append(f"Solución general: {result.parametric_solution}")
            status = "igualdad exacta" if all_ok else "no coincide"
            lines.insert(1, f"Resultado: {status}.")
            self.product_label.setText("\n".join(lines))
        else:
            self.product_label.setText(
                "No hay vector x que satisfaga A x = b (sistema inconsistente)."
            )

    def load_sample(self) -> None:
        """Caso SCD canónico (3×3 con solución única)."""
        self.grid_a.set_matrix(Matrix([
            [1, 1, 1],
            [2, -1, 1],
            [1, 2, -1],
        ]))
        self.vec_b.set_vector(Vector([4, 4, 3]))
        self.solve()

    def load_sample_sci(self) -> None:
        """Caso SCI (infinitas soluciones y variable libre)."""
        self.grid_a.set_matrix(Matrix([
            [1, 2, -1],
            [2, 4, -2],
        ]))
        self.vec_b.set_vector(Vector([4, 8]))
        self.solve()

    def load_sample_si(self) -> None:
        """Caso SI (sistema incompatible sin solución)."""
        self.grid_a.set_matrix(Matrix([
            [1, 1],
            [1, 1],
            [2, -1],
        ]))
        self.vec_b.set_vector(Vector([2, 5, 1]))
        self.solve()

    def reset(self) -> None:
        """Restablece la matriz y el vector al estado inicial."""
        self.grid_a.set_matrix(Matrix.zeros(3, 3))
        self.vec_b.set_vector(Vector([0, 0, 0]))
        self.x_view.clear()
        self.x_subtitle.setText("Incógnita a resolver")
        self.stepper.set_steps([])
        self.dashboard.clear()
        self.product_label.setText("Resuelve para verificar el producto matricial.")
        self.results_tabs.setCurrentIndex(0)
        self._refresh_formula()

    def _show_alert(self, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        apply_message_box_theme(box)
        box.exec()
