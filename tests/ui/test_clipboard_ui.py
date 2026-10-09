from fractions import Fraction
import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QGuiApplication, QKeyEvent, QContextMenuEvent
from PySide6.QtWidgets import QApplication

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.matrix_grid import DynamicMatrixGrid, MatrixCellEdit
from prettycalc.ui.modules.vectors_view import VectorColumnEditor, VectorsView
from prettycalc.ui.clipboard import (
    copy_matrix_to_clipboard,
    get_clipboard_text,
    get_matrix_from_clipboard,
    has_matrix_in_clipboard,
)


def test_ui_clipboard_copy_and_get(qtbot):
    mat = Matrix([[1, 2], [3, 4]])
    assert copy_matrix_to_clipboard(mat, mode="fraction") is True
    assert has_matrix_in_clipboard() is True
    assert get_clipboard_text() == "1\t2\n3\t4"

    retrieved = get_matrix_from_clipboard()
    assert retrieved is not None
    assert retrieved.rows == 2
    assert retrieved.cols == 2
    assert retrieved.get(0, 0) == Fraction(1)
    assert retrieved.get(1, 1) == Fraction(4)


def test_book_matrix_widget_copy(qtbot):
    widget = BookMatrixWidget()
    qtbot.addWidget(widget)
    mat = Matrix([[1, "-1/2"], [3, 4]])
    widget.set_matrix(mat, mode="fraction")

    # Copia directa
    assert widget.copy_to_clipboard() is True
    assert get_clipboard_text() == "1\t-1/2\n3\t4"

    # Tecla Ctrl+C
    QGuiApplication.clipboard().setText("")
    key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_C, Qt.ControlModifier)
    widget.keyPressEvent(key_event)
    assert get_clipboard_text() == "1\t-1/2\n3\t4"


def test_dynamic_matrix_grid_copy_and_paste_resize(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
    qtbot.addWidget(grid)

    # Configurar valores y copiar
    grid.cells[0][0].setText("5")
    grid.cells[0][1].setText("6")
    grid.cells[1][0].setText("7")
    grid.cells[1][1].setText("8")

    assert grid.copy_to_clipboard() is True
    assert get_clipboard_text() == "5\t6\n7\t8"

    # Preparar portapapeles con una matriz 3x3
    new_tsv = "1/3\t2\t3\n4\t5/2\t6\n7\t8\t9"
    QGuiApplication.clipboard().setText(new_tsv)

    # Pegar en la cuadrícula: debe redimensionar a 3x3 automáticamente
    assert grid.paste_from_clipboard() is True
    assert grid.num_rows == 3
    assert grid.num_vars == 3
    assert grid.cells[0][0].text() == "1/3"
    assert grid.cells[1][1].text() == "5/2"
    assert grid.cells[2][2].text() == "9"


def test_dynamic_matrix_grid_augmented_paste(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=True)
    qtbot.addWidget(grid)

    # En modo aumentado, 3 columnas corresponden a 2 incógnitas + 1 término independiente b
    tsv_augmented = "1\t2\t10\n3\t4\t20"
    QGuiApplication.clipboard().setText(tsv_augmented)

    assert grid.paste_from_clipboard() is True
    assert grid.num_rows == 2
    assert grid.num_vars == 2
    # Columnas: col 0 y col 1 son coeficientes, col 2 es b
    assert grid.cells[0][0].text() == "1"
    assert grid.cells[0][1].text() == "2"
    assert grid.cells[0][2].text() == "10"
    assert grid.cells[1][2].text() == "20"


def test_matrix_cell_edit_context_menu_and_shortcuts(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
    qtbot.addWidget(grid)
    cell = grid.cells[0][0]
    cell.setText("42")

    # Tecla Ctrl+C sin selección parcial debe copiar la matriz completa
    cell.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_C, Qt.ControlModifier))
    assert "\t" in get_clipboard_text() or get_clipboard_text() == "42\t0\n0\t0"

    # Tecla Ctrl+V con matriz en portapapeles dispara paste_from_clipboard
    tsv = "10\t20\n30\t40"
    QGuiApplication.clipboard().setText(tsv)
    cell.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_V, Qt.ControlModifier))
    assert grid.cells[0][0].text() == "10"
    assert grid.cells[0][1].text() == "20"
    assert grid.cells[1][1].text() == "40"

    # Tecla Ctrl+V con escalar simple pega en la celda activa
    QGuiApplication.clipboard().setText("99")
    cell.selectAll()
    cell.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_V, Qt.ControlModifier))
    assert cell.text() == "99"


def test_vector_column_editor_paste_row_vector_transposes(qtbot):
    editor = VectorColumnEditor(dimension=3, title="v1")
    qtbot.addWidget(editor)

    # Copiar un vector fila 1x3 al portapapeles
    QGuiApplication.clipboard().setText("10\t20\t30")

    # Pegar en editor de vector columna: debe transponer automáticamente a 3x1
    assert editor.paste_from_clipboard() is True
    assert editor.grid.num_rows == 3
    assert editor.grid.num_vars == 1
    assert editor.grid.cells[0][0].text() == "10"
    assert editor.grid.cells[1][0].text() == "20"
    assert editor.grid.cells[2][0].text() == "30"


def test_vector_column_editor_paste_resizes_and_syncs_dimension(qtbot):
    view = VectorsView()
    qtbot.addWidget(view)

    # Dimensión inicial en pestaña básica es 3
    assert view.basic_dim.value() == 3

    # Pegar un vector de 4 elementos en vec_u
    QGuiApplication.clipboard().setText("1\n2\n3\n4")
    assert view.vec_u.paste_from_clipboard() is True

    # El spinner básico debe haberse sincronizado a 4 y vec_u tener los 4 valores
    assert view.basic_dim.value() == 4
    assert view.vec_u.grid.num_rows == 4
    assert view.vec_u.grid.cells[3][0].text() == "4"
    assert view.vec_v.grid.num_rows == 4


def test_dynamic_matrix_grid_paste_python_list_and_latex(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
    qtbot.addWidget(grid)

    # Pegar formato Python [[...]]
    QGuiApplication.clipboard().setText("[[1, 2], [3/5, -4.5]]")
    assert grid.paste_from_clipboard() is True
    assert grid.cells[0][0].text() == "1"
    assert grid.cells[0][1].text() == "2"
    assert grid.cells[1][0].text() == "3/5"
    assert grid.cells[1][1].text() == "-9/2"

    # Pegar formato LaTeX
    QGuiApplication.clipboard().setText(r"\begin{pmatrix} 7 & 8 \\ 9 & 10 \end{pmatrix}")
    assert grid.paste_from_clipboard() is True
    assert grid.cells[0][0].text() == "7"
    assert grid.cells[0][1].text() == "8"
    assert grid.cells[1][0].text() == "9"
    assert grid.cells[1][1].text() == "10"


def test_book_matrix_widget_context_menu_action(qtbot, monkeypatch):
    widget = BookMatrixWidget()
    qtbot.addWidget(widget)
    mat = Matrix([[1, 2], [3, 4]])
    widget.set_matrix(mat)

    menu_instances = []

    class FakeMenu:
        def __init__(self, parent=None):
            self.actions_list = []
            menu_instances.append(self)

        def addAction(self, text):
            class Action:
                def __init__(self, t):
                    self._text = t
                def text(self):
                    return self._text
                def setShortcut(self, sc):
                    pass
                @property
                def triggered(self):
                    class SignalMock:
                        def connect(self, f):
                            pass
                    return SignalMock()
            action = Action(text)
            self.actions_list.append(action)
            return action

        def actions(self):
            return self.actions_list

        def exec(self, pos):
            pass

    monkeypatch.setattr("prettycalc.ui.book_matrix.QMenu", FakeMenu)

    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, QPoint(10, 10), QPoint(10, 10))
    widget.contextMenuEvent(event)
    assert len(menu_instances) == 1
    actions = [a.text() for a in menu_instances[0].actions()]
    assert "Copiar matriz" in actions


def test_dynamic_matrix_grid_cell_context_menu(qtbot, monkeypatch):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
    qtbot.addWidget(grid)
    cell = grid.cells[0][0]

    menu_instances = []

    class FakeMenu:
        def __init__(self, parent=None):
            self.actions_list = []
            menu_instances.append(self)

        def addAction(self, text):
            class Action:
                def __init__(self, t):
                    self._text = t
                    self._enabled = True
                    self._tooltip = ""
                def text(self): return self._text
                def setShortcut(self, sc): pass
                def setEnabled(self, en): self._enabled = en
                def isEnabled(self): return self._enabled
                def setToolTip(self, tip): self._tooltip = tip
                @property
                def triggered(self):
                    class SignalMock:
                        def connect(self, f): pass
                    return SignalMock()
            action = Action(text)
            self.actions_list.append(action)
            return action

        def addSeparator(self):
            pass

        def exec(self, pos):
            pass

    monkeypatch.setattr("prettycalc.ui.matrix_grid.QMenu", FakeMenu)

    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, QPoint(5, 5), QPoint(5, 5))
    cell.contextMenuEvent(event)

    assert len(menu_instances) == 1
    action_texts = [a.text() for a in menu_instances[0].actions_list]
    assert "Copiar matriz" in action_texts
    assert "Pegar matriz" in action_texts
    assert "Copiar valor de celda" in action_texts
    assert "Pegar en celda" in action_texts
    assert "Eliminar fila" in action_texts
    assert "Eliminar columna" in action_texts
