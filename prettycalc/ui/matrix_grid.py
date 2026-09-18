"""Cuadrícula interactiva DynamicMatrixGrid: matriz aumentada de libro, ghosting y teclado."""

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
        QLabel,
        QFrame,
        QSpacerItem,
        QSizePolicy,
        QMenu,
    )
    from PySide6.QtCore import Qt, Signal, QRect, QPoint, QTimer
    from PySide6.QtGui import QKeyEvent, QFont, QPainter, QColor, QPaintEvent, QAction, QFocusEvent
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.types import Matrix, parse_scalar, format_scalar
from prettycalc.ui.mathtext import variable_symbol
from prettycalc.ui.book_matrix import draw_square_brackets, draw_split_bar
from prettycalc.ui.theme import (
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_PRIMARY,
    apply_widget_class,
)


def _make_ghost_button(tooltip: str) -> QPushButton:
    """Botón fantasma permanente para expandir la matriz."""
    btn = QPushButton("+")
    apply_widget_class(btn, "ghost-cell")
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFlat(True)
    return btn


class MatrixCellEdit(QLineEdit):
    """Celda editable con validación en tiempo real y navegación por teclado."""

    navigate = Signal(int, int, str)

    def __init__(self, row: int, col: int, default_val: str = "0", parent: Optional[QWidget] = None):
        super().__init__(default_val, parent)
        self.row = row
        self.col = col
        self.setFixedSize(58, 38)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Fira Code", 12))
        self.setFrame(False)
        apply_widget_class(self, "matrix-cell")
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.textChanged.connect(self._on_text_changed)
        self._is_valid = True

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.selectAll()
        QTimer.singleShot(0, self.selectAll)

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
        apply_widget_class(self, "matrix-cell-error" if has_error else "matrix-cell")

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
    """Cuadrícula [A | b] con corchetes de libro, barra vertical y celdas fantasma."""

    matrixChanged = Signal()

    def __init__(
        self,
        initial_rows: int = 2,
        initial_cols: int = 2,
        parent: Optional[QWidget] = None,
        *,
        augmented: bool = True,
        show_headers: bool = True,
        row_expandable: bool = True,
        col_expandable: bool = True,
    ):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.augmented = augmented
        self.show_headers = show_headers
        self.row_expandable = row_expandable
        self.col_expandable = col_expandable
        self.num_rows = initial_rows
        self.num_vars = initial_cols
        self._highlight_rows: set[int] = set()
        self._highlight_cols: set[int] = set()
        self.cells: List[List[MatrixCellEdit]] = []

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(8, 4, 8, 4)

        self._center_container = QWidget()
        self._center_container.setAttribute(Qt.WA_TranslucentBackground, True)
        self._grid_layout = QGridLayout(self._center_container)
        self._grid_layout.setVerticalSpacing(8)
        self._grid_layout.setHorizontalSpacing(8)
        self._grid_layout.setContentsMargins(12, 8, 12, 8)

        self._outer_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self._outer_layout.addWidget(self._center_container, 0, Qt.AlignCenter)
        self._outer_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self._build_grid()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self.cells:
            return

        first = self.cells[0][0]
        last = self.cells[-1][-1]
        if not first.isVisible() or not last.isVisible():
            return

        top_left = first.mapTo(self, first.rect().topLeft())
        bottom_right = last.mapTo(self, last.rect().bottomRight())
        pad = 10
        bracket_rect = QRect(
            top_left.x() - pad,
            top_left.y() - pad,
            (bottom_right.x() - top_left.x()) + 2 * pad,
            (bottom_right.y() - top_left.y()) + 2 * pad,
        )

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        draw_square_brackets(painter, bracket_rect, QColor(COLOR_TEXT_PRIMARY), thickness=2)

        if self.augmented:
            b_cell = self.cells[0][-1]
            b_top = b_cell.mapTo(self, b_cell.rect().topLeft())
            last_b = self.cells[-1][-1]
            _b_bottom = last_b.mapTo(self, last_b.rect().bottomLeft())
            bar_x = b_top.x() - 6
            draw_split_bar(
                painter,
                bar_x,
                bracket_rect.top() + 4,
                bracket_rect.bottom() - 4,
                QColor(COLOR_INTERACTIVE_IDLE),
            )
        painter.end()

    def _build_grid(self) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        total_cols = self._total_cols()
        header_row = 1 if self.show_headers else 0
        self.cells = []

        if self.show_headers:
            for c in range(total_cols):
                if self.augmented:
                    text = "b" if c == self.num_vars else variable_symbol(c)
                else:
                    text = str(c + 1)
                lbl = QLabel(text)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setFixedHeight(22)
                lbl.setStyleSheet(
                    f"color: {COLOR_INTERACTIVE_IDLE}; font-style: italic; font-size: 15px; background: transparent;"
                )
                self._grid_layout.addWidget(lbl, 0, c)

        for r in range(self.num_rows):
            row_cells: List[MatrixCellEdit] = []
            for c in range(total_cols):
                cell = MatrixCellEdit(r, c)
                cell.navigate.connect(self._handle_cell_navigation)
                cell.textChanged.connect(lambda: self.matrixChanged.emit())
                self._grid_layout.addWidget(cell, r + header_row, c)
                row_cells.append(cell)
            self.cells.append(row_cells)

        self.ghost_col_btn = _make_ghost_button(
            "Agregar variable" if self.augmented else "Agregar columna"
        )
        self.ghost_col_btn.setFixedWidth(36)
        self.ghost_col_btn.setMinimumWidth(36)
        self.ghost_col_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.ghost_col_btn.clicked.connect(self.add_column)
        self._grid_layout.addWidget(self.ghost_col_btn, header_row, total_cols, self.num_rows, 1)
        if not self.col_expandable:
            self.ghost_col_btn.hide()

        self.ghost_row_btn = _make_ghost_button(
            "Agregar ecuación" if self.augmented else "Agregar fila"
        )
        self.ghost_row_btn.setFixedHeight(32)
        self.ghost_row_btn.clicked.connect(self.add_row)
        self._grid_layout.addWidget(
            self.ghost_row_btn, self.num_rows + header_row, 0, 1, total_cols
        )
        if not self.row_expandable:
            self.ghost_row_btn.hide()

        self._apply_highlight()
        self.update()

    def _total_cols(self) -> int:
        return self.num_vars + 1 if self.augmented else self.num_vars

    def data_shape(self) -> tuple[int, int]:
        """Dimensiones de la matriz de datos (filas × columnas editables)."""
        return (self.num_rows, self._total_cols())

    def set_highlight(
        self,
        rows: Optional[List[int]] = None,
        cols: Optional[List[int]] = None,
    ) -> None:
        """Resalta filas y/o columnas para el inspector de producto."""
        self._highlight_rows = set(rows or [])
        self._highlight_cols = set(cols or [])
        self._apply_highlight()

    def clear_highlight(self) -> None:
        self.set_highlight([], [])

    def _apply_highlight(self) -> None:
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                active = r in self._highlight_rows or c in self._highlight_cols
                cell.setProperty("highlighted", active)
                style = cell.style()
                if style is not None:
                    style.unpolish(cell)
                    style.polish(cell)
                cell.update()

    def _cell_at(self, pos: QPoint) -> Optional[MatrixCellEdit]:
        """Localiza la celda bajo un punto en coordenadas del contenedor."""
        for row in self.cells:
            for cell in row:
                top_left = cell.mapTo(self, cell.rect().topLeft())
                if QRect(top_left, cell.size()).contains(pos):
                    return cell
        return None

    def _show_context_menu(self, pos: QPoint) -> None:
        cell = self._cell_at(pos)
        if cell is None:
            return

        menu = QMenu(self)
        delete_row = QAction("Eliminar fila", menu)
        delete_col = QAction("Eliminar columna", menu)

        can_delete_row = self.num_rows > 1
        can_delete_col = self.num_vars > 1 and (self.augmented is False or cell.col < self.num_vars)
        delete_row.setEnabled(can_delete_row)
        delete_col.setEnabled(can_delete_col)
        if self.augmented and cell.col >= self.num_vars:
            delete_col.setToolTip("La columna de términos independientes no se puede eliminar.")
        elif self.num_vars <= 1:
            delete_col.setToolTip("Debe quedar al menos una columna.")
        if self.num_rows <= 1:
            delete_row.setToolTip("Debe quedar al menos una ecuación.")

        delete_row.triggered.connect(lambda: self.remove_row(cell.row))
        delete_col.triggered.connect(lambda: self.remove_column(cell.col))
        menu.addAction(delete_row)
        menu.addAction(delete_col)
        menu.exec(self.mapToGlobal(pos))

    def remove_row(self, index: int) -> None:
        """Elimina una ecuación. No permite dejar la matriz sin filas."""
        if self.num_rows <= 1 or index < 0 or index >= self.num_rows:
            return
        data = self.get_raw_strings()
        del data[index]
        self.num_rows -= 1
        self._build_grid()
        self.set_raw_strings(data)
        self.matrixChanged.emit()

    def remove_column(self, index: int) -> None:
        """Elimina una columna. En modo aumentado no elimina b ni deja el sistema sin incógnitas."""
        if index < 0 or self.num_vars <= 1:
            return
        if self.augmented and index >= self.num_vars:
            return
        data = self.get_raw_strings()
        trimmed = [row[:index] + row[index + 1 :] for row in data]
        self.num_vars -= 1
        self._build_grid()
        self.set_raw_strings(trimmed)
        self.matrixChanged.emit()

    def _handle_cell_navigation(self, r: int, c: int, direction: str) -> None:
        target_r, target_c = r, c
        total_cols = self._total_cols()

        if direction == "up" and r > 0:
            target_r = r - 1
        elif direction == "down":
            if r < self.num_rows - 1:
                target_r = r + 1
            elif self.row_expandable:
                self.add_row()
                target_r = r + 1
        elif direction == "left" and c > 0:
            target_c = c - 1
        elif direction == "right":
            if c < total_cols - 1:
                target_c = c + 1
            elif self.col_expandable:
                self.add_column()
                target_c = self._total_cols() - 1 if not self.augmented else self.num_vars - 1

        if 0 <= target_r < len(self.cells) and 0 <= target_c < len(self.cells[target_r]):
            self.cells[target_r][target_c].setFocus()
            self.cells[target_r][target_c].selectAll()

    def add_row(self) -> None:
        if not self.row_expandable:
            return
        current_data = self.get_raw_strings()
        self.num_rows += 1
        self._build_grid()
        self.set_raw_strings(current_data)
        self.matrixChanged.emit()

    def add_column(self) -> None:
        if not self.col_expandable:
            return
        current_data = self.get_raw_strings()
        self.num_vars += 1
        self._build_grid()
        if self.augmented:
            adjusted_data = []
            for row in current_data:
                coeffs = row[:-1]
                b_val = row[-1]
                adjusted_data.append(coeffs + ["0"] + [b_val])
            self.set_raw_strings(adjusted_data)
        else:
            padded = [row + ["0"] for row in current_data]
            self.set_raw_strings(padded)
        self.matrixChanged.emit()

    def get_matrix(self) -> Matrix:
        data: List[List[Fraction]] = []
        for row in self.cells:
            data.append([cell.get_value() for cell in row])
        return Matrix(data)

    def set_matrix(self, matrix: Matrix) -> None:
        self.num_rows = matrix.rows
        self.num_vars = matrix.cols - 1 if self.augmented else matrix.cols
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
