"""Vista de determinantes, cofactores y matriz adjunta.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Quinta pestaña de la shell: triangulación, Sarrus, Laplace y adjunta.
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
        QButtonGroup,
        QSplitter,
        QScrollArea,
        QSpinBox,
        QMessageBox,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QWidget = object  # type: ignore

from prettycalc.core.adjugate import AdjugateResult, calculate_adjugate_and_inverse
from prettycalc.core.determinants import (
    DeterminantMethod,
    DeterminantResult,
    matrix_determinant,
    singularity_diagnosis,
)
from prettycalc.core.matrix_inversion import NonSquareMatrixError
from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.module_scroll import make_module_scroll
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
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


def _badge_style(background: str, foreground: str) -> str:
    return (
        f"background-color: {background}; color: {foreground}; font-weight: 600; "
        f"font-size: 16px; padding: 10px 14px; border-radius: 6px; "
        f"font-family: {FONT_FAMILY_SANS};"
    )


def _matrix_inline(matrix: Matrix) -> str:
    rows = matrix.to_str_list(mode="fraction")
    return "  |  ".join("  ".join(row) for row in rows)


class DeterminantsView(QWidget):
    """Matriz cuadrada, selector de método y desglose de det(A), cofactores y adjunta."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("determinantsView")
        self._method = "triangulation"
        self.last_determinant: Optional[DeterminantResult] = None
        self.last_adjugate: Optional[AdjugateResult] = None
        self._setup_ui()
        self._sync_controls()

    def _setup_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        method_row = QHBoxLayout()
        method_row.setSpacing(8)
        self.method_group = QButtonGroup(self)
        self.method_group.setExclusive(True)
        self.triangulation_mode_btn = self._mode_button("Triangulación", 0, checked=True)
        self.sarrus_mode_btn = self._mode_button("Sarrus (3×3)", 1)
        self.laplace_mode_btn = self._mode_button("Cofactores de Laplace", 2)
        self.adjugate_mode_btn = self._mode_button("Matriz Adjunta", 3)
        self.method_group.idClicked.connect(self._on_method_changed)
        for button in (
            self.triangulation_mode_btn,
            self.sarrus_mode_btn,
            self.laplace_mode_btn,
            self.adjugate_mode_btn,
        ):
            method_row.addWidget(button)
        method_row.addStretch(1)
        root.addLayout(method_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        order_label = QLabel("Orden n")
        order_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )
        action_row.addWidget(order_label)
        self.order_down_btn = QPushButton("−")
        self.order_down_btn.setObjectName("secondaryAction")
        self.order_down_btn.setFixedWidth(36)
        self.order_down_btn.clicked.connect(lambda: self._resize_order(-1))
        self.order_value_label = QLabel("n = 2")
        self.order_value_label.setObjectName("determinantOrderLabel")
        self.order_value_label.setAlignment(Qt.AlignCenter)
        self.order_value_label.setMinimumWidth(72)
        self.order_value_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-family: {FONT_FAMILY_MONO}; "
            f"font-weight: 600;"
        )
        self.order_up_btn = QPushButton("+")
        self.order_up_btn.setObjectName("secondaryAction")
        self.order_up_btn.setFixedWidth(36)
        self.order_up_btn.clicked.connect(lambda: self._resize_order(1))
        action_row.addWidget(self.order_down_btn)
        action_row.addWidget(self.order_value_label)
        action_row.addWidget(self.order_up_btn)

        self.laplace_box = QWidget()
        laplace_row = QHBoxLayout(self.laplace_box)
        laplace_row.setContentsMargins(12, 0, 0, 0)
        laplace_row.setSpacing(6)
        axis_group = QButtonGroup(self)
        axis_group.setExclusive(True)
        self.laplace_row_btn = QPushButton("Fila")
        self.laplace_row_btn.setObjectName("laplaceRowButton")
        self.laplace_row_btn.setCheckable(True)
        self.laplace_row_btn.setChecked(True)
        self.laplace_col_btn = QPushButton("Columna")
        self.laplace_col_btn.setObjectName("laplaceColButton")
        self.laplace_col_btn.setCheckable(True)
        axis_group.addButton(self.laplace_row_btn)
        axis_group.addButton(self.laplace_col_btn)
        self.expansion_index = QSpinBox()
        self.expansion_index.setObjectName("expansionIndexSpin")
        self.expansion_index.setMinimum(1)
        self.expansion_index.setMaximum(MAX_DETERMINANT_ORDER)
        self.expansion_index.setValue(1)
        self.expansion_index.setPrefix("índice ")
        self.expansion_index.setStyleSheet(
            f"background: {COLOR_SURFACE_INNER}; color: {COLOR_TEXT_PRIMARY}; "
            f"border: 1px solid {COLOR_INTERACTIVE_IDLE}; padding: 4px 8px; font-size: 14px;"
        )
        laplace_row.addWidget(self.laplace_row_btn)
        laplace_row.addWidget(self.laplace_col_btn)
        laplace_row.addWidget(self.expansion_index)
        self.laplace_box.setVisible(False)
        action_row.addWidget(self.laplace_box)
        action_row.addStretch(1)

        sample_det = QPushButton("Ejemplo Sesión 11")
        sample_det.setObjectName("secondaryAction")
        sample_det.clicked.connect(self.load_session11_example)
        sample_sarrus = QPushButton("Ejemplo Sarrus")
        sample_sarrus.setObjectName("secondaryAction")
        sample_sarrus.clicked.connect(self.load_sarrus_example)
        self.compute_btn = QPushButton("Calcular")
        self.compute_btn.setObjectName("primaryAction")
        self.compute_btn.clicked.connect(self.compute)
        action_row.addWidget(sample_det)
        action_row.addWidget(sample_sarrus)
        action_row.addWidget(self.compute_btn)
        root.addLayout(action_row)

        self.badge = QLabel("")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        root.addWidget(self.badge)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setChildrenCollapsible(False)

        left_card = QFrame()
        apply_widget_class(left_card, "elevated-card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)
        grid_title = QLabel("Matriz A")
        grid_title.setStyleSheet(
            f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        left_layout.addWidget(grid_title)
        self.grid = DynamicMatrixGrid(
            initial_rows=2,
            initial_cols=2,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.grid.matrixChanged.connect(self._on_matrix_changed)
        left_layout.addWidget(self.grid, stretch=1)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setWidget(left_card)
        splitter.addWidget(left_scroll)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        steps_title = QLabel("Procedimiento")
        steps_title.setStyleSheet(
            f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        center_layout.addWidget(steps_title)
        self.stepper = AlgorithmStepperCarousel()
        center_layout.addWidget(self.stepper, stretch=1)
        splitter.addWidget(center)

        right_card = QFrame()
        apply_widget_class(right_card, "elevated-card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(10)
        result_title = QLabel("Resultado")
        result_title.setStyleSheet(
            f"font-size: 19px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        right_layout.addWidget(result_title)
        self.det_value_label = QLabel("det(A) = —")
        self.det_value_label.setObjectName("detValueLabel")
        self.det_value_label.setWordWrap(True)
        self.det_value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.det_value_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 28px; font-weight: 700; "
            f"font-family: {FONT_FAMILY_MONO};"
        )
        self.diagnosis_label = QLabel("")
        self.diagnosis_label.setObjectName("detDiagnosisLabel")
        self.diagnosis_label.setWordWrap(True)
        self.diagnosis_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;"
        )
        right_layout.addWidget(self.det_value_label)
        right_layout.addWidget(self.diagnosis_label)

        self.adjugate_section = QWidget()
        self.adjugate_section.setObjectName("adjugateSection")
        adjugate_layout = QVBoxLayout(self.adjugate_section)
        adjugate_layout.setContentsMargins(0, 8, 0, 0)
        adjugate_layout.setSpacing(8)
        self.minors_view, self.minors_readout = self._matrix_block(
            adjugate_layout, "Matriz de menores Mᵢⱼ", "minorsReadout"
        )
        self.cofactors_view, self.cofactors_readout = self._matrix_block(
            adjugate_layout, "Matriz de cofactores Cᵢⱼ", "cofactorReadout"
        )
        self.adjugate_view, self.adjugate_readout = self._matrix_block(
            adjugate_layout, "Matriz adjunta adj(A) = Cᵀ", "adjugateReadout"
        )
        self.inverse_view, self.inverse_readout = self._matrix_block(
            adjugate_layout, "Inversa por adjunta  A⁻¹ = (1/det A) · adj(A)", "inverseReadout"
        )
        self.adjugate_section.setVisible(False)
        right_layout.addWidget(self.adjugate_section)
        right_layout.addStretch(1)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setWidget(right_card)
        splitter.addWidget(right_scroll)
        splitter.setSizes([380, 520, 420])
        root.addWidget(splitter, stretch=1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    def _mode_button(self, text: str, method_id: int, checked: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("modeToggle")
        button.setCheckable(True)
        button.setChecked(checked)
        self.method_group.addButton(button, method_id)
        return button

    def _matrix_block(self, layout: QVBoxLayout, title: str, readout_name: str):
        caption = QLabel(title)
        caption.setWordWrap(True)
        caption.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 600; margin-top: 8px;"
        )
        layout.addWidget(caption)
        view = BookMatrixWidget()
        view.setMinimumHeight(180)
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

    def _on_method_changed(self, method_id: int) -> None:
        self._method = ("triangulation", "sarrus", "laplace", "adjugate")[method_id]
        self.laplace_box.setVisible(self._method == "laplace")
        self._clear_results()
        self._sync_controls()

    def _on_matrix_changed(self) -> None:
        self._clear_results()
        self._sync_controls()

    def _clear_results(self) -> None:
        self.last_determinant = None
        self.last_adjugate = None
        self.det_value_label.setText("det(A) = —")
        self.diagnosis_label.setText("")
        self.adjugate_section.setVisible(False)
        self.stepper.set_steps([])
        for view in (self.minors_view, self.cofactors_view, self.adjugate_view, self.inverse_view):
            view.clear()
        for readout in (
            self.minors_readout,
            self.cofactors_readout,
            self.adjugate_readout,
            self.inverse_readout,
        ):
            readout.setText("")

    def _blocking_reason(self) -> Optional[str]:
        if not self.grid.is_all_valid():
            return "Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales."
        matrix = self.grid.get_matrix()
        if matrix.rows != matrix.cols:
            return (
                "El determinante solo está definido para matrices cuadradas (n×n). "
                f"A es {matrix.rows}×{matrix.cols}."
            )
        if matrix.rows > MAX_DETERMINANT_ORDER:
            return f"El orden n debe estar entre 1 y {MAX_DETERMINANT_ORDER}."
        if self._method == "sarrus" and matrix.rows != 3:
            return "La regla de Sarrus solo está definida para matrices 3×3."
        return None

    def _sync_controls(self) -> None:
        matrix = self.grid.get_matrix() if self.grid.is_all_valid() else None
        if matrix is not None and matrix.rows == matrix.cols:
            order = matrix.rows
            self.order_value_label.setText(f"n = {order}")
            self.expansion_index.setMaximum(max(1, order))
            if self.expansion_index.value() > order:
                self.expansion_index.setValue(order)
            self.order_down_btn.setEnabled(order > 1)
            self.order_up_btn.setEnabled(order < MAX_DETERMINANT_ORDER)
        else:
            shape = self.grid.data_shape()
            self.order_value_label.setText(f"{shape[0]}×{shape[1]}")
            self.order_down_btn.setEnabled(True)
            self.order_up_btn.setEnabled(True)
        reason = self._blocking_reason()
        self.compute_btn.setEnabled(reason is None)
        if reason is not None:
            self.badge.setText(reason)
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
        elif self.last_determinant is None and self.last_adjugate is None:
            self.badge.setText("Matriz cuadrada lista para calcular.")
            self.badge.setStyleSheet(_badge_style(COLOR_SURFACE_INNER, COLOR_TEXT_MUTED))

    def _resize_order(self, delta: int) -> None:
        if not self.grid.is_all_valid():
            self._alert("Entrada inválida", "Corrige las celdas antes de cambiar el orden.")
            return
        current = self.grid.get_matrix()
        if current.rows == current.cols:
            new_order = min(MAX_DETERMINANT_ORDER, max(1, current.rows + delta))
        else:
            new_order = min(MAX_DETERMINANT_ORDER, max(1, min(current.rows, current.cols)))
        if new_order == current.rows and new_order == current.cols:
            return
        data = [
            [0 for _ in range(new_order)]
            for _ in range(new_order)
        ]
        for row_index in range(min(new_order, current.rows)):
            for col_index in range(min(new_order, current.cols)):
                data[row_index][col_index] = current.get(row_index, col_index)
        self.grid.set_matrix(Matrix(data))

    def _set_method(self, method: str) -> None:
        buttons = {
            "triangulation": self.triangulation_mode_btn,
            "sarrus": self.sarrus_mode_btn,
            "laplace": self.laplace_mode_btn,
            "adjugate": self.adjugate_mode_btn,
        }
        buttons[method].setChecked(True)
        self._method = method
        self.laplace_box.setVisible(method == "laplace")

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

    def compute(self) -> None:
        """Evalúa el método activo y publica el determinante o la adjunta."""
        reason = self._blocking_reason()
        if reason is not None:
            self.badge.setText(reason)
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
            self.compute_btn.setEnabled(False)
            return
        matrix = self.grid.get_matrix()
        try:
            if self._method == "adjugate":
                determinant = matrix_determinant(matrix, DeterminantMethod.TRIANGULATION)
                adjugate = calculate_adjugate_and_inverse(matrix)
            elif self._method == "sarrus":
                determinant = matrix_determinant(matrix, DeterminantMethod.SARRUS_3X3)
                adjugate = None
            elif self._method == "laplace":
                along_row = self.laplace_row_btn.isChecked()
                method = (
                    DeterminantMethod.LAPLACE_ROW
                    if along_row
                    else DeterminantMethod.LAPLACE_COL
                )
                determinant = matrix_determinant(
                    matrix,
                    method,
                    expansion_index=self.expansion_index.value() - 1,
                )
                adjugate = None
            else:
                determinant = matrix_determinant(matrix, DeterminantMethod.TRIANGULATION)
                adjugate = None
        except (NonSquareMatrixError, ValueError, IndexError) as exc:
            self._clear_results()
            self.badge.setText(str(exc))
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
            return

        self.last_determinant = determinant
        self.last_adjugate = adjugate
        self._publish(determinant, adjugate)

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
        self.stepper.set_steps(determinant.tracer.get_steps())
        if determinant.is_singular:
            self.badge.setText(f"det(A) = {shown}. Matriz singular.")
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
        else:
            self.badge.setText(f"det(A) = {shown}. Matriz no singular.")
            self.badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS, COLOR_BG_BASE))
        self.compute_btn.setEnabled(True)

        if adjugate is None:
            self.adjugate_section.setVisible(False)
            return
        self.adjugate_section.setVisible(True)
        self._show_matrix(self.minors_view, self.minors_readout, adjugate.minors_matrix)
        self._show_matrix(self.cofactors_view, self.cofactors_readout, adjugate.cofactors_matrix)
        self._show_matrix(self.adjugate_view, self.adjugate_readout, adjugate.adjugate_matrix)
        if adjugate.inverse_via_adjugate is None:
            self.inverse_view.clear()
            self.inverse_readout.setText("No existe A⁻¹ porque det(A) = 0.")
        else:
            self._show_matrix(
                self.inverse_view,
                self.inverse_readout,
                adjugate.inverse_via_adjugate,
            )

    @staticmethod
    def _show_matrix(view: BookMatrixWidget, readout: QLabel, matrix: Matrix) -> None:
        view.set_matrix(matrix, show_headers=False)
        readout.setText(_matrix_inline(matrix))

    def _alert(self, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.Ok)
        apply_message_box_theme(box)
        box.exec()
