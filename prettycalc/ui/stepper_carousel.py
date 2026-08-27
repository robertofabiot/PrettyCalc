"""Carrusel de pasos con notación de libro: corchetes, fracciones apiladas y fórmulas."""

from __future__ import annotations
from typing import List, Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QFrame = object  # type: ignore

from prettycalc.core.tracer import CalculationStep
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.mathtext import latex_to_book_html
from prettycalc.ui.theme import (
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    COLOR_FEEDBACK_SUCCESS,
    FONT_FAMILY_SANS,
    apply_widget_class,
)


class AlgorithmStepperCarousel(QFrame):
    """Stepper para navegar las transformaciones elementales del algoritmo."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self._steps: List[CalculationStep] = []
        self._current_index: int = 0
        self._display_mode: str = "fraction"
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        self.prev_btn = QPushButton("Anterior")
        self.prev_btn.setFixedWidth(118)
        self.prev_btn.clicked.connect(self.prev_step)
        nav_layout.addWidget(self.prev_btn)

        self.step_label = QLabel("Paso 0 de 0")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setMinimumWidth(140)
        self.step_label.setStyleSheet(
            f"font-weight: 600; font-size: 17px; letter-spacing: 0.04em; color: {COLOR_TEXT_PRIMARY};"
        )
        nav_layout.addWidget(self.step_label, stretch=1)

        self.next_btn = QPushButton("Siguiente")
        self.next_btn.setFixedWidth(118)
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)

        self.mode_btn = QPushButton("Fracciones")
        self.mode_btn.setObjectName("modeToggle")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.setToolTip("Interruptor: vista actual en fracciones o decimales")
        self.mode_btn.setMinimumWidth(128)
        apply_widget_class(self.mode_btn, "modeToggle")
        nav_layout.addWidget(self.mode_btn)

        layout.addLayout(nav_layout)

        formula_box = QFrame()
        formula_box.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_SURFACE_INNER};
                border: none;
                border-radius: 4px;
            }}
        """)
        formula_layout = QVBoxLayout(formula_box)
        formula_layout.setContentsMargins(14, 12, 14, 12)

        self.formula_label = QLabel("")
        self.formula_label.setAlignment(Qt.AlignCenter)
        self.formula_label.setTextFormat(Qt.RichText)
        self.formula_label.setWordWrap(True)
        formula_layout.addWidget(self.formula_label)
        layout.addWidget(formula_box)

        self.matrix_view = BookMatrixWidget()
        self.matrix_view.setStyleSheet(f"background-color: {COLOR_SURFACE_INNER}; border-radius: 4px;")
        layout.addWidget(self.matrix_view, stretch=1)

        heuristic_box = QFrame()
        heuristic_box.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_SURFACE_INNER};
                border-left: 3px solid {COLOR_FEEDBACK_SUCCESS};
                border-radius: 2px;
            }}
        """)
        heuristic_layout = QHBoxLayout(heuristic_box)
        heuristic_layout.setContentsMargins(14, 12, 14, 12)

        self.heuristic_label = QLabel("")
        self.heuristic_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.heuristic_label.setWordWrap(True)
        self.heuristic_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_PRIMARY};
                font-size: 18px;
                font-style: italic;
                font-family: {FONT_FAMILY_SANS};
                font-weight: 500;
            }}
        """)
        heuristic_layout.addWidget(self.heuristic_label)
        layout.addWidget(heuristic_box)

        self.mode_btn.toggled.connect(self._on_mode_toggled)
        self._update_view()

    def set_steps(self, steps: List[CalculationStep]) -> None:
        self._steps = steps
        self._current_index = 0
        self._update_view()

    def prev_step(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._update_view(animate=False)

    def next_step(self) -> None:
        if self._current_index < len(self._steps) - 1:
            self._current_index += 1
            self._update_view(animate=True)

    def _on_mode_toggled(self, checked: bool) -> None:
        self._display_mode = "fraction" if checked else "decimal"
        self.mode_btn.setText("Fracciones" if checked else "Decimales")
        self._update_view(animate=False)

    def _update_view(self, animate: bool = False) -> None:
        if not self._steps:
            self.step_label.setText("Sin pasos")
            self.formula_label.setText(
                f"<span style='color:{COLOR_TEXT_MUTED}; font-style:italic; font-size:16px;'>Esperando resolución</span>"
            )
            self.heuristic_label.setText("Ingresa el sistema y pulsa Resolver.")
            self.matrix_view.clear()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        total = len(self._steps)
        curr = self._current_index
        step = self._steps[curr]

        if curr == 0:
            self.step_label.setText(f"1 / {total}   inicial")
        else:
            self.step_label.setText(f"{curr + 1} / {total}")

        self.formula_label.setText(latex_to_book_html(step.latex_formula))
        self.heuristic_label.setText(step.heuristic_text)

        self.prev_btn.setEnabled(curr > 0)
        self.next_btn.setEnabled(curr < total - 1)

        self.matrix_view.set_matrix(
            step.matrix,
            split_col=step.split_col,
            pivot=step.pivot_pos,
            mode=self._display_mode,
            actor_row=step.actor_row,
            affected_rows=step.affected_rows,
            animate=animate,
        )
