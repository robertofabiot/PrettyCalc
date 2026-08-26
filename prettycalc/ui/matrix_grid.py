"""Cuadrícula interactiva DynamicMatrixGrid con soporte de Ghosting, validación en tiempo real y navegación por teclado."""

from __future__ import annotations
from typing import List, Optional, Tuple, Callable
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
    )
    from PySide6.QtCore import Qt, Signal, QEvent
    from PySide6.QtGui import QKeyEvent
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.types import Matrix, parse_scalar, format_scalar
from prettycalc.ui.theme import (
    COLOR_INTERACTIVE_IDLE,
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_SURFACE_ELEVATED,
)


class MatrixCellEdit(QLineEdit):
    """Celda editable individual con validación en tiempo real y navegación por teclado."""

    # Señal emitida al navegar con flechas: (row, col, direction: 'up'|'down'|'left'|'right')
    navigate = Signal(int, int, str)

    def __init__(self, row: int, col: int, default_val: str = "0", parent: Optional[QWidget] = None):
        super().__init__(default_val, parent)
        self.row = row
        self.col = col
        self.setProperty("class", "matrix-cell")
        self.setAlignment(Qt.AlignCenter)
        self.textChanged.connect(self._on_text_changed)
        self._is_valid = True

    def _on_text_changed(self, text: str) -> None:
        """Valida en tiempo real que el contenido sea un escalar admisible."""
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
            self.setStyleSheet(
                f"border: 2px solid {COLOR_FEEDBACK_ERROR}; background-color: #3E2426; color: {COLOR_TEXT_PRIMARY};"
            )
        else:
            self.setStyleSheet("")

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    def get_value(self) -> Fraction:
        text = self.text().strip()
        if not text:
            return Fraction(0, 1)
        return parse_scalar(text)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Navegación con flechas del teclado
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
    """Contenedor de cuadrícula matricial aumentada [A | b] con crecimiento dinámico (Ghosting)."""

    matrixChanged = Signal()

    def __init__(self, initial_rows: int = 2, initial_cols: int = 2, parent: Optional[QWidget] = None):
        """Inicializa la cuadrícula en 2x2 (+ columna b) por defecto."""
        super().__init__(parent)
        self.setProperty("class", "elevated-card")
        self.num_rows = initial_rows
        self.num_vars = initial_cols  # Número de variables de A
        self.cells: List[List[MatrixCellEdit]] = []

        self._main_layout = QVBoxLayout(self)
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(6)
        self._main_layout.addLayout(self._grid_layout)

        self._build_grid()

    def _build_grid(self) -> None:
        """Reconstruye los widgets de la cuadrícula respetando dimensiones actuales y celdas fantasma."""
        # Limpiar layout anterior
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total_cols = self.num_vars + 1  # Variables A + Vector b
        self.cells = []

        # Encabezados de columnas (x1, x2, ..., | b)
        for c in range(self.num_vars):
            lbl = QLabel(f"x{c+1}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-weight: bold; font-size: 11px;")
            self._grid_layout.addWidget(lbl, 0, c)

        # Encabezado del vector b
        lbl_b = QLabel("b")
        lbl_b.setAlignment(Qt.AlignCenter)
        lbl_b.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-weight: bold; font-size: 12px; border-left: 2px solid {COLOR_INTERACTIVE_IDLE};")
        self._grid_layout.addWidget(lbl_b, 0, self.num_vars)

        # Celdas editables activas
        for r in range(self.num_rows):
            row_cells: List[MatrixCellEdit] = []
            for c in range(total_cols):
                cell = MatrixCellEdit(r, c)
                cell.navigate.connect(self._handle_cell_navigation)
                cell.textChanged.connect(lambda: self.matrixChanged.emit())
                self._grid_layout.addWidget(cell, r + 1, c)
                row_cells.append(cell)
            self.cells.append(row_cells)

        # Celda fantasma en la derecha (para agregar variable / columna)
        ghost_col_btn = QPushButton("+")
        ghost_col_btn.setProperty("class", "ghost-cell")
        ghost_col_btn.setToolTip("Haz clic para agregar una variable (columna)")
        ghost_col_btn.setFixedWidth(28)
        ghost_col_btn.clicked.connect(self.add_column)
        self._grid_layout.addWidget(ghost_col_btn, 1, total_cols, self.num_rows, 1)

        # Celda fantasma inferior (para agregar ecuación / fila)
        ghost_row_btn = QPushButton("+")
        ghost_row_btn.setProperty("class", "ghost-cell")
        ghost_row_btn.setToolTip("Haz clic para agregar una ecuación (fila)")
        ghost_row_btn.setFixedHeight(26)
        ghost_row_btn.clicked.connect(self.add_row)
        self._grid_layout.addWidget(ghost_row_btn, self.num_rows + 1, 0, 1, total_cols)

    def _handle_cell_navigation(self, r: int, c: int, direction: str) -> None:
        """Navega el foco entre celdas al presionar flechas de dirección."""
        target_r, target_c = r, c
        total_cols = self.num_vars + 1

        if direction == "up" and r > 0:
            target_r = r - 1
        elif direction == "down":
            if r < self.num_rows - 1:
                target_r = r + 1
            else:
                # Si está en la última fila y presiona abajo, expandir orgánicamente
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
        """Añade una fila adicional de forma fluida."""
        current_data = self.get_raw_strings()
        self.num_rows += 1
        self._build_grid()
        self.set_raw_strings(current_data)
        self.matrixChanged.emit()

    def add_column(self) -> None:
        """Añade una columna de coeficientes adicional."""
        current_data = self.get_raw_strings()
        self.num_vars += 1
        self._build_grid()
        # Ajustar datos anteriores insertando 0 antes de la columna b
        adjusted_data = []
        for row in current_data:
            coeffs = row[:-1]
            b_val = row[-1]
            adjusted_data.append(coeffs + ["0"] + [b_val])
        self.set_raw_strings(adjusted_data)
        self.matrixChanged.emit()

    def get_matrix(self) -> Matrix:
        """Extrae la matriz aumentada completa [A | b] como objeto Matrix."""
        data: List[List[Fraction]] = []
        for row in self.cells:
            data.append([cell.get_value() for cell in row])
        return Matrix(data)

    def set_matrix(self, matrix: Matrix) -> None:
        """Rellena la cuadrícula a partir de una matriz dada."""
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
        """Retorna True si todas las celdas contienen entradas numéricas válidas."""
        return all(cell.is_valid for row in self.cells for cell in row)
