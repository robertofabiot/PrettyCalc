"""Vista de ecuaciones matriciales A x = b con comprobación por producto."""

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
    )
    from PySide6.QtCore import Qt
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.classifier import SystemType
from prettycalc.core.matrix_equations import solve_matrix_equation
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.core.verifier import SolutionVerifier
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
    FONT_FAMILY_MONO,
    apply_message_box_theme,
    apply_widget_class,
)


class MatrixEquationsView(QWidget):
    """Entrada de A y b, resolución por filas y verificación de A · x = b."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("matrixEquationsView")
        self._setup_ui()
        self._refresh_formula()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.formula_lbl = QLabel("A · x = b")
        self.formula_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {COLOR_TEXT_PRIMARY}; "
            f"font-family: {FONT_FAMILY_MONO};"
        )
        header.addWidget(self.formula_lbl)
        header.addStretch(1)
        sample = QPushButton("Ejemplo 3×3")
        sample.clicked.connect(self.load_sample)
        header.addWidget(sample)
        root.addLayout(header)

        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setWordWrap(True)
        root.addWidget(self.badge)

        body = QHBoxLayout()
        body.setSpacing(10)

        self.grid_a = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
        self.grid_a.matrixChanged.connect(self._on_a_changed)
        body.addWidget(self._card("Matriz A", self.grid_a), stretch=3)

        dot = QLabel("·")
        dot.setStyleSheet(
            f"font-size: 32px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        body.addWidget(dot, 0, Qt.AlignCenter)

        x_card = QFrame()
        apply_widget_class(x_card, "elevated-card")
        x_layout = QVBoxLayout(x_card)
        self.x_title = QLabel("x  (incógnita)")
        self.x_title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        x_layout.addWidget(self.x_title)
        self.x_view = BookMatrixWidget()
        x_layout.addWidget(self.x_view, stretch=1)
        body.addWidget(x_card, stretch=1)

        eq = QLabel("=")
        eq.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 8px;"
        )
        body.addWidget(eq, 0, Qt.AlignCenter)

        self.vec_b = VectorColumnEditor(3, "Vector b")
        self.vec_b.changed.connect(self._refresh_formula)
        body.addWidget(self.vec_b, stretch=1)
        root.addLayout(body, stretch=2)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.solve_btn = QPushButton("Resolver ecuación matricial")
        self.solve_btn.setObjectName("primaryAction")
        self.solve_btn.clicked.connect(self.solve)
        actions.addWidget(self.solve_btn)
        root.addLayout(actions)

        bottom = QHBoxLayout()
        stepper_box = QVBoxLayout()
        steps_title = QLabel("Eliminación por filas de [A | b]")
        steps_title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        stepper_box.addWidget(steps_title)
        self.stepper = AlgorithmStepperCarousel()
        stepper_box.addWidget(self.stepper, stretch=1)
        bottom.addLayout(stepper_box, stretch=3)

        right = QVBoxLayout()
        self.dashboard = ResultsDashboardCard()
        right.addWidget(self.dashboard, stretch=1)
        self.product_card = QFrame()
        apply_widget_class(self.product_card, "elevated-card")
        prod_layout = QVBoxLayout(self.product_card)
        prod_title = QLabel("Comprobación  A · x = b")
        prod_title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        prod_layout.addWidget(prod_title)
        self.product_label = QLabel("Resuelve para verificar el producto matricial.")
        self.product_label.setWordWrap(True)
        self.product_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-family: {FONT_FAMILY_MONO};"
        )
        prod_layout.addWidget(self.product_label)
        right.addWidget(self.product_card)
        bottom.addLayout(right, stretch=2)
        root.addLayout(bottom, stretch=3)

    def _card(self, title: str, body: QWidget) -> QFrame:
        card = QFrame()
        apply_widget_class(card, "elevated-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
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
        self.formula_lbl.setText(
            f"A_{{{m}×{n}}}  ·  x_{{{n}×1}}  =  b_{{{b_dim}×1}}"
        )
        self.x_title.setText(f"x ∈ ℝ^{n}")
        ok = m == b_dim and self.grid_a.is_all_valid() and self.vec_b.is_valid()
        if not self.grid_a.is_all_valid() or not self.vec_b.is_valid():
            self.badge.setText("✕ Hay entradas no numéricas en A o en b.")
            self.badge.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_ERROR}; color: {COLOR_TEXT_PRIMARY}; "
                "font-weight: 600; padding: 10px 14px; border-radius: 6px;"
            )
            self.solve_btn.setEnabled(False)
            return
        if m != b_dim:
            self.badge.setText(
                f"✕ La ecuación no es conformable: A tiene {m} filas y b ∈ ℝ^{b_dim}. "
                "Se requiere dim(b) = filas de A."
            )
            self.badge.setStyleSheet(
                f"background-color: {COLOR_FEEDBACK_ERROR}; color: {COLOR_TEXT_PRIMARY}; "
                "font-weight: 600; padding: 10px 14px; border-radius: 6px;"
            )
            self.solve_btn.setEnabled(False)
            return
        self.badge.setText(
            f"✓ Ecuación conformable: A_{{{m}×{n}}} · x_{{{n}×1}} = b_{{{m}×1}}"
        )
        self.badge.setStyleSheet(
            f"background-color: {COLOR_FEEDBACK_SUCCESS}; color: {COLOR_BG_BASE}; "
            "font-weight: 600; padding: 10px 14px; border-radius: 6px;"
        )
        self.solve_btn.setEnabled(ok)

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
        else:
            self.x_view.clear()

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
        self.grid_a.set_matrix(Matrix([
            [1, 1, 1],
            [2, -1, 1],
            [1, 2, -1],
        ]))
        self.vec_b.set_vector(Vector([4, 4, 3]))
        self.solve()

    def _show_alert(self, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        apply_message_box_theme(box)
        box.exec()
