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

# Constantes de Color
COLOR_BG_BASE = "#1A181B"
COLOR_SURFACE_ELEVATED = "#564D65"
COLOR_TEXT_PRIMARY = "#E0FBFC"
COLOR_INTERACTIVE_IDLE = "#98C1D9"
COLOR_INTERACTIVE_DISABLED = "#3A3642"
COLOR_FEEDBACK_ERROR = "#EE6C4D"
COLOR_FEEDBACK_SUCCESS = "#81B29A"
COLOR_ACCENT_WARNING = "#E9C46A"

# Familias Tipográficas
FONT_FAMILY_MONO = "Fira Code, Roboto Mono, Courier New, monospace"
FONT_FAMILY_SANS = "Inter, Segoe UI, Ubuntu, sans-serif"


def get_global_stylesheet() -> str:
    """Genera la hoja de estilos global QSS para la aplicación."""
    return f"""
    QMainWindow, QWidget#rootWidget {{
        background-color: {COLOR_BG_BASE};
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_SANS};
        font-size: 13px;
    }}

    /* Paneles y Cards Elevadas */
    QFrame.elevated-card, QWidget.elevated-card {{
        background-color: {COLOR_SURFACE_ELEVATED};
        border-radius: 8px;
        padding: 12px;
        color: {COLOR_TEXT_PRIMARY};
    }}

    /* Tipografía y Etiquetas */
    QLabel {{
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_SANS};
    }}

    QLabel.title {{
        font-size: 18px;
        font-weight: bold;
        color: {COLOR_TEXT_PRIMARY};
    }}

    QLabel.subtitle {{
        font-size: 13px;
        color: {COLOR_INTERACTIVE_IDLE};
        font-style: italic;
    }}

    /* Botones Principales */
    QPushButton {{
        background-color: {COLOR_SURFACE_ELEVATED};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {COLOR_INTERACTIVE_IDLE};
        color: {COLOR_BG_BASE};
    }}

    QPushButton:pressed {{
        background-color: {COLOR_FEEDBACK_SUCCESS};
        color: {COLOR_BG_BASE};
    }}

    QPushButton:disabled {{
        background-color: {COLOR_INTERACTIVE_DISABLED};
        color: #7A7585;
        border-color: {COLOR_INTERACTIVE_DISABLED};
    }}

    /* Celdas de la Matriz */
    QLineEdit.matrix-cell {{
        background-color: #2A262E;
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_MONO};
        font-size: 14px;
        border: 1px solid {COLOR_INTERACTIVE_IDLE};
        border-radius: 4px;
        padding: 4px;
        qproperty-alignment: AlignCenter;
    }}

    QLineEdit.matrix-cell:focus {{
        border: 2px solid {COLOR_TEXT_PRIMARY};
        background-color: #35303B;
    }}

    QLineEdit.matrix-cell-error {{
        border: 2px solid {COLOR_FEEDBACK_ERROR} !important;
        background-color: #3E2426 !important;
    }}

    /* Celdas Fantasma (Ghosting) */
    QPushButton.ghost-cell {{
        background-color: transparent;
        color: #7A7585;
        border: 1px dashed #7A7585;
        border-radius: 4px;
        font-size: 16px;
        font-weight: bold;
    }}

    QPushButton.ghost-cell:hover {{
        background-color: rgba(152, 193, 217, 0.15);
        color: {COLOR_INTERACTIVE_IDLE};
        border: 1px dashed {COLOR_INTERACTIVE_IDLE};
    }}

    /* Scrollbars */
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
    }}
    """
