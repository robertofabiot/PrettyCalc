"""Preferencias de apariencia y ayuda de atajos de teclado.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (accesibilidad): tema oscuro, alto contraste o claro, y escala
global de la interfaz para baja visión. La escala usa ``QT_SCALE_FACTOR``,
que Qt solo lee al arrancar; por eso el diálogo ofrece reiniciar en un clic.
"""

from __future__ import annotations

import sys
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import QProcess, Qt
except ImportError:  # pragma: no cover
    QDialog = object  # type: ignore

from prettycalc.ui.theme import (
    ACTIVE_SCALE,
    ACTIVE_THEME,
    COLOR_TEXT_MUTED,
    PALETTES,
    SCALE_OPTIONS,
    THEME_LABELS,
    apply_message_box_theme,
    contrast_ratio,
    save_appearance,
)


SHORTCUTS = (
    ("Navegación", (
        ("Ctrl+1 … Ctrl+6", "Cambiar de módulo"),
        ("F1", "Mostrar esta ayuda de atajos"),
        ("Ctrl+,", "Preferencias de apariencia y accesibilidad"),
    )),
    ("Cuadrículas", (
        ("Tab / Mayús+Tab", "Celda siguiente / anterior"),
        ("Flechas, Intro", "Moverse entre celdas (↓ en la última fila agrega una ecuación)"),
        ("Ctrl+Intro", "Calcular o resolver con los datos actuales"),
        ("Ctrl+Z / Ctrl+Y", "Deshacer / rehacer reinicios, ejemplos, pegados y cambios de tamaño"),
        ("Ctrl+Supr", "Eliminar la fila de la celda activa"),
        ("Ctrl+Mayús+Supr", "Eliminar la columna de la celda activa"),
        ("Ctrl+C / Ctrl+V", "Copiar / pegar la matriz completa (TSV, Excel, LaTeX)"),
    )),
    ("Procedimiento", (
        ("← / →", "Paso anterior / siguiente (con el carrusel enfocado)"),
        ("Inicio / Fin", "Primer / último paso"),
        ("Exportar", "PDF, HTML, LaTeX o texto del procedimiento completo"),
    )),
)


def shortcuts_html() -> str:
    blocks = []
    for section, rows in SHORTCUTS:
        items = "".join(
            f"<tr><td style='padding:3px 14px 3px 0; font-family:Fira Code; font-weight:700;'>{keys}</td>"
            f"<td style='padding:3px 0;'>{text}</td></tr>"
            for keys, text in rows
        )
        blocks.append(f"<h3 style='margin:10px 0 4px 0;'>{section}</h3><table>{items}</table>")
    return "".join(blocks)


class ShortcutsDialog(QDialog):
    """Hoja de referencia de atajos (Nielsen #10: ayuda y documentación)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Atajos de teclado — PrettyCalc")
        self.setObjectName("shortcutsDialog")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        label = QLabel(shortcuts_html())
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        layout.addWidget(label)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        close.setDefault(True)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)
        apply_message_box_theme(self)
        self.resize(560, 520)


class PreferencesDialog(QDialog):
    """Tema y escala de interfaz, guardados para el próximo arranque."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Apariencia y accesibilidad — PrettyCalc")
        self.setObjectName("preferencesDialog")
        self.restart_requested = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        intro = QLabel(
            "Elige el tema y el tamaño de la interfaz. Todos los temas cumplen el "
            "contraste WCAG 2.1 AA (4.5:1) para el texto principal. Las fuentes vienen "
            "incluidas con PrettyCalc, así que se ve igual en Windows y en Linux."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(10)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        for key, label in THEME_LABELS.items():
            self.theme_combo.addItem(label, key)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(ACTIVE_THEME)))
        form.addRow("Tema", self.theme_combo)

        self.scale_combo = QComboBox()
        self.scale_combo.setObjectName("scaleCombo")
        for factor in SCALE_OPTIONS:
            self.scale_combo.addItem(f"{int(round(factor * 100))} %", factor)
        current = min(range(len(SCALE_OPTIONS)), key=lambda i: abs(SCALE_OPTIONS[i] - ACTIVE_SCALE))
        self.scale_combo.setCurrentIndex(current)
        form.addRow("Tamaño de la interfaz", self.scale_combo)
        layout.addLayout(form)

        self.contrast_label = QLabel("")
        self.contrast_label.setObjectName("contrastReport")
        self.contrast_label.setWordWrap(True)
        self.contrast_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(self.contrast_label)
        self.theme_combo.currentIndexChanged.connect(self._refresh_report)
        self._refresh_report()

        note = QLabel("Los cambios se aplican al reiniciar PrettyCalc.")
        note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Guardar")
        save.setObjectName("savePreferences")
        save.clicked.connect(self._save)
        restart = QPushButton("Guardar y reiniciar")
        restart.setObjectName("saveAndRestart")
        restart.setDefault(True)
        restart.clicked.connect(self._save_and_restart)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        buttons.addWidget(restart)
        layout.addLayout(buttons)
        apply_message_box_theme(self)
        self.resize(540, 320)

    def selected_theme(self) -> str:
        return str(self.theme_combo.currentData())

    def selected_scale(self) -> float:
        return float(self.scale_combo.currentData())

    def _refresh_report(self) -> None:
        palette = PALETTES[self.selected_theme()]
        text = contrast_ratio(palette["text_primary"], palette["surface_elevated"])
        muted = contrast_ratio(palette["text_muted"], palette["surface_elevated"])
        self.contrast_label.setText(
            f"Contraste en tarjetas: texto {text:.1f}:1 · texto secundario {muted:.1f}:1"
        )

    def _save(self) -> None:
        save_appearance(self.selected_theme(), self.selected_scale())
        self.accept()

    def _save_and_restart(self) -> None:
        save_appearance(self.selected_theme(), self.selected_scale())
        self.restart_requested = True
        self.accept()


def restart_application() -> bool:
    """Relanza PrettyCalc con los mismos argumentos y cierra la instancia actual."""
    app = QApplication.instance()
    if app is None:
        return False
    started = QProcess.startDetached(sys.executable, sys.argv)
    if isinstance(started, tuple):
        started = started[0]
    if started:
        app.quit()
    return bool(started)
