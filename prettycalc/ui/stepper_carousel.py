"""Visor de Pasos en Carrusel / Stepper con notación matemática limpia y resaltado sutil de pivotes."""

from __future__ import annotations
import re
from typing import List, Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QFrame,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
except ImportError:
    QFrame = object  # type: ignore

from prettycalc.core.tracer import CalculationStep
from prettycalc.core.types import format_scalar
from prettycalc.ui.theme import (
    COLOR_INTERACTIVE_IDLE,
    COLOR_INTERACTIVE_DISABLED,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_SURFACE_ELEVATED,
    COLOR_BG_BASE,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
)


def latex_to_pretty_text(latex: str) -> str:
    """Convierte fórmulas LaTeX crudas a notación matemática legible con HTML Rich Text."""
    if not latex:
        return ""

    if "\\text{" in latex:
        # Títulos de estado inicial tipo \text{Sistema Inicial } [A \mid b]
        text_clean = re.sub(r"\\text\{([^}]+)\}", r"\1", latex)
        text_clean = text_clean.replace("\\mid", "│")
        return f"<b>{text_clean}</b>"

    result = latex

    # Reemplazar fracciones LaTeX \frac{a}{b} -> (a/b)
    result = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1/\2)", result)

    # Reemplazar flechas LaTeX
    result = result.replace("\\underset{\\sim}\\rightarrow", "→")
    result = result.replace("\\leftrightarrow", "↔")
    result = result.replace("\\cdot", "·")

    # Reemplazar f_{i} por F<sub>i</sub>
    result = re.sub(r"f_\{(\d+)\}", r"F<sub>\1</sub>", result)
    result = re.sub(r"f(\d+)", r"F<sub>\1</sub>", result)

    return f"<span style='font-size: 16px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};'>{result}</span>"


class AlgorithmStepperCarousel(QFrame):
    """Componente Stepper/Carrusel para navegar paso a paso por las transformaciones del algoritmo."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "elevated-card")
        self._steps: List[CalculationStep] = []
        self._current_index: int = 0
        self._display_mode: str = "fraction"

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 1. Barra de Navegación Superior
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.setFixedWidth(110)
        self.prev_btn.clicked.connect(self.prev_step)
        nav_layout.addWidget(self.prev_btn)

        self.step_label = QLabel("Paso 0 de 0")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {COLOR_TEXT_PRIMARY};"
        )
        nav_layout.addWidget(self.step_label, stretch=1)

        self.next_btn = QPushButton("Siguiente ▶")
        self.next_btn.setFixedWidth(110)
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)

        self.mode_btn = QPushButton("Modo: Fracciones")
        self.mode_btn.setToolTip("Alternar entre vista de Fracciones y Decimales")
        self.mode_btn.clicked.connect(self._toggle_mode)
        nav_layout.addWidget(self.mode_btn)

        layout.addLayout(nav_layout)

        # 2. Caja de Fórmula Matemática Elegante
        formula_box = QFrame()
        formula_box.setStyleSheet(f"""
            QFrame {{
                background-color: #242028;
                border: 1px solid {COLOR_SURFACE_ELEVATED};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        formula_layout = QHBoxLayout(formula_box)
        formula_layout.setContentsMargins(8, 4, 8, 4)

        self.formula_label = QLabel("")
        self.formula_label.setAlignment(Qt.AlignCenter)
        self.formula_label.setTextFormat(Qt.RichText)
        formula_layout.addWidget(self.formula_label)
        layout.addWidget(formula_box)

        # 3. Tabla Visual de la Matriz Centrada y Proporcionada
        self.matrix_table = QTableWidget()
        self.matrix_table.setShowGrid(True)
        self.matrix_table.horizontalHeader().setVisible(False)
        self.matrix_table.verticalHeader().setVisible(False)
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matrix_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #242028;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_ELEVATED};
                border-radius: 8px;
                font-family: {FONT_FAMILY_MONO};
                font-size: 15px;
                gridline-color: #3A3642;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
        """)
        layout.addWidget(self.matrix_table, stretch=1)

        # 4. Tarjeta Heurística Inferior
        heuristic_box = QFrame()
        heuristic_box.setStyleSheet(f"""
            QFrame {{
                background-color: #2A2632;
                border-left: 3px solid {COLOR_FEEDBACK_SUCCESS};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        heuristic_layout = QHBoxLayout(heuristic_box)
        heuristic_layout.setContentsMargins(10, 6, 10, 6)

        self.heuristic_label = QLabel("")
        self.heuristic_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.heuristic_label.setWordWrap(True)
        self.heuristic_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_PRIMARY};
                font-size: 13px;
                font-family: {FONT_FAMILY_SANS};
            }}
        """)
        heuristic_layout.addWidget(self.heuristic_label)
        layout.addWidget(heuristic_box)

        self._update_view()

    def set_steps(self, steps: List[CalculationStep]) -> None:
        self._steps = steps
        self._current_index = 0
        self._update_view()

    def prev_step(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._update_view()

    def next_step(self) -> None:
        if self._current_index < len(self._steps) - 1:
            self._current_index += 1
            self._update_view()

    def _toggle_mode(self) -> None:
        self._display_mode = "decimal" if self._display_mode == "fraction" else "fraction"
        self.mode_btn.setText("Modo: " + ("Fracciones" if self._display_mode == "fraction" else "Decimales"))
        self._update_view()

    def _update_view(self) -> None:
        if not self._steps:
            self.step_label.setText("Sin pasos registrados")
            self.formula_label.setText("<span style='color:#7A7585;'>Esperando resolución</span>")
            self.heuristic_label.setText("Ingresa los datos en la matriz y presiona 'Resolver Sistema'.")
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        total = len(self._steps)
        curr = self._current_index
        step = self._steps[curr]

        self.step_label.setText(f"Paso {curr} de {total - 1}")
        self.formula_label.setText(latex_to_pretty_text(step.latex_formula))
        self.heuristic_label.setText(f"💡 <i>{step.heuristic_text}</i>")

        self.prev_btn.setEnabled(curr > 0)
        self.next_btn.setEnabled(curr < total - 1)

        matrix = step.matrix
        self.matrix_table.setRowCount(matrix.rows)
        self.matrix_table.setColumnCount(matrix.cols)

        pivot_r, pivot_c = step.pivot_pos if step.pivot_pos else (-1, -1)

        for r in range(matrix.rows):
            for c in range(matrix.cols):
                val = matrix.get(r, c)
                val_str = format_scalar(val, mode=self._display_mode)
                item = QTableWidgetItem(val_str)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                # Resaltado limpio del pivote
                if r == pivot_r and c == pivot_c:
                    item.setBackground(QColor(COLOR_FEEDBACK_SUCCESS))
                    item.setForeground(QColor(COLOR_BG_BASE))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif step.split_col is not None and c == step.split_col:
                    # Columna b
                    item.setForeground(QColor(COLOR_INTERACTIVE_IDLE))

                self.matrix_table.setItem(r, c, item)
