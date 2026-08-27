"""Design System Cromático y Hojas de Estilo QSS para PrettyCalc.

Tokens Oficiales:
- color-bg-base: #1A181B (Shadow Grey)
- color-surface-elevated: #564D65 (Vintage Grape)
- color-text-primary: #E0FBFC (Light Cyan)
- color-interactive-idle: #98C1D9 (Powder Blue)
- color-interactive-disabled: #3A3642 (Dimmed Grape)
- color-feedback-error: #EE6C4D (Burnt Peach)
- color-feedback-success: #81B29A (Muted Sage)
"""

from __future__ import annotations

from typing import Any

try:
    from PySide6.QtCore import Qt as _Qt
    _WA_STYLED_BG = _Qt.WA_StyledBackground
except ImportError:
    _WA_STYLED_BG = 0  # type: ignore

# Constantes de Color
COLOR_BG_BASE = "#1A181B"
COLOR_SURFACE_ELEVATED = "#564D65"
COLOR_SURFACE_INNER = "#242028"
COLOR_TEXT_PRIMARY = "#E0FBFC"
COLOR_TEXT_MUTED = "#7A7585"
COLOR_INTERACTIVE_IDLE = "#98C1D9"
COLOR_INTERACTIVE_DISABLED = "#3A3642"
COLOR_FEEDBACK_ERROR = "#EE6C4D"
COLOR_FEEDBACK_SUCCESS = "#81B29A"
COLOR_ACCENT_WARNING = "#E9C46A"

# Familias Tipográficas
FONT_FAMILY_MONO = "Fira Code, Roboto Mono, Courier New, monospace"
FONT_FAMILY_SANS = "Inter, Segoe UI, Ubuntu, sans-serif"


def apply_widget_class(widget: Any, class_name: str) -> None:
    """Asigna la propiedad CSS `class` y fuerza a Qt a reaplicar el QSS."""
    widget.setProperty("class", class_name)
    widget.setAttribute(_WA_STYLED_BG, True)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)


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

    QPushButton:disabled {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: {COLOR_TEXT_MUTED};
        border-color: {COLOR_INTERACTIVE_DISABLED};
    }}

    QPushButton#primaryAction {{
        background-color: {COLOR_FEEDBACK_SUCCESS};
        color: {COLOR_BG_BASE};
        border: none;
        font-size: 16px;
        padding: 10px 20px;
    }}

    QPushButton#primaryAction:hover {{
        background-color: #93C4AE;
        color: {COLOR_BG_BASE};
    }}

    QPushButton#secondaryAction {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        font-size: 15px;
        padding: 10px 18px;
    }}

    QPushButton#secondaryAction:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QPushButton#modeToggle {{
        background-color: transparent;
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        font-size: 15px;
        padding: 8px 12px;
    }}
    QPushButton#modeToggle:checked {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
    }}
    QPushButton#modeToggle:hover {{
        background-color: rgba(152, 193, 217, 0.28);
        color: {COLOR_TEXT_PRIMARY};
    }}
    QPushButton#modeToggle:checked:hover {{
        background-color: #B3D4E6;
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
        color: {COLOR_TEXT_MUTED};
    }}

    QLineEdit[class="matrix-cell"] {{
        background-color: transparent;
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_MONO};
        font-size: 14px;
        border: none;
        border-bottom: 1px solid {COLOR_INTERACTIVE_DISABLED};
        border-radius: 0px;
        padding: 4px 2px;
        qproperty-alignment: AlignCenter;
    }}

    QLineEdit[class="matrix-cell"]:focus {{
        border: none;
        border-bottom: 2px solid {COLOR_TEXT_PRIMARY};
        background-color: rgba(224, 251, 252, 0.06);
    }}

    QLineEdit[class="matrix-cell-error"] {{
        background-color: rgba(238, 108, 77, 0.12);
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_MONO};
        font-size: 14px;
        border: none;
        border-bottom: 2px solid {COLOR_FEEDBACK_ERROR};
        border-radius: 0px;
        padding: 4px 2px;
        qproperty-alignment: AlignCenter;
    }}

    QPushButton[class="ghost-cell"] {{
        background-color: rgba(152, 193, 217, 0.08);
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
        background-color: rgba(152, 193, 217, 0.28);
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_TEXT_PRIMARY};
    }}

    QSplitter::handle:horizontal {{
        background: {COLOR_BG_BASE};
        width: 8px;
    }}

    QScrollBar:vertical, QScrollBar:horizontal {{
        background: {COLOR_BG_BASE};
        border: none;
        width: 8px;
        height: 8px;
    }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background: {COLOR_SURFACE_ELEVATED};
        border-radius: 4px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        background: none;
        width: 0;
        height: 0;
    }}
    """
