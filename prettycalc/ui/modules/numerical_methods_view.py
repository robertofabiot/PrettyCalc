"""Módulo 9: Métodos Numéricos — vista PySide6.



RESUMEN — qué hace este archivo (solo interfaz; QTabWidget de 4 pestañas):
  1. Bisección           — captura f(x), a, b, E, max_iter; llena la tabla
                           de iteraciones y muestra teórico vs SciPy.
  2. Graficador          — grafica f(x) dentro de la app (matplotlib).
  3. Notación Posicional — muestra la descomposición en base 10 y base 2.
  4. Errores Numéricos   — teoría, propagación de error y error abs/rel/%.

RESTRICCIONES:
  - No contiene lógica matemática: toda ella vive en core/numerical_methods.py.
  - No usa eval(); el texto de f(x) se entrega al core, que lo parsea con sympy.
  - Solo formatea y presenta los resultados (p. ej. Eβ y εₐ con 6 decimales).
"""

from __future__ import annotations

import math
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSpinBox,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

# Matplotlib embedding
try:
    import matplotlib
    matplotlib.use("QtAgg")  # backend compatible con PySide6
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    _MPL_OK = True
except ImportError:  # pragma: no cover
    _MPL_OK = False

try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:  # pragma: no cover
    _NUMPY_OK = False

from prettycalc.core.numerical_methods import (
    bisection,
    compute_plot_data,
    compute_positional,
    propagate_error,
    compute_numerical_error,
    BisectionResult,
)
from prettycalc.ui.feedback import show_toast
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

__all__ = ["NumericalMethodsView"]

# ---------------------------------------------------------------------------
# Helpers de UI compartidos
# ---------------------------------------------------------------------------

def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-weight: 600; font-size: 17px; "
        f"color: {COLOR_TEXT_PRIMARY}; margin-top: 6px;"
    )
    return lbl


def _mono_label(html: str = "", selectable: bool = True) -> QLabel:
    lbl = QLabel()
    lbl.setTextFormat(Qt.RichText)
    lbl.setWordWrap(True)
    if selectable:
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    lbl.setText(html)
    lbl.setStyleSheet(
        f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; "
        f"font-family: {FONT_FAMILY_MONO}; padding: 2px 0;"
    )
    return lbl


def _field_row(label: str, widget: QWidget, tip: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setStyleSheet(
        f"color: {COLOR_TEXT_MUTED}; font-size: 14px; min-width: 110px;"
    )
    row.addWidget(lbl)
    row.addWidget(widget, stretch=1)
    if tip:
        widget.setToolTip(tip)
    return row


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {COLOR_SURFACE_INNER};")
    return line


def _make_line_edit(placeholder: str = "", text: str = "") -> QLineEdit:
    le = QLineEdit()
    le.setPlaceholderText(placeholder)
    if text:
        le.setText(text)
    le.setStyleSheet(
        f"font-family: {FONT_FAMILY_MONO}; font-size: 14px;"
    )
    return le


def _result_badge(text: str, color: str = "") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    if color:
        lbl.setStyleSheet(badge_style(color))
    else:
        lbl.setStyleSheet(idle_badge_style())
    return lbl


# ---------------------------------------------------------------------------
# Pestaña 1 — Bisección
# ---------------------------------------------------------------------------

class _BisectionTab(QWidget):
    """Pestaña del método de bisección con tabla de historial iterativo."""

    _HEADERS = ["k", "a", "b", "xr", "f(a)", "f(b)", "f(xr)", "Eβ", "εₐ"]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)

        # ── Panel izquierdo: inputs ──────────────────────────────────────────
        left = QWidget()
        left.setMaximumWidth(380)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 8, 0)
        lv.setSpacing(8)

        lv.addWidget(_section_title("Parámetros"))

        self._fx_edit = _make_line_edit("ej: x**3 - 2*x - 5", "x**3 - 2*x - 5")
        self._a_edit = _make_line_edit("límite izquierdo a", "2")
        self._b_edit = _make_line_edit("límite derecho b", "3")
        self._tol_edit = _make_line_edit("tolerancia E", "0.0001")
        self._maxiter_spin = QSpinBox()
        self._maxiter_spin.setRange(1, 500)
        self._maxiter_spin.setValue(50)
        self._maxiter_spin.setStyleSheet(f"font-size: 14px; font-family: {FONT_FAMILY_MONO};")

        lv.addLayout(_field_row("f(x) =", self._fx_edit, "Expresión en x. Usa ** para potencia."))
        lv.addLayout(_field_row("a =", self._a_edit))
        lv.addLayout(_field_row("b =", self._b_edit))
        lv.addLayout(_field_row("Tolerancia E =", self._tol_edit))
        lv.addLayout(_field_row("Máx. iteraciones =", self._maxiter_spin))

        self._calc_btn = QPushButton("Calcular — Bisección")
        self._calc_btn.setObjectName("primaryAction")
        self._calc_btn.setCursor(Qt.PointingHandCursor)
        self._calc_btn.clicked.connect(self._calculate)
        lv.addWidget(self._calc_btn)
        lv.addWidget(_separator())

        # Resultados resumen
        lv.addWidget(_section_title("Resumen"))
        self._badge = _result_badge("Esperando cálculo")
        lv.addWidget(self._badge)

        self._info_lbl = _mono_label()
        lv.addWidget(self._info_lbl)

        self._scipy_lbl = _mono_label()
        lv.addWidget(self._scipy_lbl)

        lv.addStretch(1)
        splitter.addWidget(left)

        # ── Panel derecho: tabla ─────────────────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(6)
        rv.addWidget(_section_title("Historial de iteraciones"))

        self._table = QTableWidget(0, len(self._HEADERS))
        self._table.setHorizontalHeaderLabels(self._HEADERS)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setStyleSheet(
            f"font-family: {FONT_FAMILY_MONO}; font-size: 13px;"
        )
        rv.addWidget(self._table, stretch=1)
        splitter.addWidget(right)

        splitter.setSizes([360, 700])
        root.addWidget(splitter, stretch=1)

    @staticmethod
    def _format_ea(ea: str) -> str:
        """Muestra εₐ como decimal fijo (6 decimales); respeta «—» y «No definido»."""
        try:
            return f"{float(ea):.6f}"
        except ValueError:
            return ea

    def _calculate(self) -> None:
        # Leer parámetros
        fx_str = self._fx_edit.text().strip()
        try:
            a = float(self._a_edit.text())
            b = float(self._b_edit.text())
            tol = float(self._tol_edit.text())
            max_it = self._maxiter_spin.value()
        except ValueError:
            show_toast(self, "Revisa que a, b y E sean números válidos.", kind="error")
            return

        try:
            result: BisectionResult = bisection(fx_str, a, b, tol, max_it)
        except ValueError as exc:
            self._badge.setText(str(exc))
            self._badge.setStyleSheet(badge_style(COLOR_FEEDBACK_ERROR))
            self._info_lbl.setText("")
            self._scipy_lbl.setText("")
            self._table.setRowCount(0)
            show_toast(self, str(exc), kind="error")
            return
        except Exception as exc:  # noqa: BLE001
            show_toast(self, f"Error inesperado: {exc}", kind="error")
            return

        # Mostrar en tabla
        self._table.setRowCount(0)
        for row in result.history:
            r = self._table.rowCount()
            self._table.insertRow(r)
            vals = [
                str(row.k),
                f"{row.a:.8g}", f"{row.b:.8g}",
                f"{row.xr:.10g}",
                f"{row.fa:.6g}", f"{row.fb:.6g}", f"{row.fxr:.6g}",
                f"{row.eb:.6f}",
                self._format_ea(row.ea),
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(r, c, item)

        self._table.resizeColumnsToContents()

        # Badge y resumen
        color = COLOR_FEEDBACK_SUCCESS if result.converged else COLOR_ACCENT_WARNING
        root_str = f"{result.root:.10g}" if result.root is not None else "—"
        self._badge.setText(
            f"{'Convergió' if result.converged else 'No convergió'} — "
            f"Raíz ≈ {root_str}"
        )
        self._badge.setStyleSheet(badge_style(color))

        info_lines = [
            f"<b>Iteraciones teóricas:</b> {result.theoretical_iters}",
            f"<b>Iteraciones realizadas:</b> {len(result.history)}",
            f"<b>f(a₀) = f({result.a0}):</b> {result.fa0:.6g}",
            f"<b>f(b₀) = f({result.b0}):</b> {result.fb0:.6g}",
            f"<b>Motivo de parada:</b> {result.stop_reason}",
        ]
        self._info_lbl.setText("<br>".join(info_lines))

        if result.scipy_available and result.scipy_root is not None:
            diff_str = f"{result.scipy_diff:.6e}" if result.scipy_diff is not None else "—"
            self._scipy_lbl.setText(
                f"<span style='color:{COLOR_INTERACTIVE_IDLE}; font-weight:600;'>Contraste SciPy:</span> "
                f"raíz = {result.scipy_root:.10g}&nbsp;&nbsp;|&nbsp;&nbsp;"
                f"diferencia absoluta = {diff_str}"
            )
        elif not result.scipy_available:
            self._scipy_lbl.setText(
                "<i style='color: gray;'>SciPy no disponible para contraste.</i>"
            )
        else:
            self._scipy_lbl.setText("")

        show_toast(self, f"Bisección completada. Raíz ≈ {root_str}.", kind="success")


# ---------------------------------------------------------------------------
# Pestaña 2 — Graficador
# ---------------------------------------------------------------------------

class _PlotterTab(QWidget):
    """Pestaña de graficador de funciones con matplotlib embebido."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── Fila de controles ────────────────────────────────────────────────
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self._fx_edit = _make_line_edit("f(x) = ...", "sin(x) + x**2 / 10")
        self._fx_edit.setMinimumWidth(240)

        self._xmin_edit = _make_line_edit("x mín", "-10")
        self._xmax_edit = _make_line_edit("x máx", "10")

        for lbl_text, widget in [
            ("f(x) =", self._fx_edit),
            ("x mín =", self._xmin_edit),
            ("x máx =", self._xmax_edit),
        ]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
            ctrl_row.addWidget(lbl)
            ctrl_row.addWidget(widget)

        self._plot_btn = QPushButton("Graficar")
        self._plot_btn.setObjectName("primaryAction")
        self._plot_btn.setCursor(Qt.PointingHandCursor)
        self._plot_btn.clicked.connect(self._plot)
        ctrl_row.addWidget(self._plot_btn)

        self._clear_btn = QPushButton("Limpiar")
        self._clear_btn.setObjectName("secondaryAction")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear)
        ctrl_row.addWidget(self._clear_btn)
        ctrl_row.addStretch(1)
        root.addLayout(ctrl_row)

        # ── Canvas de matplotlib ─────────────────────────────────────────────
        if _MPL_OK:
            self._fig = Figure(figsize=(8, 4.5), dpi=96, tight_layout=True)
            self._ax = self._fig.add_subplot(111)
            self._canvas = FigureCanvas(self._fig)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._canvas.setMinimumHeight(300)
            root.addWidget(self._canvas, stretch=1)
            self._draw_empty()
        else:
            lbl = QLabel(
                "⚠ matplotlib no está instalado. Instálalo con: pip install matplotlib"
            )
            lbl.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 15px;")
            lbl.setAlignment(Qt.AlignCenter)
            root.addWidget(lbl, stretch=1)

    def _draw_empty(self) -> None:
        self._ax.clear()
        self._ax.set_facecolor("#1a1a2e")
        self._fig.patch.set_facecolor("#13131f")
        self._ax.set_xlabel("x", color="#b0b0d0")
        self._ax.set_ylabel("f(x)", color="#b0b0d0")
        self._ax.tick_params(colors="#b0b0d0")
        self._ax.spines["bottom"].set_color("#444466")
        self._ax.spines["left"].set_color("#444466")
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.set_title("Ingresa f(x) y pulsa Graficar", color="#888899")
        self._ax.grid(True, color="#2a2a4a", linestyle="--", linewidth=0.6)
        self._canvas.draw()

    def _plot(self) -> None:
        if not _MPL_OK or not _NUMPY_OK:
            show_toast(self, "matplotlib/numpy no disponibles.", kind="error")
            return

        fx_str = self._fx_edit.text().strip()
        try:
            x_min = float(self._xmin_edit.text())
            x_max = float(self._xmax_edit.text())
        except ValueError:
            show_toast(self, "x mín y x máx deben ser números.", kind="error")
            return

        try:
            data = compute_plot_data(fx_str, x_min, x_max)
        except (ValueError, ImportError) as exc:
            show_toast(self, str(exc), kind="error")
            return
        except Exception as exc:  # noqa: BLE001
            show_toast(self, f"Error al graficar: {exc}", kind="error")
            return

        self._ax.clear()
        self._ax.set_facecolor("#1a1a2e")
        self._fig.patch.set_facecolor("#13131f")

        self._ax.plot(
            data.x, data.y,
            color="#7ec8e3", linewidth=1.8,
            label=f"f(x) = {fx_str}",
        )
        self._ax.axhline(0, color="#555577", linewidth=0.8, linestyle="-")
        self._ax.axvline(0, color="#555577", linewidth=0.8, linestyle="-")
        self._ax.set_xlabel("x", color="#b0b0d0", fontsize=11)
        self._ax.set_ylabel("f(x)", color="#b0b0d0", fontsize=11)
        self._ax.set_title(f"f(x) = {fx_str}", color="#d0d0ee", fontsize=12)
        self._ax.tick_params(colors="#b0b0d0")
        self._ax.spines["bottom"].set_color("#444466")
        self._ax.spines["left"].set_color("#444466")
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.grid(True, color="#2a2a4a", linestyle="--", linewidth=0.6)
        legend = self._ax.legend(
            facecolor="#1a1a2e", edgecolor="#444466",
            labelcolor="#d0d0ee", fontsize=10,
        )
        self._canvas.draw()
        show_toast(self, "Gráfica actualizada.", kind="success")

    def _clear(self) -> None:
        if _MPL_OK:
            self._draw_empty()


# ---------------------------------------------------------------------------
# Pestaña 3 — Notación Posicional
# ---------------------------------------------------------------------------

class _PositionalTab(QWidget):
    """Pestaña de descomposición de enteros en base 10 y base 2."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Fila de entrada
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        lbl = QLabel("Entero:")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        self._num_edit = _make_line_edit("ej: 85920 o -255", "85920")
        self._calc_btn = QPushButton("Descomponer")
        self._calc_btn.setObjectName("primaryAction")
        self._calc_btn.setCursor(Qt.PointingHandCursor)
        self._calc_btn.clicked.connect(self._calculate)
        ctrl.addWidget(lbl)
        ctrl.addWidget(self._num_edit, stretch=1)
        ctrl.addWidget(self._calc_btn)
        root.addLayout(ctrl)
        root.addWidget(_separator())

        # Resultados
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setStyleSheet(
            f"background-color: transparent; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"font-family: {FONT_FAMILY_MONO}; "
            f"font-size: 15px; "
            f"border: none;"
        )
        self._browser.setPlaceholderText("Ingresa un entero y pulsa «Descomponer».")
        root.addWidget(self._browser, stretch=1)

    def _calculate(self) -> None:
        raw = self._num_edit.text().strip()
        try:
            number = int(raw)
        except ValueError:
            show_toast(self, f'"{raw}" no es un entero válido.', kind="error")
            return

        try:
            res = compute_positional(number)
        except (TypeError, ValueError) as exc:
            show_toast(self, str(exc), kind="error")
            return

        sign = "−" if res.is_negative else ""
        lines: list[str] = [
            f"<h3 style='color:{COLOR_INTERACTIVE_IDLE};'>"
            f"Número: {sign}{res.abs_number}</h3>",
        ]

        # ── Base 10 ──────────────────────────────────────────────────────────
        lines.append(
            f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>━ Base 10 (Decimal)</b>"
        )
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED};'>Representación:</span> "
            f"<b>{sign}{res.abs_number}</b>"
        )
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED};'>Descomposición:</span> "
            f"<b>{sign}({res.base10_expr})</b>"
        )
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED};'>Suma:</span> "
            f"{sign}({res.base10_sum}) = <b>{number}</b>"
        )

        lines.append("<hr style='border-color:#333355;'>")

        # ── Base 2 ───────────────────────────────────────────────────────────
        lines.append(
            f"<b style='color:{COLOR_ACCENT_WARNING};'>━ Base 2 (Binario)</b>"
        )
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED};'>Representación:</span> "
            f"<b>{sign}{res.base2_repr}₂</b>"
        )
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED};'>Descomposición:</span> "
            f"<b>{sign}({res.base2_expr})</b>"
        )
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED};'>Suma:</span> "
            f"{sign}({res.base2_sum}) = <b>{sign}{res.base2_decimal_check}</b> ✓"
        )

        lines.append("<hr style='border-color:#333355;'>")
        lines.append(
            f"<span style='color:{COLOR_TEXT_MUTED}; font-size:13px;'>"
            f"Verificación: {sign}{res.base2_decimal_check} (binario a decimal) = {number} ✓"
            f"</span>"
        )

        self._browser.setHtml("<br>".join(lines))
        show_toast(self, f"{number} descompuesto en base 10 y base 2.", kind="success")


# ---------------------------------------------------------------------------
# Pestaña 4 — Errores Numéricos
# ---------------------------------------------------------------------------

class _NumericalErrorsTab(QWidget):
    """Pestaña de errores numéricos: propagación y error abs/rel/porcentual."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Scroll para toda la pestaña
        content = QWidget()
        cv = QVBoxLayout(content)
        cv.setContentsMargins(12, 12, 12, 12)
        cv.setSpacing(14)

        # ── Bloque 1: Tipos de error (panel informativo) ──────────────────────
        info_box = QGroupBox("Fundamentos: Tipos de Error Numérico")
        info_box.setStyleSheet(
            f"QGroupBox {{ font-weight: 600; font-size: 15px; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"border: 1px solid {COLOR_SURFACE_INNER}; "
            f"border-radius: 6px; padding-top: 14px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        ib = QVBoxLayout(info_box)
        ib.setSpacing(6)

        try:
            import numpy as np
            eps_val = np.finfo(float).eps
            eps_str = f"{eps_val:.6e}"
        except Exception:
            eps_str = "≈ 2.22×10⁻¹⁶"

        info_html = (
            f"<p style='font-size:14px; color:{COLOR_TEXT_PRIMARY};'>"
            "<b>Error Absoluto</b> |eₐ| = |x<sub>v</sub> − x<sub>a</sub>|: "
            "mide la distancia entre el valor verdadero y el aproximado en las "
            "mismas unidades del problema.</p>"

            f"<p style='font-size:14px; color:{COLOR_TEXT_PRIMARY};'>"
            "<b>Error Relativo</b> εᵣ = |eₐ| / |x<sub>v</sub>|: "
            "normaliza el error absoluto respecto al valor verdadero, "
            "permitiendo comparar errores de magnitudes distintas.</p>"

            f"<p style='font-size:14px; color:{COLOR_TEXT_PRIMARY};'>"
            "<b>Error Relativo Porcentual</b> εᵣ% = εᵣ × 100: "
            "versión en porcentaje del error relativo.</p>"

            f"<p style='font-size:14px; color:{COLOR_TEXT_PRIMARY};'>"
            "<b>¿Por qué 0.1 + 0.2 ≠ 0.3?</b><br>"
            "Los números de punto flotante (IEEE 754) representan solo fracciones "
            "cuyo denominador es potencia de 2. El valor 0.1 en base 2 es "
            "periódico (como 1/3 en base 10), por lo que se redondea al almacenarse. "
            "La suma de dos redondeos produce un tercer error: "
            "<code style='font-size:13px;'>0.1 + 0.2 = 0.30000000000000004</code>.</p>"

            f"<p style='font-size:14px; color:{COLOR_TEXT_PRIMARY};'>"
            f"<b>Épsilon de máquina</b> (numpy.finfo(float).eps) = "
            f"<code style='font-size:13px;'>{eps_str}</code>: "
            "el número positivo más pequeño tal que "
            "<code>1.0 + ε ≠ 1.0</code> en aritmética de punto flotante de 64 bits. "
            "Representa la cota del error relativo de redondeo unitario.</p>"
        )
        info_lbl = QLabel()
        info_lbl.setTextFormat(Qt.RichText)
        info_lbl.setWordWrap(True)
        info_lbl.setText(info_html)
        ib.addWidget(info_lbl)
        cv.addWidget(info_box)

        # ── Bloque 2: Propagación de error ───────────────────────────────────
        prop_box = QGroupBox("Calculadora de Propagación de Error  —  f(x) = sin(x) + x²")
        prop_box.setStyleSheet(info_box.styleSheet())
        pb = QVBoxLayout(prop_box)
        pb.setSpacing(8)

        formula_lbl = QLabel(
            "<i style='font-size:14px;'>"
            "f′(x) = cos(x) + 2x&nbsp;&nbsp;|&nbsp;&nbsp;"
            "Δy ≈ f′(x)·Δx&nbsp;&nbsp;|&nbsp;&nbsp;"
            "Δy<sub>real</sub> = f(x+Δx) − f(x)"
            "</i>"
        )
        formula_lbl.setTextFormat(Qt.RichText)
        formula_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        pb.addWidget(formula_lbl)

        input_row = QHBoxLayout()
        self._prop_x_edit = _make_line_edit("valor de x", "1.0")
        self._prop_dx_edit = _make_line_edit("Δx", "0.1")
        self._prop_btn = QPushButton("Calcular Propagación")
        self._prop_btn.setObjectName("primaryAction")
        self._prop_btn.setCursor(Qt.PointingHandCursor)
        self._prop_btn.clicked.connect(self._calc_propagation)

        for lbl_text, widget in [("x =", self._prop_x_edit), ("Δx =", self._prop_dx_edit)]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; min-width: 30px;")
            input_row.addWidget(lbl)
            input_row.addWidget(widget)
        input_row.addWidget(self._prop_btn)
        pb.addLayout(input_row)

        self._prop_result_lbl = _mono_label()
        pb.addWidget(self._prop_result_lbl)
        cv.addWidget(prop_box)

        # ── Bloque 3: Calculadora de error ───────────────────────────────────
        err_box = QGroupBox("Calculadora de Error  —  dado xᵥ (verdadero) y xₐ (aproximado)")
        err_box.setStyleSheet(info_box.styleSheet())
        eb = QVBoxLayout(err_box)
        eb.setSpacing(8)

        err_input_row = QHBoxLayout()
        self._xtrue_edit = _make_line_edit("valor verdadero xᵥ", "3.141592653589793")
        self._xapprox_edit = _make_line_edit("valor aproximado xₐ", "3.14159")
        self._err_btn = QPushButton("Calcular Errores")
        self._err_btn.setObjectName("primaryAction")
        self._err_btn.setCursor(Qt.PointingHandCursor)
        self._err_btn.clicked.connect(self._calc_error)

        for lbl_text, widget in [
            ("xᵥ =", self._xtrue_edit), ("xₐ =", self._xapprox_edit)
        ]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; min-width: 36px;")
            err_input_row.addWidget(lbl)
            err_input_row.addWidget(widget)
        err_input_row.addWidget(self._err_btn)
        eb.addLayout(err_input_row)

        self._err_result_lbl = _mono_label()
        eb.addWidget(self._err_result_lbl)
        cv.addWidget(err_box)

        cv.addStretch(1)

        # Envolver en QScrollArea
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _calc_propagation(self) -> None:
        try:
            x = float(self._prop_x_edit.text())
            dx = float(self._prop_dx_edit.text())
        except ValueError:
            show_toast(self, "Ingresa valores numéricos válidos para x y Δx.", kind="error")
            return

        try:
            res = propagate_error(x, dx)
        except Exception as exc:  # noqa: BLE001
            show_toast(self, f"Error: {exc}", kind="error")
            return

        c = COLOR_INTERACTIVE_IDLE
        lines = [
            f"<b style='color:{c};'>f(x)</b> = sin({x}) + {x}² = <b>{res.fx:.10g}</b>",
            f"<b style='color:{c};'>f′(x)</b> = cos({x}) + 2·{x} = <b>{res.fpx:.10g}</b>",
            f"<b style='color:{c};'>Δy ≈ f′(x)·Δx</b> = {res.fpx:.6g} · {dx} = "
            f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>{res.dy_approx:.10g}</b>",
            f"<b style='color:{c};'>f(x+Δx)</b> = f({x}+{dx}) = <b>{res.fx_dx:.10g}</b>",
            f"<b style='color:{c};'>Δy<sub>real</sub></b> = f(x+Δx) − f(x) = "
            f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>{res.dy_real:.10g}</b>",
            f"<b style='color:{c};'>|Δy_aprox − Δy_real|</b> = "
            f"<b style='color:{COLOR_ACCENT_WARNING};'>{res.abs_diff:.6e}</b>",
        ]
        self._prop_result_lbl.setText("<br>".join(lines))
        show_toast(self, "Propagación calculada.", kind="success")

    def _calc_error(self) -> None:
        try:
            x_true = float(self._xtrue_edit.text())
            x_approx = float(self._xapprox_edit.text())
        except ValueError:
            show_toast(self, "Ingresa valores numéricos válidos.", kind="error")
            return

        try:
            res = compute_numerical_error(x_true, x_approx)
        except Exception as exc:  # noqa: BLE001
            show_toast(self, f"Error: {exc}", kind="error")
            return

        c = COLOR_INTERACTIVE_IDLE
        lines = [
            f"<b style='color:{c};'>x<sub>v</sub> (verdadero):</b> {res.x_true}",
            f"<b style='color:{c};'>x<sub>a</sub> (aproximado):</b> {res.x_approx}",
            "",
            f"<b style='color:{c};'>Error absoluto</b> |x<sub>v</sub> − x<sub>a</sub>| = "
            f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>{res.abs_error:.10e}</b>",
        ]

        if res.zero_true:
            lines.append(
                f"<span style='color:{COLOR_FEEDBACK_ERROR};'>"
                "Error relativo: indefinido (x<sub>v</sub> = 0, división por cero)."
                "</span>"
            )
        else:
            lines += [
                f"<b style='color:{c};'>Error relativo</b> |eₐ|/|x<sub>v</sub>| = "
                f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>{res.rel_error:.10e}</b>",
                f"<b style='color:{c};'>Error relativo %</b> = "
                f"<b style='color:{COLOR_FEEDBACK_SUCCESS};'>{res.rel_error_pct:.8g}%</b>",
            ]

        self._err_result_lbl.setText("<br>".join(lines))
        show_toast(self, "Errores calculados.", kind="success")


# ---------------------------------------------------------------------------
# Vista principal del módulo
# ---------------------------------------------------------------------------

class NumericalMethodsView(QWidget):
    """Módulo 9: Métodos Numéricos — Bisección, Graficador, Posicional, Errores."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("numericalMethodsView")
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("nmTabs")

        self._bisection_tab = _BisectionTab()
        self._plotter_tab = _PlotterTab()
        self._positional_tab = _PositionalTab()
        self._errors_tab = _NumericalErrorsTab()

        self._tabs.addTab(self._bisection_tab, "Bisección")
        self._tabs.addTab(self._plotter_tab, "Graficador  f(x)")
        self._tabs.addTab(self._positional_tab, "Notación Posicional")
        self._tabs.addTab(self._errors_tab, "Errores Numéricos")

        root.addWidget(self._tabs)

