"""Visor de Pasos en Carrusel / Stepper con resaltado de pivote y heurística explicativa."""

from __future__ import annotations
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
)


class AlgorithmStepperCarousel(QFrame):
    """Componente Stepper/Carrusel para navegar paso a paso por las transformaciones del algoritmo."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "elevated-card")
        self._steps: List[CalculationStep] = []
        self._current_index: int = 0
        self._display_mode: str = "fraction"  # 'fraction' o 'decimal'

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 1. Barra de Control Superior (Anterior | Indicador | Siguiente | Modo)
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Paso Anterior")
        self.prev_btn.clicked.connect(self.prev_step)
        nav_layout.addWidget(self.prev_btn)

        self.step_label = QLabel("Paso 0 de 0")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        nav_layout.addWidget(self.step_label, stretch=1)

        self.next_btn = QPushButton("Siguiente Paso ▶")
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)

        self.mode_btn = QPushButton("Alternar Formato")
        self.mode_btn.setToolTip("Cambiar entre Fracciones y Decimales")
        self.mode_btn.clicked.connect(self._toggle_mode)
        nav_layout.addWidget(self.mode_btn)

        layout.addLayout(nav_layout)

        # 2. Fórmula LaTeX y Notación Formal
        self.formula_label = QLabel("")
        self.formula_label.setAlignment(Qt.AlignCenter)
        self.formula_label.setStyleSheet(
            f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 15px; font-weight: bold; padding: 4px;"
        )
        layout.addWidget(self.formula_label)

        # 3. Tabla Visual de la Matriz en este paso
        self.matrix_table = QTableWidget()
        self.matrix_table.setShowGrid(True)
        self.matrix_table.horizontalHeader().setVisible(False)
        self.matrix_table.verticalHeader().setVisible(False)
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matrix_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #2A262E;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_ELEVATED};
                border-radius: 6px;
                font-family: {FONT_FAMILY_MONO};
                font-size: 14px;
            }}
            QTableWidget::item {{
                padding: 6px;
                alignment: center;
            }}
        """)
        layout.addWidget(self.matrix_table, stretch=1)

        # 4. Texto Heurístico Explicativo
        self.heuristic_label = QLabel("")
        self.heuristic_label.setAlignment(Qt.AlignCenter)
        self.heuristic_label.setWordWrap(True)
        self.heuristic_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-style: italic; font-size: 13px; padding: 6px;"
        )
        layout.addWidget(self.heuristic_label)

        self._update_view()

    def set_steps(self, steps: List[CalculationStep]) -> None:
        """Carga la secuencia de pasos calculados."""
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
            self.formula_label.setText("")
            self.heuristic_label.setText("Introduce una matriz y presiona Resolver para ver el desglose paso a paso.")
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        total = len(self._steps)
        curr = self._current_index
        step = self._steps[curr]

        self.step_label.setText(f"Paso {curr} de {total - 1}")
        self.formula_label.setText(step.latex_formula)
        self.heuristic_label.setText(f"ℹ️ {step.heuristic_text}")

        # Habilitar/Deshabilitar botones de navegación
        self.prev_btn.setEnabled(curr > 0)
        self.next_btn.setEnabled(curr < total - 1)

        # Renderizar la matriz en la tabla
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

                # Resaltar la celda pivote activa
                if r == pivot_r and c == pivot_c:
                    item.setBackground(QColor(COLOR_FEEDBACK_SUCCESS))
                    item.setForeground(QColor(COLOR_BG_BASE))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif step.split_col is not None and c == step.split_col:
                    # Columna de términos independientes b
                    item.setForeground(QColor(COLOR_INTERACTIVE_IDLE))

                self.matrix_table.setItem(r, c, item)
