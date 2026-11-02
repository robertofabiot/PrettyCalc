"""Módulo 8: Espacios Vectoriales — Conjuntos Generadores, Bases y Dimensión.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Autores / Grupo: Grupo 4.

Funcionalidades:
  - Pestaña 1 — Conjunto Generador: ingresa vectores como columnas de A,
    determina si generan ℝᵐ mediante la RREF y muestra el rango.
  - Pestaña 2 — Base y Dimensión: ingresa los coeficientes del sistema
    homogéneo Ax = 0, extrae la base del espacio nulo y su dimensión.

Widgets reutilizados (sin modificarlos):
  DynamicMatrixGrid, MatrixSizeControl, AlgorithmStepperCarousel,
  theme, feedback, mathtext.

En resumen:
este archivo arma la ventana de los Espacios Vectoriales. Lo más destacable aquí a nivel de programación 
es que reciclamos los mismos componentes de interfaz (como la cuadrícula y el carrusel de Gauss-Jordan) 
del módulo anterior, manteniendo un código limpio y una arquitectura profesional.

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
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.core.vector_spaces import (
    GeneratingSetResult,
    SubspaceBasisResult,
    check_generating_set,
    compute_subspace_basis,
    format_basis_vectors,
    generating_summary,
    subspace_summary,
)
from prettycalc.core.types import Matrix, Vector, format_scalar
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.mathtext import plain_formula_to_html
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

__all__ = ["VectorSpacesView"]

_MAX_DIM = 8   # dimensión máxima permitida


# ---------------------------------------------------------------------------
# Ejemplos cargables
# ---------------------------------------------------------------------------

# Ejemplo 1: 3 vectores en ℝ³ que SÍ generan ℝ³
_EX1_GEN_A = Matrix([
    [1, 0, 2],
    [0, 1, -1],
    [0, 0, 1],
])
_EX1_GEN_LABEL = "3 vectores en ℝ³ que generan ℝ³"

# Ejemplo 2: 2 vectores en ℝ³ que NO generan ℝ³ (rango 2 < 3)
_EX2_GEN_A = Matrix([
    [1,  2],
    [-1, 0],
    [2,  4],
])
_EX2_GEN_LABEL = "2 vectores en ℝ³ — NO generan ℝ³"

# Ejemplo 3: Subespacio de ℝ⁴ definido por 2 ecuaciones (nulidad = 2)
_EX1_SUB_A = Matrix([
    [1, -2,  1,  0],
    [2, -4,  0,  2],
])
_EX1_SUB_LABEL = "Subespacio de ℝ⁴ — dim = 2"

# Ejemplo 4: Solo el vector cero (rango completo → espacio trivial)
_EX2_SUB_A = Matrix([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
])
_EX2_SUB_LABEL = "Subespacio trivial {0} en ℝ³"


# ---------------------------------------------------------------------------
# Helpers de UI (locales, sin modificar widgets compartidos)
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
    """Línea clave-valor en HTML para el panel de resultados."""
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


def _sup(n: int) -> str:
    """Superíndice Unicode para enteros pequeños."""
    sups = "⁰¹²³⁴⁵⁶⁷⁸⁹"
    return "".join(sups[int(d)] for d in str(n) if d.isdigit())


def _sub(n: int) -> str:
    """Subíndice Unicode para enteros pequeños."""
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return "".join(subs[int(d)] for d in str(n) if d.isdigit())


def _cols_str(cols: List[int]) -> str:
    return ", ".join(str(c + 1) for c in cols) if cols else "—"


# ---------------------------------------------------------------------------
# Panel de resultados — Conjunto Generador
# ---------------------------------------------------------------------------

class _GeneratingSetPanel(QFrame):
    """Muestra si el conjunto de vectores genera ℝᵐ con detalles de rango."""

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

    def show_result(self, result: GeneratingSetResult) -> None:
        gen_color = COLOR_FEEDBACK_SUCCESS if result.generates else COLOR_FEEDBACK_ERROR
        gen_text = "SÍ GENERA" if result.generates else "NO GENERA"

        self._badge.setText(
            f"Rango = {result.rank}  ·  ℝ{_sup(result.n_rows)}  →  {gen_text}"
        )
        self._badge.setStyleSheet(badge_style(gen_color))
        self._clear_content()

        # ── Resumen numérico ────────────────────────────────────────────
        self._content.addWidget(_section_title("Resumen"))
        for key, val, color in [
            ("Número de vectores", str(result.n_cols), COLOR_TEXT_PRIMARY),
            ("Dimensión del espacio", f"ℝ{_sup(result.n_rows)}  (m = {result.n_rows})", COLOR_TEXT_PRIMARY),
            ("Rango de A", str(result.rank), COLOR_FEEDBACK_SUCCESS),
            ("Columnas pivote", _cols_str(result.pivot_cols), COLOR_INTERACTIVE_IDLE),
        ]:
            lbl = QLabel()
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(_kv_html(key, val, color))
            self._content.addWidget(lbl)

        self._content.addWidget(_separator())

        # ── Conclusión ──────────────────────────────────────────────────
        self._content.addWidget(_section_title("Conclusión"))
        if result.generates:
            concl_html = (
                f"<span style='font-size:17px; font-family:{FONT_FAMILY_MONO};'>"
                f"rango(A) = <b>{result.rank}</b> = m = <b>{result.n_rows}</b><br>"
                f"<span style='color:{COLOR_FEEDBACK_SUCCESS}; font-size:19px;'>"
                f"✓ El conjunto <b>SÍ genera ℝ{_sup(result.n_rows)}</b>.</span><br>"
                f"Toda fila de la RREF tiene pivote → ninguna ecuación es incompatible."
                f"</span>"
            )
        else:
            concl_html = (
                f"<span style='font-size:17px; font-family:{FONT_FAMILY_MONO};'>"
                f"rango(A) = <b>{result.rank}</b> &lt; m = <b>{result.n_rows}</b><br>"
                f"<span style='color:{COLOR_FEEDBACK_ERROR}; font-size:19px;'>"
                f"✗ El conjunto <b>NO genera ℝ{_sup(result.n_rows)}</b>.</span><br>"
                f"Existen {result.n_rows - result.rank} fila(s) nula(s) en la RREF → "
                f"hay direcciones de ℝ{_sup(result.n_rows)} no cubiertas."
                f"</span>"
            )
        concl_lbl = QLabel()
        concl_lbl.setTextFormat(Qt.RichText)
        concl_lbl.setWordWrap(True)
        concl_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 17px; "
            f"font-family: {FONT_FAMILY_MONO}; padding: 6px 0;"
        )
        concl_lbl.setText(concl_html)
        self._content.addWidget(concl_lbl)

    def _clear_content(self) -> None:
        while self._content.count():
            item = self._content.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()


# ---------------------------------------------------------------------------
# Panel de resultados — Base y Dimensión
# ---------------------------------------------------------------------------

class _SubspaceBasisPanel(QFrame):
    """Muestra la base del subespacio definido por Ax = 0 y su dimensión."""

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

    def show_result(self, result: SubspaceBasisResult) -> None:
        dim_color = (
            COLOR_TEXT_PRIMARY if result.dimension > 0 else COLOR_ACCENT_WARNING
        )
        self._badge.setText(
            f"Dimensión = {result.dimension}  ·  Rango = {result.n_vars - result.dimension}"
        )
        self._badge.setStyleSheet(badge_style(COLOR_FEEDBACK_SUCCESS))
        self._clear_content()

        # ── Resumen numérico ────────────────────────────────────────────
        self._content.addWidget(_section_title("Resumen"))
        for key, val, color in [
            ("Variables / dimensión ambiente", f"n = {result.n_vars}", COLOR_TEXT_PRIMARY),
            ("Rango de A", str(result.n_vars - result.dimension), COLOR_FEEDBACK_SUCCESS),
            ("Nulidad (dim del subespacio)", str(result.dimension), dim_color),
            ("Columnas pivote", _cols_str(result.pivot_cols), COLOR_INTERACTIVE_IDLE),
            ("Variables libres", _cols_str(result.free_cols) if result.free_cols else "ninguna", COLOR_ACCENT_WARNING),
        ]:
            lbl = QLabel()
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(_kv_html(key, val, color))
            self._content.addWidget(lbl)

        self._content.addWidget(_separator())

        # ── Base del subespacio ─────────────────────────────────────────
        self._content.addWidget(_section_title("Base del Subespacio  (Ker A)"))
        if result.dimension == 0:
            self._content.addWidget(
                _info_label("<i>Ker(A) = {<b>0</b>} — la única solución es el vector cero.</i>")
            )
        else:
            for k, vec in enumerate(result.basis, start=1):
                self._content.addWidget(
                    _info_label(_vector_html(vec, label=f"b{_sub(k)}"))
                )

        self._content.addWidget(_separator())

        # ── Verificación dim + rango = n ────────────────────────────────
        self._content.addWidget(_section_title("Teorema de la Dimensión"))
        rank = result.n_vars - result.dimension
        thm_html = (
            f"dim(Ker A) + rango(A) = n<br>"
            f"<b>{result.dimension} + {rank} = {result.n_vars}</b>"
            f"&nbsp;&nbsp;"
            f"<span style='color:{COLOR_FEEDBACK_SUCCESS}; font-size:20px;'>✓</span>"
        )
        thm_lbl = QLabel()
        thm_lbl.setTextFormat(Qt.RichText)
        thm_lbl.setWordWrap(True)
        thm_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 18px; "
            f"font-family: {FONT_FAMILY_MONO}; padding: 6px 0;"
        )
        thm_lbl.setText(thm_html)
        self._content.addWidget(thm_lbl)

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

class VectorSpacesView(QWidget):
    """Módulo 8: Espacios Vectoriales — Conjuntos Generadores, Bases y Dimensión."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("vectorSpacesView")
        self._last_gen_result: Optional[GeneratingSetResult] = None
        self._last_sub_result: Optional[SubspaceBasisResult] = None
        self._setup_ui()
        # Conectar señales
        self.grid_gen.matrixChanged.connect(self._on_gen_matrix_changed)
        self.grid_gen.submitRequested.connect(self.compute_generating_set)
        self.grid_sub.matrixChanged.connect(self._on_sub_matrix_changed)
        self.grid_sub.submitRequested.connect(self.compute_subspace_basis)

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # Layout raíz horizontal: izquierda pestañas, derecha scroll de resultados
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ── Panel izquierdo: controles ──────────────────────────────────
        left_container = QWidget()
        left_container.setMaximumWidth(500)
        left_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_vbox = QVBoxLayout(left_container)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(8)

        # Barra de botones superiores
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.reset_btn = QPushButton("Reiniciar")
        self.reset_btn.setObjectName("secondaryAction")
        self.reset_btn.setToolTip("Limpia todas las entradas")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch(1)

        # Botones de ejemplos — Generador
        self.ex_gen1_btn = QPushButton("Ej Gen 1")
        self.ex_gen1_btn.setObjectName("secondaryAction")
        self.ex_gen1_btn.setToolTip(_EX1_GEN_LABEL)
        self.ex_gen1_btn.setCursor(Qt.PointingHandCursor)
        self.ex_gen1_btn.clicked.connect(self.load_example_gen1)
        btn_row.addWidget(self.ex_gen1_btn)

        self.ex_gen2_btn = QPushButton("Ej Gen 2")
        self.ex_gen2_btn.setObjectName("secondaryAction")
        self.ex_gen2_btn.setToolTip(_EX2_GEN_LABEL)
        self.ex_gen2_btn.setCursor(Qt.PointingHandCursor)
        self.ex_gen2_btn.clicked.connect(self.load_example_gen2)
        btn_row.addWidget(self.ex_gen2_btn)

        # Botones de ejemplos — Subespacio
        self.ex_sub1_btn = QPushButton("Ej Base 1")
        self.ex_sub1_btn.setObjectName("secondaryAction")
        self.ex_sub1_btn.setToolTip(_EX1_SUB_LABEL)
        self.ex_sub1_btn.setCursor(Qt.PointingHandCursor)
        self.ex_sub1_btn.clicked.connect(self.load_example_sub1)
        btn_row.addWidget(self.ex_sub1_btn)

        self.ex_sub2_btn = QPushButton("Ej Base 2")
        self.ex_sub2_btn.setObjectName("secondaryAction")
        self.ex_sub2_btn.setToolTip(_EX2_SUB_LABEL)
        self.ex_sub2_btn.setCursor(Qt.PointingHandCursor)
        self.ex_sub2_btn.clicked.connect(self.load_example_sub2)
        btn_row.addWidget(self.ex_sub2_btn)

        left_vbox.addLayout(btn_row)

        # ── Pestañas ────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setObjectName("vsTabs")

        # Pestaña 1: Conjunto Generador
        tab_gen = QWidget()
        self._setup_tab_gen(tab_gen)
        self._tabs.addTab(tab_gen, "Conjunto Generador")

        # Pestaña 2: Base y Dimensión
        tab_sub = QWidget()
        self._setup_tab_sub(tab_sub)
        self._tabs.addTab(tab_sub, "Base  ·  Dimensión")

        # Conectar cambio de pestaña para limpiar hint del stepper
        self._tabs.currentChanged.connect(self._on_tab_changed)

        left_vbox.addWidget(self._tabs, stretch=1)
        root.addWidget(left_container)

        # ── Panel derecho: resultados + stepper ─────────────────────────
        # Usar QScrollArea PLAIN (no make_module_scroll) con ScrollBarAlwaysOn
        # para evitar el bucle de redimensionado que causa parpadeo.
        content_widget = QWidget()
        right_layout = QVBoxLayout(content_widget)
        right_layout.setContentsMargins(8, 4, 8, 8)
        right_layout.setSpacing(10)

        # Panel de resultado activo (swap entre los dos paneles)
        self._gen_panel = _GeneratingSetPanel()
        self._sub_panel = _SubspaceBasisPanel()
        right_layout.addWidget(self._gen_panel)
        right_layout.addWidget(self._sub_panel)
        self._sub_panel.hide()  # solo uno visible a la vez

        # Carrusel de pasos Gauss-Jordan
        carousel_title = _section_title("Procedimiento paso a paso — reducción a RREF")
        right_layout.addWidget(carousel_title)

        self.stepper = AlgorithmStepperCarousel(
            alert_mode=ALERT_NONE,
            variable_headers=False,
        )
        self.stepper.set_empty_hint(
            "Ingresa los datos en la pestaña izquierda y pulsa «Calcular» para ver los pasos."
        )
        self.stepper.set_export_title("RREF — Espacios Vectoriales")
        self.stepper.setMinimumHeight(380)
        right_layout.addWidget(self.stepper)
        right_layout.addStretch(1)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("vsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.viewport().setAutoFillBackground(False)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidget(content_widget)

        root.addWidget(self.scroll_area, stretch=1)

    # ── Pestaña 1: Conjunto Generador ───────────────────────────────────

    def _setup_tab_gen(self, parent: QWidget) -> None:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        layout.addWidget(
            _section_title("Vectores del conjunto  (columnas de A, m × k)")
        )

        # IMPORTANTE: Instanciar el grid ANTES de MatrixSizeControl
        self.grid_gen = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.size_control_gen = MatrixSizeControl(
            self.grid_gen,
            rows_label="Filas  m",
            cols_label="Vectores  k",
            caption="Tamaño",
            minimum=1,
            maximum=_MAX_DIM,
        )
        layout.addWidget(self.size_control_gen)
        layout.addWidget(self.grid_gen)

        hint = QLabel(
            "<i>Cada columna es un vector. Se verifica si generan ℝᵐ (m = número de filas).</i>"
        )
        hint.setTextFormat(Qt.RichText)
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(hint)

        self.compute_gen_btn = QPushButton("Calcular  —  ¿Genera ℝᵐ?")
        self.compute_gen_btn.setObjectName("primaryAction")
        self.compute_gen_btn.setToolTip("Aplica Gauss-Jordan y verifica si rango = m  (Ctrl+Intro)")
        self.compute_gen_btn.setCursor(Qt.PointingHandCursor)
        self.compute_gen_btn.clicked.connect(self.compute_generating_set)
        layout.addWidget(self.compute_gen_btn)
        layout.addStretch(1)

    # ── Pestaña 2: Base y Dimensión ─────────────────────────────────────

    def _setup_tab_sub(self, parent: QWidget) -> None:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        layout.addWidget(
            _section_title("Sistema homogéneo  Ax = 0  (filas = ecuaciones)")
        )

        # IMPORTANTE: Instanciar el grid ANTES de MatrixSizeControl
        self.grid_sub = DynamicMatrixGrid(
            initial_rows=2,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.size_control_sub = MatrixSizeControl(
            self.grid_sub,
            rows_label="Ecuaciones  m",
            cols_label="Variables  n",
            caption="Tamaño",
            minimum=1,
            maximum=_MAX_DIM,
        )
        layout.addWidget(self.size_control_sub)
        layout.addWidget(self.grid_sub)

        hint = QLabel(
            "<i>Cada fila es una ecuación homogénea. "
            "Se calcula la base del espacio solución (Ker A).</i>"
        )
        hint.setTextFormat(Qt.RichText)
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(hint)

        self.compute_sub_btn = QPushButton("Calcular  —  Base del Subespacio")
        self.compute_sub_btn.setObjectName("primaryAction")
        self.compute_sub_btn.setToolTip("Aplica Gauss-Jordan y extrae la base de Ker(A)  (Ctrl+Intro)")
        self.compute_sub_btn.setCursor(Qt.PointingHandCursor)
        self.compute_sub_btn.clicked.connect(self.compute_subspace_basis)
        layout.addWidget(self.compute_sub_btn)
        layout.addStretch(1)

    # ------------------------------------------------------------------
    # Lógica de cálculo
    # ------------------------------------------------------------------

    def compute_generating_set(self) -> None:
        """Pestaña 1: verifica si el conjunto de vectores genera ℝᵐ."""
        try:
            A = self._read_matrix(self.grid_gen)
        except ValueError as exc:
            self._gen_panel.show_error(str(exc))
            show_toast(self, str(exc), kind="error")
            return

        try:
            result = check_generating_set(A)
        except Exception as exc:  # noqa: BLE001
            self._gen_panel.show_error(f"Error inesperado: {exc}")
            return

        self._last_gen_result = result
        self._gen_panel.show_result(result)
        self.stepper.set_steps(result.tracer.get_steps())
        self.stepper.set_export_title("RREF — Conjunto Generador")

        gen_str = "SÍ genera" if result.generates else "NO genera"
        show_toast(
            self,
            f"Rango = {result.rank}  (m = {result.n_rows})  →  {gen_str} ℝ{_sup(result.n_rows)}.",
            kind="success" if result.generates else "error",
        )

    def compute_subspace_basis(self) -> None:
        """Pestaña 2: calcula la base del subespacio Ax = 0."""
        try:
            A = self._read_matrix(self.grid_sub)
        except ValueError as exc:
            self._sub_panel.show_error(str(exc))
            show_toast(self, str(exc), kind="error")
            return

        try:
            result = compute_subspace_basis(A)
        except Exception as exc:  # noqa: BLE001
            self._sub_panel.show_error(f"Error inesperado: {exc}")
            return

        self._last_sub_result = result
        self._sub_panel.show_result(result)
        self.stepper.set_steps(result.tracer.get_steps())
        self.stepper.set_export_title("RREF — Base del Subespacio")

        show_toast(
            self,
            f"Dimensión del subespacio = {result.dimension}.",
            kind="success",
        )

    # ------------------------------------------------------------------
    # Cambio de pestaña
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index: int) -> None:
        """Muestra el panel de resultados correspondiente a la pestaña activa."""
        if index == 0:
            self._gen_panel.show()
            self._sub_panel.hide()
            # Restaurar pasos del último cálculo de generador (si existe)
            if self._last_gen_result is not None:
                self.stepper.set_steps(self._last_gen_result.tracer.get_steps())
                self.stepper.set_export_title("RREF — Conjunto Generador")
            else:
                self.stepper.set_steps([])
        else:
            self._gen_panel.hide()
            self._sub_panel.show()
            # Restaurar pasos del último cálculo de subespacio (si existe)
            if self._last_sub_result is not None:
                self.stepper.set_steps(self._last_sub_result.tracer.get_steps())
                self.stepper.set_export_title("RREF — Base del Subespacio")
            else:
                self.stepper.set_steps([])

    # ------------------------------------------------------------------
    # Carga de ejemplos
    # ------------------------------------------------------------------

    def load_example_gen1(self) -> None:
        """Carga: 3 vectores en ℝ³ que SÍ generan."""
        self._tabs.setCurrentIndex(0)
        self.grid_gen.set_matrix(_EX1_GEN_A)
        self.grid_gen.flash()
        show_toast(self, f"Ejemplo cargado: {_EX1_GEN_LABEL}", kind="info")

    def load_example_gen2(self) -> None:
        """Carga: 2 vectores en ℝ³ que NO generan."""
        self._tabs.setCurrentIndex(0)
        self.grid_gen.set_matrix(_EX2_GEN_A)
        self.grid_gen.flash()
        show_toast(self, f"Ejemplo cargado: {_EX2_GEN_LABEL}", kind="info")

    def load_example_sub1(self) -> None:
        """Carga: subespacio de ℝ⁴ con dimensión 2."""
        self._tabs.setCurrentIndex(1)
        self.grid_sub.set_matrix(_EX1_SUB_A)
        self.grid_sub.flash()
        show_toast(self, f"Ejemplo cargado: {_EX1_SUB_LABEL}", kind="info")

    def load_example_sub2(self) -> None:
        """Carga: subespacio trivial {0} en ℝ³."""
        self._tabs.setCurrentIndex(1)
        self.grid_sub.set_matrix(_EX2_SUB_A)
        self.grid_sub.flash()
        show_toast(self, f"Ejemplo cargado: {_EX2_SUB_LABEL}", kind="info")

    # ------------------------------------------------------------------
    # Reinicio
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Restaura todas las entradas a cero y limpia los resultados."""
        self.grid_gen.checkpoint()
        self.grid_gen.resize_to(3, 3)
        self.grid_sub.checkpoint()
        self.grid_sub.resize_to(2, 3)
        self._gen_panel.clear()
        self._sub_panel.clear()
        self._last_gen_result = None
        self._last_sub_result = None
        self.stepper.set_steps([])
        show_toast(self, "Vista reiniciada.", kind="info")

    # ------------------------------------------------------------------
    # Señales de cambio de matriz (reservadas para validaciones futuras)
    # ------------------------------------------------------------------

    def _on_gen_matrix_changed(self) -> None:
        pass

    def _on_sub_matrix_changed(self) -> None:
        pass

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

