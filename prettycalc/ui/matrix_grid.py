"""Cuadrícula interactiva DynamicMatrixGrid: matriz aumentada de libro, ghosting y teclado.

Sprint 10 (auditoría UI/UX, Módulo 7):

- Historial de deshacer/rehacer (``Ctrl+Z`` / ``Ctrl+Y``) para reinicios,
  ejemplos cargados, pegados y cambios de tamaño.
- Mensaje en línea bajo la cuadrícula que explica qué celda falló y por qué.
- Una celda que queda vacía al perder el foco se completa con ``0``.
- ``Ctrl+Supr`` elimina la fila activa y ``Ctrl+Mayús+Supr`` la columna.
- ``Ctrl+Intro`` emite ``submitRequested`` para calcular sin tocar el ratón.
- Pegar una matriz muestra un aviso con «Deshacer» y un destello en las celdas.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
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
    from PySide6.QtGui import (
        QKeyEvent,
        QPainter,
        QColor,
        QPaintEvent,
        QFocusEvent,
        QContextMenuEvent,
        QKeySequence,
        QGuiApplication,
    )
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.input_diagnostics import diagnose_scalar_text
from prettycalc.core.types import Matrix, parse_scalar, format_scalar
from prettycalc.ui.clipboard import (
    copy_matrix_to_clipboard,
    get_clipboard_text,
    get_matrix_from_clipboard,
    has_matrix_in_clipboard,
)
from prettycalc.ui.book_matrix import draw_square_brackets, draw_split_bar
from prettycalc.ui.theme import (
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_PRIMARY,
    apply_widget_class,
    repolish,
    ui_font,
)

#: Estado restaurable de la cuadrícula: (filas, columnas de coeficientes, textos).
GridSnapshot = Tuple[int, int, Tuple[Tuple[str, ...], ...]]

_HISTORY_LIMIT = 60
_FLASH_MS = 520


def _make_ghost_button(tooltip: str) -> QPushButton:
    """Botón fantasma permanente para expandir la matriz."""
    btn = QPushButton("+")
    apply_widget_class(btn, "ghost-cell")
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFlat(True)
    btn.setFocusPolicy(Qt.NoFocus)
    return btn


def _is_shortcut(event: QKeyEvent, key: int, modifiers) -> bool:
    return event.key() == key and event.modifiers() == modifiers


class MatrixCellEdit(QLineEdit):
    """Celda editable con validación en tiempo real y navegación por teclado."""

    navigate = Signal(int, int, str)

    def __init__(
        self,
        row: int,
        col: int,
        default_val: str = "0",
        parent: Optional[QWidget] = None,
        grid: Optional["DynamicMatrixGrid"] = None,
    ):
        super().__init__(default_val, parent)
        self.row = row
        self.col = col
        self._grid = grid
        self.error_message = ""
        self.setFixedSize(58, 38)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(ui_font(16, mono=True))
        self.setFrame(False)
        apply_widget_class(self, "matrix-cell")
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setAccessibleName(f"Celda fila {row + 1}, columna {col + 1}")
        self.textChanged.connect(self._on_text_changed)
        self._is_valid = True

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self._grid is not None:
            self._grid.show_cell_context_menu(self, event.globalPos())
            event.accept()
        else:
            super().contextMenuEvent(event)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.selectAll()

        def _safe_select_all():
            try:
                self.selectAll()
            except RuntimeError:
                pass

        QTimer.singleShot(0, _safe_select_all)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Una celda vacía se completa con 0: evita ambigüedad entre módulos."""
        super().focusOutEvent(event)
        if not self.text().strip():
            self.setText("0")

    def _on_text_changed(self, text: str) -> None:
        diagnosis = diagnose_scalar_text(text, allow_empty=True)
        self.error_message = "" if diagnosis.is_valid else diagnosis.message
        self.setToolTip(self.error_message)
        self._set_error_state(not diagnosis.is_valid)

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
        ctrl = Qt.ControlModifier
        ctrl_shift = Qt.ControlModifier | Qt.ShiftModifier

        if self._grid is not None:
            if event.matches(QKeySequence.Undo) or _is_shortcut(event, Qt.Key_Z, ctrl):
                if self.isUndoAvailable():
                    super().keyPressEvent(event)
                else:
                    self._grid.undo()
                event.accept()
                return
            if (
                event.matches(QKeySequence.Redo)
                or _is_shortcut(event, Qt.Key_Y, ctrl)
                or _is_shortcut(event, Qt.Key_Z, ctrl_shift)
            ):
                if self.isRedoAvailable():
                    super().keyPressEvent(event)
                else:
                    self._grid.redo()
                event.accept()
                return
            if _is_shortcut(event, Qt.Key_Delete, ctrl):
                if self._grid.row_expandable:
                    self._grid.remove_row(self.row, focus_after=True)
                event.accept()
                return
            if _is_shortcut(event, Qt.Key_Delete, ctrl_shift):
                if self._grid.col_expandable:
                    self._grid.remove_column(self.col, focus_after=True)
                event.accept()
                return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ControlModifier:
                self._grid.submitRequested.emit()
                event.accept()
                return

        if event.matches(QKeySequence.Copy) or (
            event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier
        ):
            # Si el usuario seleccionó un fragmento parcial dentro de la celda (ej: '1' en '1/2')
            if self.hasSelectedText() and len(self.selectedText()) < len(self.text()):
                super().keyPressEvent(event)
                return
            # Si no hay selección o toda la celda está seleccionada, copiar la matriz completa
            if self._grid is not None:
                self._grid.copy_to_clipboard()
                event.accept()
                return

        if event.matches(QKeySequence.Paste) or (
            event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier
        ):
            clip_text = get_clipboard_text().strip()
            # Si el portapapeles contiene una estructura de matriz o múltiples valores
            if ("\t" in clip_text or "\n" in clip_text or "[" in clip_text or "\\begin{" in clip_text) and has_matrix_in_clipboard():
                if self._grid is not None:
                    self._grid.paste_from_clipboard()
                    event.accept()
                    return

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
    validityChanged = Signal(bool)
    submitRequested = Signal()
    historyChanged = Signal()

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
        show_hint: bool = True,
    ):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("DynamicMatrixGrid { background: transparent; }")
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
        self._alert_rows: set[int] = set()
        self.cells: List[List[MatrixCellEdit]] = []
        self._undo_stack: List[GridSnapshot] = []
        self._redo_stack: List[GridSnapshot] = []
        self._restoring = False
        self._last_valid = True
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._end_flash)

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

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("gridHint")
        self.hint_label.setWordWrap(True)
        self.hint_label.setAlignment(Qt.AlignCenter)
        apply_widget_class(self.hint_label, "grid-hint")
        self.hint_label.setVisible(False)
        self._show_hint = show_hint
        self._outer_layout.addWidget(self.hint_label)

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
                    if c == self.num_vars:
                        lbl = QLabel("b")
                        lbl.setStyleSheet(
                            f"color: {COLOR_INTERACTIVE_IDLE}; font-style: italic; font-size: 15px; background: transparent;"
                        )
                    else:
                        lbl = QLabel(f"<i>x</i><sub style='font-size:10px;'>{c + 1}</sub>")
                        lbl.setTextFormat(Qt.RichText)
                        lbl.setStyleSheet(
                            f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 16px; background: transparent;"
                        )
                else:
                    lbl = QLabel(str(c + 1))
                    lbl.setStyleSheet(
                        f"color: {COLOR_INTERACTIVE_IDLE}; font-style: italic; font-size: 15px; background: transparent;"
                    )
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setFixedHeight(22)
                self._grid_layout.addWidget(lbl, 0, c)

        for r in range(self.num_rows):
            row_cells: List[MatrixCellEdit] = []
            for c in range(total_cols):
                cell = MatrixCellEdit(r, c, grid=self)
                cell.navigate.connect(self._handle_cell_navigation)
                cell.textChanged.connect(self._on_cell_text_changed)
                self._grid_layout.addWidget(cell, r + header_row, c)
                row_cells.append(cell)
            self.cells.append(row_cells)

        self.ghost_col_btn = _make_ghost_button(
            "Agregar variable (o pulsa → al final de la última columna)"
            if self.augmented
            else "Agregar columna (o pulsa → al final de la última columna)"
        )
        self.ghost_col_btn.setFixedWidth(36)
        self.ghost_col_btn.setMinimumWidth(36)
        self.ghost_col_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.ghost_col_btn.clicked.connect(self.add_column)
        self._grid_layout.addWidget(self.ghost_col_btn, header_row, total_cols, self.num_rows, 1)
        if not self.col_expandable:
            self.ghost_col_btn.hide()

        self.ghost_row_btn = _make_ghost_button(
            "Agregar ecuación (o pulsa ↓ en la última fila)"
            if self.augmented
            else "Agregar fila (o pulsa ↓ en la última fila)"
        )
        self.ghost_row_btn.setFixedHeight(32)
        self.ghost_row_btn.clicked.connect(self.add_row)
        self._grid_layout.addWidget(
            self.ghost_row_btn, self.num_rows + header_row, 0, 1, total_cols
        )
        if not self.row_expandable:
            self.ghost_row_btn.hide()

        self._apply_highlight()
        self._refresh_hint()
        self.update()

    def _total_cols(self) -> int:
        return self.num_vars + 1 if self.augmented else self.num_vars

    def data_shape(self) -> tuple[int, int]:
        """Dimensiones de la matriz de datos (filas × columnas editables)."""
        return (self.num_rows, self._total_cols())

    # ------------------------------------------------------------------
    # Validación visible
    # ------------------------------------------------------------------

    def _on_cell_text_changed(self, _text: str = "") -> None:
        self._refresh_hint()
        self.matrixChanged.emit()

    def first_invalid_cell(self) -> Optional[MatrixCellEdit]:
        for row in self.cells:
            for cell in row:
                if not cell.is_valid:
                    return cell
        return None

    def validation_message(self) -> str:
        """Explicación de la primera celda inválida, o cadena vacía."""
        cell = self.first_invalid_cell()
        if cell is None:
            return ""
        if self.augmented and cell.col == self.num_vars:
            where = f"Fila {cell.row + 1}, columna b"
        else:
            where = f"Fila {cell.row + 1}, columna {cell.col + 1}"
        invalid_count = sum(1 for row in self.cells for c in row if not c.is_valid)
        extra = ""
        if invalid_count > 1:
            others = invalid_count - 1
            extra = f" (y {others} celda{'s' if others > 1 else ''} más)"
        return f"{where}: {cell.error_message}{extra}"

    def _refresh_hint(self) -> None:
        message = self.validation_message()
        valid = not message
        if self._show_hint:
            self.hint_label.setText(f"✕  {message}" if message else "")
            self.hint_label.setVisible(bool(message))
        if valid != self._last_valid:
            self._last_valid = valid
            self.validityChanged.emit(valid)

    def focus_first_invalid(self) -> bool:
        cell = self.first_invalid_cell()
        if cell is None:
            return False
        cell.setFocus()
        cell.selectAll()
        return True

    # ------------------------------------------------------------------
    # Resaltados
    # ------------------------------------------------------------------

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

    def set_alert_rows(self, rows: Optional[List[int]] = None) -> None:
        """Marca filas en ocre (por ejemplo, filas permutadas en P · A = L · U)."""
        self._alert_rows = set(rows or [])
        self._apply_highlight()

    def highlighted_rows(self) -> set[int]:
        return set(self._highlight_rows)

    def highlighted_cols(self) -> set[int]:
        return set(self._highlight_cols)

    def alert_rows(self) -> set[int]:
        return set(self._alert_rows)

    def _apply_highlight(self) -> None:
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                active = r in self._highlight_rows or c in self._highlight_cols
                cell.setProperty("highlighted", active)
                cell.setProperty("alert", r in self._alert_rows and not active)
                repolish(cell)

    def flash(self) -> None:
        """Destello breve en todas las celdas: confirma que el contenido cambió."""
        for row in self.cells:
            for cell in row:
                cell.setProperty("flash", True)
                repolish(cell)
        self._flash_timer.start(_FLASH_MS)

    def _end_flash(self) -> None:
        for row in self.cells:
            for cell in row:
                try:
                    cell.setProperty("flash", False)
                    repolish(cell)
                except RuntimeError:
                    pass

    # ------------------------------------------------------------------
    # Historial (deshacer / rehacer)
    # ------------------------------------------------------------------

    def snapshot(self) -> GridSnapshot:
        return (
            self.num_rows,
            self.num_vars,
            tuple(tuple(cell.text() for cell in row) for row in self.cells),
        )

    def checkpoint(self) -> None:
        """Guarda el estado actual antes de un cambio masivo (reinicio, ejemplo, pegado)."""
        if self._restoring:
            return
        state = self.snapshot()
        if self._undo_stack and self._undo_stack[-1] == state:
            return
        self._undo_stack.append(state)
        if len(self._undo_stack) > _HISTORY_LIMIT:
            del self._undo_stack[0]
        self._redo_stack.clear()
        self.historyChanged.emit()

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def _restore(self, state: GridSnapshot) -> None:
        rows, num_vars, data = state
        self._restoring = True
        try:
            self.num_rows = rows
            self.num_vars = num_vars
            self._build_grid()
            self.set_raw_strings([list(row) for row in data])
        finally:
            self._restoring = False
        self._refresh_hint()
        self.matrixChanged.emit()
        self.flash()

    def undo(self) -> bool:
        """Restaura el estado anterior al último cambio masivo."""
        if not self._undo_stack:
            return False
        current = self.snapshot()
        previous = self._undo_stack.pop()
        self._redo_stack.append(current)
        self._restore(previous)
        self.historyChanged.emit()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        current = self.snapshot()
        following = self._redo_stack.pop()
        self._undo_stack.append(current)
        self._restore(following)
        self.historyChanged.emit()
        return True

    # ------------------------------------------------------------------
    # Menú contextual
    # ------------------------------------------------------------------

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
        self.show_cell_context_menu(cell, self.mapToGlobal(pos))

    def show_cell_context_menu(self, cell: Optional[MatrixCellEdit], global_pos: QPoint) -> None:
        menu = QMenu(self)

        copy_action = menu.addAction("Copiar matriz")
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_to_clipboard)

        paste_action = menu.addAction("Pegar matriz")
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.setEnabled(has_matrix_in_clipboard())
        paste_action.triggered.connect(self.paste_from_clipboard)

        if cell is not None:
            menu.addSeparator()

            copy_cell_action = menu.addAction("Copiar valor de celda")
            copy_cell_action.triggered.connect(
                lambda: QGuiApplication.clipboard().setText(cell.text())
                if QGuiApplication.clipboard() is not None
                else None
            )

            def _paste_cell_val():
                txt = get_clipboard_text().strip()
                if txt:
                    cell.setText(txt)

            paste_cell_action = menu.addAction("Pegar en celda")
            paste_cell_action.setEnabled(bool(get_clipboard_text().strip()))
            paste_cell_action.triggered.connect(_paste_cell_val)

            menu.addSeparator()

            delete_row = menu.addAction("Eliminar fila")
            delete_row.setShortcut(QKeySequence("Ctrl+Delete"))
            delete_col = menu.addAction("Eliminar columna")
            delete_col.setShortcut(QKeySequence("Ctrl+Shift+Delete"))

            can_delete_row = self.num_rows > 1 and self.row_expandable
            can_delete_col = self.num_vars > 1 and self.col_expandable and (
                self.augmented is False or cell.col < self.num_vars
            )
            delete_row.setEnabled(can_delete_row)
            delete_col.setEnabled(can_delete_col)

            if self.augmented and cell.col >= self.num_vars:
                delete_col.setToolTip("La columna de términos independientes no se puede eliminar.")
            elif self.num_vars <= 1 or not self.col_expandable:
                delete_col.setToolTip("Debe quedar al menos una columna.")
            if self.num_rows <= 1 or not self.row_expandable:
                delete_row.setToolTip("Debe quedar al menos una fila.")

            delete_row.triggered.connect(lambda: self.remove_row(cell.row))
            delete_col.triggered.connect(lambda: self.remove_column(cell.col))

        menu.addSeparator()
        undo_action = menu.addAction("Deshacer cambio de matriz")
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setEnabled(self.can_undo())
        undo_action.triggered.connect(self.undo)
        redo_action = menu.addAction("Rehacer")
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.setEnabled(self.can_redo())
        redo_action.triggered.connect(self.redo)

        menu.exec(global_pos)

    # ------------------------------------------------------------------
    # Cambios estructurales
    # ------------------------------------------------------------------

    def remove_row(self, index: int, focus_after: bool = False) -> None:
        """Elimina una ecuación. No permite dejar la matriz sin filas."""
        if self.num_rows <= 1 or index < 0 or index >= self.num_rows:
            return
        self.checkpoint()
        data = self.get_raw_strings()
        del data[index]
        self.num_rows -= 1
        self._build_grid()
        self.set_raw_strings(data)
        self.matrixChanged.emit()
        if focus_after:
            self._focus_cell(min(index, self.num_rows - 1), 0)

    def remove_column(self, index: int, focus_after: bool = False) -> None:
        """Elimina una columna. En modo aumentado no elimina b ni deja el sistema sin incógnitas."""
        if index < 0 or self.num_vars <= 1:
            return
        if self.augmented and index >= self.num_vars:
            return
        self.checkpoint()
        data = self.get_raw_strings()
        trimmed = [row[:index] + row[index + 1 :] for row in data]
        self.num_vars -= 1
        self._build_grid()
        self.set_raw_strings(trimmed)
        self.matrixChanged.emit()
        if focus_after:
            self._focus_cell(0, min(index, self.num_vars - 1))

    def _focus_cell(self, row: int, col: int) -> None:
        if 0 <= row < len(self.cells) and 0 <= col < len(self.cells[row]):
            self.cells[row][col].setFocus()
            self.cells[row][col].selectAll()

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

        self._focus_cell(target_r, target_c)

    def add_row(self) -> None:
        if not self.row_expandable:
            return
        self.checkpoint()
        current_data = self.get_raw_strings()
        self.num_rows += 1
        self._build_grid()
        self.set_raw_strings(current_data)
        self.matrixChanged.emit()

    def add_column(self) -> None:
        if not self.col_expandable:
            return
        self.checkpoint()
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

    def resize_to(self, rows: int, data_cols: int) -> None:
        """Fija el tamaño de golpe conservando las entradas que caben.

        ``data_cols`` cuenta todas las columnas editables; en modo aumentado
        incluye la columna ``b`` (que se conserva como última columna).
        """
        rows = max(1, rows)
        min_cols = 2 if self.augmented else 1
        data_cols = max(min_cols, data_cols)
        if (rows, data_cols) == self.data_shape():
            return
        self.checkpoint()
        current = self.get_raw_strings()
        new_data: List[List[str]] = []
        for r in range(rows):
            source = current[r] if r < len(current) else []
            if self.augmented:
                coeffs = source[:-1] if source else []
                b_val = source[-1] if source else "0"
                coeffs = (coeffs + ["0"] * data_cols)[: data_cols - 1]
                new_data.append(coeffs + [b_val or "0"])
            else:
                new_data.append((source + ["0"] * data_cols)[:data_cols])
        self.num_rows = rows
        self.num_vars = data_cols - 1 if self.augmented else data_cols
        self._build_grid()
        self.set_raw_strings(new_data)
        self.matrixChanged.emit()

    def get_matrix(self) -> Matrix:
        data: List[List[Fraction]] = []
        for row in self.cells:
            data.append([cell.get_value() for cell in row])
        return Matrix(data)

    def set_matrix(self, matrix: Matrix, *, record: bool = True) -> None:
        if record:
            self.checkpoint()
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

    def copy_to_clipboard(self) -> bool:
        """Copia la matriz completa al portapapeles en formato TSV universal."""
        try:
            mat = self.get_matrix()
            return copy_matrix_to_clipboard(mat, mode="fraction")
        except Exception:
            raw = self.get_raw_strings()
            return copy_matrix_to_clipboard(raw)

    def paste_from_clipboard(self) -> bool:
        """Pega una matriz del portapapeles redimensionando la cuadrícula automáticamente."""
        pasted_mat = get_matrix_from_clipboard()
        if pasted_mat is None:
            return False

        self.checkpoint()
        p_rows = pasted_mat.rows
        p_cols = pasted_mat.cols

        if self.augmented:
            if p_cols >= 2:
                self.num_rows = p_rows
                self.num_vars = p_cols - 1
                self._build_grid()
                for r in range(p_rows):
                    for c in range(p_cols):
                        val_str = format_scalar(pasted_mat.get(r, c), mode="fraction")
                        self.cells[r][c].setText(val_str)
            else:
                self.num_rows = p_rows
                self.num_vars = 1
                self._build_grid()
                for r in range(p_rows):
                    val_str = format_scalar(pasted_mat.get(r, 0), mode="fraction")
                    self.cells[r][0].setText(val_str)
                    self.cells[r][1].setText("0")
        else:
            if not self.col_expandable and self.num_vars == 1 and p_rows == 1 and p_cols > 1:
                # Transponer vector fila 1xK a vector columna Kx1 para editor de vectores columna
                self.num_rows = p_cols
                self.num_vars = 1
                self._build_grid()
                for r in range(p_cols):
                    val_str = format_scalar(pasted_mat.get(0, r), mode="fraction")
                    self.cells[r][0].setText(val_str)
            else:
                self.num_rows = p_rows
                self.num_vars = p_cols
                self._build_grid()
                for r in range(p_rows):
                    for c in range(p_cols):
                        val_str = format_scalar(pasted_mat.get(r, c), mode="fraction")
                        self.cells[r][c].setText(val_str)

        self.matrixChanged.emit()
        self.flash()
        rows, cols = self.data_shape()
        try:
            from prettycalc.ui.feedback import show_toast

            show_toast(
                self,
                f"Matriz {rows}×{cols} pegada. Ctrl+Z restaura la anterior.",
                kind="success",
                action_text="Deshacer",
                action=self.undo,
            )
        except Exception:
            pass
        return True

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.Copy) or (
            event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier
        ):
            self.copy_to_clipboard()
            event.accept()
            return
        if event.matches(QKeySequence.Paste) or (
            event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier
        ):
            if self.paste_from_clipboard():
                event.accept()
                return
        if event.matches(QKeySequence.Undo):
            if self.undo():
                event.accept()
                return
        if event.matches(QKeySequence.Redo) or _is_shortcut(event, Qt.Key_Y, Qt.ControlModifier):
            if self.redo():
                event.accept()
                return
        super().keyPressEvent(event)
