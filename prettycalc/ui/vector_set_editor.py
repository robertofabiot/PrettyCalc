"""Editores de vectores columna y de conjuntos {v₁, …, vₖ}.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10. Se usan en el Módulo 3 (combinación e independencia lineal) y en
el Módulo 4 (vectores u, v, b):

- Validación en línea con el nombre del vector y la componente (Nielsen #9),
  sin diálogos modales que interrumpan.
- Los vectores se distribuyen en varias filas (``FlowLayout``) en lugar de
  una tira con desplazamiento horizontal (Nielsen #8).
- «Pegar matriz como columnas» carga un ejercicio completo del libro en un
  paso (Nielsen #7), y quitar un vector se puede deshacer (Nielsen #3).
- Aviso pedagógico cuando k > n antes de evaluar (Nielsen #5).
"""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

try:
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QMenu,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore
    QFrame = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.clipboard import get_matrix_from_clipboard
from prettycalc.ui.feedback import show_toast
from prettycalc.ui.mathtext import to_subscript, to_superscript
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.responsive import FlowLayout
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    apply_widget_class,
)


MAX_DIMENSION = 10


def _component_name(base: str, index: int) -> str:
    return f"{base}{to_subscript(index)}"


class VectorColumnEditor(QFrame):
    """Editor de un vector columna con título y eliminación opcional."""

    removed = Signal()
    changed = Signal()
    dimensionChanged = Signal(int)
    submitRequested = Signal()

    def __init__(
        self,
        dimension: int,
        title: str,
        removable: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self._title = title
        self._current_dim = dimension
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        header.addWidget(self.title_lbl)
        header.addStretch(1)
        self.delete_btn: Optional[QPushButton] = None
        if removable:
            delete_btn = QPushButton("×")
            delete_btn.setObjectName("deleteAction")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setToolTip(f"Quitar {title} del conjunto")
            delete_btn.setAccessibleName(f"Quitar {title}")
            delete_btn.clicked.connect(self.removed.emit)
            header.addWidget(delete_btn)
            self.delete_btn = delete_btn
        layout.addLayout(header)

        self.grid = DynamicMatrixGrid(
            initial_rows=dimension,
            initial_cols=1,
            augmented=False,
            show_headers=False,
            row_expandable=False,
            col_expandable=False,
            show_hint=False,
        )
        self.grid.matrixChanged.connect(self._on_grid_changed)
        self.grid.submitRequested.connect(self.submitRequested.emit)
        layout.addWidget(self.grid)

    def _on_grid_changed(self) -> None:
        if self.grid.num_rows != self._current_dim:
            self._current_dim = self.grid.num_rows
            self.dimensionChanged.emit(self._current_dim)
        self.changed.emit()

    def title(self) -> str:
        return self._title

    def set_title(self, title: str) -> None:
        self._title = title
        self.title_lbl.setText(title)
        if self.delete_btn is not None:
            self.delete_btn.setToolTip(f"Quitar {title} del conjunto")
            self.delete_btn.setAccessibleName(f"Quitar {title}")

    def set_removable_enabled(self, enabled: bool, reason: str = "") -> None:
        if self.delete_btn is None:
            return
        self.delete_btn.setEnabled(enabled)
        self.delete_btn.setToolTip(f"Quitar {self._title} del conjunto" if enabled else reason)

    def dimension(self) -> int:
        return self.grid.num_rows

    def set_dimension(self, n: int) -> None:
        if n == self.grid.num_rows:
            return
        self._current_dim = n
        current = [row[0] if row else "0" for row in self.grid.get_raw_strings()]
        while len(current) < n:
            current.append("0")
        data = [[val] for val in current[:n]]
        self.grid.set_matrix(Matrix(data))

    def raw_values(self) -> List[str]:
        return [row[0] if row else "0" for row in self.grid.get_raw_strings()]

    def set_raw_values(self, values: Sequence[str]) -> None:
        self._current_dim = len(values)
        self.grid.set_matrix(Matrix([[0] for _ in values]))
        self.grid.set_raw_strings([[value] for value in values])

    def get_vector(self) -> Vector:
        return Vector.from_column_matrix(self.grid.get_matrix())

    def set_vector(self, vector: Vector) -> None:
        self._current_dim = vector.dimension
        self.grid.set_matrix(vector.to_column_matrix())

    def copy_to_clipboard(self) -> bool:
        return self.grid.copy_to_clipboard()

    def paste_from_clipboard(self) -> bool:
        return self.grid.paste_from_clipboard()

    def is_valid(self) -> bool:
        return self.grid.is_all_valid()

    def validation_message(self) -> str:
        """«v₂, componente 3: …» para la primera componente inválida."""
        cell = self.grid.first_invalid_cell()
        if cell is None:
            return ""
        return f"{self._title}, componente {cell.row + 1}: {cell.error_message}"

    def focus_first_invalid(self) -> bool:
        return self.grid.focus_first_invalid()

    def highlight_component(self, index: Optional[int]) -> None:
        if index is None:
            self.grid.clear_highlight()
        else:
            self.grid.set_highlight(rows=[index])


Snapshot = Tuple[int, List[List[str]]]


class VectorSetEditor(QFrame):
    """Tarjeta con un conjunto {v₁, …, vₖ} editable, pegable y con deshacer."""

    changed = Signal()
    dimensionChanged = Signal(int)
    submitRequested = Signal()

    def __init__(
        self,
        title: str,
        dimension: int,
        *,
        initial_count: int = 2,
        min_dimension: int = 1,
        max_vectors: int = 10,
        name: str = "v",
        crowded_hint: Optional[Callable[[int, int], str]] = None,
        extra_paste_actions: Sequence[Tuple[str, Callable[[], None]]] = (),
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self.editors: List[VectorColumnEditor] = []
        self._dimension = dimension
        self._min_dimension = min_dimension
        self._max_vectors = max_vectors
        self._name = name
        self._crowded_hint = crowded_hint

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        header.addWidget(self.title_lbl)
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        header.addWidget(self.count_lbl)
        header.addStretch(1)
        self.paste_btn = QPushButton("Pegar matriz")
        self.paste_btn.setObjectName("secondaryAction")
        self.paste_btn.setCursor(Qt.PointingHandCursor)
        self.paste_btn.setToolTip(
            "Pega una matriz copiada (Excel, LaTeX o texto): cada columna se convierte en un vector"
        )
        menu = QMenu(self.paste_btn)
        menu.addAction("Cada columna es un vector", self.paste_columns_from_clipboard)
        for label, callback in extra_paste_actions:
            menu.addAction(label, callback)
        self.paste_btn.setMenu(menu)
        header.addWidget(self.paste_btn)
        layout.addLayout(header)

        self.host = QWidget()
        self.host.setAutoFillBackground(False)
        self.flow = FlowLayout(self.host, spacing=10)
        layout.addWidget(self.host)

        footer = QHBoxLayout()
        self.add_btn = QPushButton("+  Agregar vector")
        self.add_btn.setObjectName("secondaryAction")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(lambda: self.add_vector())
        self.add_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        footer.addWidget(self.add_btn)
        self.crowded_lbl = QLabel("")
        self.crowded_lbl.setObjectName("crowdedHint")
        self.crowded_lbl.setWordWrap(True)
        self.crowded_lbl.setStyleSheet(f"color: {COLOR_ACCENT_WARNING}; font-size: 14px;")
        self.crowded_lbl.setVisible(False)
        footer.addWidget(self.crowded_lbl, 1)
        footer.addStretch(0)
        layout.addLayout(footer)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("vectorSetError")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 14px; font-weight: 600;")
        self.error_lbl.setVisible(False)
        layout.addWidget(self.error_lbl)

        for _ in range(initial_count):
            self.add_vector(record=False)

    # ------------------------------------------------------------------ estado
    def dimension(self) -> int:
        return self._dimension

    def count(self) -> int:
        return len(self.editors)

    def vectors(self) -> List[Vector]:
        return [editor.get_vector() for editor in self.editors]

    def is_valid(self) -> bool:
        return all(editor.is_valid() for editor in self.editors)

    def validation_message(self) -> str:
        for editor in self.editors:
            message = editor.validation_message()
            if message:
                return message
        return ""

    def focus_first_invalid(self) -> bool:
        return any(editor.focus_first_invalid() for editor in self.editors if not editor.is_valid())

    def snapshot(self) -> Snapshot:
        return self._dimension, [editor.raw_values() for editor in self.editors]

    def restore(self, snapshot: Snapshot) -> None:
        dimension, values = snapshot
        self._dimension = dimension
        while len(self.editors) > len(values):
            self._drop(self.editors[-1])
        while len(self.editors) < len(values):
            self.add_vector(record=False)
        for editor, raw in zip(self.editors, values):
            editor.set_raw_values(raw)
        self._refresh()
        self.dimensionChanged.emit(dimension)
        self.changed.emit()

    # -------------------------------------------------------------- edición
    def set_dimension(self, n: int) -> None:
        self._dimension = n
        for editor in self.editors:
            editor.set_dimension(n)
        self._refresh()

    def add_vector(self, vector: Optional[Vector] = None, *, record: bool = True) -> Optional[VectorColumnEditor]:
        if len(self.editors) >= self._max_vectors:
            return None
        editor = VectorColumnEditor(self._dimension, self._name, removable=True, parent=self.host)
        editor.removed.connect(lambda e=editor: self.remove_vector(e))
        editor.dimensionChanged.connect(self._on_editor_dimension)
        editor.changed.connect(self._on_editor_changed)
        editor.submitRequested.connect(self.submitRequested.emit)
        if vector is not None:
            editor.set_vector(vector)
        self.editors.append(editor)
        self.flow.addWidget(editor)
        editor.show()
        self._refresh()
        if record:
            self.changed.emit()
        return editor

    def _drop(self, editor: VectorColumnEditor) -> None:
        self.editors.remove(editor)
        self.flow.removeWidget(editor)
        editor.hide()
        editor.setParent(None)
        editor.deleteLater()

    def remove_vector(self, editor: VectorColumnEditor, *, offer_undo: bool = True) -> None:
        if len(self.editors) <= 1 or editor not in self.editors:
            return
        before = self.snapshot()
        title = editor.title()
        self._drop(editor)
        self._refresh()
        self.changed.emit()
        if offer_undo:
            show_toast(
                self,
                f"Se quitó {title}.",
                action_text="Deshacer",
                action=lambda: self.restore(before),
            )

    def set_vectors(self, vectors: Sequence[Vector]) -> None:
        """Carga un conjunto completo (ejemplos y pegado)."""
        if not vectors:
            return
        self._dimension = vectors[0].dimension
        while len(self.editors) > len(vectors):
            self._drop(self.editors[-1])
        while len(self.editors) < len(vectors):
            self.add_vector(record=False)
        for editor, vector in zip(self.editors, vectors):
            editor.set_vector(vector)
        self._refresh()
        self.dimensionChanged.emit(self._dimension)
        self.changed.emit()

    def paste_matrix(self, matrix: Matrix) -> bool:
        """Cada columna de ``matrix`` pasa a ser un vector vⱼ."""
        if not self._min_dimension <= matrix.rows <= MAX_DIMENSION:
            show_toast(
                self,
                f"La matriz pegada tiene {matrix.rows} filas; la dimensión admitida es de "
                f"{self._min_dimension} a {MAX_DIMENSION}.",
                kind="error",
            )
            return False
        if matrix.cols > self._max_vectors:
            show_toast(
                self,
                f"La matriz pegada tiene {matrix.cols} columnas; el conjunto admite hasta "
                f"{self._max_vectors} vectores.",
                kind="error",
            )
            return False
        before = self.snapshot()
        columns = [Vector([matrix.get(r, c) for r in range(matrix.rows)]) for c in range(matrix.cols)]
        self.set_vectors(columns)
        show_toast(
            self,
            f"Se cargaron {matrix.cols} vectores de ℝ{to_superscript(matrix.rows)} (una columna por vector).",
            kind="success",
            action_text="Deshacer",
            action=lambda: self.restore(before),
        )
        return True

    def paste_columns_from_clipboard(self) -> bool:
        matrix = get_matrix_from_clipboard()
        if matrix is None:
            show_toast(
                self,
                "El portapapeles no contiene una matriz numérica. Copia la matriz desde una "
                "hoja de cálculo, LaTeX o texto con columnas separadas por tabuladores o espacios.",
                kind="error",
            )
            return False
        return self.paste_matrix(matrix)

    # ------------------------------------------------------------ reacciones
    def _on_editor_dimension(self, n: int) -> None:
        if not self._min_dimension <= n <= MAX_DIMENSION or n == self._dimension:
            return
        self._dimension = n
        for editor in self.editors:
            editor.set_dimension(n)
        self._refresh()
        self.dimensionChanged.emit(n)

    def _on_editor_changed(self) -> None:
        self._refresh_error()
        self.changed.emit()

    def _refresh(self) -> None:
        k = len(self.editors)
        for index, editor in enumerate(self.editors, start=1):
            editor.set_title(_component_name(self._name, index))
            editor.set_removable_enabled(k > 1, "El conjunto necesita al menos un vector")
        self.count_lbl.setText(f"k = {k}  ·  ℝ{to_superscript(self._dimension)}")
        full = k >= self._max_vectors
        self.add_btn.setEnabled(not full)
        self.add_btn.setToolTip(
            f"Máximo {self._max_vectors} vectores" if full else "Agrega un vector de ceros al conjunto"
        )
        message = self._crowded_hint(k, self._dimension) if self._crowded_hint else ""
        self.crowded_lbl.setText(message)
        self.crowded_lbl.setVisible(bool(message))
        self._refresh_error()
        self.host.updateGeometry()

    def _refresh_error(self) -> None:
        message = self.validation_message()
        self.error_lbl.setText(f"✕  {message}" if message else "")
        self.error_lbl.setVisible(bool(message))

    def crowded_text(self) -> str:
        return self.crowded_lbl.text() if self.crowded_lbl.isVisibleTo(self) else ""
