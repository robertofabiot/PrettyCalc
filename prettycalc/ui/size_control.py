"""Control directo de dimensiones para una ``DynamicMatrixGrid``.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (Nielsen #7): pasar de 2×2 a 5×5 es un solo gesto (escribir o
girar la rueda del ratón) en lugar de varios clics en los botones ``+``.
El control y la cuadrícula se mantienen sincronizados en ambos sentidos.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QWidget
    from PySide6.QtCore import Signal
except ImportError:  # pragma: no cover
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.theme import COLOR_TEXT_MUTED, COLOR_TEXT_PRIMARY, FONT_FAMILY_MONO


class MatrixSizeControl(QWidget):
    """Spinboxes ``filas × columnas`` (o un único orden n para matrices cuadradas).

    En una cuadrícula aumentada las columnas cuentan las incógnitas: la columna
    ``b`` se agrega sola. Con ``caption`` se muestra un único rótulo compacto
    («Ecuaciones × incógnitas») en lugar de uno por spinbox.
    """

    sizeChanged = Signal(int, int)

    def __init__(
        self,
        grid: DynamicMatrixGrid,
        *,
        square: bool = False,
        rows_label: str = "Filas",
        cols_label: str = "Columnas",
        order_label: str = "Orden n",
        caption: str = "",
        minimum: int = 1,
        maximum: int = 8,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.grid = grid
        self.square = square
        self._syncing = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        caption_style = f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        compact = bool(caption) and not square
        self.rows_caption = QLabel(caption if compact else (order_label if square else rows_label))
        self.rows_caption.setStyleSheet(caption_style)
        layout.addWidget(self.rows_caption)

        self.rows_spin = QSpinBox()
        self.rows_spin.setObjectName("sizeRowsSpin")
        self.rows_spin.setRange(minimum, maximum)
        self.rows_spin.setAccelerated(True)
        self.rows_spin.setAccessibleName(order_label if square else rows_label)
        self.rows_spin.setToolTip(
            f"{order_label if square else rows_label}: escribe un valor entre {minimum} y {maximum}"
        )
        layout.addWidget(self.rows_spin)

        self.times_label = QLabel("×")
        self.times_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 16px; font-family: {FONT_FAMILY_MONO};"
        )
        self.cols_caption = QLabel(cols_label)
        self.cols_caption.setStyleSheet(caption_style)
        self.cols_spin = QSpinBox()
        self.cols_spin.setObjectName("sizeColsSpin")
        self.cols_spin.setRange(minimum, maximum)
        self.cols_spin.setAccelerated(True)
        self.cols_spin.setAccessibleName(cols_label)
        self.cols_spin.setToolTip(f"{cols_label}: escribe un valor entre {minimum} y {maximum}")
        if square:
            self.times_label.hide()
            self.cols_caption.hide()
            self.cols_spin.hide()
        else:
            layout.addWidget(self.times_label)
            if compact:
                self.cols_caption.hide()
            else:
                layout.addWidget(self.cols_caption)
            layout.addWidget(self.cols_spin)
        layout.addStretch(1)

        self.rows_spin.valueChanged.connect(self._on_spin_changed)
        self.cols_spin.valueChanged.connect(self._on_spin_changed)
        grid.matrixChanged.connect(self.sync_from_grid)
        self.sync_from_grid()

    def _grid_dims(self) -> tuple[int, int]:
        rows, data_cols = self.grid.data_shape()
        unknowns = data_cols - 1 if self.grid.augmented else data_cols
        return rows, unknowns

    def dimensions(self) -> tuple[int, int]:
        return self._grid_dims()

    def sync_from_grid(self) -> None:
        if self._syncing:
            return
        rows, cols = self._grid_dims()
        self._syncing = True
        try:
            self.rows_spin.setValue(rows)
            self.cols_spin.setValue(cols)
        finally:
            self._syncing = False

    def _on_spin_changed(self, _value: int = 0) -> None:
        if self._syncing:
            return
        rows = self.rows_spin.value()
        cols = rows if self.square else self.cols_spin.value()
        self.set_size(rows, cols)

    def set_size(self, rows: int, cols: int) -> None:
        """Redimensiona la cuadrícula; ``cols`` son incógnitas si es aumentada."""
        data_cols = cols + 1 if self.grid.augmented else cols
        self._syncing = True
        try:
            self.rows_spin.setValue(rows)
            self.cols_spin.setValue(cols)
            self.grid.resize_to(rows, data_cols)
        finally:
            self._syncing = False
        self.sizeChanged.emit(rows, cols)
