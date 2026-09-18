"""Vista de vectores en ℝⁿ: operaciones básicas y evaluador de combinación lineal."""

from __future__ import annotations

from typing import List, Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
        QSpinBox,
        QTabWidget,
        QScrollArea,
        QButtonGroup,
        QLineEdit,
        QMessageBox,
        QStackedWidget,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.classifier import SystemType
from prettycalc.core.linear_combination import evaluate_linear_combination, format_combination_equation
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar, parse_scalar
from prettycalc.core.vector_ops import vector_add, vector_scale, vector_sub
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_BG_BASE,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_message_box_theme,
    apply_widget_class,
)


def _badge_style(bg: str, fg: str) -> str:
    return (
        f"background-color: {bg}; color: {fg}; font-weight: 600; font-size: 16px; "
        f"padding: 12px 14px; border-radius: 6px;"
    )


class VectorColumnEditor(QFrame):
    """Editor de un vector columna con título y eliminación opcional."""

    removed = Signal()
    changed = Signal()

    def __init__(
        self,
        dimension: int,
        title: str,
        removable: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self._title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        header.addWidget(self.title_lbl)
        header.addStretch(1)
        if removable:
            delete_btn = QPushButton("Eliminar")
            delete_btn.setObjectName("secondaryAction")
            delete_btn.clicked.connect(self.removed.emit)
            header.addWidget(delete_btn)
        layout.addLayout(header)

        self.grid = DynamicMatrixGrid(
            initial_rows=dimension,
            initial_cols=1,
            augmented=False,
            show_headers=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.grid.matrixChanged.connect(self.changed.emit)
        layout.addWidget(self.grid)

    def set_title(self, title: str) -> None:
        self._title = title
        self.title_lbl.setText(title)

    def set_dimension(self, n: int) -> None:
        current = [row[0] if row else "0" for row in self.grid.get_raw_strings()]
        while len(current) < n:
            current.append("0")
        data = [[val] for val in current[:n]]
        self.grid.set_matrix(Matrix(data))

    def get_vector(self) -> Vector:
        return Vector.from_column_matrix(self.grid.get_matrix())

    def set_vector(self, vector: Vector) -> None:
        self.grid.set_matrix(vector.to_column_matrix())

    def is_valid(self) -> bool:
        return self.grid.is_all_valid()


class VectorsView(QWidget):
    """Subpestañas: operaciones u ± v / k·v y combinación lineal Σ cᵢ vᵢ = b."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("vectorsView")
        self._combo_editors: List[VectorColumnEditor] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        tabs.addTab(self._build_basic_tab(), "Operaciones básicas")
        tabs.addTab(self._build_combination_tab(), "Combinación lineal")
        root.addWidget(tabs)

    def _build_basic_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        controls = QHBoxLayout()
        dim_lbl = QLabel("Dimensión n")
        dim_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;")
        self.basic_dim = QSpinBox()
        self.basic_dim.setRange(2, 10)
        self.basic_dim.setValue(3)
        self.basic_dim.valueChanged.connect(self._on_basic_dimension)
        controls.addWidget(dim_lbl)
        controls.addWidget(self.basic_dim)

        self.basic_op_group = QButtonGroup(self)
        self.basic_op_group.setExclusive(True)
        self.basic_add_btn = QPushButton("u + v")
        self.basic_sub_btn = QPushButton("u − v")
        self.basic_scale_btn = QPushButton("k · v")
        for i, btn in enumerate((self.basic_add_btn, self.basic_sub_btn, self.basic_scale_btn)):
            btn.setCheckable(True)
            btn.setObjectName("modeToggle")
            self.basic_op_group.addButton(btn, i)
            controls.addWidget(btn)
        self.basic_add_btn.setChecked(True)
        self.basic_op_group.idClicked.connect(self._on_basic_op)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.basic_badge = QLabel("")
        self.basic_badge.setAlignment(Qt.AlignCenter)
        self.basic_badge.setWordWrap(True)
        layout.addWidget(self.basic_badge)

        body = QHBoxLayout()
        self.vec_u = VectorColumnEditor(3, "Vector u")
        self.vec_u.changed.connect(self._refresh_basic_badge)
        body.addWidget(self.vec_u)

        self.basic_mid = QStackedWidget()
        self.vec_v = VectorColumnEditor(3, "Vector v")
        self.vec_v.changed.connect(self._refresh_basic_badge)
        self.basic_mid.addWidget(self.vec_v)

        scale_card = QFrame()
        apply_widget_class(scale_card, "elevated-card")
        scale_layout = QVBoxLayout(scale_card)
        scale_layout.addWidget(QLabel("Escalar k"))
        self.basic_k = QLineEdit("2")
        self.basic_k.setObjectName("scalarField")
        self.basic_k.setAlignment(Qt.AlignCenter)
        self.basic_k.setFont(QFont("Fira Code", 14))
        self.basic_k.textChanged.connect(self._refresh_basic_badge)
        scale_layout.addWidget(self.basic_k)
        scale_layout.addStretch(1)
        self.basic_mid.addWidget(scale_card)
        body.addWidget(self.basic_mid)

        eq = QLabel("=")
        eq.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE};")
        body.addWidget(eq, 0, Qt.AlignCenter)

        result_card = QFrame()
        apply_widget_class(result_card, "elevated-card")
        result_layout = QVBoxLayout(result_card)
        result_layout.addWidget(QLabel("Resultado"))
        self.basic_result = BookMatrixWidget()
        result_layout.addWidget(self.basic_result, stretch=1)
        body.addWidget(result_card, stretch=1)
        layout.addLayout(body, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.basic_compute_btn = QPushButton("Calcular")
        self.basic_compute_btn.setObjectName("primaryAction")
        self.basic_compute_btn.clicked.connect(self._compute_basic)
        actions.addWidget(self.basic_compute_btn)
        layout.addLayout(actions)

        self._refresh_basic_badge()
        return page

    def _build_combination_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        top = QHBoxLayout()
        dim_lbl = QLabel("Espacio ℝⁿ   n =")
        dim_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;")
        self.combo_dim = QSpinBox()
        self.combo_dim.setRange(2, 10)
        self.combo_dim.setValue(3)
        self.combo_dim.valueChanged.connect(self._on_combo_dimension)
        top.addWidget(dim_lbl)
        top.addWidget(self.combo_dim)
        top.addStretch(1)
        sample_ok = QPushButton("Ejemplo SCD")
        sample_ok.clicked.connect(self.load_combination_scd_sample)
        sample_si = QPushButton("Ejemplo SI")
        sample_si.clicked.connect(self.load_combination_si_sample)
        top.addWidget(sample_ok)
        top.addWidget(sample_si)
        layout.addLayout(top)

        body = QHBoxLayout()

        generators = QFrame()
        apply_widget_class(generators, "elevated-card")
        gen_layout = QVBoxLayout(generators)
        gen_title = QLabel("Conjunto {v₁, …, vₖ}")
        gen_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        gen_layout.addWidget(gen_title)

        self.combo_list_host = QWidget()
        self.combo_list_layout = QHBoxLayout(self.combo_list_host)
        self.combo_list_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.combo_list_host)
        gen_layout.addWidget(scroll, stretch=1)

        add_btn = QPushButton("+  Agregar vector")
        add_btn.setObjectName("secondaryAction")
        add_btn.clicked.connect(self._add_combo_vector)
        gen_layout.addWidget(add_btn)
        body.addWidget(generators, stretch=3)

        self.target_editor = VectorColumnEditor(3, "Vector objetivo  b")
        self.target_editor.setStyleSheet(
            f"QFrame {{ border: 2px solid {COLOR_INTERACTIVE_IDLE}; border-radius: 8px; }}"
        )
        body.addWidget(self.target_editor, stretch=1)
        layout.addLayout(body, stretch=2)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.combo_btn = QPushButton("Evaluar combinación lineal")
        self.combo_btn.setObjectName("primaryAction")
        self.combo_btn.clicked.connect(self._evaluate_combination)
        actions.addWidget(self.combo_btn)
        layout.addLayout(actions)

        results = QFrame()
        apply_widget_class(results, "elevated-card")
        res_layout = QVBoxLayout(results)
        self.combo_badge = QLabel("Esperando evaluación")
        self.combo_badge.setAlignment(Qt.AlignCenter)
        self.combo_badge.setWordWrap(True)
        self.combo_badge.setStyleSheet(_badge_style("#3A3642", COLOR_TEXT_PRIMARY))
        res_layout.addWidget(self.combo_badge)

        self.combo_summary = QLabel("")
        self.combo_summary.setWordWrap(True)
        self.combo_summary.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;")
        self.combo_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        res_layout.addWidget(self.combo_summary)

        self.combo_checklist = QVBoxLayout()
        res_layout.addLayout(self.combo_checklist)

        self.show_steps_btn = QPushButton("Ver procedimiento de escalonamiento")
        self.show_steps_btn.setObjectName("secondaryAction")
        self.show_steps_btn.setCheckable(True)
        self.show_steps_btn.clicked.connect(self._toggle_combo_steps)
        self.show_steps_btn.setEnabled(False)
        res_layout.addWidget(self.show_steps_btn)

        self.combo_stepper = AlgorithmStepperCarousel()
        self.combo_stepper.setVisible(False)
        res_layout.addWidget(self.combo_stepper)
        layout.addWidget(results, stretch=2)

        self._add_combo_vector()
        self._add_combo_vector()
        return page

    def _on_basic_dimension(self, n: int) -> None:
        self.vec_u.set_dimension(n)
        self.vec_v.set_dimension(n)
        self.basic_result.clear()
        self._refresh_basic_badge()

    def _on_basic_op(self, op_id: int) -> None:
        self.basic_mid.setCurrentIndex(1 if op_id == 2 else 0)
        self.basic_result.clear()
        self._refresh_basic_badge()

    def _refresh_basic_badge(self) -> None:
        n = self.basic_dim.value()
        if self.basic_scale_btn.isChecked():
            try:
                parse_scalar(self.basic_k.text())
            except Exception:
                self.basic_badge.setText("✕ El escalar k no es un número válido.")
                self.basic_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
                self.basic_compute_btn.setEnabled(False)
                return
            if not self.vec_u.is_valid():
                self.basic_badge.setText("✕ Hay componentes no numéricas en v.")
                self.basic_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
                self.basic_compute_btn.setEnabled(False)
                return
            self.basic_badge.setText(f"✓ Escalado definido en ℝ^{n}: (k · v) ∈ ℝ^{n}")
            self.basic_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS, COLOR_BG_BASE))
            self.basic_compute_btn.setEnabled(True)
            return

        if not self.vec_u.is_valid() or not self.vec_v.is_valid():
            self.basic_badge.setText("✕ Hay componentes no numéricas.")
            self.basic_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
            self.basic_compute_btn.setEnabled(False)
            return
        self.basic_badge.setText(
            f"✓ u, v ∈ ℝ^{n} con la misma dimensión. La suma y la resta están definidas."
        )
        self.basic_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS, COLOR_BG_BASE))
        self.basic_compute_btn.setEnabled(True)

    def _compute_basic(self) -> None:
        try:
            if self.basic_scale_btn.isChecked():
                result = vector_scale(self.vec_u.get_vector(), self.basic_k.text())
            elif self.basic_sub_btn.isChecked():
                result = vector_sub(self.vec_u.get_vector(), self.vec_v.get_vector())
            else:
                result = vector_add(self.vec_u.get_vector(), self.vec_v.get_vector())
            self.basic_result.set_matrix(
                result.to_column_matrix(), split_col=None, show_headers=False
            )
        except DimensionMismatchError as exc:
            self.basic_badge.setText(f"✕ {exc}")
            self.basic_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))
            self.basic_compute_btn.setEnabled(False)

    def _on_combo_dimension(self, n: int) -> None:
        for editor in self._combo_editors:
            editor.set_dimension(n)
        self.target_editor.set_dimension(n)

    def _retitle_combo_vectors(self) -> None:
        for i, editor in enumerate(self._combo_editors):
            editor.set_title(f"v{i + 1}")

    def _add_combo_vector(self) -> None:
        editor = VectorColumnEditor(
            self.combo_dim.value(),
            f"v{len(self._combo_editors) + 1}",
            removable=True,
        )
        editor.removed.connect(lambda e=editor: self._remove_combo_vector(e))
        self._combo_editors.append(editor)
        self.combo_list_layout.addWidget(editor)
        self._retitle_combo_vectors()

    def _remove_combo_vector(self, editor: VectorColumnEditor) -> None:
        if len(self._combo_editors) <= 1:
            return
        self._combo_editors.remove(editor)
        editor.hide()
        editor.setParent(None)
        editor.deleteLater()
        self._retitle_combo_vectors()

    def _clear_combo_checklist(self) -> None:
        while self.combo_checklist.count():
            item = self.combo_checklist.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _evaluate_combination(self) -> None:
        if not all(ed.is_valid() for ed in self._combo_editors) or not self.target_editor.is_valid():
            self._show_alert("Entrada inválida", "Corrige las componentes no numéricas.")
            return
        try:
            vectors = [ed.get_vector() for ed in self._combo_editors]
            target = self.target_editor.get_vector()
            result = evaluate_linear_combination(vectors, target)
        except (DimensionMismatchError, ValueError) as exc:
            self._show_alert("Dimensiones incompatibles", str(exc))
            return

        self._clear_combo_checklist()
        self.show_steps_btn.setEnabled(True)
        self.combo_stepper.set_steps(result.tracer.get_steps())

        if result.system_type == SystemType.CONSISTENT_DETERMINED:
            self.combo_badge.setText("SÍ ES COMBINACIÓN LINEAL ÚNICA  (SCD)")
            self.combo_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_SUCCESS, COLOR_BG_BASE))
        elif result.system_type == SystemType.CONSISTENT_INDETERMINED:
            self.combo_badge.setText("SÍ ES COMBINACIÓN LINEAL  (infinitas combinaciones, SCI)")
            self.combo_badge.setStyleSheet(_badge_style(COLOR_ACCENT_WARNING, COLOR_BG_BASE))
        else:
            self.combo_badge.setText("NO ES COMBINACIÓN LINEAL  (SI)")
            self.combo_badge.setStyleSheet(_badge_style(COLOR_FEEDBACK_ERROR, COLOR_TEXT_PRIMARY))

        lines: List[str] = []
        if result.weights is not None:
            lines.append(f"b  =  {format_combination_equation(vectors, result.weights)}")
            weight_bits = [
                f"c{i + 1} = {format_scalar(c)}" for i, c in enumerate(result.weights)
            ]
            lines.append("Pesos:  " + " ,  ".join(weight_bits))
        if result.parametric_solution:
            lines.append(f"Solución paramétrica:  {result.parametric_solution}")
        if result.contradiction_info:
            lines.append(result.contradiction_info)
        self.combo_summary.setText("\n".join(lines))

        for label, got, expected, ok in result.verification_checklist:
            mark = "✓" if ok else "✗"
            color = COLOR_FEEDBACK_SUCCESS if ok else COLOR_FEEDBACK_ERROR
            row = QLabel(
                f"{mark}  {label}:  {format_scalar(got)}  =  {format_scalar(expected)}"
            )
            row.setStyleSheet(
                f"color: {color}; font-size: 16px; font-family: {FONT_FAMILY_MONO}; padding: 2px 0;"
            )
            self.combo_checklist.addWidget(row)

        if result.system_type == SystemType.INCONSISTENT:
            row = QLabel("Contradicción: aparece una fila [0 … 0 | c ≠ 0].")
            row.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-size: 16px; font-style: italic; "
                f"padding: 8px; background-color: {COLOR_SURFACE_INNER};"
            )
            self.combo_checklist.addWidget(row)

    def _toggle_combo_steps(self) -> None:
        self.combo_stepper.setVisible(self.show_steps_btn.isChecked())

    def load_combination_scd_sample(self) -> None:
        self.combo_dim.setValue(3)
        while len(self._combo_editors) > 3:
            self._remove_combo_vector(self._combo_editors[-1])
        while len(self._combo_editors) < 3:
            self._add_combo_vector()
        self._combo_editors[0].set_vector(Vector([1, 0, 0]))
        self._combo_editors[1].set_vector(Vector([0, 1, 0]))
        self._combo_editors[2].set_vector(Vector([0, 0, 1]))
        self.target_editor.set_vector(Vector([2, "-1/2", 3]))
        self._evaluate_combination()

    def load_combination_si_sample(self) -> None:
        self.combo_dim.setValue(3)
        while len(self._combo_editors) > 2:
            self._remove_combo_vector(self._combo_editors[-1])
        while len(self._combo_editors) < 2:
            self._add_combo_vector()
        self._combo_editors[0].set_vector(Vector([1, 0, 0]))
        self._combo_editors[1].set_vector(Vector([0, 1, 0]))
        self.target_editor.set_vector(Vector([0, 0, 1]))
        self._evaluate_combination()

    def _show_alert(self, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        apply_message_box_theme(box)
        box.exec()
