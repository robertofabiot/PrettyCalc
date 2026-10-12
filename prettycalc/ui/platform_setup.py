"""Apariencia idéntica en Windows, Linux y macOS.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10. Qt toma del sistema operativo tres cosas que cambian el aspecto de
la aplicación: el estilo de los controles, las fuentes y los iconos. Este
módulo fija las tres para que PrettyCalc se vea igual en cualquier equipo:

1. Estilo ``Fusion`` (el mismo motor de dibujo en todas las plataformas).
2. Fuentes empaquetadas en ``assets/fonts``: Inter (texto), Fira Code
   (números y matrices) y DejaVu Sans (símbolos matemáticos como ℝ, ᵀ, ∘, ≟,
   ✓, ✕). Así nunca se recurre a Segoe UI, Cantarell ni a la fuente que tenga
   instalada cada sistema.
3. Tamaños en píxeles (no en puntos): un punto mide distinto según el DPI
   lógico que reporte cada sistema, un píxel lógico no.
4. Iconos de los diálogos dibujados por la propia aplicación.

También fija la política de escalado de alta densidad (``PassThrough``) para
que 125 % o 150 % en Windows y en Linux se traten igual.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

try:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import (
        QColor,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QIcon,
        QPainter,
        QPen,
        QPixmap,
    )
    from PySide6.QtWidgets import QApplication, QStyleFactory
except ImportError:  # pragma: no cover - entorno sin Qt
    QApplication = None  # type: ignore

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"

#: Archivos de fuente que se registran al arrancar.
BUNDLED_FONT_FILES: Sequence[str] = (
    "Inter-Regular.ttf",
    "Inter-Italic.ttf",
    "Inter-Medium.ttf",
    "Inter-SemiBold.ttf",
    "Inter-Bold.ttf",
    "FiraCode-Regular.ttf",
    "FiraCode-SemiBold.ttf",
    "FiraCode-Bold.ttf",
    "DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf",
)

SANS_FAMILY = "Inter"
MONO_FAMILY = "Fira Code"
SYMBOL_FAMILY = "DejaVu Sans"

#: Orden de búsqueda de glifos: la fuente principal y, para símbolos que no
#: tiene, DejaVu Sans (también empaquetada). Nunca se llega a fuentes del sistema.
SANS_FAMILIES: List[str] = [SANS_FAMILY, SYMBOL_FAMILY]
MONO_FAMILIES: List[str] = [MONO_FAMILY, SYMBOL_FAMILY]

#: Tamaño base del texto de la interfaz, en píxeles lógicos.
BASE_FONT_PX = 15

_loaded_families: Optional[List[str]] = None


def bundled_font_paths() -> List[Path]:
    return [FONTS_DIR / name for name in BUNDLED_FONT_FILES]


def load_bundled_fonts() -> List[str]:
    """Registra las fuentes empaquetadas (una sola vez). Devuelve las familias cargadas."""
    global _loaded_families
    if _loaded_families is not None:
        return list(_loaded_families)
    families: List[str] = []
    for path in bundled_font_paths():
        if not path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            continue
        for family in QFontDatabase.applicationFontFamilies(font_id):
            if family not in families:
                families.append(family)
    _loaded_families = families
    return list(families)


def fonts_available() -> bool:
    families = load_bundled_fonts()
    return SANS_FAMILY in families and MONO_FAMILY in families and SYMBOL_FAMILY in families


def make_font(
    px: int,
    *,
    mono: bool = False,
    weight: int = 400,
    italic: bool = False,
) -> "QFont":
    """Fuente de la aplicación con tamaño en píxeles y la cadena de respaldo empaquetada."""
    font = QFont()
    font.setFamilies(MONO_FAMILIES if mono else SANS_FAMILIES)
    font.setPixelSize(max(1, int(px)))
    font.setWeight(QFont.Weight(weight))
    font.setItalic(italic)
    font.setHintingPreference(QFont.PreferNoHinting)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font


def configure_high_dpi() -> None:
    """Debe llamarse antes de crear ``QApplication``."""
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except (AttributeError, RuntimeError):
        pass


def prepare_application(app: Optional[Any] = None) -> bool:
    """Aplica estilo, fuentes y fuente por defecto. Es idempotente.

    Devuelve ``True`` si las fuentes empaquetadas quedaron disponibles.
    """
    app = app or QApplication.instance()
    if app is None:
        return False
    if getattr(app, "_prettycalc_prepared", False):
        return fonts_available()
    # Fusion dibuja igual en todas las plataformas. No se envuelve en un
    # QProxyStyle de Python: styleHint se consulta decenas de miles de veces y
    # el puente Python lo volvía lento. Los diálogos propios fijan el orden de
    # sus botones en el layout.
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    ok = fonts_available()
    app.setFont(make_font(BASE_FONT_PX))
    try:
        app.setEffectEnabled(Qt.UI_AnimateCombo, False)
        app.setEffectEnabled(Qt.UI_AnimateTooltip, False)
        app.setEffectEnabled(Qt.UI_FadeTooltip, False)
    except (AttributeError, RuntimeError):
        pass
    setattr(app, "_prettycalc_prepared", True)
    return ok


# ---------------------------------------------------------------------------
# Iconos de estado dibujados por la aplicación (no por el tema del sistema)
# ---------------------------------------------------------------------------

def status_pixmap(kind: str, color: str, foreground: str, size: int = 40) -> "QPixmap":
    """Círculo de color con ``!``, ``✕``, ``i`` o ``?`` trazado con líneas.

    Los iconos de ``QMessageBox`` vienen del tema del sistema (distintos en
    Windows, GNOME y KDE); este se ve igual en todos.
    """
    ratio = 2.0
    pixmap = QPixmap(int(size * ratio), int(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(QRectF(1, 1, size - 2, size - 2))
    pen = QPen(QColor(foreground), size * 0.11)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    c = size / 2
    if kind == "error":
        d = size * 0.18
        painter.drawLine(QPointF(c - d, c - d), QPointF(c + d, c + d))
        painter.drawLine(QPointF(c + d, c - d), QPointF(c - d, c + d))
    elif kind == "info":
        painter.drawPoint(QPointF(c, size * 0.29))
        painter.drawLine(QPointF(c, size * 0.45), QPointF(c, size * 0.72))
    elif kind == "question":
        painter.setFont(make_font(int(size * 0.6), weight=700))
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "?")
    else:  # warning
        painter.drawLine(QPointF(c, size * 0.24), QPointF(c, size * 0.56))
        painter.drawPoint(QPointF(c, size * 0.74))
    painter.end()
    return pixmap


def missing_glyphs(text: str, families: Iterable[str] = ()) -> str:
    """Caracteres de ``text`` que ninguna fuente empaquetada puede dibujar."""
    from PySide6.QtGui import QRawFont

    raws = []
    for path in bundled_font_paths():
        raw = QRawFont(str(path), 16)
        if raw.isValid():
            raws.append(raw)
    missing = []
    for char in sorted(set(text)):
        if char.isspace() or ord(char) < 32:
            continue
        if not any(raw.supportsCharacter(ord(char)) for raw in raws):
            missing.append(char)
    return "".join(missing)
