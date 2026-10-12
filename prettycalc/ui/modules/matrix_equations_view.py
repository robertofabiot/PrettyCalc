"""Módulo 4: ecuación matricial A · x = b con comprobación del producto.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).

Sprint 10 (auditoría UI/UX, Módulo 4, flujo 1):

- Un único botón «Resolver» (Ctrl+Enter desde cualquier celda) y control
  directo m × n de A con atajo «Hacer cuadrada».
- Errores explicados en línea con fila y columna (sin diálogos modales).
- En un SCI el visor de x lleva la insignia «Solución particular (variables
  libres = 0)» y resalta las componentes libres; en un SI se nombra la fila
  contradictoria con su valor.
- Al editar después de resolver, el resultado se marca como desactualizado.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.classifier import SystemType
from prettycalc.core.matrix_equations import solve_matrix_equation
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.verifier import SolutionVerifier
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.mathtext import format_comparison_row_html, prettify_math_text, to_subscript, to_superscript
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.modules.matrix_vector_properties_view import MatrixVectorPropertiesView
from prettycalc.ui.results_dashboard import ResultsDashboardCard
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.stepper_carousel import ALERT_SYSTEM, AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_widget_class,
    badge_style,
)
from prettycalc.ui.vector_set_editor import VectorColumnEditor

_IDLE_PRODUCT_TEXT = "Resuelve para verificar el producto matricial."


class MatrixEquationsView(QWidget):
    """Entrada de A y b, resolución por filas y verificación de A · x = b."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixEquationsView")
        self._has_result = False
        self._setup_ui()
        self._refresh_formula()

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
        root.setContentsMargins(4, 4, 10, 16)
        root.setSpacing(12)

        # 1. Cabecera: título, ejemplos y la única acción primaria
        header_card = QFrame()
        apply_widget_class(header_card, "elevated-card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        main_title = QLabel("Ecuación matricial  A · x = b")
        main_title.setStyleSheet(f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.formula_lbl = QLabel("A (3×3)  ·  x (3×1)  =  b (3×1)")
        self.formula_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 500; color: {COLOR_INTERACTIVE_IDLE}; "
            f"font-family: {FONT_FAMILY_MONO};"
        )
        title_col.addWidget(main_title)
        title_col.addWidget(self.formula_lbl)
        header_layout.addLayout(title_col, stretch=1)

        samples_row = QHBoxLayout()
        samples_row.setSpacing(8)
        for text, tip, slot in (
            ("Ejemplo SCD (3×3)", "Sistema con solución única: x = (2, 1, 1)", self.load_sample),
            ("Ejemplo SCI (2×3)", "Infinitas soluciones con variables libres", self.load_sample_sci),
            ("Ejemplo SI (3×2)", "Sistema incompatible, sin solución", self.load_sample_si),
        ):
            button = QPushButton(text)
            button.setObjectName("secondaryAction")
            button.setToolTip(tip)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(slot)
            samples_row.addWidget(button)

        self.reset_btn = QPushButton("Limpiar")
        self.reset_btn.setObjectName("secondaryAction")
        self.reset_btn.setToolTip("Restablece A y b a ceros (se puede deshacer)")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset)
        samples_row.addWidget(self.reset_btn)

        self.solve_btn = QPushButton("▶  Resolver A · x = b")
        self.solve_btn.setObjectName("primaryAction")
        self.solve_btn.setToolTip("Resolver la ecuación (Ctrl+Enter desde cualquier celda)")
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        self.solve_btn.clicked.connect(self.solve)
        samples_row.addWidget(self.solve_btn)
        self.header_solve_btn = self.solve_btn
        header_layout.addLayout(samples_row)
        root.addWidget(header_card)

        # 2. Badge de conformabilidad y validación
        badge_row = QHBoxLayout()
        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setWordWrap(True)
        badge_row.addWidget(self.badge, 1)
        self.fix_b_btn = QPushButton("")
        apply_widget_class(self.fix_b_btn, "link-action")
        self.fix_b_btn.setCursor(Qt.PointingHandCursor)
        self.fix_b_btn.clicked.connect(self.match_b_to_rows)
        self.fix_b_btn.setVisible(False)
        badge_row.addWidget(self.fix_b_btn)
        root.addLayout(badge_row)

        # 3. Planteamiento  [A] · [x] = [b]
        equation_card = QFrame()
        apply_widget_class(equation_card, "elevated-card")
        eq_card_layout = QVBoxLayout(equation_card)
        eq_card_layout.setContentsMargins(14, 12, 14, 14)
        eq_card_layout.setSpacing(10)

        eq_title = QLabel("Planteamiento de la ecuación")
        eq_title.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        eq_card_layout.addWidget(eq_title)

        body = QHBoxLayout()
        body.setSpacing(10)

        self.grid_a = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
        self.grid_a.matrixChanged.connect(self._on_a_changed)
        self.grid_a.submitRequested.connect(self.solve)
        a_card = QFrame()
        apply_widget_class(a_card, "elevated-card")
        a_layout = QVBoxLayout(a_card)
        a_layout.setContentsMargins(12, 10, 12, 10)
        a_layout.setSpacing(6)
        a_title = QLabel("Matriz de coeficientes  A")
        a_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        a_layout.addWidget(a_title)
        size_row = QHBoxLayout()
        self.size_control = MatrixSizeControl(
            self.grid_a,
            rows_label="Ecuaciones m",
            cols_label="Incógnitas n",
            caption="Ecuaciones × incógnitas",
            minimum=1,
            maximum=8,
        )
        size_row.addWidget(self.size_control)
        self.make_square_btn = QPushButton("Hacer cuadrada")
        apply_widget_class(self.make_square_btn, "link-action")
        self.make_square_btn.setCursor(Qt.PointingHandCursor)
        self.make_square_btn.setToolTip("Iguala el número de ecuaciones al de incógnitas (se puede deshacer)")
        self.make_square_btn.clicked.connect(self.make_square)
        size_row.addWidget(self.make_square_btn)
        size_row.addStretch(1)
        a_layout.addLayout(size_row)
        self.grid_a.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        a_layout.addWidget(self.grid_a, stretch=1)
        body.addWidget(a_card, stretch=4)

        body.addWidget(self._operator("·", 40), 0, Qt.AlignCenter)

        x_card = QFrame()
        x_card.setObjectName("xCard")
        x_card.setStyleSheet(
            f"QFrame#xCard {{ background-color: {COLOR_SURFACE_INNER}; border-radius: 6px; }}"
        )
        x_layout = QVBoxLayout(x_card)
        x_layout.setContentsMargins(10, 10, 10, 10)
        x_layout.setSpacing(4)
        self.x_title = QLabel("x ∈ ℝ³")
        self.x_title.setAlignment(Qt.AlignCenter)
        self.x_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.x_subtitle = QLabel("Incógnita a resolver")
        self.x_subtitle.setAlignment(Qt.AlignCenter)
        self.x_subtitle.setWordWrap(True)
        self.x_subtitle.setStyleSheet(f"font-size: 13px; color: {COLOR_INTERACTIVE_IDLE}; font-style: italic;")
        self.x_badge = QLabel("Solución particular (variables libres = 0)")
        self.x_badge.setObjectName("xParticularBadge")
        self.x_badge.setAlignment(Qt.AlignCenter)
        self.x_badge.setWordWrap(True)
        self.x_badge.setStyleSheet(badge_style(COLOR_ACCENT_WARNING, font_size=12, padding="4px 8px"))
        self.x_badge.setVisible(False)
        x_layout.addWidget(self.x_title)
        x_layout.addWidget(self.x_subtitle)
        x_layout.addWidget(self.x_badge)
        self.x_view = BookMatrixWidget()
        self.x_view.setMinimumSize(90, 160)
        self.x_view.set_empty_text("x = ?")
        x_layout.addWidget(self.x_view, stretch=1)
        body.addWidget(x_card, stretch=2)

        body.addWidget(self._operator("=", 30), 0, Qt.AlignCenter)

        self.vec_b = VectorColumnEditor(3, "Vector de términos  b")
        self.vec_b.changed.connect(self._on_inputs_changed)
        self.vec_b.submitRequested.connect(self.solve)
        body.addWidget(self.vec_b, stretch=2)
        eq_card_layout.addLayout(body)
        root.addWidget(equation_card)

        # 4. Resultados y procedimiento
        self.results_tabs = QTabWidget()
        self.results_tabs.setMinimumHeight(440)

        tab_results = QWidget()
        tab_results_layout = QHBoxLayout(tab_results)
        tab_results_layout.setContentsMargins(10, 12, 10, 12)
        tab_results_layout.setSpacing(14)

        self.dashboard = ResultsDashboardCard()
        self.dashboard.setMinimumWidth(320)
        tab_results_layout.addWidget(self.dashboard, stretch=1)

        self.product_card = QFrame()
        apply_widget_class(self.product_card, "elevated-card")
        prod_layout = QVBoxLayout(self.product_card)
        prod_layout.setContentsMargins(14, 14, 14, 14)
        prod_layout.setSpacing(10)
        prod_title = QLabel("Comprobación  A · x = b")
        prod_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        prod_layout.addWidget(prod_title)
        prod_desc = QLabel("Cada fila de A por x debe dar exactamente la componente de b:")
        prod_desc.setWordWrap(True)
        prod_desc.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MUTED};")
        prod_layout.addWidget(prod_desc)
        self.product_label = QLabel(_IDLE_PRODUCT_TEXT)
        self.product_label.setWordWrap(True)
        self.product_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.product_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 600; "
            f"font-family: {FONT_FAMILY_MONO}; "
            f"background-color: {COLOR_SURFACE_INNER}; border-radius: 6px; padding: 12px;"
        )
        prod_layout.addWidget(self.product_label)
        prod_layout.addStretch(1)
        tab_results_layout.addWidget(self.product_card, stretch=1)
        self.results_tabs.addTab(tab_results, "Comprobación y solución")

        tab_stepper = QWidget()
        tab_stepper_layout = QVBoxLayout(tab_stepper)
        tab_stepper_layout.setContentsMargins(10, 12, 10, 12)
        tab_stepper_layout.setSpacing(10)
        steps_title = QLabel("Gauss-Jordan sobre la matriz aumentada [A | b]")
        steps_title.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        tab_stepper_layout.addWidget(steps_title)
        self.stepper = AlgorithmStepperCarousel(alert_mode=ALERT_SYSTEM)
        self.stepper.setMinimumHeight(340)
        self.stepper.set_export_title("Ecuación matricial A · x = b")
        self.stepper.set_empty_hint("Ingresa A y b y pulsa Resolver.")
        tab_stepper_layout.addWidget(self.stepper, stretch=1)
        self.results_tabs.addTab(tab_stepper, "Procedimiento paso a paso [A | b]")

        root.addWidget(self.results_tabs)
        self.scroll_area.setWidget(content)
        content.setAutoFillBackground(False)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.scroll_area, "Ecuación  A · x = b")
        self.properties_view = MatrixVectorPropertiesView()
        self.tabs.addTab(self.properties_view, "Propiedades del producto  A · x")
        self.main_tabs = self.tabs
        main_layout.addWidget(self.tabs)

    @staticmethod
    def _operator(symbol: str, size: int) -> QLabel:
        label = QLabel(symbol)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"font-size: {size}px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 4px;")
        return label

    # ------------------------------------------------------------------ estado
    def _on_a_changed(self) -> None:
        rows, _cols = self.grid_a.data_shape()
        if self.vec_b.grid.num_rows != rows:
            self.vec_b.set_dimension(rows)
        self._on_inputs_changed()

    def _on_inputs_changed(self, *_args) -> None:
        self._refresh_formula()
        self._mark_stale()

    def _mark_stale(self) -> None:
        if not self._has_result:
            return
        self._has_result = False
        self.x_view.clear()
        self.x_badge.setVisible(False)
        self.x_subtitle.setText("Datos modificados: vuelve a resolver")
        self.stepper.set_steps([])
        self.dashboard.clear()
        self.product_label.setTextFormat(Qt.PlainText)
        self.product_label.setText(_IDLE_PRODUCT_TEXT)

    def _input_problem(self) -> str:
        message = self.grid_a.validation_message()
        if message:
            return f"A, {message[0].lower()}{message[1:]}"
        return self.vec_b.validation_message()

    def _set_badge(self, text: str, ok: bool) -> None:
        self.badge.setText(text)
        self.badge.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR))

    def _refresh_formula(self) -> None:
        m, n = self.grid_a.data_shape()
        b_dim = self.vec_b.grid.num_rows
        self.formula_lbl.setText(f"A ({m}×{n})  ·  x ({n}×1)  =  b ({b_dim}×1)")
        self.x_title.setText(f"x ∈ ℝ{to_superscript(n)}")
        self.make_square_btn.setVisible(m != n)
        self.make_square_btn.setText(f"Hacer cuadrada {n}×{n}")
        self.fix_b_btn.setVisible(False)
        problem = self._input_problem()
        if problem:
            self._set_badge(f"✕ {problem}", False)
            self.solve_btn.setEnabled(False)
            return
        if m != b_dim:
            self._set_badge(
                f"✕ La ecuación no es conformable: A tiene {m} filas y b ∈ ℝ{to_superscript(b_dim)}. "
                "Se requiere dim(b) = filas de A.",
                False,
            )
            self.fix_b_btn.setText(f"Ajustar b a {m} componentes")
            self.fix_b_btn.setVisible(True)
            self.solve_btn.setEnabled(False)
            return
        shape = "cuadrado" if m == n else ("con más incógnitas que ecuaciones" if n > m else "con más ecuaciones que incógnitas")
        self._set_badge(f"✓ Ecuación conformable: A ({m}×{n}) · x ({n}×1) = b ({m}×1) · sistema {shape}", True)
        self.solve_btn.setEnabled(True)

    def match_b_to_rows(self) -> None:
        rows, _ = self.grid_a.data_shape()
        self.vec_b.set_dimension(rows)
        self._on_inputs_changed()

    def make_square(self) -> None:
        """Iguala m a n conservando las entradas que caben (se puede deshacer)."""
        _m, n = self.grid_a.data_shape()
        self.grid_a.resize_to(n, n)
        show_toast(
            self,
            f"A ahora es {n}×{n}. Completa las ecuaciones nuevas.",
            action_text="Deshacer",
            action=self.grid_a.undo,
        )

    # ------------------------------------------------------------- resolución
    def solve(self) -> None:
        if not self.solve_btn.isEnabled():
            if not self.grid_a.focus_first_invalid():
                self.vec_b.focus_first_invalid()
            return
        try:
            a = self.grid_a.get_matrix()
            b = self.vec_b.get_vector()
            result = solve_matrix_equation(a, b)
        except DimensionMismatchError as exc:
            self._set_badge(f"✕ {exc}", False)
            self.solve_btn.setEnabled(False)
            return

        self._has_result = True
        self.stepper.set_steps(result.tracer.get_steps())
        analysis = result.analysis
        verifications = None
        if result.solution is not None:
            verifications = SolutionVerifier.verify(
                result.augmented_matrix,
                result.solution.to_list(),
                split_col=a.cols,
            )
            free = list(analysis.free_variables or [])
            self.x_view.set_matrix(
                result.solution.to_column_matrix(),
                split_col=None,
                show_headers=False,
                highlight_cells=tuple((index, 0) for index in free),
            )
            if analysis.system_type == SystemType.CONSISTENT_INDETERMINED and free:
                names = ", ".join(f"x{to_subscript(index + 1)}" for index in free)
                self.x_subtitle.setText(f"Una de infinitas soluciones ({result.solution.dimension}×1)")
                self.x_badge.setText(f"Solución particular (variables libres = 0: {names})")
                self.x_badge.setToolTip(
                    f"Solución general: {prettify_math_text(result.parametric_solution)}"
                    if result.parametric_solution
                    else ""
                )
                self.x_badge.setVisible(True)
            else:
                self.x_subtitle.setText(f"Solución única x ({result.solution.dimension}×1)")
                self.x_badge.setVisible(False)
        else:
            self.x_view.clear()
            self.x_view.set_empty_text("Sin solución")
            self.x_subtitle.setText("Sin solución")
            self.x_badge.setVisible(False)

        self.dashboard.display_results(analysis, verifications)

        if result.product_Ax is not None and result.solution is not None:
            all_ok = result.product_matches
            status_color = COLOR_FEEDBACK_SUCCESS if all_ok else COLOR_FEEDBACK_ERROR
            status_text = (
                "✓ ¡Igualdad exacta comprobada!  A · x = b (igualdad exacta)" if all_ok else "✕ No coincide la igualdad"
            )
            rows = [
                f'<div style="background-color:rgba(129, 178, 154, 0.12); border:1px solid rgba(129, 178, 154, 0.40); '
                f'border-radius:6px; padding:10px 14px; margin-bottom:12px;">'
                f'<span style="font-size:22px; font-weight:700; color:{status_color};">{status_text}</span>'
                f"</div>"
            ]
            for label, got, expected, ok in result.verification_checklist:
                comp_idx = label.split()[-1] if " " in label else label
                rows.append(
                    format_comparison_row_html(
                        "✓" if ok else "✗",
                        label,
                        f"(A·x)_{comp_idx} = {format_scalar(got)}",
                        f"b_{comp_idx} = {format_scalar(expected)}",
                        ok,
                        font_size_px=22,
                    )
                )
            if analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
                rows.append(
                    f'<div style="font-size:18px; font-weight:600; color:{COLOR_TEXT_PRIMARY}; '
                    f'padding:10px 0; font-family:{FONT_FAMILY_MONO};">'
                    f"Solución general: {prettify_math_text(result.parametric_solution or '')}</div>"
                    f'<div style="font-size:15px; color:{COLOR_TEXT_MUTED};">'
                    "El x mostrado arriba es el caso particular con las variables libres en 0.</div>"
                )
            self.product_label.setTextFormat(Qt.RichText)
            self.product_label.setText("".join(rows))
        else:
            text = "No hay vector x que satisfaga A x = b (sistema inconsistente)."
            if analysis.inconsistent_row is not None and analysis.inconsistent_value is not None:
                value = format_scalar(analysis.inconsistent_value)
                text += (
                    f"\n\nLa fila {analysis.inconsistent_row + 1} de la forma escalonada queda "
                    f"[0 … 0 | {value}]: 0 = {value}, imposible."
                )
            self.product_label.setTextFormat(Qt.PlainText)
            self.product_label.setText(text)

        self.scroll_area.ensureWidgetVisible(self.results_tabs)

    # --------------------------------------------------------------- ejemplos
    def _load(self, a: Matrix, b: Vector) -> None:
        self.grid_a.set_matrix(a)
        self.vec_b.set_vector(b)
        self.solve()

    def load_sample(self) -> None:
        """Caso SCD canónico (3×3 con solución única)."""
        self._load(Matrix([[1, 1, 1], [2, -1, 1], [1, 2, -1]]), Vector([4, 4, 3]))

    def load_sample_sci(self) -> None:
        """Caso SCI (infinitas soluciones y variables libres)."""
        self._load(Matrix([[1, 2, -1], [2, 4, -2]]), Vector([4, 8]))

    def load_sample_si(self) -> None:
        """Caso SI (sistema incompatible sin solución)."""
        self._load(Matrix([[1, 1], [1, 1], [2, -1]]), Vector([2, 5, 1]))

    def reset(self) -> None:
        """Restablece A y b a ceros 3×3; un aviso permite deshacerlo."""
        before_a = self.grid_a.snapshot()
        before_b = self.vec_b.raw_values()
        self.grid_a.set_matrix(Matrix.zeros(3, 3))
        self.vec_b.set_vector(Vector([0, 0, 0]))
        self._has_result = True
        self._mark_stale()
        self.x_subtitle.setText("Incógnita a resolver")
        self.x_view.set_empty_text("x = ?")
        self.results_tabs.setCurrentIndex(0)
        self._refresh_formula()

        def undo() -> None:
            self.grid_a.undo()
            self.vec_b.set_raw_values(before_b)

        if before_a != self.grid_a.snapshot() or any(value not in ("0", "") for value in before_b):
            show_toast(self, "A y b se restablecieron a ceros.", action_text="Deshacer", action=undo)
