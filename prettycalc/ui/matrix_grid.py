"""Cuadrícula interactiva DynamicMatrixGrid con soporte de Ghosting, validación en tiempo real y centrado armónico."""

from __future__ import annotations
from typing import List, Optional
from fractions import Fraction

try:
    from PySide6.QtWidgets import (
        QWidget,
        QGridLayout,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QFrame,
        QSpacerItem,
        QSizePolicy,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QKeyEvent, QFont
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.types import Matrix, parse_scalar, format_scalar
from prettycalc.ui.theme import (
    COLOR_INTERACTIVE_IDLE,
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_SURFACE_ELEVATED,
    FONT_FAMILY_MONO,
)


class MatrixCellEdit(QLineEdit):
    """Celda editable individual con tamaño ergonómico, validación y navegación por teclado."""

    navigate = Signal(int, int, str)

    def __init__(self, row: int, col: int, default_val: str = "0", parent: Optional[QWidget] = None):
        super().__init__(default_val, parent)
        self.row = row
        self.col = col
        self.setFixedSize(56, 36)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Fira Code", 11))
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: #2A262E;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_INTERACTIVE_IDLE};
                border-radius: 5px;
                font-family: {FONT_FAMILY_MONO};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_TEXT_PRIMARY};
                background-color: #35303B;
            }}
        """)
        self.textChanged.connect(self._on_text_changed)
        self._is_valid = True

    def _on_text_changed(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            self._set_error_state(False)
            return

        try:
            parse_scalar(cleaned)
            self._set_error_state(False)
        except Exception:
            self._set_error_state(True)

    def _set_error_state(self, has_error: bool) -> None:
        self._is_valid = not has_error
        if has_error:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {COLOR_FEEDBACK_ERROR};
                    background-color: #3E2426;
                    color: {COLOR_TEXT_PRIMARY};
                    border-radius: 5px;
                    font-family: {FONT_FAMILY_MONO};
                    font-size: 13px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #2A262E;
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_INTERACTIVE_IDLE};
                    border-radius: 5px;
                    font-family: {FONT_FAMILY_MONO};
                    font-size: 13px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {COLOR_TEXT_PRIMARY};
                    background-color: #35303B;
                }}
            """)

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    def get_value(self) -> Fraction:
        text = self.text().strip()
        if not text:
            return Fraction(0, 1)
        return parse_scalar(text)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Up:
            self.navigate.emit(self.row, self.col, "up")
            return
        if event.key() == Qt.Key_Down:
            self.navigate.emit(self.row, self.col, "down")
            return
        if event.key() == Qt.Key_Left and self.cursorPosition() == 0:
            self.navigate.emit(self.row, self.col, "left")
            return
        if event.key() == Qt.Key_Right and self.cursorPosition() == len(self.text()):
            self.navigate.emit(self.row, self.col, "right")
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.navigate.emit(self.row, self.col, "down")
            return

        super().keyPressEvent(event)


class DynamicMatrixGrid(QFrame):
    """Contenedor de cuadrícula matricial aumentada [A | b] centrada geométricamente."""

    matrixChanged = Signal()

    def __init__(self, initial_rows: int = 2, initial_cols: int = 2, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "elevated-card")
        self.num_rows = initial_rows
        self.num_vars = initial_cols
        self.cells: List[List[MatrixCellEdit]] = []

        # Layout exterior con espaciadores para centrar vertical y horizontalmente
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(12, 12, 12, 12)

        self._center_container = QWidget()
        self._grid_layout = QGridLayout(self._center_container)
        self._grid_layout.setSpacing(6)
        self._grid_layout.setVerticalSpacing(6)
        self._grid_layout.setHorizontalSpacing(6)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)

        # Centrar la cuadrícula en el panel
        self._outer_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self._outer_layout.addWidget(self._center_container, 0, Qt.AlignCenter)
        self._outer_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self._build_grid()

    def _build_grid(self) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total_cols = self.num_vars + 1
        self.cells = []

        # Encabezados de columnas (x1, x2, ..., | b)
        for c in range(self.num_vars):
            lbl = QLabel(f"x{c+1}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(20)
            lbl.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-weight: bold; font-size: 12px;")
            self._grid_layout.addWidget(lbl, 0, c)

        # Encabezado de la columna b (términos independientes)
        lbl_b = QLabel("b")
        lbl_b.setAlignment(Qt.AlignCenter)
        lbl_b.setFixedHeight(20)
        lbl_b.setStyleSheet(
            f"color: {COLOR_INTERACTIVE_IDLE}; font-weight: bold; font-size: 13px; border-left: 2px solid {COLOR_INTERACTIVE_IDLE}; padding-left: 2px;"
        )
        self._grid_layout.addWidget(lbl_b, 0, self.num_vars)

        # Celdas editables de la matriz
        for r in range(self.num_rows):
            row_cells: List[MatrixCellEdit] = []
            for c in range(total_cols):
                cell = MatrixCellEdit(r, c)
                cell.navigate.connect(self._handle_cell_navigation)
                cell.textChanged.connect(lambda: self.matrixChanged.emit())
                self._grid_layout.addWidget(cell, r + 1, c)
                row_cells.append(cell)
            self.cells.append(row_cells)

        # Celda fantasma en la derecha (+)
        ghost_col_btn = QPushButton("+")
        ghost_col_btn.setProperty("class", "ghost-cell")
        ghost_col_btn.setToolTip("Agregar columna (variable)")
        ghost_col_btn.setFixedSize(30, 36 * self.num_rows + 6 * (self.num_rows - 1))
        ghost_col_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_INTERACTIVE_IDLE};
                border: 1px dashed {COLOR_INTERACTIVE_IDLE};
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(152, 193, 217, 0.2);
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)
        ghost_col_btn.clicked.connect(self.add_column)
        self._grid_layout.addWidget(ghost_col_btn, 1, total_cols, self.num_rows, 1, Qt.AlignVCenter)

        # Celda fantasma inferior (+)
        ghost_row_btn = QPushButton("+")
        ghost_row_btn.setProperty("class", "ghost-cell")
        ghost_row_btn.setToolTip("Agregar fila (ecuación)")
        ghost_row_btn.setFixedHeight(28)
        ghost_row_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_INTERACTIVE_IDLE};
                border: 1px dashed {COLOR_INTERACTIVE_IDLE};
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(152, 193, 217, 0.2);
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)
        ghost_row_btn.clicked.connect(self.add_row)
        self._grid_layout.addWidget(ghost_row_btn, self.num_rows + 1, 0, 1, total_cols)

    def _handle_cell_navigation(self, r: int, c: int, direction: str) -> None:
        target_r, target_c = r, c
        total_cols = self.num_vars + 1

        if direction == "up" and r > 0:
            target_r = r - 1
        elif direction == "down":
            if r < self.num_rows - 1:
                target_r = r + 1
            else:
                self.add_row()
                target_r = r + 1
        elif direction == "left" and c > 0:
            target_c = c - 1
        elif direction == "right":
            if c < total_cols - 1:
                target_c = c + 1

        if 0 <= target_r < len(self.cells) and 0 <= target_c < len(self.cells[target_r]):
            self.cells[target_r][target_c].setFocus()
            self.cells[target_r][target_c].selectAll()

    def add_row(self) -> None:
        current_data = self.get_raw_strings()
        self.num_rows += 1
        self._build_grid()
        self.set_raw_strings(current_data)
        self.matrixChanged.emit()

    def add_column(self) -> None:
        current_data = self.get_raw_strings()
        self.num_vars += 1
        self._build_grid()
        adjusted_data = []
        for row in current_data:
            coeffs = row[:-1]
            b_val = row[-1]
            adjusted_data.append(coeffs + ["0"] + [b_val])
        self.set_raw_strings(adjusted_data)
        self.matrixChanged.emit()

    def get_matrix(self) -> Matrix:
        data: List[List[Fraction]] = []
        for row in self.cells:
            data.append([cell.get_value() for cell in row])
        return Matrix(data)

    def set_matrix(self, matrix: Matrix) -> None:
        self.num_rows = matrix.rows
        self.num_vars = matrix.cols - 1
        self._build_grid()
        for r in range(matrix.rows):
            for c in range(matrix.cols):
                val_str = format_scalar(matrix.get(r, c), mode="fraction")
                self.cells[r][c].setText(val_str)
        self.matrixChanged.emit()

    def get_raw_strings(self) -> List[List[str]]:
        return [[cell.text() for cell in row] for row in self.cells]

    def set_raw_strings(self, data: List[List[str]]) -> None:
        for r, row in enumerate(data):
            if r < len(self.cells):
                for c, text in enumerate(row):
                    if c < len(self.cells[r]):
                        self.cells[r][c].setText(text)

    def is_all_valid(self) -> bool:
        return all(cell.is_valid for row in self.cells for cell in row)
