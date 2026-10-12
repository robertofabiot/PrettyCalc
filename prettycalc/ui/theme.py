"""Design System Cromático y Hojas de Estilo QSS para PrettyCalc.

Tokens oficiales del tema oscuro (predeterminado):

- color-bg-base: #1A181B (Shadow Grey)
- color-surface-elevated: #4A4257 (Vintage Grape profundo, Sprint 10)
- color-surface-inner: #242028
- color-text-primary: #E0FBFC (Light Cyan)
- color-text-muted: #C9C3D6 (Lilac Grey, Sprint 10: ≥ 4.5:1 sobre tarjetas)
- color-interactive-idle: #98C1D9 (Powder Blue)
- color-interactive-disabled: #3A3642 (Dimmed Grape)
- color-feedback-error: #EE6C4D (Burnt Peach)
- color-feedback-success: #81B29A (Muted Sage)
- color-accent-warning: #E9C46A (Warm Ochre)

Sprint 10 añade dos temas de accesibilidad (alto contraste y claro) y una
escala global de interfaz. El tema se elige al arrancar: las vistas leen las
constantes ``COLOR_*`` de este módulo, así que cambiarlo exige reiniciar la
aplicación (``preferences_dialog`` ofrece hacerlo en un clic).

Tipografía: las familias apuntan a las fuentes empaquetadas en
``assets/fonts`` (ver ``platform_setup``), con tamaños en píxeles, para que
Windows y Linux muestren exactamente las mismas letras y medidas.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QColor, QPalette
    _WA_STYLED_BG = _Qt.WA_StyledBackground
except ImportError:
    _WA_STYLED_BG = 0  # type: ignore
    QColor = object  # type: ignore
    QPalette = object  # type: ignore


# ---------------------------------------------------------------------------
# Paletas
# ---------------------------------------------------------------------------

PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg_base": "#1A181B",
        "surface_elevated": "#4A4257",
        "surface_inner": "#242028",
        "text_primary": "#E0FBFC",
        "text_muted": "#C9C3D6",
        "text_disabled": "#A8A3B2",
        "interactive_idle": "#98C1D9",
        "interactive_hover": "#B3D4E6",
        "interactive_disabled": "#3A3642",
        "feedback_error": "#EE6C4D",
        "feedback_success": "#81B29A",
        "success_hover": "#93C4AE",
        "accent_warning": "#E9C46A",
    },
    "high_contrast": {
        "bg_base": "#000000",
        "surface_elevated": "#1C1A22",
        "surface_inner": "#0B0A0D",
        "text_primary": "#FFFFFF",
        "text_muted": "#E6E1EF",
        "text_disabled": "#BEB8C8",
        "interactive_idle": "#9FD8FF",
        "interactive_hover": "#C8EAFF",
        "interactive_disabled": "#2A2731",
        "feedback_error": "#FF8A66",
        "feedback_success": "#8EF0B8",
        "success_hover": "#B5F7D0",
        "accent_warning": "#FFD866",
    },
    "light": {
        "bg_base": "#F3F0F6",
        "surface_elevated": "#FFFFFF",
        "surface_inner": "#ECE7F1",
        "text_primary": "#1E1A24",
        "text_muted": "#4F4859",
        "text_disabled": "#6E6779",
        "interactive_idle": "#24658C",
        "interactive_hover": "#3A7FA8",
        "interactive_disabled": "#D8D2DF",
        "feedback_error": "#B3412A",
        "feedback_success": "#2D7A57",
        "success_hover": "#368F67",
        "accent_warning": "#8A6400",
    },
}

THEME_LABELS: Dict[str, str] = {
    "dark": "Oscuro (predeterminado)",
    "high_contrast": "Alto contraste",
    "light": "Claro",
}

SCALE_OPTIONS: Tuple[float, ...] = (0.9, 1.0, 1.15, 1.3, 1.5)

_SETTINGS_ORG = "PrettyCalc"
_SETTINGS_APP = "PrettyCalc"


def _settings() -> Any:
    try:
        from PySide6.QtCore import QSettings
    except ImportError:
        return None
    return QSettings(_SETTINGS_ORG, _SETTINGS_APP)


def load_appearance() -> Tuple[str, float]:
    """Tema y escala guardados. Las variables de entorno mandan sobre lo guardado.

    ``PRETTYCALC_THEME`` y ``PRETTYCALC_SCALE`` permiten forzar la apariencia.
    Bajo pytest se usa siempre el tema oscuro a escala 1 para que las pruebas
    no dependan de las preferencias de quien las ejecuta.
    """
    env_theme = os.environ.get("PRETTYCALC_THEME", "").strip()
    env_scale = os.environ.get("PRETTYCALC_SCALE", "").strip()
    theme_name = "dark"
    scale = 1.0
    if "pytest" not in sys.modules:
        settings = _settings()
        if settings is not None:
            stored_theme = str(settings.value("appearance/theme", "dark") or "dark")
            if stored_theme in PALETTES:
                theme_name = stored_theme
            try:
                scale = float(settings.value("appearance/scale", 1.0) or 1.0)
            except (TypeError, ValueError):
                scale = 1.0
    if env_theme in PALETTES:
        theme_name = env_theme
    if env_scale:
        try:
            scale = float(env_scale)
        except ValueError:
            pass
    scale = min(max(scale, 0.75), 2.0)
    return theme_name, scale


def save_appearance(theme_name: str, scale: float) -> bool:
    """Guarda el tema y la escala para el próximo arranque."""
    if theme_name not in PALETTES:
        return False
    settings = _settings()
    if settings is None:
        return False
    settings.setValue("appearance/theme", theme_name)
    settings.setValue("appearance/scale", float(scale))
    settings.sync()
    return True


ACTIVE_THEME, ACTIVE_SCALE = load_appearance()
_P = PALETTES[ACTIVE_THEME]

# Constantes de color (se resuelven con el tema activo al importar)
COLOR_BG_BASE = _P["bg_base"]
COLOR_SURFACE_ELEVATED = _P["surface_elevated"]
COLOR_SURFACE_INNER = _P["surface_inner"]
COLOR_TEXT_PRIMARY = _P["text_primary"]
COLOR_TEXT_MUTED = _P["text_muted"]
COLOR_TEXT_DISABLED = _P["text_disabled"]
COLOR_INTERACTIVE_IDLE = _P["interactive_idle"]
COLOR_INTERACTIVE_HOVER = _P["interactive_hover"]
COLOR_INTERACTIVE_DISABLED = _P["interactive_disabled"]
COLOR_FEEDBACK_ERROR = _P["feedback_error"]
COLOR_FEEDBACK_SUCCESS = _P["feedback_success"]
COLOR_SUCCESS_HOVER = _P["success_hover"]
COLOR_ACCENT_WARNING = _P["accent_warning"]

# Familias tipográficas: primero la fuente empaquetada, después DejaVu Sans
# (empaquetada) para los símbolos que Inter o Fira Code no traen.
FONT_FAMILY_MONO = "Fira Code, DejaVu Sans, monospace"
FONT_FAMILY_SANS = "Inter, DejaVu Sans, sans-serif"


def ui_font(px: int, *, mono: bool = False, weight: int = 400, italic: bool = False) -> Any:
    """Atajo a ``platform_setup.make_font``: tamaño en píxeles y fuentes empaquetadas."""
    from prettycalc.ui.platform_setup import make_font

    return make_font(px, mono=mono, weight=weight, italic=italic)


# ---------------------------------------------------------------------------
# Utilidades de color y contraste (WCAG 2.1)
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    value = hex_color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgba(hex_color: str, alpha: float) -> str:
    """``rgba(r, g, b, a)`` a partir de un token: tintes coherentes con el tema activo."""
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha:.2f})"


def relative_luminance(hex_color: str) -> float:
    """Luminancia relativa según WCAG 2.1."""

    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = _hex_to_rgb(hex_color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(foreground: str, background: str) -> float:
    """Relación de contraste WCAG entre dos colores hexadecimales."""
    la = relative_luminance(foreground)
    lb = relative_luminance(background)
    light, dark = max(la, lb), min(la, lb)
    return (light + 0.05) / (dark + 0.05)


def readable_text_on(background: str) -> str:
    """Elige el token de texto (claro u oscuro) con mejor contraste sobre ``background``."""
    candidates = (COLOR_BG_BASE, COLOR_TEXT_PRIMARY)
    return max(candidates, key=lambda fg: contrast_ratio(fg, background))


def badge_style(
    background: str,
    foreground: Optional[str] = None,
    *,
    font_size: int = 16,
    padding: str = "10px 14px",
) -> str:
    """Estilo único de badge. Sin ``foreground`` elige el texto legible automáticamente."""
    fg = foreground if foreground is not None else readable_text_on(background)
    if contrast_ratio(fg, background) < 4.5:
        fg = readable_text_on(background)
    return (
        f"background-color: {background}; color: {fg}; font-weight: 600; "
        f"font-size: {font_size}px; padding: {padding}; border-radius: 6px; "
        f"font-family: {FONT_FAMILY_SANS};"
    )


def idle_badge_style(font_size: int = 16) -> str:
    """Badge neutro de espera (antes del primer cálculo)."""
    return badge_style(COLOR_INTERACTIVE_DISABLED, COLOR_TEXT_PRIMARY, font_size=font_size)


# ---------------------------------------------------------------------------
# Recursos (flechas de spinbox teñidas con el tema)
# ---------------------------------------------------------------------------

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _arrow_svg(direction: str, color: str) -> str:
    points = "5,0 10,6 0,6" if direction == "up" else "5,6 10,0 0,0"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6">'
        f'<polygon points="{points}" fill="{color}"/></svg>'
    )


def _ensure_assets() -> Tuple[str, str]:
    """Flechas del tema activo.

    El tema oscuro usa los archivos que vienen con el paquete. Los otros temas
    se generan en la carpeta temporal del usuario: la carpeta del paquete puede
    ser de solo lectura en una instalación de Windows (``Program Files``).
    Las rutas se pasan con ``/`` porque QSS no acepta ``\\`` de Windows.
    """
    if ACTIVE_THEME == "dark":
        folder = _ASSETS_DIR
    else:
        folder = Path(tempfile.gettempdir()) / "prettycalc-assets" / ACTIVE_THEME
    up = folder / "arrow_up.svg"
    down = folder / "arrow_down.svg"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if not up.exists():
            up.write_text(_arrow_svg("up", COLOR_TEXT_PRIMARY), encoding="utf-8")
        if not down.exists():
            down.write_text(_arrow_svg("down", COLOR_TEXT_PRIMARY), encoding="utf-8")
    except OSError:
        pass
    return up.as_posix(), down.as_posix()


_UP_ARROW_SVG, _DOWN_ARROW_SVG = _ensure_assets()


def apply_widget_class(widget: Any, class_name: str) -> None:
    """Asigna la propiedad CSS `class` y fuerza a Qt a reaplicar el QSS."""
    widget.setProperty("class", class_name)
    widget.setAttribute(_WA_STYLED_BG, True)
    repolish(widget)


def repolish(widget: Any) -> None:
    """Reaplica el QSS tras cambiar una propiedad dinámica usada en selectores."""
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def get_message_box_stylesheet() -> str:
    """Estilos para diálogos: sin esto el diálogo nativo queda blanco sobre blanco."""
    return f"""
    QMessageBox, QDialog {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_SANS};
        font-size: 15px;
    }}
    QMessageBox QLabel, QDialog QLabel {{
        color: {COLOR_TEXT_PRIMARY};
        background-color: transparent;
        font-size: 15px;
    }}
    QMessageBox QPushButton, QDialog QPushButton {{
        background-color: {COLOR_BG_BASE};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 8px 16px;
        min-width: 88px;
        font-size: 15px;
        font-weight: 600;
    }}
    QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}
    QMessageBox QPushButton:default, QDialog QPushButton:default {{
        border: 2px solid {COLOR_INTERACTIVE_IDLE};
    }}
    """


def _status_icon_for(box: Any) -> None:
    """Sustituye el icono del tema del sistema por uno dibujado con los tokens."""
    try:
        from PySide6.QtWidgets import QMessageBox
        from prettycalc.ui.platform_setup import status_pixmap
    except ImportError:
        return
    if not hasattr(box, "icon"):
        return
    icon = box.icon()
    mapping = {
        QMessageBox.Warning: ("warning", COLOR_ACCENT_WARNING),
        QMessageBox.Critical: ("error", COLOR_FEEDBACK_ERROR),
        QMessageBox.Information: ("info", COLOR_INTERACTIVE_IDLE),
        QMessageBox.Question: ("question", COLOR_INTERACTIVE_IDLE),
    }
    if icon not in mapping:
        return
    kind, color = mapping[icon]
    box.setIconPixmap(status_pixmap(kind, color, readable_text_on(color)))


def apply_message_box_theme(box: Any) -> None:
    """Fondo de tarjeta, texto primario e iconos propios en cualquier sistema."""
    box.setAttribute(_WA_STYLED_BG, True)
    box.setAutoFillBackground(True)
    pal = box.palette()
    bg = QColor(COLOR_SURFACE_ELEVATED)
    fg = QColor(COLOR_TEXT_PRIMARY)
    btn = QColor(COLOR_BG_BASE)
    for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        pal.setColor(group, QPalette.Window, bg)
        pal.setColor(group, QPalette.Base, bg)
        pal.setColor(group, QPalette.Light, bg)
        pal.setColor(group, QPalette.Mid, bg)
        pal.setColor(group, QPalette.Dark, btn)
        pal.setColor(group, QPalette.WindowText, fg)
        pal.setColor(group, QPalette.Text, fg)
        pal.setColor(group, QPalette.ButtonText, fg)
        pal.setColor(group, QPalette.Button, btn)
    box.setPalette(pal)
    box.setStyleSheet(get_message_box_stylesheet())
    _status_icon_for(box)
    try:
        from PySide6.QtWidgets import QLabel
        for label in box.findChildren(QLabel):
            label.setStyleSheet(
                f"color: {COLOR_TEXT_PRIMARY}; background-color: transparent;"
            )
    except Exception:
        pass


def get_app_palette() -> Any:
    """Retorna la paleta cromática oficial de PrettyCalc para QApplication y widgets."""
    if QPalette is object or QColor is object:
        return None
    palette = QPalette()
    bg = QColor(COLOR_BG_BASE)
    fg = QColor(COLOR_TEXT_PRIMARY)
    elevated = QColor(COLOR_SURFACE_ELEVATED)
    inner = QColor(COLOR_SURFACE_INNER)
    disabled_text = QColor(COLOR_TEXT_DISABLED)
    for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        palette.setColor(group, QPalette.Window, bg)
        palette.setColor(group, QPalette.Base, inner)
        palette.setColor(group, QPalette.AlternateBase, elevated)
        palette.setColor(group, QPalette.WindowText, fg)
        palette.setColor(group, QPalette.Text, fg)
        palette.setColor(group, QPalette.Button, elevated)
        palette.setColor(group, QPalette.ButtonText, fg)
        palette.setColor(group, QPalette.BrightText, fg)
        palette.setColor(group, QPalette.ToolTipBase, inner)
        palette.setColor(group, QPalette.ToolTipText, fg)
        palette.setColor(group, QPalette.PlaceholderText, QColor(COLOR_TEXT_MUTED))
        palette.setColor(group, QPalette.Highlight, QColor(COLOR_INTERACTIVE_IDLE))
        palette.setColor(group, QPalette.HighlightedText, bg)
        palette.setColor(group, QPalette.Link, QColor(COLOR_INTERACTIVE_IDLE))
        palette.setColor(group, QPalette.Light, elevated)
        palette.setColor(group, QPalette.Midlight, elevated)
        palette.setColor(group, QPalette.Mid, inner)
        palette.setColor(group, QPalette.Dark, bg)
        palette.setColor(group, QPalette.Shadow, bg)
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, disabled_text)
    return palette


def get_global_stylesheet() -> str:
    """Genera la hoja de estilos global QSS para la aplicación."""
    return f"""
    QMainWindow, QWidget#rootWidget {{
        background-color: {COLOR_BG_BASE};
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_SANS};
        font-size: 16px;
    }}

    QFrame[class="elevated-card"], QWidget[class="elevated-card"] {{
        background-color: {COLOR_SURFACE_ELEVATED};
        border: 1px solid {rgba(COLOR_INTERACTIVE_IDLE, 0.14)};
        border-radius: 8px;
        padding: 12px;
        color: {COLOR_TEXT_PRIMARY};
    }}

    QLabel {{
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_SANS};
    }}

    QLabel.title {{
        font-size: 26px;
        font-weight: 600;
        color: {COLOR_TEXT_PRIMARY};
        letter-spacing: 0.02em;
    }}

    QLabel.subtitle {{
        font-size: 16px;
        color: {COLOR_INTERACTIVE_IDLE};
        font-style: italic;
    }}

    QLabel.section-title {{
        font-size: 17px;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {COLOR_INTERACTIVE_IDLE};
    }}

    QLabel[class="field-hint"] {{
        color: {COLOR_TEXT_MUTED};
        font-size: 13px;
        background: transparent;
    }}

    QLabel[class="grid-hint"] {{
        color: {COLOR_FEEDBACK_ERROR};
        font-size: 13px;
        font-weight: 600;
        background: transparent;
        padding: 2px 4px;
    }}

    QPushButton {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 15px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QPushButton:pressed {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QPushButton:focus {{
        outline: none;
        border: 2px solid {COLOR_TEXT_PRIMARY};
    }}

    QPushButton:disabled {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: {COLOR_TEXT_DISABLED};
        border-color: {COLOR_INTERACTIVE_DISABLED};
    }}

    QPushButton#primaryAction, QPushButton[class="primaryAction"] {{
        background-color: {COLOR_FEEDBACK_SUCCESS};
        color: {COLOR_BG_BASE};
        border: 1px solid {COLOR_FEEDBACK_SUCCESS};
        border-radius: 6px;
        font-size: 15px;
        font-weight: 700;
        padding: 8px 18px;
    }}

    QPushButton#primaryAction:hover, QPushButton[class="primaryAction"]:hover {{
        background-color: {COLOR_SUCCESS_HOVER};
        color: {COLOR_BG_BASE};
        border: 1px solid {COLOR_SUCCESS_HOVER};
    }}
    QPushButton#primaryAction:focus, QPushButton[class="primaryAction"]:focus {{
        border: 2px solid {COLOR_TEXT_PRIMARY};
    }}
    QPushButton#primaryAction:disabled, QPushButton[class="primaryAction"]:disabled {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: {COLOR_TEXT_DISABLED};
        border: 1px solid {COLOR_INTERACTIVE_DISABLED};
    }}

    QPushButton#secondaryAction, QPushButton[class="secondaryAction"] {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        font-size: 15px;
        font-weight: 600;
        padding: 8px 16px;
    }}

    QPushButton#secondaryAction:hover, QPushButton[class="secondaryAction"]:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}
    QPushButton#secondaryAction:checked, QPushButton[class="secondaryAction"]:checked {{
        background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.22)};
        color: {COLOR_TEXT_PRIMARY};
        border: 2px solid {COLOR_INTERACTIVE_IDLE};
    }}
    QPushButton#secondaryAction:focus, QPushButton[class="secondaryAction"]:focus {{
        border: 2px solid {COLOR_TEXT_PRIMARY};
    }}
    QPushButton#secondaryAction:disabled, QPushButton[class="secondaryAction"]:disabled {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: {COLOR_TEXT_DISABLED};
        border-color: {COLOR_INTERACTIVE_DISABLED};
    }}

    QPushButton[class="chip"] {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {rgba(COLOR_INTERACTIVE_IDLE, 0.55)};
        border-radius: 11px;
        font-size: 13px;
        font-weight: 600;
        padding: 2px 10px;
        min-height: 20px;
    }}
    QPushButton[class="chip"]:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QPushButton[class="link-action"] {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: none;
        border-bottom: 1px dashed {COLOR_INTERACTIVE_IDLE};
        border-radius: 0px;
        font-size: 14px;
        font-weight: 600;
        padding: 2px 2px;
    }}
    QPushButton[class="link-action"]:hover {{
        color: {COLOR_TEXT_PRIMARY};
        background-color: transparent;
        border-bottom: 1px solid {COLOR_TEXT_PRIMARY};
    }}

    QPushButton#deleteAction, QPushButton[class="deleteAction"], QPushButton[class="delete-btn"] {{
        background-color: transparent;
        color: {COLOR_FEEDBACK_ERROR};
        border: 1px solid {rgba(COLOR_FEEDBACK_ERROR, 0.45)};
        border-radius: 4px;
        font-size: 18px;
        font-weight: 700;
        padding: 0px;
        min-width: 28px;
        max-width: 32px;
        min-height: 28px;
        max-height: 32px;
    }}

    QPushButton#deleteAction:hover, QPushButton[class="deleteAction"]:hover, QPushButton[class="delete-btn"]:hover {{
        background-color: {COLOR_FEEDBACK_ERROR};
        color: {readable_text_on(COLOR_FEEDBACK_ERROR)};
        border: 1px solid {COLOR_FEEDBACK_ERROR};
    }}

    QPushButton#modeToggle, QPushButton[class="modeToggle"] {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        padding: 6px 12px;
    }}
    QPushButton#modeToggle:checked, QPushButton[class="modeToggle"]:checked {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
    }}
    QPushButton#modeToggle:hover, QPushButton[class="modeToggle"]:hover {{
        background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.28)};
        color: {COLOR_TEXT_PRIMARY};
    }}
    QPushButton#modeToggle:checked:hover, QPushButton[class="modeToggle"]:checked:hover {{
        background-color: {COLOR_INTERACTIVE_HOVER};
        color: {COLOR_BG_BASE};
    }}
    QPushButton#modeToggle:focus, QPushButton[class="modeToggle"]:focus {{
        border: 2px solid {COLOR_TEXT_PRIMARY};
    }}
    QPushButton#modeToggle:disabled, QPushButton[class="modeToggle"]:disabled {{
        background-color: transparent;
        color: {COLOR_TEXT_DISABLED};
        border: 1px dashed {COLOR_TEXT_DISABLED};
    }}

    QWidget#modularNavigationBar {{
        background: transparent;
    }}
    QFrame#navSegmentBar {{
        background-color: {COLOR_BG_BASE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 8px;
    }}
    QPushButton#navSegment {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 14px;
        font-weight: 600;
        font-family: {FONT_FAMILY_SANS};
    }}
    QPushButton#navSegment:hover {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: {COLOR_TEXT_PRIMARY};
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QPushButton#navSegment:checked {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
        border: none;
        border-bottom: 2px solid {COLOR_INTERACTIVE_IDLE};
    }}
    QPushButton#navSegment:checked:hover {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
    }}

    QPushButton#headerTool {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {rgba(COLOR_INTERACTIVE_IDLE, 0.55)};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton#headerTool:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QMenu {{
        background-color: {COLOR_SURFACE_INNER};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        padding: 6px;
        font-size: 15px;
    }}
    QMenu::item {{
        padding: 8px 18px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {COLOR_SURFACE_ELEVATED};
    }}
    QMenu::item:disabled {{
        color: {COLOR_TEXT_DISABLED};
    }}
    QMenu::separator {{
        height: 1px;
        background: {COLOR_SURFACE_ELEVATED};
        margin: 4px 8px;
    }}

    QLineEdit[class="matrix-cell"] {{
        background-color: transparent;
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_MONO};
        font-size: 14px;
        border: none;
        border-bottom: 1px solid {COLOR_TEXT_DISABLED};
        border-radius: 0px;
        padding: 4px 2px;
        qproperty-alignment: AlignCenter;
    }}

    QLineEdit[class="matrix-cell"]:focus {{
        border: none;
        border-bottom: 2px solid {COLOR_TEXT_PRIMARY};
        background-color: {rgba(COLOR_TEXT_PRIMARY, 0.06)};
    }}

    QLineEdit[class="matrix-cell-error"] {{
        background-color: {rgba(COLOR_FEEDBACK_ERROR, 0.12)};
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_MONO};
        font-size: 14px;
        border: none;
        border-bottom: 2px solid {COLOR_FEEDBACK_ERROR};
        border-radius: 0px;
        padding: 4px 2px;
        qproperty-alignment: AlignCenter;
    }}

    QLineEdit[class="matrix-cell"][highlighted="true"] {{
        background-color: {rgba(COLOR_FEEDBACK_SUCCESS, 0.32)};
        border-bottom: 2px solid {COLOR_FEEDBACK_SUCCESS};
    }}

    QLineEdit[class="matrix-cell"][flash="true"] {{
        background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.30)};
        border-bottom: 2px solid {COLOR_INTERACTIVE_IDLE};
    }}

    QLineEdit[class="matrix-cell"][alert="true"] {{
        background-color: {rgba(COLOR_ACCENT_WARNING, 0.22)};
        border-bottom: 2px solid {COLOR_ACCENT_WARNING};
    }}

    QPushButton[class="ghost-cell"] {{
        background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.08)};
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px dashed {COLOR_INTERACTIVE_IDLE};
        border-radius: 4px;
        font-size: 18px;
        font-weight: bold;
        padding: 0px;
        min-width: 28px;
        min-height: 28px;
    }}

    QPushButton[class="ghost-cell"]:hover {{
        background-color: {rgba(COLOR_INTERACTIVE_IDLE, 0.28)};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_TEXT_PRIMARY};
    }}

    QSplitter::handle:horizontal {{
        background: {COLOR_BG_BASE};
        width: 8px;
    }}
    QSplitter::handle:vertical {{
        background: {COLOR_BG_BASE};
        height: 8px;
    }}

    QSpinBox, QComboBox {{
        background-color: {COLOR_SURFACE_INNER};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 15px;
        font-family: {FONT_FAMILY_SANS};
        min-height: 28px;
    }}
    QSpinBox:focus, QComboBox:focus {{
        border: 2px solid {COLOR_TEXT_PRIMARY};
    }}
    QSpinBox:disabled, QComboBox:disabled {{
        color: {COLOR_TEXT_DISABLED};
        border-color: {COLOR_INTERACTIVE_DISABLED};
    }}
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        background: {COLOR_SURFACE_ELEVATED};
        border-left: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-bottom: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-top-right-radius: 5px;
        width: 22px;
    }}
    QSpinBox::up-button:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
    }}
    QSpinBox::up-arrow {{
        image: url("{_UP_ARROW_SVG}");
        width: 10px;
        height: 6px;
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        background: {COLOR_SURFACE_ELEVATED};
        border-left: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-bottom-right-radius: 5px;
        width: 22px;
    }}
    QSpinBox::down-button:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
    }}
    QSpinBox::down-arrow {{
        image: url("{_DOWN_ARROW_SVG}");
        width: 10px;
        height: 6px;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 26px;
        border-left: 1px solid {COLOR_INTERACTIVE_IDLE};
        background: {COLOR_SURFACE_ELEVATED};
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
    }}
    QComboBox::drop-down:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
    }}
    QComboBox::down-arrow {{
        image: url("{_DOWN_ARROW_SVG}");
        width: 10px;
        height: 6px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_SURFACE_INNER};
        color: {COLOR_TEXT_PRIMARY};
        selection-background-color: {COLOR_SURFACE_ELEVATED};
        selection-color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        outline: none;
    }}

    QCheckBox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: 14px;
        spacing: 8px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 4px;
        background: {COLOR_SURFACE_INNER};
    }}
    QCheckBox::indicator:checked {{
        background: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: {COLOR_INTERACTIVE_DISABLED};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {COLOR_INTERACTIVE_IDLE};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {COLOR_TEXT_PRIMARY};
        border: 2px solid {COLOR_INTERACTIVE_IDLE};
        width: 14px;
        height: 14px;
        margin: -7px 0;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:disabled {{
        background: {COLOR_INTERACTIVE_DISABLED};
        border-color: {COLOR_INTERACTIVE_DISABLED};
    }}

    QTabWidget::pane {{
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 8px;
        background: {COLOR_BG_BASE};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        padding: 10px 20px;
        border: none;
        border-bottom: 2px solid transparent;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: 600;
        font-size: 15px;
        font-family: {FONT_FAMILY_SANS};
    }}
    QTabBar::tab:hover {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: {COLOR_TEXT_PRIMARY};
    }}
    QTabBar::tab:selected {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
        border-bottom: 2px solid {COLOR_INTERACTIVE_IDLE};
    }}

    QPushButton#opSelect, QPushButton[class="opSelect"] {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        min-width: 52px;
        min-height: 44px;
        font-size: 22px;
        font-weight: 700;
        padding: 8px;
    }}
    QPushButton#opSelect:hover, QPushButton[class="opSelect"]:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}
    QPushButton#opSelect:checked, QPushButton[class="opSelect"]:checked {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
    }}

    QScrollBar:vertical {{
        background: {COLOR_BG_BASE};
        width: 14px;
        margin: 2px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_INTERACTIVE_IDLE};
        min-height: 28px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: transparent;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: {COLOR_BG_BASE};
        height: 14px;
        margin: 2px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_INTERACTIVE_IDLE};
        min-width: 28px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: transparent;
    }}

    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background: {COLOR_INTERACTIVE_HOVER};
    }}

    QLineEdit#scalarField, QLineEdit[class="scalar-field"] {{
        background-color: {COLOR_SURFACE_INNER};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 8px 12px;
        font-family: {FONT_FAMILY_MONO};
        font-size: 18px;
        qproperty-alignment: AlignCenter;
        min-width: 88px;
    }}
    QLineEdit#scalarField:focus, QLineEdit[class="scalar-field"]:focus {{
        border: 2px solid {COLOR_TEXT_PRIMARY};
    }}
    QLineEdit[invalid="true"] {{
        border: 2px solid {COLOR_FEEDBACK_ERROR};
        background-color: {rgba(COLOR_FEEDBACK_ERROR, 0.12)};
    }}

    QLineEdit[class="text-field"] {{
        background-color: {COLOR_SURFACE_INNER};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 6px 10px;
        font-family: {FONT_FAMILY_MONO};
        font-size: 14px;
        selection-background-color: {COLOR_INTERACTIVE_IDLE};
        selection-color: {COLOR_SURFACE_INNER};
    }}

    QToolTip {{
        background-color: {COLOR_SURFACE_INNER};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 5px;
        padding: 6px 10px;
        font-size: 13px;
        font-family: {FONT_FAMILY_SANS};
    }}

    QFrame#toast {{
        background-color: {COLOR_SURFACE_INNER};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-left: 4px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 8px;
    }}
    QFrame#toast[kind="success"] {{
        border-left: 4px solid {COLOR_FEEDBACK_SUCCESS};
    }}
    QFrame#toast[kind="warning"] {{
        border-left: 4px solid {COLOR_ACCENT_WARNING};
    }}
    QFrame#toast[kind="error"] {{
        border-left: 4px solid {COLOR_FEEDBACK_ERROR};
    }}
    QFrame#toast QLabel {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: 14px;
        background: transparent;
    }}
    QFrame#toast QPushButton {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 13px;
        font-weight: 700;
    }}
    QFrame#toast QPushButton:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QScrollArea {{
        background: transparent;
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget#qt_scrollarea_viewport {{
        background: transparent;
        background-color: transparent;
    }}
    QWidget#linearSystemsView, QWidget#matrixOperationsView, QWidget#vectorsView {{
        background-color: {COLOR_BG_BASE};
    }}
    """ + get_message_box_stylesheet()
