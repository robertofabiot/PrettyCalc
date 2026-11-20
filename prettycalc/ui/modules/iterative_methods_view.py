"""Módulo 10: métodos iterativos de Jacobi y Gauss-Seidel (Programa 8).

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).

- Entrada [A | b] cuadrada, vector inicial x⁽⁰⁾, tolerancia ε, criterio de
  paro y máximo de iteraciones.
- Diagnóstico en vivo mientras se escribe: dominancia diagonal fila por fila,
  simetría definida positiva y ρ(T) de cada método en un medidor.
- Cada método tiene su carrusel (despeje, criterios, cada iteración con sus
  sustituciones y la comparación final con la solución exacta) y una tabla
  de iteraciones sincronizada con el carrusel.
- La pestaña de comparación grafica la convergencia de ambos en escala
  logarítmica y resume cuál conviene y por qué.
- «Reordenar filas» busca la permutación de ecuaciones que da dominancia
  diagonal (se deshace con Ctrl+Z).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QButtonGroup,
        QComboBox,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.iterative_methods import (
    DEFAULT_MAX_ITERATIONS,
    MAX_ALLOWED_ITERATIONS,
    ConvergenceAnalysis,
    IterationStatus,
    IterativeMethod,
    IterativeResult,
    StopCriterion,
    ZeroDiagonalError,
    analyze_convergence,
    comparison_summary,
    dominance_lines,
    format_decimal,
    format_vector,
    reorder_for_dominance,
    solve_iterative,
    superscript_iter,
)
from prettycalc.core.types import Matrix, Vector, subscript
from prettycalc.ui.convergence_plot import (
    GAUSS_SEIDEL_COLOR,
    JACOBI_COLOR,
    ConvergencePlot,
    PlotSeries,
    SpectralGauge,
)
from prettycalc.ui.feedback import busy, show_toast
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.module_scroll import make_module_scroll, track_content_width
from prettycalc.ui.responsive import ResponsiveRow, StackingSplitterHost
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.stepper_carousel import AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_ELEVATED,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_widget_class,
    badge_style,
    idle_badge_style,
    rgba,
    ui_font,
)

MAX_ITERATIVE_ORDER = 8

#: Índice del carrusel donde está x⁽⁰⁾: inicial, dominancia, despeje, ρ(T).
FIRST_ITERATION_STEP = 4

#: Tolerancias ofrecidas (texto, valor exacto).
TOLERANCES = (
    ("10⁻²  (0.01)", Fraction(1, 10**2)),
    ("10⁻³  (0.001)", Fraction(1, 10**3)),
    ("10⁻⁴  (0.0001)", Fraction(1, 10**4)),
    ("10⁻⁵", Fraction(1, 10**5)),
    ("10⁻⁶", Fraction(1, 10**6)),
    ("10⁻⁸", Fraction(1, 10**8)),
    ("10⁻¹⁰", Fraction(1, 10**10)),
)
DEFAULT_TOLERANCE_INDEX = 2

#: Casos de prueba: (id, rótulo, ayuda, A, b).
EXAMPLES = (
    (
        "dominant",
        "I · Diagonal dominante",
        "Ambos convergen; Gauss-Seidel en menos iteraciones. x* = (1, 2, −1, 1)",
        [[10, -1, 2, 0], [-1, 11, -1, 3], [2, -1, 10, -1], [0, 3, -1, 8]],
        [6, 25, -11, 15],
    ),
    (
        "gs_only",
        "II · Solo Gauss-Seidel",
        "ρ(T_J) ≈ 1.118 > 1 y ρ(T_GS) = 0.5: Jacobi diverge. x* = (1, 2, −1)",
        [[2, -1, 1], [2, 2, 2], [-1, -1, 2]],
        [-1, 4, -5],
    ),
    (
        "jacobi_only",
        "III · Solo Jacobi",
        "ρ(T_J) = 0 y ρ(T_GS) = 2: Gauss-Seidel diverge. x* = (1, 2, −1)",
        [[1, 2, -2], [1, 1, 1], [2, 2, 1]],
        [7, 2, 5],
    ),
    (
        "neither",
        "IV · Ninguno (reordenar)",
        "Ninguno converge hasta intercambiar las ecuaciones. x* = (1, 1)",
        [[1, -5], [7, -1]],
        [-4, 6],
    ),
)

_METHOD_COLORS = {
    IterativeMethod.JACOBI: JACOBI_COLOR,
    IterativeMethod.GAUSS_SEIDEL: GAUSS_SEIDEL_COLOR,
}


def _title(text: str, size: int = 19) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size: {size}px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
    return label


def _muted(text: str = "", size: int = 14) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: {size}px;")
    return label


def _card() -> tuple:
    card = QFrame()
    apply_widget_class(card, "elevated-card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    return card, layout


def _scroll(widget: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setWidget(widget)
    track_content_width(scroll)
    return scroll


def _chip_style(color: str) -> str:
    return (
        f"background-color: {rgba(color, 0.18)}; color: {COLOR_TEXT_PRIMARY}; "
        f"border: 1px solid {rgba(color, 0.8)}; border-radius: 10px; padding: 2px 10px; "
        f"font-size: 13px; font-weight: 600;"
    )


def _status_color(status: IterationStatus) -> str:
    return {
        IterationStatus.CONVERGED: COLOR_FEEDBACK_SUCCESS,
        IterationStatus.DIVERGED: COLOR_FEEDBACK_ERROR,
        IterationStatus.MAX_ITERATIONS: COLOR_ACCENT_WARNING,
    }[status]


class IterationTable(QTableWidget):
    """k, x₁ … xₙ, ‖Δ‖∞ y error real de cada iterado."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("iterationTable")
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.horizontalHeader().setHighlightSections(False)
        self.setMinimumHeight(300)
        self.setFont(ui_font(14, mono=True))
        self.setStyleSheet(
            f"""
            QTableWidget#iterationTable {{
                background-color: {COLOR_SURFACE_INNER};
                alternate-background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.06)};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                selection-background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.30)};
                selection-color: {COLOR_TEXT_PRIMARY};
                font-family: {FONT_FAMILY_MONO};
                font-size: 14px;
            }}
            QTableWidget#iterationTable::item {{ padding: 4px 10px; }}
            QHeaderView::section {{
                background-color: {COLOR_SURFACE_ELEVATED};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                border-bottom: 2px solid {COLOR_INTERACTIVE_IDLE};
                padding: 6px 10px;
                font-weight: 600;
                font-size: 14px;
            }}
            """
        )

    def show_result(self, result: Optional[IterativeResult]) -> None:
        self.clear()
        if result is None:
            self.setRowCount(0)
            self.setColumnCount(0)
            return
        n = result.A.rows
        has_error = result.exact_solution is not None
        headers = ["k"] + [f"x{subscript(i + 1)}{superscript_iter('k')}" for i in range(n)]
        headers.append("‖Δx‖∞")
        if has_error:
            headers.append("‖x − x*‖∞")
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        tips = {n + 1: "‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞: cambio entre iterados consecutivos (criterio de paro)"}
        if has_error:
            tips[n + 2] = "‖x⁽ᵏ⁾ − x*‖∞: distancia a la solución exacta de Gauss-Jordan"
        for col, tip in tips.items():
            self.horizontalHeaderItem(col).setToolTip(tip)
        self.setRowCount(len(result.iterations))
        right = Qt.AlignRight | Qt.AlignVCenter
        for row, record in enumerate(result.iterations):
            cells = [str(record.k)] + [format_decimal(v, 6, fixed=True) for v in record.x]
            cells.append("—" if record.delta_norm is None else format_decimal(record.delta_norm, 6, fixed=True))
            if has_error:
                cells.append("—" if record.error_norm is None else format_decimal(record.error_norm, 6, fixed=True))
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter if col == 0 else right)
                self.setItem(row, col, item)
        last = len(result.iterations) - 1
        color = QColor(_status_color(result.status))
        for col in range(self.columnCount()):
            item = self.item(last, col)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setForeground(color)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)


class MethodPanel(QWidget):
    """Carrusel del método y su tabla de iteraciones, sincronizados."""

    def __init__(self, method: IterativeMethod, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.method = method
        self.result: Optional[IterativeResult] = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(10)
        self.chip = QLabel(method.label)
        self.chip.setStyleSheet(_chip_style(_METHOD_COLORS[method]))
        head.addWidget(self.chip)
        self.status_label = QLabel("")
        self.status_label.setObjectName(f"{method.value}Status")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 15px;")
        head.addWidget(self.status_label, stretch=1)
        layout.addLayout(head)

        # Lado a lado solo con ancho de sobra; si no, la tabla baja bajo el carrusel.
        self.row = ResponsiveRow(breakpoint=1500, spacing=12)
        self.stepper = AlgorithmStepperCarousel(variable_headers=True)
        self.stepper.setObjectName(f"{method.value}Stepper")
        self.stepper.set_export_title(f"Método de {method.label}")
        self.stepper.set_empty_hint(f"Pulsa Iterar para ver el método de {method.label} paso a paso.")
        self.stepper.mode_btn.setChecked(False)  # decimales: los iterados tienen denominadores enormes
        self.stepper.setMinimumHeight(560)
        self.row.add_widget(self.stepper, stretch=1)

        table_box, table_layout = _card()
        table_layout.addWidget(_title("Tabla de iteraciones", 16))
        self.table_hint = _muted("Haz clic en una fila para ver esa iteración en el carrusel.", 13)
        table_layout.addWidget(self.table_hint)
        self.table = IterationTable()
        table_layout.addWidget(self.table, stretch=1)
        self.row.add_widget(table_box, stretch=1)
        layout.addWidget(self.row, stretch=1)

        self.table.itemSelectionChanged.connect(self._on_table_selection)
        self.stepper.stepChanged.connect(self._on_step_changed)
        self._syncing = False

    def show_result(self, result: Optional[IterativeResult]) -> None:
        self.result = result
        if result is None:
            self.stepper.set_steps([])
            self.table.show_result(None)
            self.status_label.setText("")
            return
        self.stepper.set_steps(result.tracer.get_steps())
        self.table.show_result(result)
        color = _status_color(result.status)
        self.status_label.setText(
            f"<span style='color:{color}; font-weight:600;'>{result.status.label}</span>"
            f"<span style='color:{COLOR_TEXT_MUTED};'> · {result.iteration_count} iteraciones</span>"
        )

    def show_error(self, steps) -> None:
        self.result = None
        self.stepper.set_steps(steps)
        self.table.show_result(None)
        self.status_label.setText(
            f"<span style='color:{COLOR_FEEDBACK_ERROR}; font-weight:600;'>No aplicable</span>"
        )
        if steps:
            self.stepper.go_to_step(len(steps) - 1)

    def _on_table_selection(self) -> None:
        if self._syncing:
            return
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if rows:
            self._syncing = True
            try:
                self.stepper.go_to_step(FIRST_ITERATION_STEP + rows[0].row())
            finally:
                self._syncing = False

    def _on_step_changed(self, index: int) -> None:
        if self._syncing or self.result is None:
            return
        row = index - FIRST_ITERATION_STEP
        self._syncing = True
        try:
            if 0 <= row < self.table.rowCount():
                self.table.selectRow(row)
                self.table.scrollToItem(self.table.item(row, 0))
            else:
                self.table.clearSelection()
        finally:
            self._syncing = False


class IterativeMethodsView(QWidget):
    """Jacobi y Gauss-Seidel: entrada, diagnóstico, pasos, tablas y comparación."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("iterativeMethodsView")
        self.results: Dict[IterativeMethod, IterativeResult] = {}
        self.analysis: Optional[ConvergenceAnalysis] = None
        self.active_example: Optional[str] = None
        self._loading = False
        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.setInterval(120)
        self._analysis_timer.timeout.connect(self.refresh_analysis)
        self._setup_ui()
        self.grid.matrixChanged.connect(self._on_system_changed)
        self.x0_grid.matrixChanged.connect(self._on_parameters_changed)
        self._sync_x0()
        self.refresh_analysis()
        self._sync_controls()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Método, parámetros y acción principal.
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self._caption("Método"))
        self.method_group = QButtonGroup(self)
        self.method_group.setExclusive(True)
        self.jacobi_btn = self._toggle("Jacobi", "Solo el método de Jacobi")
        self.gs_btn = self._toggle("Gauss-Seidel", "Solo el método de Gauss-Seidel")
        self.both_btn = self._toggle("Comparar ambos", "Ejecuta los dos con los mismos datos y los compara")
        self.both_btn.setChecked(True)
        for index, button in enumerate((self.jacobi_btn, self.gs_btn, self.both_btn)):
            self.method_group.addButton(button, index)
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        self.iterate_btn = QPushButton("Iterar")
        self.iterate_btn.setObjectName("primaryAction")
        self.iterate_btn.setToolTip("Ejecuta el método (Ctrl+Intro desde cualquier celda)")
        self.iterate_btn.setCursor(Qt.PointingHandCursor)
        self.iterate_btn.clicked.connect(self.iterate)
        toolbar.addWidget(self.iterate_btn)
        root.addLayout(toolbar)

        params = QHBoxLayout()
        params.setSpacing(8)
        params.addWidget(self._caption("Tolerancia ε"))
        self.tolerance_combo = QComboBox()
        self.tolerance_combo.setObjectName("toleranceCombo")
        for text, _value in TOLERANCES:
            self.tolerance_combo.addItem(text)
        self.tolerance_combo.setCurrentIndex(DEFAULT_TOLERANCE_INDEX)
        self.tolerance_combo.setToolTip("El método se detiene cuando la medida de paro es menor que ε")
        params.addWidget(self.tolerance_combo)
        params.addSpacing(10)
        params.addWidget(self._caption("Criterio"))
        self.criterion_combo = QComboBox()
        self.criterion_combo.setObjectName("criterionCombo")
        self.criterion_combo.addItem("Absoluto  ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ < ε")
        self.criterion_combo.addItem("Relativo  ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ / ‖x⁽ᵏ⁾‖∞ < ε")
        params.addWidget(self.criterion_combo)
        params.addSpacing(10)
        params.addWidget(self._caption("Máx. iteraciones"))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setObjectName("maxIterSpin")
        self.max_iter_spin.setRange(1, MAX_ALLOWED_ITERATIONS)
        self.max_iter_spin.setValue(DEFAULT_MAX_ITERATIONS)
        self.max_iter_spin.setToolTip(f"Entre 1 y {MAX_ALLOWED_ITERATIONS}")
        params.addWidget(self.max_iter_spin)
        params.addStretch(1)
        root.addLayout(params)
        for widget in (self.tolerance_combo, self.criterion_combo):
            widget.currentIndexChanged.connect(self._on_parameters_changed)
        self.max_iter_spin.valueChanged.connect(self._on_parameters_changed)

        examples = QHBoxLayout()
        examples.setSpacing(8)
        examples.addWidget(_muted("Casos de prueba"))
        self.example_buttons: Dict[str, QPushButton] = {}
        for key, label, tip, _a, _b in EXAMPLES:
            button = QPushButton(label)
            button.setObjectName("secondaryAction")
            button.setCheckable(True)
            button.setToolTip(tip)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, k=key: self.load_example(k))
            self.example_buttons[key] = button
            examples.addWidget(button)
        examples.addStretch(1)
        root.addLayout(examples)

        self.badge = QLabel("")
        self.badge.setObjectName("iterativeBadge")
        self.badge.setWordWrap(True)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setTextFormat(Qt.PlainText)
        root.addWidget(self.badge)

        # Fila superior: sistema · diagnóstico · resultados.
        upper = QSplitter(Qt.Horizontal)
        upper.setHandleWidth(10)
        upper.setChildrenCollapsible(False)
        upper.setMinimumHeight(470)

        input_card, input_layout = _card()
        input_layout.addWidget(_title("Sistema  [A | b]"))
        self.grid = DynamicMatrixGrid(
            initial_rows=3, initial_cols=3, row_expandable=False, col_expandable=False
        )
        self.size_control = MatrixSizeControl(
            self.grid, square=True, order_label="Orden n", minimum=2, maximum=MAX_ITERATIVE_ORDER
        )
        input_layout.addWidget(self.size_control)
        input_layout.addWidget(self.grid, stretch=1)
        self.grid.submitRequested.connect(self.iterate)
        input_layout.addWidget(self._caption("Vector inicial x⁽⁰⁾"))
        self.x0_grid = DynamicMatrixGrid(
            initial_rows=1,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
            show_hint=False,
            variable_headers=True,
        )
        self.x0_grid.submitRequested.connect(self.iterate)
        input_layout.addWidget(self.x0_grid)
        reorder_row = QHBoxLayout()
        self.reorder_btn = QPushButton("Reordenar filas para dominancia")
        apply_widget_class(self.reorder_btn, "link-action")
        self.reorder_btn.setToolTip(
            "Intercambia ecuaciones para que cada |aᵢᵢ| supere la suma del resto de su fila (Ctrl+Z deshace)"
        )
        self.reorder_btn.setCursor(Qt.PointingHandCursor)
        self.reorder_btn.clicked.connect(self.reorder_rows)
        reorder_row.addWidget(self.reorder_btn)
        reorder_row.addStretch(1)
        self.zero_x0_btn = QPushButton("x⁽⁰⁾ = 0")
        apply_widget_class(self.zero_x0_btn, "link-action")
        self.zero_x0_btn.setToolTip("Vuelve al vector inicial nulo")
        self.zero_x0_btn.clicked.connect(self.reset_x0)
        reorder_row.addWidget(self.zero_x0_btn)
        input_layout.addLayout(reorder_row)
        upper.addWidget(_scroll(input_card))

        diag_card, diag_layout = _card()
        diag_layout.addWidget(_title("Diagnóstico de convergencia"))
        diag_layout.addWidget(self._caption("Dominancia diagonal estricta por filas"))
        self.dominance_label = QLabel("")
        self.dominance_label.setObjectName("dominanceLabel")
        self.dominance_label.setTextFormat(Qt.RichText)
        self.dominance_label.setWordWrap(True)
        self.dominance_label.setStyleSheet("font-size: 15px;")
        diag_layout.addWidget(self.dominance_label)
        self.spd_label = QLabel("")
        self.spd_label.setObjectName("spdLabel")
        self.spd_label.setTextFormat(Qt.RichText)
        self.spd_label.setWordWrap(True)
        self.spd_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        diag_layout.addWidget(self.spd_label)
        diag_layout.addWidget(self._caption("Radio espectral de la matriz de iteración"))
        self.jacobi_gauge = SpectralGauge("Jacobi  ·  ρ(T)", JACOBI_COLOR)
        self.gs_gauge = SpectralGauge("Gauss-Seidel  ·  ρ(T)", GAUSS_SEIDEL_COLOR)
        diag_layout.addWidget(self.jacobi_gauge)
        diag_layout.addWidget(self.gs_gauge)
        self.verdict_label = QLabel("")
        self.verdict_label.setObjectName("verdictLabel")
        self.verdict_label.setTextFormat(Qt.RichText)
        self.verdict_label.setWordWrap(True)
        self.verdict_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_PRIMARY};")
        diag_layout.addWidget(self.verdict_label)
        diag_layout.addWidget(
            _muted("Converge para todo x⁽⁰⁾ si y solo si ρ(T) < 1. La dominancia diagonal es suficiente, no necesaria.", 13)
        )
        diag_layout.addStretch(1)
        upper.addWidget(_scroll(diag_card))

        result_card, result_layout = _card()
        result_layout.addWidget(_title("Resultados"))
        self.result_labels: Dict[IterativeMethod, QLabel] = {}
        for method in IterativeMethod:
            label = QLabel("")
            label.setObjectName(f"{method.value}Result")
            label.setTextFormat(Qt.RichText)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setStyleSheet(
                f"background-color: {COLOR_SURFACE_INNER}; border-left: 4px solid {_METHOD_COLORS[method]}; "
                f"border-radius: 4px; padding: 10px 12px; font-size: 14px; color: {COLOR_TEXT_PRIMARY};"
            )
            self.result_labels[method] = label
            result_layout.addWidget(label)
        self.exact_label = QLabel("")
        self.exact_label.setObjectName("exactLabel")
        self.exact_label.setWordWrap(True)
        self.exact_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.exact_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        result_layout.addWidget(self.exact_label)
        result_layout.addStretch(1)
        upper.addWidget(_scroll(result_card))
        upper.setSizes([380, 420, 400])
        self.upper_splitter = upper
        self.upper_host = StackingSplitterHost(upper)
        root.addWidget(self.upper_host)

        # Pestañas: cada método y la comparación.
        self.tabs = QTabWidget()
        self.tabs.setObjectName("iterativeTabs")
        self.tabs.setMinimumHeight(640)
        self.panels: Dict[IterativeMethod, MethodPanel] = {}
        for method in IterativeMethod:
            panel = MethodPanel(method)
            self.panels[method] = panel
            self.tabs.addTab(panel, method.label)
        compare = QWidget()
        compare_layout = QVBoxLayout(compare)
        compare_layout.setContentsMargins(8, 10, 8, 8)
        compare_layout.setSpacing(10)
        plot_head = QHBoxLayout()
        plot_head.addWidget(_title("Convergencia en escala logarítmica", 17))
        plot_head.addStretch(1)
        self.measure_group = QButtonGroup(self)
        self.delta_measure_btn = self._toggle("‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞", "Diferencia entre iterados consecutivos (criterio de paro)")
        self.error_measure_btn = self._toggle("Error real ‖x⁽ᵏ⁾ − x*‖∞", "Distancia a la solución exacta de Gauss-Jordan")
        self.delta_measure_btn.setChecked(True)
        self.measure_group.addButton(self.delta_measure_btn, 0)
        self.measure_group.addButton(self.error_measure_btn, 1)
        self.measure_group.idClicked.connect(lambda _id: self._refresh_plot())
        plot_head.addWidget(self.delta_measure_btn)
        plot_head.addWidget(self.error_measure_btn)
        compare_layout.addLayout(plot_head)
        self.plot = ConvergencePlot()
        self.plot.setObjectName("convergencePlot")
        self.plot.setMinimumHeight(340)
        compare_layout.addWidget(self.plot, stretch=1)
        self.compare_table = QTableWidget()
        self.compare_table.setObjectName("compareTable")
        self.compare_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.compare_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.compare_table.verticalHeader().setVisible(False)
        self.compare_table.setShowGrid(False)
        self.compare_table.setFocusPolicy(Qt.NoFocus)
        self.compare_table.setStyleSheet(self._compare_table_style())
        self.compare_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.compare_table.setMinimumHeight(60)
        compare_layout.addWidget(self.compare_table)
        self.compare_summary = QLabel("")
        self.compare_summary.setObjectName("compareSummary")
        self.compare_summary.setWordWrap(True)
        self.compare_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.compare_summary.setStyleSheet(
            f"background-color: {COLOR_SURFACE_INNER}; border-left: 3px solid {COLOR_FEEDBACK_SUCCESS}; "
            f"border-radius: 2px; padding: 12px 14px; font-size: 16px; font-style: italic; color: {COLOR_TEXT_PRIMARY};"
        )
        compare_layout.addWidget(self.compare_summary)
        self.tabs.addTab(compare, "Comparación")
        root.addWidget(self.tabs)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_module_scroll(content))

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;")
        return label

    def _toggle(self, text: str, tip: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("modeToggle")
        button.setCheckable(True)
        button.setToolTip(tip)
        button.setCursor(Qt.PointingHandCursor)
        return button

    @staticmethod
    def _compare_table_style() -> str:
        return f"""
            QTableWidget#compareTable {{
                background-color: {COLOR_SURFACE_INNER};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QTableWidget#compareTable::item {{ padding: 4px 12px; }}
            QHeaderView::section {{
                background-color: {COLOR_SURFACE_ELEVATED};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                border-bottom: 2px solid {COLOR_INTERACTIVE_IDLE};
                padding: 6px 12px;
                font-weight: 600;
                font-size: 14px;
            }}
        """

    # ------------------------------------------------------------------
    # Estado de la entrada
    # ------------------------------------------------------------------
    def selected_methods(self) -> List[IterativeMethod]:
        if self.jacobi_btn.isChecked():
            return [IterativeMethod.JACOBI]
        if self.gs_btn.isChecked():
            return [IterativeMethod.GAUSS_SEIDEL]
        return [IterativeMethod.JACOBI, IterativeMethod.GAUSS_SEIDEL]

    def tolerance(self) -> Fraction:
        return TOLERANCES[self.tolerance_combo.currentIndex()][1]

    def criterion(self) -> StopCriterion:
        return StopCriterion.ABSOLUTE if self.criterion_combo.currentIndex() == 0 else StopCriterion.RELATIVE

    def order(self) -> int:
        return self.grid.data_shape()[0]

    def system(self) -> Optional[tuple]:
        """(A, b) si la cuadrícula es válida y cuadrada; si no, None."""
        if not self.grid.is_all_valid():
            return None
        augmented = self.grid.get_matrix()
        n = augmented.rows
        if augmented.cols != n + 1:
            return None
        A = Matrix([[augmented.get(i, j) for j in range(n)] for i in range(n)])
        b = Vector([augmented.get(i, n) for i in range(n)])
        return A, b

    def x0(self) -> Optional[Vector]:
        if not self.x0_grid.is_all_valid():
            return None
        row = self.x0_grid.get_matrix()
        if row.cols != self.order():
            return None
        return Vector([row.get(0, j) for j in range(row.cols)])

    def _blocking_reason(self) -> Optional[str]:
        message = self.grid.validation_message()
        if message:
            return f"[A | b], {message[0].lower()}{message[1:]}"
        if self.system() is None:
            return "A debe ser cuadrada: una ecuación por incógnita."
        message = self.x0_grid.validation_message()
        if message:
            return f"x⁽⁰⁾, {message[0].lower()}{message[1:]}"
        return None

    def _sync_x0(self) -> None:
        n = self.order()
        if self.x0_grid.data_shape() == (1, n):
            return
        values = [0] * n
        if self.x0_grid.is_all_valid():
            current = self.x0_grid.get_matrix()
            for j in range(min(n, current.cols)):
                values[j] = current.get(0, j)
        self.x0_grid.set_matrix(Matrix([values]), record=False)

    def _sync_controls(self) -> None:
        reason = self._blocking_reason()
        self.iterate_btn.setEnabled(reason is None)
        self.reorder_btn.setEnabled(self.system() is not None)
        if reason is not None:
            self._set_badge(reason, COLOR_FEEDBACK_ERROR)
        elif not self.results:
            self._set_badge("Sistema listo. Elige el método y pulsa Iterar.", None)

    def _set_badge(self, text: str, color: Optional[str]) -> None:
        self.badge.setText(text)
        self.badge.setStyleSheet(idle_badge_style() if color is None else badge_style(color))

    def _on_system_changed(self) -> None:
        self._sync_x0()
        self._clear_results()
        if not self._loading:
            self.active_example = None
            for button in self.example_buttons.values():
                button.setChecked(False)
        self._analysis_timer.start()
        self._sync_controls()

    def _on_parameters_changed(self, *_args) -> None:
        if self._loading:
            return
        had = bool(self.results)
        self._clear_results()
        self._sync_controls()
        if had:
            self._set_badge("Cambiaron los parámetros: vuelve a pulsar Iterar.", None)

    def _clear_results(self) -> None:
        self.results = {}
        for panel in self.panels.values():
            panel.show_result(None)
        for label in self.result_labels.values():
            label.setText("")
        self.exact_label.setText("")
        self.plot.clear()
        self.compare_table.clear()
        self.compare_table.setRowCount(0)
        self.compare_table.setColumnCount(0)
        self.compare_summary.setText("")
        self.compare_summary.setVisible(False)
        self.grid.set_alert_rows([])
        self._show_placeholders()

    def _show_placeholders(self) -> None:
        for method, label in self.result_labels.items():
            label.setText(
                f"<b>{method.label}</b><br><span style='color:{COLOR_TEXT_MUTED};'>Sin ejecutar.</span>"
            )

    # ------------------------------------------------------------------
    # Diagnóstico en vivo
    # ------------------------------------------------------------------
    def refresh_analysis(self) -> None:
        system = self.system()
        if system is None:
            self.analysis = None
            self.dominance_label.setText(
                f"<span style='color:{COLOR_TEXT_MUTED};'>Completa [A | b].</span>"
            )
            self.spd_label.setText("")
            self.verdict_label.setText("")
            self.jacobi_gauge.set_radius(None)
            self.gs_gauge.set_radius(None)
            return
        A, b = system
        self.analysis = analysis = analyze_convergence(A, b)
        cell = "padding: 2px 10px; text-align: right;"
        rows = [
            "<table cellspacing='0' style='margin-bottom:6px;'>"
            f"<tr style='color:{COLOR_TEXT_MUTED};'>"
            f"<td style='{cell} text-align:left;'>Fila</td><td style='{cell}'>|a<sub>ii</sub>|</td>"
            f"<td style='{cell}'></td><td style='{cell}'>Σ<sub>j≠i</sub> |a<sub>ij</sub>|</td><td></td></tr>"
        ]
        for row in analysis.rows:
            color = COLOR_FEEDBACK_SUCCESS if row.strict else COLOR_FEEDBACK_ERROR
            relation = ">" if row.strict else ("=" if row.diagonal == row.off_diagonal_sum else "<")
            rows.append(
                f"<tr style='color:{COLOR_TEXT_PRIMARY};'>"
                f"<td style='{cell} text-align:left;'>F<sub>{row.row + 1}</sub></td>"
                f"<td style='{cell}'>{format_decimal(row.diagonal, 4)}</td>"
                f"<td style='{cell} color:{color};'>{relation}</td>"
                f"<td style='{cell}'>{format_decimal(row.off_diagonal_sum, 4)}</td>"
                f"<td style='{cell} color:{color}; font-weight:700;'>{'✓' if row.strict else '✗'}</td></tr>"
            )
        rows[-1] += "</table>"
        self.dominance_label.setToolTip("\n".join(dominance_lines(A, analysis)))
        rows = ["".join(rows)]
        dominant = analysis.strictly_dominant
        conclusion_color = COLOR_FEEDBACK_SUCCESS if dominant else COLOR_ACCENT_WARNING
        conclusion = (
            "Estrictamente dominante: ambos métodos convergen."
            if dominant
            else "No es estrictamente dominante: decide ρ(T)."
        )
        rows.append(
            f"<span style='color:{conclusion_color}; font-weight:600;'>{conclusion}</span>"
        )
        self.dominance_label.setText("".join(rows))

        minors = ", ".join(format_decimal(m, 4) for m in analysis.leading_minors)
        if analysis.positive_definite:
            spd = (
                f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>✓ Simétrica definida positiva</b> "
                f"(menores principales {minors} &gt; 0): Gauss-Seidel converge."
            )
        elif analysis.symmetric:
            spd = (
                f"<span style='color:{COLOR_TEXT_MUTED};'>Simétrica, pero no definida positiva "
                f"(menores principales {minors}).</span>"
            )
        else:
            spd = f"<span style='color:{COLOR_TEXT_MUTED};'>A no es simétrica.</span>"
        self.spd_label.setText(spd)

        if analysis.zero_diagonal_rows:
            self.jacobi_gauge.set_radius(None)
            self.gs_gauge.set_radius(None)
            rows_text = ", ".join(str(r + 1) for r in analysis.zero_diagonal_rows)
            self.verdict_label.setText(
                f"<b style='color:{COLOR_FEEDBACK_ERROR};'>aᵢᵢ = 0 en la fila {rows_text}:</b> "
                "no se puede despejar esa incógnita. Usa «Reordenar filas»."
            )
            return
        self.jacobi_gauge.set_radius(analysis.jacobi.radius)
        self.gs_gauge.set_radius(analysis.gauss_seidel.radius)
        verdicts = []
        for method in IterativeMethod:
            converges = analysis.predicts_convergence(method)
            color = COLOR_FEEDBACK_SUCCESS if converges else COLOR_FEEDBACK_ERROR
            verdicts.append(
                f"<b style='color:{_METHOD_COLORS[method]};'>{method.label}:</b> "
                f"<span style='color:{color};'>{analysis.verdict(method)}</span>"
            )
        self.verdict_label.setText("<br>".join(verdicts))

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def load_example(self, key: str) -> None:
        """Carga un caso de prueba y lo ejecuta con los dos métodos."""
        entry = next(e for e in EXAMPLES if e[0] == key)
        _key, _label, _tip, a, b = entry
        self._loading = True
        try:
            self.grid.set_matrix(Matrix([row + [value] for row, value in zip(a, b)]))
            self._sync_x0()
            self.x0_grid.set_matrix(Matrix([[0] * len(a)]), record=False)
            self.both_btn.setChecked(True)
        finally:
            self._loading = False
        self.active_example = key
        for other, button in self.example_buttons.items():
            button.setChecked(other == key)
        self._analysis_timer.stop()
        self.refresh_analysis()
        self.iterate()

    def reset_x0(self) -> None:
        self.x0_grid.set_matrix(Matrix([[0] * self.order()]))

    def reorder_rows(self) -> None:
        """Permuta las ecuaciones buscando dominancia diagonal (deshacer: Ctrl+Z)."""
        system = self.system()
        if system is None:
            return
        A, b = system
        reordering = reorder_for_dominance(A, b)
        if reordering is None:
            show_toast(self, "Ningún orden de las ecuaciones deja la diagonal sin ceros: A es singular.", kind="error")
            return
        if not reordering.changed:
            show_toast(self, reordering.explanation, kind="info")
            return
        n = A.rows
        self.grid.set_matrix(
            Matrix([[reordering.A.get(i, j) for j in range(n)] + [reordering.b[i]] for i in range(n)])
        )
        self._analysis_timer.stop()
        self.refresh_analysis()
        self.grid.set_alert_rows([])
        show_toast(
            self,
            reordering.explanation,
            kind="success" if reordering.strictly_dominant else "info",
            action_text="Deshacer",
            action=self.grid.undo,
            timeout_ms=7000,
        )

    def iterate(self) -> None:
        """Ejecuta el método o los métodos elegidos y publica pasos, tablas y gráfica."""
        reason = self._blocking_reason()
        if reason is not None:
            self._set_badge(reason, COLOR_FEEDBACK_ERROR)
            return
        A, b = self.system()
        x0 = self.x0()
        if self.analysis is None or self.analysis.A != A:
            self.refresh_analysis()
        self.results = {}
        errors: List[str] = []
        with busy(self.iterate_btn, "Iterando…"):
            for method in IterativeMethod:
                panel = self.panels[method]
                if method not in self.selected_methods():
                    panel.show_result(None)
                    continue
                try:
                    result = solve_iterative(
                        A,
                        b,
                        method,
                        x0=x0,
                        tolerance=self.tolerance(),
                        max_iterations=self.max_iter_spin.value(),
                        criterion=self.criterion(),
                        analysis=self.analysis,
                    )
                except ZeroDiagonalError as exc:
                    panel.show_error(exc.tracer.get_steps() if exc.tracer else [])
                    self.grid.set_alert_rows(list(exc.rows))
                    errors.append(str(exc))
                    continue
                self.results[method] = result
                panel.show_result(result)
        self._publish_summary(errors)

    # ------------------------------------------------------------------
    # Publicación
    # ------------------------------------------------------------------
    def _publish_summary(self, errors: List[str]) -> None:
        self._show_placeholders()
        exact = None
        for method, result in self.results.items():
            exact = exact or result.exact_solution
            color = _status_color(result.status)
            lines = [
                f"<b style='color:{_METHOD_COLORS[method]};'>{method.label}</b>"
                f"&nbsp;&nbsp;<span style='color:{color}; font-weight:600;'>{result.status.label}</span>"
                f"<span style='color:{COLOR_TEXT_MUTED};'> · {result.iteration_count} iteraciones</span>",
                f"<span style='font-size:15px;'>x{superscript_iter(result.iteration_count)} ≈ "
                f"<b>{format_vector(result.approximation.components)}</b></span>",
            ]
            if result.final_error is not None:
                lines.append(
                    f"<span style='color:{COLOR_TEXT_MUTED};'>Error real ‖x − x*‖∞ = "
                    f"{format_decimal(result.final_error)}</span>"
                )
            lines.append(
                f"<span style='color:{COLOR_TEXT_MUTED};'>Residuo ‖b − Ax‖∞ = {format_decimal(result.final_residual)}</span>"
            )
            self.result_labels[method].setText("<br>".join(lines))
        if errors:
            for method in self.selected_methods():
                if method not in self.results:
                    self.result_labels[method].setText(
                        f"<b style='color:{_METHOD_COLORS[method]};'>{method.label}</b>&nbsp;&nbsp;"
                        f"<span style='color:{COLOR_FEEDBACK_ERROR}; font-weight:600;'>No aplicable</span><br>"
                        "Hay un cero en la diagonal."
                    )
        if exact is not None:
            self.exact_label.setText(f"Solución exacta (Gauss-Jordan): x* = {format_vector(exact.components)}")
        elif self.results:
            self.exact_label.setText("A es singular: no hay solución única que aproximar.")

        self._refresh_plot()
        self._fill_compare_table()
        both = IterativeMethod.JACOBI in self.results and IterativeMethod.GAUSS_SEIDEL in self.results
        if both:
            summary = comparison_summary(self.results[IterativeMethod.JACOBI], self.results[IterativeMethod.GAUSS_SEIDEL])
            self.compare_summary.setText(summary)
            self.compare_summary.setVisible(True)
        if errors:
            self._set_badge(errors[0], COLOR_FEEDBACK_ERROR)
            self.tabs.setCurrentIndex(0 if IterativeMethod.JACOBI in self.selected_methods() else 1)
            return
        if not any(r.converged for r in self.results.values()):
            self._offer_reordering()
        if both:
            parts = []
            for method in IterativeMethod:
                result = self.results[method]
                if result.converged:
                    parts.append(f"{method.label} converge en {result.iteration_count} iteraciones")
                else:
                    parts.append(f"{method.label} {result.status.label.lower()}")
            self._set_badge(" · ".join(parts) + ".", self._badge_color())
            self.tabs.setCurrentIndex(2)
        else:
            (method, result), = self.results.items()
            self._set_badge(result.summary, _status_color(result.status))
            self.tabs.setCurrentIndex(0 if method is IterativeMethod.JACOBI else 1)

    def _offer_reordering(self) -> None:
        """Si ningún método converge y reordenar da dominancia, lo ofrece en un clic."""
        system = self.system()
        if system is None or (self.analysis is not None and self.analysis.strictly_dominant):
            return
        reordering = reorder_for_dominance(*system)
        if reordering is None or not reordering.changed or not reordering.strictly_dominant:
            return

        def apply() -> None:
            self.reorder_rows()
            self.iterate()

        show_toast(
            self,
            "No converge con este orden de ecuaciones, pero reordenándolas A queda diagonal dominante.",
            kind="info",
            action_text="Reordenar e iterar",
            action=apply,
            timeout_ms=9000,
        )

    def _badge_color(self) -> str:
        statuses = [r.status for r in self.results.values()]
        if all(s is IterationStatus.CONVERGED for s in statuses):
            return COLOR_FEEDBACK_SUCCESS
        if any(s is IterationStatus.CONVERGED for s in statuses):
            return COLOR_ACCENT_WARNING
        return COLOR_FEEDBACK_ERROR

    def _refresh_plot(self) -> None:
        use_error = self.error_measure_btn.isChecked()
        series = []
        for method, result in self.results.items():
            if use_error:
                points = tuple((r.k, r.error_norm) for r in result.iterations if r.error_norm is not None)
            else:
                points = tuple((r.k, r.delta_norm) for r in result.iterations if r.delta_norm is not None)
            series.append(
                PlotSeries(
                    name=method.label,
                    color=_METHOD_COLORS[method],
                    points=points,
                    status=f"{result.status.label.lower()} ({result.iteration_count})",
                )
            )
        caption = "Error real ‖x⁽ᵏ⁾ − x*‖∞" if use_error else "‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ (criterio de paro)"
        absolute = self.criterion() is StopCriterion.ABSOLUTE
        tolerance = self.tolerance() if self.results and (absolute or use_error) else None
        self.plot.set_series(series, tolerance=tolerance, y_caption=caption)

    def _fill_compare_table(self) -> None:
        methods = [m for m in IterativeMethod if m in self.results]
        table = self.compare_table
        table.clear()
        if not methods:
            table.setRowCount(0)
            table.setColumnCount(0)
            return
        analysis = self.results[methods[0]].analysis
        rows = [
            ("Estado", lambda r: r.status.label),
            ("Iteraciones", lambda r: str(r.iteration_count)),
            ("ρ(T)", lambda r: f"{analysis.spectral(r.method).radius:.4f}"),
            ("Aproximación", lambda r: format_vector(r.approximation.components, 6)),
            ("Error real ‖x − x*‖∞", lambda r: "—" if r.final_error is None else format_decimal(r.final_error)),
            ("Residuo ‖b − Ax‖∞", lambda r: format_decimal(r.final_residual)),
            ("Actualización", lambda r: "x⁽ᵏ⁾ completo" if r.method is IterativeMethod.JACOBI else "componente a componente"),
        ]
        table.setColumnCount(1 + len(methods))
        table.setHorizontalHeaderLabels(["Medida"] + [m.label for m in methods])
        table.setRowCount(len(rows))
        for row, (name, getter) in enumerate(rows):
            head = QTableWidgetItem(name)
            font = head.font()
            font.setBold(True)
            head.setFont(font)
            table.setItem(row, 0, head)
            for col, method in enumerate(methods, start=1):
                result = self.results[method]
                item = QTableWidgetItem(getter(result))
                item.setTextAlignment(Qt.AlignCenter)
                if name == "Estado":
                    item.setForeground(QColor(_status_color(result.status)))
                    bold = item.font()
                    bold.setBold(True)
                    item.setFont(bold)
                table.setItem(row, col, item)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        table.resizeRowsToContents()
        height = header.height() + sum(table.rowHeight(r) for r in range(table.rowCount())) + 6
        table.setMinimumHeight(height)
        table.setMaximumHeight(height)
