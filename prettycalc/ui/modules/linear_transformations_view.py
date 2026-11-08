"""Módulo 7: Transformaciones Lineales T: ℝⁿ → ℝᵐ.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.

Funcionalidades:
  - Pestaña 1 — Evaluación T(v) = A·v: ingresa A y v, muestra el vector imagen
    y el desglose por fila (qué múltiplos de columna se suman).
  - Pestaña 2 — Propiedades: núcleo nu(T), imagen im(T), rango, nulidad y
    verificación del Teorema de la Dimensión, con carrusel de pasos Gauss-Jordan.

Widgets reutilizados (sin modificarlos):
  DynamicMatrixGrid, AlgorithmStepperCarousel, theme, feedback, mathtext,
  module_scroll, size_control.


  En resumen:
  aquí usamos PySide6. Este archivo no calcula nada de matemáticas; solo arma la ventana, 
  recibe los números que teclea el usuario, se los manda al archivo lógico y grafica el resultado en pantalla 
  junto con el carrusel de pasos interactivo.
  
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional

try:
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSplitter,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt, QTimer
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.linear_transformations import (
    LinearTransformResult,
    compute_kernel_and_image,
    evaluate_transform,
    format_vector_set,
    kernel_summary,
    image_summary,
    theorem_summary,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.mathtext import plain_formula_to_html, to_html_subscripts
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.stepper_carousel import ALERT_NONE, AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
    apply_widget_class,
    badge_style,
    idle_badge_style,
)

__all__ = ["LinearTransformationsView"]

_MAX_DIM = 8   # dimensión máxima permitida para A

# ---------------------------------------------------------------------------
# Ejemplos cargables
# ---------------------------------------------------------------------------
_EXAMPLE1_A = Matrix([
    [1, 0, -1],
    [0, 1,  1],
    [0, 0,  0],
])
_EXAMPLE1_V = Vector([Fraction(2), Fraction(-1), Fraction(1)])
_EXAMPLE1_LABEL = "T: ℝ³→ℝ³ con núcleo no trivial"

_EXAMPLE2_A = Matrix([
    [1, -3,  0,  2],
    [-2,  6,  1, -1],
    [0,  0,  1,  3],
])
_EXAMPLE2_V = Vector([Fraction(1), Fraction(1), Fraction(1), Fraction(1)])
_EXAMPLE2_LABEL = "T: ℝ⁴→ℝ³ rectangular"

_EXAMPLE3_A = Matrix([
    [1,  0],
    [0,  1],
    [-1, 2],
])
_EXAMPLE3_V = Vector([Fraction(3), Fraction(-1)])
_EXAMPLE3_LABEL = "T: ℝ²→ℝ³ inyectiva"


# ---------------------------------------------------------------------------
# Helpers de UI
# ---------------------------------------------------------------------------

def _section_title(text: str) -> QLabel:
    """Etiqueta de sección con el estilo del design system."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-weight: 600; font-size: 18px; "
        f"color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;"
    )
    return lbl


def _info_label(html: str) -> QLabel:
    """Etiqueta de texto enriquecido, seleccionable y con ajuste de línea."""
    lbl = QLabel()
    lbl.setTextFormat(Qt.RichText)
    lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    lbl.setText(html)
    lbl.setStyleSheet(
        f"color: {COLOR_TEXT_PRIMARY}; font-size: 17px; "
        f"font-family: {FONT_FAMILY_MONO}; padding: 4px 0;"
    )
    return lbl


def _kv_html(key: str, value: str, value_color: str = COLOR_TEXT_PRIMARY) -> str:
    """Línea clave-valor en HTML para el panel de propiedades."""
    return (
        f"<span style='color:{COLOR_INTERACTIVE_IDLE}; font-weight:600; font-size:17px;'>"
        f"{key}:</span>&nbsp;&nbsp;"
        f"<span style='color:{value_color}; font-family:{FONT_FAMILY_MONO}; "
        f"font-size:18px; font-weight:600;'>{value}</span>"
    )


def _vector_html(v: Vector, label: str = "") -> str:
    """Representa un vector como [a, b, c]ᵀ en HTML compacto."""
    comps = ",  ".join(
        f"<b>{format_scalar(c, mode='fraction')}</b>" for c in v.components
    )
    if label:
        return f"<span style='color:{COLOR_INTERACTIVE_IDLE};'>{label}</span> = [{comps}]ᵀ"
    return f"[{comps}]ᵀ"


def _separator() -> QFrame:
    """Línea horizontal divisoria."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {COLOR_SURFACE_INNER};")
    return line


def _card(content_layout: QVBoxLayout) -> QFrame:
    """Tarjeta elevada con el estilo del design system."""
    card = QFrame()
    apply_widget_class(card, "elevated-card")
    card.setLayout(content_layout)
    return card


def _operand_caption(text: str) -> QLabel:
    """Rótulo pequeño sobre cada operando (A, v)."""
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 600;")
    return lbl


def _action_row(primary: QPushButton) -> QHBoxLayout:
    """Acción principal alineada a la derecha, con su ancho natural."""
    row = QHBoxLayout()
    row.addStretch(1)
    row.addWidget(primary)
    return row


# ---------------------------------------------------------------------------
# Panel de resultados de T(v)
# ---------------------------------------------------------------------------

class _TVResultPanel(QFrame):
    """Muestra T(v) = A·v con el desglose por fila."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)

        self._badge = QLabel("Esperando cálculo")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setWordWrap(True)
        self._badge.setStyleSheet(idle_badge_style())
        self._layout.addWidget(self._badge)

        self._result_area = QVBoxLayout()
        self._result_area.setSpacing(6)
        self._layout.addLayout(self._result_area)
        self._layout.addStretch(1)

    def clear(self) -> None:
        self._badge.setText("Esperando cálculo")
        self._badge.setStyleSheet(idle_badge_style())
        self._clear_results()

    def show_error(self, message: str) -> None:
        self._badge.setText("Error de dimensiones")
        self._badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
        self._clear_results()
        err = QLabel(message)
        err.setWordWrap(True)
        err.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 16px;")
        self._result_area.addWidget(err)

    def show_result(self, Tv: Vector, steps: List[str]) -> None:
        self._badge.setText("T(v) calculado ✓")
        self._badge.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS))
        self._clear_results()

        # Resultado principal
        self._result_area.addWidget(_section_title("Vector imagen T(v)"))
        comps_str = "  ".join(
            f"<b>{format_scalar(c, mode='fraction')}</b>" for c in Tv.components
        )
        result_lbl = _info_label(f"T(v) = [{comps_str}]ᵀ")
        self._result_area.addWidget(result_lbl)

        self._result_area.addWidget(_separator())

        # Desglose por fila
        self._result_area.addWidget(_section_title("Desglose fila a fila"))
        for step_text in steps:
            lbl = _info_label(plain_formula_to_html(step_text))
            self._result_area.addWidget(lbl)

    def _clear_results(self) -> None:
        while self._result_area.count():
            item = self._result_area.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()


# ---------------------------------------------------------------------------
# Panel de propiedades (núcleo, imagen, rango, nulidad, teorema)
# ---------------------------------------------------------------------------

class _PropertiesPanel(QFrame):
    """Muestra rango, nulidad, bases del núcleo y la imagen, y el Teorema."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)

        self._badge = QLabel("Esperando cálculo")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setWordWrap(True)
        self._badge.setStyleSheet(idle_badge_style())
        self._layout.addWidget(self._badge)

        self._content = QVBoxLayout()
        self._content.setSpacing(8)
        self._layout.addLayout(self._content)
        self._layout.addStretch(1)

    def clear(self) -> None:
        self._badge.setText("Esperando cálculo")
        self._badge.setStyleSheet(idle_badge_style())
        self._clear_content()

    def show_error(self, message: str) -> None:
        self._badge.setText("Error")
        self._badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
        self._clear_content()
        err = QLabel(message)
        err.setWordWrap(True)
        err.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 16px;")
        self._content.addWidget(err)

    def show_result(self, result: LinearTransformResult) -> None:
        theorem_color = COLOR_FEEDBACK_SUCCESS if result.theorem_holds else COLOR_FEEDBACK_ERROR
        self._badge.setText(
            f"Rango {result.rank}  ·  Nulidad {result.nullity}"
        )
        self._badge.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS))
        self._clear_content()

        # ── Resumen numérico ────────────────────────────────────────────
        self._content.addWidget(_section_title("Resumen"))
        for key, val, color in [
            ("Dominio", f"ℝ{self._sup(result.domain_dim)}", COLOR_TEXT_PRIMARY),
            ("Codominio", f"ℝ{self._sup(result.codomain_dim)}", COLOR_TEXT_PRIMARY),
            ("Rango  (dim im T)", str(result.rank), COLOR_FEEDBACK_SUCCESS),
            ("Nulidad  (dim nu T)", str(result.nullity), COLOR_ACCENT_WARNING),
            ("Columnas pivote", self._cols_str(result.pivot_cols), COLOR_INTERACTIVE_IDLE),
            ("Variables libres", self._cols_str(result.free_cols) or "ninguna", COLOR_ACCENT_WARNING),
        ]:
            lbl = QLabel()
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(_kv_html(key, val, color))
            self._content.addWidget(lbl)

        self._content.addWidget(_separator())

        # ── Núcleo nu(T) ────────────────────────────────────────────────
        self._content.addWidget(_section_title("Base del Núcleo  nu(T)"))
        if result.nullity == 0:
            self._content.addWidget(
                _info_label("<i>nu(T) = {<b>0</b>} — T es inyectiva</i>")
            )
        else:
            for k, vec in enumerate(result.kernel_basis, start=1):
                self._content.addWidget(
                    _info_label(_vector_html(vec, label=f"n{self._sub(k)}"))
                )

        self._content.addWidget(_separator())

        # ── Imagen im(T) ────────────────────────────────────────────────
        self._content.addWidget(_section_title("Base de la Imagen  im(T)"))
        if result.rank == 0:
            self._content.addWidget(_info_label("<i>im(T) = {<b>0</b>}</i>"))
        else:
            for k, vec in enumerate(result.image_basis, start=1):
                self._content.addWidget(
                    _info_label(_vector_html(vec, label=f"c{self._sub(k)}"))
                )

        self._content.addWidget(_separator())

        # ── Teorema de la Dimensión ─────────────────────────────────────
        self._content.addWidget(_section_title("Teorema de la Dimensión"))
        thm_text = (
            f"dim(dominio) = nulidad + rango<br>"
            f"<b>{result.domain_dim} = {result.nullity} + {result.rank}</b>"
            f"&nbsp;&nbsp;"
            f"<span style='color:{theorem_color}; font-size:20px;'>"
            f"{'✓ CUMPLE' if result.theorem_holds else '✗ ERROR'}</span>"
        )
        thm_lbl = QLabel()
        thm_lbl.setTextFormat(Qt.RichText)
        thm_lbl.setWordWrap(True)
        thm_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 18px; "
            f"font-family: {FONT_FAMILY_MONO}; padding: 6px 0;"
        )
        thm_lbl.setText(thm_text)
        self._content.addWidget(thm_lbl)

    # ── Helpers de formato ──────────────────────────────────────────────
    @staticmethod
    def _sup(n: int) -> str:
        """Superíndice Unicode para enteros pequeños."""
        sups = "⁰¹²³⁴⁵⁶⁷⁸⁹"
        return "".join(sups[int(d)] for d in str(n) if d.isdigit())

    @staticmethod
    def _sub(n: int) -> str:
        """Subíndice Unicode para enteros pequeños."""
        subs = "₀₁₂₃₄₅₆₇₈₉"
        return "".join(subs[int(d)] for d in str(n) if d.isdigit())

    @staticmethod
    def _cols_str(cols: List[int]) -> str:
        return ", ".join(str(c + 1) for c in cols) if cols else "—"

    def _clear_content(self) -> None:
        while self._content.count():
            item = self._content.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()


# ---------------------------------------------------------------------------
# Vista principal del módulo
# ---------------------------------------------------------------------------

class LinearTransformationsView(QWidget):
    """Módulo 7: Transformaciones Lineales — evaluación y propiedades."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("linearTransformationsView")
        self._last_result: Optional[LinearTransformResult] = None
        self._setup_ui()
        # Conectar señales
        self.grid_A.matrixChanged.connect(self._on_matrix_changed)
        self.grid_A.submitRequested.connect(self.compute_tv)
        self.grid_v.submitRequested.connect(self.compute_tv)
        self.grid_props_A.matrixChanged.connect(self._on_props_matrix_changed)
        self.grid_props_A.submitRequested.connect(self.compute_properties)
        # Sincronizar tamaños iniciales
        self._sync_v_size()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # ── Layout raíz con scroll ──────────────────────────────────────
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ── Barra de controles superiores ───────────────────────────────
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self.reset_btn = QPushButton("Reiniciar")
        self.reset_btn.setObjectName("secondaryAction")
        self.reset_btn.setToolTip("Limpia todas las entradas")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset)

        examples_caption = QLabel("Ejemplos")
        examples_caption.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 600;")

        self.ex1_btn = QPushButton("ℝ³ → ℝ³  ·  núcleo no trivial")
        self.ex1_btn.setObjectName("secondaryAction")
        self.ex1_btn.setToolTip(_EXAMPLE1_LABEL)
        self.ex1_btn.setCursor(Qt.PointingHandCursor)
        self.ex1_btn.clicked.connect(self.load_example_1)

        self.ex2_btn = QPushButton("ℝ⁴ → ℝ³  ·  rectangular")
        self.ex2_btn.setObjectName("secondaryAction")
        self.ex2_btn.setToolTip(_EXAMPLE2_LABEL)
        self.ex2_btn.setCursor(Qt.PointingHandCursor)
        self.ex2_btn.clicked.connect(self.load_example_2)

        self.ex3_btn = QPushButton("ℝ² → ℝ³  ·  inyectiva")
        self.ex3_btn.setObjectName("secondaryAction")
        self.ex3_btn.setToolTip(_EXAMPLE3_LABEL)
        self.ex3_btn.setCursor(Qt.PointingHandCursor)
        self.ex3_btn.clicked.connect(self.load_example_3)

        # Mismo patrón que los demás módulos: ejemplos a la izquierda con su
        # rótulo descriptivo y el reinicio a la derecha.
        controls_row.addWidget(examples_caption)
        controls_row.addWidget(self.ex1_btn)
        controls_row.addWidget(self.ex2_btn)
        controls_row.addWidget(self.ex3_btn)
        controls_row.addStretch(1)
        controls_row.addWidget(self.reset_btn)
        root.addLayout(controls_row)

        # ── Pestañas ────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setObjectName("ltTabs")

        # Pestaña 1: Evaluación T(v)
        tab_tv = QWidget()
        self._setup_tab_tv(tab_tv)
        self._tabs.addTab(tab_tv, "T(v) = A · v")

        # Pestaña 2: Propiedades
        tab_props = QWidget()
        self._setup_tab_props(tab_props)
        self._tabs.addTab(tab_props, "Propiedades  (nu T · im T · rango)")

        root.addWidget(self._tabs, stretch=1)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("ltScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.viewport().setAutoFillBackground(False)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.scroll_area, stretch=1)

    # ── Pestaña 1: T(v) ─────────────────────────────────────────────────

    def _setup_tab_tv(self, parent: QWidget) -> None:
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Panel izquierdo: entradas A y v, lado a lado como en el papel (A · v)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)
        left = _card(left_layout)
        left.setMaximumWidth(560)

        left_layout.addWidget(_section_title("Evaluar  T(v) = A · v"))
        self.grid_A = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.size_control_tv = MatrixSizeControl(
            self.grid_A,
            rows_label="Filas  m",
            cols_label="Columnas  n",
            caption="Tamaño de A",
            minimum=1,
            maximum=_MAX_DIM,
        )
        self.size_control_tv.sizeChanged.connect(self._sync_v_size)
        left_layout.addWidget(self.size_control_tv)

        operands = QHBoxLayout()
        operands.setSpacing(10)
        a_box = QVBoxLayout()
        a_box.addWidget(_operand_caption("Matriz  A  (m × n)"))
        a_box.addWidget(self.grid_A, 1)
        operands.addLayout(a_box, 3)
        dot = QLabel("·")
        dot.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {COLOR_INTERACTIVE_IDLE}; padding: 0 4px;")
        operands.addWidget(dot, 0, Qt.AlignCenter)
        self.grid_v = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=1,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
            show_headers=False,
        )
        v_box = QVBoxLayout()
        v_box.addWidget(_operand_caption("Vector  v"))
        v_box.addWidget(self.grid_v, 1)
        operands.addLayout(v_box, 1)
        left_layout.addLayout(operands, 1)

        self.compute_tv_btn = QPushButton("Calcular  T(v)")
        self.compute_tv_btn.setObjectName("primaryAction")
        self.compute_tv_btn.setToolTip("Calcula T(v) = A · v  (Ctrl+Intro)")
        self.compute_tv_btn.setCursor(Qt.PointingHandCursor)
        self.compute_tv_btn.clicked.connect(self.compute_tv)
        left_layout.addLayout(_action_row(self.compute_tv_btn))

        # Panel derecho: resultado T(v)
        self._tv_result = _TVResultPanel()

        layout.addWidget(left, 0, Qt.AlignTop)
        layout.addWidget(self._tv_result, stretch=1)

    # ── Pestaña 2: Propiedades ───────────────────────────────────────────

    def _setup_tab_props(self, parent: QWidget) -> None:
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Panel izquierdo: entrada A
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)
        left = _card(left_layout)
        left.setMaximumWidth(480)

        left_layout.addWidget(_section_title("Matriz de transformación  A  (m × n)"))
        self.grid_props_A = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.size_control_props = MatrixSizeControl(
            self.grid_props_A,
            rows_label="Filas  m",
            cols_label="Columnas  n",
            caption="Tamaño de A",
            minimum=1,
            maximum=_MAX_DIM,
        )
        left_layout.addWidget(self.size_control_props)
        left_layout.addWidget(self.grid_props_A)

        self.compute_props_btn = QPushButton("Calcular  nu(T) · im(T) · rango")
        self.compute_props_btn.setObjectName("primaryAction")
        self.compute_props_btn.setToolTip("Aplica Gauss-Jordan y determina las propiedades de T  (Ctrl+Intro)")
        self.compute_props_btn.setCursor(Qt.PointingHandCursor)
        self.compute_props_btn.clicked.connect(self.compute_properties)
        left_layout.addStretch(1)
        left_layout.addLayout(_action_row(self.compute_props_btn))

        # Panel derecho: propiedades + carrusel
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self._props_panel = _PropertiesPanel()
        right_layout.addWidget(self._props_panel)

        # Carrusel de pasos Gauss-Jordan
        carousel_title = _section_title("Procedimiento paso a paso — reducción de A a RREF")
        right_layout.addWidget(carousel_title)

        self.stepper = AlgorithmStepperCarousel(
            alert_mode=ALERT_NONE,
            variable_headers=False,
        )
        self.stepper.set_empty_hint(
            "Ingresa la matriz A y pulsa «Calcular» para ver los pasos."
        )
        self.stepper.set_export_title("RREF de A — Transformación Lineal")
        self.stepper.setMinimumHeight(380)
        right_layout.addWidget(self.stepper)
        right_layout.addStretch(1)

        layout.addWidget(left, 0, Qt.AlignTop)
        layout.addWidget(right, stretch=1)

    # ------------------------------------------------------------------
    # Lógica de cálculo
    # ------------------------------------------------------------------

    def compute_tv(self) -> None:
        """Pestaña 1: calcula T(v) = A · v."""
        try:
            A = self._read_matrix(self.grid_A)
            v = self._read_vector(self.grid_v)
        except ValueError as exc:
            self._tv_result.show_error(str(exc))
            show_toast(self, str(exc), kind="error")
            return

        try:
            Tv, steps = evaluate_transform(A, v)
        except DimensionMismatchError as exc:
            self._tv_result.show_error(str(exc))
            show_toast(self, "Dimensiones incompatibles.", kind="error")
            return
        except Exception as exc:  # noqa: BLE001
            self._tv_result.show_error(f"Error inesperado: {exc}")
            return

        self._tv_result.show_result(Tv, steps)
        show_toast(self, "T(v) calculado.", kind="success")

    def compute_properties(self) -> None:
        """Pestaña 2: calcula núcleo, imagen, rango y nulidad de T."""
        try:
            A = self._read_matrix(self.grid_props_A)
        except ValueError as exc:
            self._props_panel.show_error(str(exc))
            show_toast(self, str(exc), kind="error")
            return

        try:
            result = compute_kernel_and_image(A)
        except Exception as exc:  # noqa: BLE001
            self._props_panel.show_error(f"Error inesperado: {exc}")
            return

        self._last_result = result
        self._props_panel.show_result(result)
        self.stepper.set_steps(result.tracer.get_steps())
        show_toast(
            self,
            f"Rango = {result.rank},  Nulidad = {result.nullity}.",
            kind="success",
        )

    # ------------------------------------------------------------------
    # Carga de ejemplos
    # ------------------------------------------------------------------

    def _load_example(
        self,
        A: Matrix,
        v: Vector,
        label: str,
    ) -> None:
        """Carga una matriz y un vector en ambas pestañas."""
        # Pestaña T(v)
        self.grid_A.set_matrix(A)
        self._sync_v_size()
        self._fill_vector_grid(self.grid_v, v)
        self.grid_A.flash()

        # Pestaña Propiedades (misma A)
        self.grid_props_A.set_matrix(A)
        self.grid_props_A.flash()

        show_toast(self, f"Ejemplo cargado: {label}", kind="info")

    def load_example_1(self) -> None:
        self._load_example(_EXAMPLE1_A, _EXAMPLE1_V, _EXAMPLE1_LABEL)

    def load_example_2(self) -> None:
        self._load_example(_EXAMPLE2_A, _EXAMPLE2_V, _EXAMPLE2_LABEL)

    def load_example_3(self) -> None:
        self._load_example(_EXAMPLE3_A, _EXAMPLE3_V, _EXAMPLE3_LABEL)

    # ------------------------------------------------------------------
    # Reinicio
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Restaura todas las entradas a cero y limpia los resultados."""
        for grid in (self.grid_A, self.grid_v, self.grid_props_A):
            grid.checkpoint()
            grid.resize_to(3, 3 if grid is not self.grid_v else 1)
        self._tv_result.clear()
        self._props_panel.clear()
        self._last_result = None
        self.stepper.set_steps([])
        show_toast(self, "Vista reiniciada.", kind="info")

    # ------------------------------------------------------------------
    # Sincronización de dimensiones
    # ------------------------------------------------------------------

    def _on_matrix_changed(self) -> None:
        """Sincroniza la longitud del vector v con las columnas de A."""
        self._sync_v_size()

    def _on_props_matrix_changed(self) -> None:
        pass  # reservado para validaciones futuras

    def _sync_v_size(self) -> None:
        """El vector v debe tener tantas filas como columnas tiene A."""
        n = self.grid_A.num_vars  # columnas de A (no augmented → num_vars = cols)
        if self.grid_v.num_rows != n:
            self.grid_v.resize_to(n, 1)

    # ------------------------------------------------------------------
    # Helpers de lectura de grids
    # ------------------------------------------------------------------

    @staticmethod
    def _read_matrix(grid: DynamicMatrixGrid) -> Matrix:
        """Lee la cuadrícula y construye una Matrix. Lanza ValueError si hay celdas inválidas."""
        msg = grid.validation_message()
        if msg:
            raise ValueError(f"Entrada inválida: {msg}")
        rows = []
        for row_cells in grid.cells:
            rows.append([cell.get_value() for cell in row_cells])
        return Matrix(rows)

    @staticmethod
    def _read_vector(grid: DynamicMatrixGrid) -> Vector:
        """Lee la cuadrícula de una sola columna y construye un Vector."""
        msg = grid.validation_message()
        if msg:
            raise ValueError(f"Entrada inválida: {msg}")
        components = [grid.cells[r][0].get_value() for r in range(grid.num_rows)]
        return Vector(components)

    # ------------------------------------------------------------------
    # Helpers de escritura de grids
    # ------------------------------------------------------------------

    @staticmethod
    def _fill_grid(grid: DynamicMatrixGrid, A: Matrix) -> None:
        """Escribe los valores de la matriz A en la cuadrícula."""
        for r in range(min(A.rows, grid.num_rows)):
            for c in range(min(A.cols, len(grid.cells[r]))):
                grid.cells[r][c].setText(format_scalar(A.get(r, c), mode="fraction"))

    @staticmethod
    def _fill_vector_grid(grid: DynamicMatrixGrid, v: Vector) -> None:
        """Escribe los componentes del vector v en la cuadrícula de una columna."""
        for r in range(min(v.dimension, grid.num_rows)):
            grid.cells[r][0].setText(format_scalar(v[r], mode="fraction"))

