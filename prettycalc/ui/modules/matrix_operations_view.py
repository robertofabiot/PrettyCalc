"""Vista de álgebra matricial: A ± B, k·A, A·B con badge dimensional e inspector."""

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
        QSizePolicy,
        QMessageBox,
        QScrollArea,
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
)
from prettycalc.core.types import DimensionMismatchError, Matrix, format_scalar, parse_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.theme import (
    COLOR_BG_BASE,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
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
        mode_group.addButton(self.binary_mode_btn, 0)
        mode_group.addButton(self.scalar_mode_btn, 1)
        mode_group.idClicked.connect(self._on_mode_changed)
        toolbar.addWidget(self.binary_mode_btn)
        toolbar.addWidget(self.scalar_mode_btn)
        toolbar.addStretch(1)

        sample_ok = QPushButton("Ejemplo 2×3 · 3×2")
        sample_ok.clicked.connect(self.load_compatible_product_sample)
        sample_bad = QPushButton("Ejemplo incompatible")
        sample_bad.clicked.connect(self.load_incompatible_sample)
        toolbar.addWidget(sample_ok)
        toolbar.addWidget(sample_bad)
        root.addLayout(toolbar)

        self.badge = QLabel("")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        root.addWidget(self.badge)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_binary_page())
        self.pages.addWidget(self._build_scalar_page())
        root.addWidget(self.pages, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.compute_btn = QPushButton("Calcular")
        self.compute_btn.setObjectName("primaryAction")
        self.compute_btn.clicked.connect(self.compute)
        actions.addWidget(self.compute_btn)
        root.addLayout(actions)

        inspector_card = QFrame()
        apply_widget_class(inspector_card, "elevated-card")
        inspector_layout = QVBoxLayout(inspector_card)
        inspector_layout.setContentsMargins(14, 12, 14, 12)
        inspector_title = QLabel("Inspector de producto  Cᵢⱼ = Σ Aᵢₖ Bₖⱼ")
        inspector_title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        inspector_layout.addWidget(inspector_title)
        self.inspector_label = QLabel(
            "Calcula un producto A · B y pulsa una celda de C para ver la fila de A, "
            "la columna de B y la sumatoria de productos parciales."
        )
        self.inspector_label.setWordWrap(True)
        self.inspector_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.inspector_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-family: {FONT_FAMILY_MONO};"
        )
        inspector_layout.addWidget(self.inspector_label)
        root.addWidget(inspector_card)

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

    def _wrap_matrix_card(self, title: str, body: QWidget) -> QFrame:
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(body)
        layout.addWidget(scroll, stretch=1)
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

    def _refresh_compatibility(self) -> None:
        ok, message = self._compatibility_state()
        self.badge.setText(message)
        self.badge.setStyleSheet(_badge_style(ok))
        self.compute_btn.setEnabled(ok)
        self.compute_btn.setToolTip("" if ok else message)

    def _compatibility_state(self) -> Tuple[bool, str]:
        if self._is_scalar_mode():
            text = self.scalar_edit.text().strip()
            try:
                parse_scalar(text)
            except Exception:
                return False, "✕ El escalar k no es un número válido (usa enteros, a/b o decimales)."
            if not self.grid_scalar.is_all_valid():
                return False, "✕ Hay celdas no numéricas en A."
            r, c = self.grid_scalar.data_shape()
            return True, f"✓ Multiplicación escalar definida: k · A_{{{r}×{c}}}"

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
            "El producto A_{m×n} · B_{n×p} exige que las columnas de A igualen las filas de B.",
        )

    def compute(self) -> None:
        ok, message = self._compatibility_state()
        if not ok:
            self.compute_btn.setEnabled(False)
            self.badge.setText(message)
            return

        try:
            if self._is_scalar_mode():
                k = parse_scalar(self.scalar_edit.text())
                a = self.grid_scalar.get_matrix()
                result = matrix_scale(a, k)
                self.scalar_result_view.set_matrix(
                    result, split_col=None, clickable=False, show_headers=False
                )
                self._result = result
                self._details = []
                self.inspector_label.setText(
                    f"Cada celda se escala: Cᵢⱼ = ({format_scalar(k)}) · Aᵢⱼ."
                )
                return

            a = self.grid_a.get_matrix()
            b = self.grid_b.get_matrix()
            if self._op == "add":
                result = matrix_add(a, b)
                self._details = []
                self.inspector_label.setText("Suma elemento a elemento: Cᵢⱼ = Aᵢⱼ + Bᵢⱼ.")
            elif self._op == "sub":
                result = matrix_sub(a, b)
                self._details = []
                self.inspector_label.setText("Resta elemento a elemento: Cᵢⱼ = Aᵢⱼ − Bᵢⱼ.")
            else:
                result, self._details = matrix_multiply_with_details(a, b)
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
        self._clear_highlights()
        self.inspector_label.setText(
            "Calcula un producto A · B y pulsa una celda de C para ver la fila de A, "
            "la columna de B y la sumatoria de productos parciales."
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
