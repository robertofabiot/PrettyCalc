"""Gráfica de convergencia y medidor del radio espectral (Programa 8).

``ConvergencePlot`` dibuja log₁₀ de una medida por iteración (‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞
o el error real ‖x⁽ᵏ⁾ − x*‖∞) para Jacobi y Gauss-Seidel en los mismos ejes,
con la tolerancia ε como línea punteada. En escala logarítmica una
convergencia lineal es una recta de pendiente log₁₀ ρ(T): Gauss-Seidel baja
más empinado cuando su ρ es menor, y una serie que sube es una divergencia.

``SpectralGauge`` sitúa ρ(T) en una barra de 0 a 2 con la zona convergente
(ρ < 1) y la divergente (ρ > 1).

Todo se pinta con ``QPainter`` y los tokens del tema, igual que las matrices
de libro: se ve idéntico en Windows y en Linux.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

try:
    from PySide6.QtCore import QPointF, QRectF, QSize, Qt
    from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
    from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore

from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    rgba,
    ui_font,
)

#: Colores fijos por método en toda la vista.
JACOBI_COLOR = COLOR_INTERACTIVE_IDLE
GAUSS_SEIDEL_COLOR = COLOR_ACCENT_WARNING

_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
#: Un valor exactamente 0 se dibuja en este piso (log₁₀ no existe en 0).
_ZERO_FLOOR = -16.0


def _decade_label(exponent: int) -> str:
    if exponent == 0:
        return "1"
    if exponent == 1:
        return "10"
    return "10" + str(exponent).translate(_SUP)


@dataclass(frozen=True)
class PlotSeries:
    """Una serie: nombre, color y pares (k, valor ≥ 0)."""

    name: str
    color: str
    points: Tuple[Tuple[int, Fraction], ...]
    status: str = ""


class ConvergencePlot(QWidget):
    """log₁₀ de la medida de cada iteración, con ε como referencia."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._series: List[PlotSeries] = []
        self._tolerance: Optional[Fraction] = None
        self._y_caption = "‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞"
        self._hover: Optional[Tuple[int, int]] = None
        self._screen_points: List[List[Tuple[QPointF, int, Fraction]]] = []
        self.setMinimumHeight(320)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAccessibleName("Gráfica de convergencia")

    # -- API --------------------------------------------------------------
    def set_series(
        self,
        series: Sequence[PlotSeries],
        *,
        tolerance: Optional[Fraction] = None,
        y_caption: Optional[str] = None,
    ) -> None:
        self._series = [s for s in series if s.points]
        self._tolerance = tolerance
        if y_caption:
            self._y_caption = y_caption
        self._hover = None
        self.update()

    def clear(self) -> None:
        self.set_series([])

    def series(self) -> List[PlotSeries]:
        return list(self._series)

    def sizeHint(self) -> "QSize":  # noqa: N802
        return QSize(640, 360)

    # -- geometría --------------------------------------------------------
    @staticmethod
    def _log(value: Fraction) -> float:
        if value <= 0:
            return _ZERO_FLOOR
        try:
            return max(_ZERO_FLOOR, math.log10(value))
        except (OverflowError, ValueError):  # pragma: no cover - magnitudes absurdas
            return 300.0

    def _ranges(self) -> Tuple[int, int, int]:
        max_k = max((k for s in self._series for k, _ in s.points), default=1)
        logs = [self._log(v) for s in self._series for _, v in s.points]
        if self._tolerance is not None:
            logs.append(self._log(self._tolerance))
        low = math.floor(min(logs)) if logs else -4
        high = math.ceil(max(logs)) if logs else 1
        if high <= low:
            high = low + 1
        return max(1, max_k), low, high

    # -- pintura ----------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802, ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(COLOR_SURFACE_INNER))
        self._screen_points = []

        if not self._series:
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.setFont(ui_font(15, italic=True))
            painter.drawText(self.rect(), Qt.AlignCenter, "Pulsa Iterar para comparar la convergencia.")
            painter.end()
            return

        max_k, low, high = self._ranges()
        label_font = ui_font(12)
        metrics = QFontMetrics(label_font)
        left = 18 + metrics.horizontalAdvance("10⁻¹⁶") + 10
        plot = QRectF(left, 44, self.width() - left - 22, self.height() - 44 - 48)
        if plot.width() < 60 or plot.height() < 60:
            painter.end()
            return

        def to_x(k: float) -> float:
            return plot.left() + plot.width() * (k / max_k)

        def to_y(log_value: float) -> float:
            return plot.bottom() - plot.height() * ((log_value - low) / (high - low))

        # Rejilla por décadas.
        painter.setFont(label_font)
        decades = high - low
        step = max(1, math.ceil(decades / 8))
        for exponent in range(low, high + 1):
            y = to_y(exponent)
            painter.setPen(QPen(QColor(rgba(COLOR_TEXT_MUTED, 0.18)), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            if (exponent - low) % step == 0:
                painter.setPen(QColor(COLOR_TEXT_MUTED))
                text = _decade_label(exponent)
                painter.drawText(
                    QRectF(0, y - 9, left - 8, 18), Qt.AlignRight | Qt.AlignVCenter, text
                )
        k_step = max(1, math.ceil(max_k / 10))
        for k in range(0, max_k + 1, k_step):
            x = to_x(k)
            painter.setPen(QPen(QColor(rgba(COLOR_TEXT_MUTED, 0.12)), 1))
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.drawText(QRectF(x - 20, plot.bottom() + 6, 40, 18), Qt.AlignCenter, str(k))

        # Ejes.
        painter.setPen(QPen(QColor(COLOR_TEXT_MUTED), 1.4))
        painter.drawLine(plot.bottomLeft(), plot.bottomRight())
        painter.drawLine(plot.bottomLeft(), plot.topLeft())
        painter.setFont(ui_font(13, weight=600))
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 24, plot.width(), 20), Qt.AlignCenter, "Iteración k"
        )
        painter.drawText(QRectF(left - 4, 10, plot.width(), 22), Qt.AlignLeft | Qt.AlignVCenter, self._y_caption)

        # Tolerancia.
        if self._tolerance is not None:
            y = to_y(self._log(self._tolerance))
            pen = QPen(QColor(COLOR_FEEDBACK_SUCCESS), 1.6, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setFont(ui_font(12, weight=600))
            painter.drawText(
                QRectF(plot.right() - 160, y - 20, 156, 18), Qt.AlignRight | Qt.AlignVCenter, "tolerancia ε"
            )

        # Series.
        painter.setClipRect(plot.adjusted(-6, -6, 6, 6))
        for s_index, series in enumerate(self._series):
            color = QColor(series.color)
            path = QPainterPath()
            screen = []
            for index, (k, value) in enumerate(series.points):
                point = QPointF(to_x(k), to_y(self._log(value)))
                screen.append((point, k, value))
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
            painter.setPen(QPen(color, 2.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
            painter.setPen(QPen(QColor(COLOR_SURFACE_INNER), 1.5))
            painter.setBrush(color)
            for p_index, (point, _k, _v) in enumerate(screen):
                hovered = self._hover == (s_index, p_index)
                radius = 6.5 if hovered else 4.0
                painter.drawEllipse(point, radius, radius)
            self._screen_points.append(screen)
        painter.setClipping(False)

        # Leyenda.
        painter.setFont(ui_font(13, weight=600))
        legend_metrics = QFontMetrics(ui_font(13, weight=600))
        x = plot.right()
        for series in reversed(self._series):
            text = series.name + (f" · {series.status}" if series.status else "")
            width = legend_metrics.horizontalAdvance(text)
            x -= width
            painter.setPen(QColor(COLOR_TEXT_PRIMARY))
            painter.drawText(QRectF(x, 12, width, 20), Qt.AlignVCenter | Qt.AlignLeft, text)
            x -= 22
            painter.setPen(QPen(QColor(series.color), 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(x, 22), QPointF(x + 16, 22))
            x -= 18
        painter.end()

    # -- interacción ------------------------------------------------------
    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        position = event.position()
        best = None
        best_distance = 14.0 ** 2
        for s_index, screen in enumerate(self._screen_points):
            for p_index, (point, _k, _v) in enumerate(screen):
                distance = (point.x() - position.x()) ** 2 + (point.y() - position.y()) ** 2
                if distance < best_distance:
                    best, best_distance = (s_index, p_index), distance
        if best != self._hover:
            self._hover = best
            self.update()
        if best is None:
            QToolTip.hideText()
            return
        s_index, p_index = best
        _point, k, value = self._screen_points[s_index][p_index]
        from prettycalc.core.iterative_methods import format_decimal

        QToolTip.showText(
            event.globalPosition().toPoint(),
            f"{self._series[s_index].name}, k = {k}: {format_decimal(value, 8)}",
            self,
        )

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = None
        self.update()
        super().leaveEvent(event)


class SpectralGauge(QWidget):
    """Barra 0 – 2 con ρ(T): verde si ρ < 1, rojo si ρ ≥ 1."""

    MAX_SHOWN = 2.0

    def __init__(self, title: str, color: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._title = title
        self._color = color
        self._radius: Optional[float] = None
        self.setMinimumHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAccessibleName(title)

    def set_radius(self, radius: Optional[float]) -> None:
        self._radius = radius
        if radius is None:
            self.setToolTip("")
        else:
            self.setToolTip(f"{self._title} ≈ {radius:.6f}")
        self.update()

    def radius(self) -> Optional[float]:
        return self._radius

    def sizeHint(self) -> "QSize":  # noqa: N802
        return QSize(260, 64)

    def paintEvent(self, event) -> None:  # noqa: N802, ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        width = self.width()
        painter.setFont(ui_font(14, weight=600))
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        painter.drawText(QRectF(0, 0, width * 0.6, 22), Qt.AlignLeft | Qt.AlignVCenter, self._title)
        if self._radius is None:
            value_text, value_color = "—", COLOR_TEXT_MUTED
        else:
            converges = self._radius < 1 - 1e-9
            value_text = f"≈ {self._radius:.4f}"
            value_color = COLOR_FEEDBACK_SUCCESS if converges else COLOR_FEEDBACK_ERROR
        painter.setPen(QColor(value_color))
        painter.setFont(ui_font(15, mono=True, weight=600))
        painter.drawText(QRectF(width * 0.4, 0, width * 0.6, 22), Qt.AlignRight | Qt.AlignVCenter, value_text)

        bar = QRectF(2, 30, width - 4, 10)
        half = bar.width() / 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(rgba(COLOR_FEEDBACK_SUCCESS, 0.30)))
        painter.drawRoundedRect(QRectF(bar.left(), bar.top(), half, bar.height()), 5, 5)
        painter.setBrush(QColor(rgba(COLOR_FEEDBACK_ERROR, 0.30)))
        painter.drawRoundedRect(QRectF(bar.left() + half, bar.top(), half, bar.height()), 5, 5)
        painter.setPen(QPen(QColor(COLOR_TEXT_MUTED), 1.2))
        middle = bar.left() + half
        painter.drawLine(QPointF(middle, bar.top() - 3), QPointF(middle, bar.bottom() + 3))
        painter.setFont(ui_font(11))
        painter.drawText(QRectF(bar.left(), bar.bottom() + 2, 30, 16), Qt.AlignLeft, "0")
        painter.drawText(QRectF(middle - 15, bar.bottom() + 2, 30, 16), Qt.AlignCenter, "1")
        painter.drawText(QRectF(bar.right() - 30, bar.bottom() + 2, 30, 16), Qt.AlignRight, "≥ 2")

        if self._radius is not None:
            shown = min(self._radius, self.MAX_SHOWN)
            x = bar.left() + bar.width() * (shown / self.MAX_SHOWN)
            converges = self._radius < 1 - 1e-9
            marker = QColor(COLOR_FEEDBACK_SUCCESS if converges else COLOR_FEEDBACK_ERROR)
            painter.setPen(QPen(QColor(COLOR_SURFACE_INNER), 2))
            painter.setBrush(marker)
            painter.drawEllipse(QPointF(x, bar.center().y()), 8, 8)
            painter.setBrush(QColor(self._color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, bar.center().y()), 3.5, 3.5)
        painter.end()
