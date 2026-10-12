"""Carrusel de pasos con notación de libro: corchetes, fracciones apiladas y fórmulas.

Sprint 10:

- Barra de desplazamiento para saltar a cualquier paso y atajos de teclado
  (←/→, Inicio/Fin, RePág/AvPág) cuando el carrusel tiene el foco.
- Alertas automáticas de filas nulas: en una inversión señala el paso exacto
  en que el rango colapsa; en un sistema señala la fila [0 … 0 | c].
- Menú «Exportar» con el procedimiento completo en PDF, HTML, LaTeX o texto.
"""

from __future__ import annotations
from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFrame,
        QSlider,
        QMenu,
        QFileDialog,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QGuiApplication, QKeyEvent
except ImportError:
    QFrame = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.tracer import CalculationStep
from prettycalc.core.types import format_scalar
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.mathtext import latex_to_book_html, variable_html
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    COLOR_FEEDBACK_SUCCESS,
    FONT_FAMILY_SANS,
    apply_widget_class,
)

#: Interpretación de una fila nula en el bloque izquierdo.
ALERT_NONE = ""
ALERT_SINGULAR = "singular"
ALERT_SYSTEM = "system"


def zero_row_alerts(step: CalculationStep, mode: str) -> Tuple[Tuple[int, ...], str, bool]:
    """Filas nulas del bloque izquierdo de ``step``, un mensaje y si es crítico.

    Crítico significa que la fila prueba singularidad o una contradicción.
    """
    if not mode:
        return tuple(step.alert_rows), "", False
    matrix = step.matrix
    split = step.split_col if step.split_col is not None else matrix.cols
    rows: List[int] = []
    contradictions: List[Tuple[int, str]] = []
    for r in range(matrix.rows):
        if not all(matrix.get(r, c) == 0 for c in range(split)):
            continue
        rows.append(r)
        if mode == ALERT_SYSTEM and split < matrix.cols:
            rhs = matrix.get(r, split)
            if rhs != 0:
                contradictions.append((r, format_scalar(rhs)))
    rows_tuple = tuple(sorted(set(rows) | set(step.alert_rows)))
    if not rows:
        return rows_tuple, "", False
    names = ", ".join(str(r + 1) for r in rows)
    plural = len(rows) > 1
    if mode == ALERT_SINGULAR:
        return rows_tuple, (
            f"Rango deficiente: fila{'s' if plural else ''} {names} nula{'s' if plural else ''} en el bloque "
            "izquierdo. El rango es menor que n, así que la matriz es singular."
        ), True
    if contradictions:
        r, value = contradictions[0]
        return rows_tuple, (
            f"Contradicción en la fila {r + 1}: 0 = {value}. El sistema no tiene solución."
        ), True
    return rows_tuple, (
        f"Fila{'s' if plural else ''} {names} nula{'s' if plural else ''} (0 = 0): "
        "ecuación redundante; si hay menos pivotes que incógnitas, aparecen variables libres."
    ), False


class AlgorithmStepperCarousel(QFrame):
    """Stepper para navegar las transformaciones elementales del algoritmo."""

    #: Índice del paso visible (−1 sin pasos). Permite sincronizar diagramas externos.
    stepChanged = Signal(int)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        alert_mode: str = ALERT_NONE,
        variable_headers: bool = True,
    ):
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        # Las cabeceras x₁ … xₙ solo tienen sentido sobre un sistema [A | b];
        # en determinantes, LU o vectores se ocultan.
        self._variable_headers = variable_headers
        self._steps: List[CalculationStep] = []
        self._current_index: int = 0
        self._display_mode: str = "fraction"
        self._alert_mode = alert_mode
        self._export_title = "Procedimiento"
        self._empty_hint = "Ingresa el sistema y pulsa Resolver."
        self.setFocusPolicy(Qt.StrongFocus)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        self.prev_btn = QPushButton("Anterior")
        self.prev_btn.setMinimumWidth(96)
        self.prev_btn.setToolTip("Paso anterior (←)")
        self.prev_btn.clicked.connect(self.prev_step)
        nav_layout.addWidget(self.prev_btn)

        self.step_label = QLabel("Paso 0 de 0")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setMinimumWidth(96)
        self.step_label.setStyleSheet(
            f"font-weight: 600; font-size: 17px; letter-spacing: 0.04em; color: {COLOR_TEXT_PRIMARY};"
        )
        nav_layout.addWidget(self.step_label, stretch=1)

        self.next_btn = QPushButton("Siguiente")
        self.next_btn.setMinimumWidth(106)
        self.next_btn.setToolTip("Paso siguiente (→)")
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)

        self.mode_btn = QPushButton("Fracciones")
        self.mode_btn.setObjectName("modeToggle")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.setToolTip("Interruptor: vista actual en fracciones o decimales")
        self.mode_btn.setMinimumWidth(106)
        apply_widget_class(self.mode_btn, "modeToggle")
        nav_layout.addWidget(self.mode_btn)

        layout.addLayout(nav_layout)

        scrub_row = QHBoxLayout()
        scrub_row.setContentsMargins(0, 0, 0, 0)
        scrub_row.setSpacing(10)
        self.jump_caption = QLabel("Ir al paso")
        self.jump_caption.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        scrub_row.addWidget(self.jump_caption)
        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setObjectName("stepSlider")
        self.step_slider.setMinimum(1)
        self.step_slider.setMaximum(1)
        self.step_slider.setPageStep(1)
        self.step_slider.setToolTip("Arrastra para saltar a cualquier paso (Inicio/Fin: primero/último)")
        self.step_slider.setAccessibleName("Selector de paso del procedimiento")
        self.step_slider.valueChanged.connect(self._on_slider_moved)
        scrub_row.addWidget(self.step_slider, stretch=1)
        self.export_btn = QPushButton("Exportar")
        self.export_btn.setObjectName("secondaryAction")
        self.export_btn.setToolTip("Copiar o guardar el procedimiento completo (PDF, HTML, LaTeX o texto)")
        self.export_btn.clicked.connect(self._show_export_menu)
        scrub_row.addWidget(self.export_btn)
        self.scrub_host = QWidget()
        self.scrub_host.setLayout(scrub_row)
        self.scrub_host.setVisible(False)
        layout.addWidget(self.scrub_host)

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
        self.formula_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        formula_layout.addWidget(self.formula_label)
        layout.addWidget(formula_box)

        self.matrix_view = BookMatrixWidget()
        self.matrix_view.setStyleSheet(f"background-color: {COLOR_SURFACE_INNER}; border-radius: 4px;")
        layout.addWidget(self.matrix_view, stretch=1)

        self.alert_label = QLabel("")
        self.alert_label.setObjectName("stepAlert")
        self.alert_label.setWordWrap(True)
        self.alert_label.setVisible(False)
        layout.addWidget(self.alert_label)

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
        self.heuristic_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.heuristic_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_PRIMARY};
                font-size: 18px;
                font-style: italic;
                font-family: {FONT_FAMILY_SANS};
                font-weight: 500;
            }}
        """)
        heuristic_layout.addWidget(self.heuristic_label, stretch=1)

        self.pivot_badge = QLabel("")
        self.pivot_badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pivot_badge.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_FEEDBACK_SUCCESS};
                font-size: 15px;
                font-weight: 600;
                font-family: {FONT_FAMILY_SANS};
                padding-left: 8px;
            }}
        """)
        heuristic_layout.addWidget(self.pivot_badge)
        layout.addWidget(heuristic_box)

        self.mode_btn.toggled.connect(self._on_mode_toggled)
        self._update_view()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_steps(self, steps: List[CalculationStep]) -> None:
        self._steps = steps
        self._current_index = 0
        self._update_view()

    def set_alert_mode(self, mode: str) -> None:
        self._alert_mode = mode
        self._update_view()

    def set_export_title(self, title: str) -> None:
        self._export_title = title

    def set_empty_hint(self, text: str) -> None:
        self._empty_hint = text
        if not self._steps:
            self._update_view()

    def steps(self) -> List[CalculationStep]:
        return list(self._steps)

    def current_index(self) -> int:
        return self._current_index

    def go_to_step(self, index: int) -> None:
        """Salta al paso ``index`` (base 0), acotado al rango disponible."""
        if not self._steps:
            return
        index = max(0, min(index, len(self._steps) - 1))
        if index == self._current_index:
            return
        forward = index == self._current_index + 1
        self._current_index = index
        self._update_view(animate=forward)

    def first_alert_index(self) -> Optional[int]:
        """Primer paso con una fila nula crítica (singularidad o contradicción)."""
        for index, step in enumerate(self._steps):
            rows, _message, critical = zero_row_alerts(step, self._alert_mode)
            if rows and critical:
                return index
        return None

    def prev_step(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._update_view(animate=False)

    def next_step(self) -> None:
        if self._current_index < len(self._steps) - 1:
            self._current_index += 1
            self._update_view(animate=True)

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if not self._steps:
            super().keyPressEvent(event)
            return
        if key in (Qt.Key_Right, Qt.Key_PageDown):
            self.next_step()
        elif key in (Qt.Key_Left, Qt.Key_PageUp):
            self.prev_step()
        elif key == Qt.Key_Home:
            self.go_to_step(0)
        elif key == Qt.Key_End:
            self.go_to_step(len(self._steps) - 1)
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------

    def _show_export_menu(self) -> None:
        menu = QMenu(self)
        text_action = menu.addAction("Copiar procedimiento como texto")
        text_action.triggered.connect(self.copy_steps_as_text)
        latex_action = menu.addAction("Copiar procedimiento como LaTeX")
        latex_action.triggered.connect(self.copy_steps_as_latex)
        menu.addSeparator()
        save_action = menu.addAction("Guardar informe (PDF, HTML, LaTeX)…")
        save_action.triggered.connect(self.save_steps_dialog)
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))

    def copy_steps_as_text(self) -> bool:
        from prettycalc.ui.export import steps_to_text

        return self._copy(steps_to_text(self._steps, self._export_title), "texto")

    def copy_steps_as_latex(self) -> bool:
        from prettycalc.ui.export import steps_to_latex

        return self._copy(steps_to_latex(self._steps, self._export_title), "LaTeX")

    def _copy(self, payload: str, label: str) -> bool:
        if not self._steps:
            return False
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return False
        clipboard.setText(payload)
        from prettycalc.ui.feedback import show_toast

        show_toast(self, f"Procedimiento copiado como {label} ({len(self._steps)} pasos).", kind="success")
        return True

    def save_steps_dialog(self) -> Optional[str]:
        if not self._steps:
            return None
        safe = "".join(ch if ch.isalnum() else "_" for ch in self._export_title).strip("_") or "procedimiento"
        # Diálogo de Qt (no el del sistema) para que se vea igual en Windows y Linux.
        path, _selected = QFileDialog.getSaveFileName(
            self,
            "Guardar procedimiento",
            f"{safe.lower()}.pdf",
            "PDF (*.pdf);;Página web (*.html);;LaTeX (*.tex);;Texto (*.txt)",
            "",
            QFileDialog.DontUseNativeDialog,
        )
        if not path:
            return None
        return self.save_steps(path)

    def save_steps(self, path: str) -> Optional[str]:
        from prettycalc.ui.export import write_report
        from prettycalc.ui.feedback import show_toast

        try:
            written = write_report(path, self._steps, self._export_title)
        except OSError as exc:
            show_toast(self, f"No se pudo guardar: {exc}", kind="error")
            return None
        show_toast(self, f"Informe guardado en {written}", kind="success")
        return written

    # ------------------------------------------------------------------
    # Vista
    # ------------------------------------------------------------------

    def _on_mode_toggled(self, checked: bool) -> None:
        self._display_mode = "fraction" if checked else "decimal"
        self.mode_btn.setText("Fracciones" if checked else "Decimales")
        self._update_view(animate=False)

    def _on_slider_moved(self, value: int) -> None:
        target = value - 1
        if target != self._current_index:
            self.go_to_step(target)

    def _sync_slider(self) -> None:
        total = len(self._steps)
        self.scrub_host.setVisible(total > 0)
        self.jump_caption.setVisible(total > 2)
        self.step_slider.setVisible(total > 2)
        self.step_slider.blockSignals(True)
        self.step_slider.setMaximum(max(1, total))
        self.step_slider.setValue(self._current_index + 1)
        self.step_slider.setEnabled(total > 1)
        self.step_slider.blockSignals(False)

    def _update_view(self, animate: bool = False) -> None:
        self.export_btn.setEnabled(bool(self._steps))
        if not self._steps:
            self.step_label.setText("Sin pasos")
            self.formula_label.setText(
                f"<span style='color:{COLOR_TEXT_MUTED}; font-style:italic; font-size:16px;'>Esperando resolución</span>"
            )
            self.heuristic_label.setText(self._empty_hint)
            self.pivot_badge.setText("")
            self.alert_label.setVisible(False)
            self.matrix_view.clear()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self._sync_slider()
            self.stepChanged.emit(-1)
            return

        total = len(self._steps)
        curr = self._current_index
        step = self._steps[curr]

        if curr == 0:
            self.step_label.setText(f"1 / {total}   inicial")
        elif curr == total - 1:
            self.step_label.setText(f"{curr + 1} / {total}   final")
        else:
            self.step_label.setText(f"{curr + 1} / {total}")

        self.formula_label.setText(latex_to_book_html(step.latex_formula))
        self.heuristic_label.setText(step.heuristic_text)

        if step.pivot_pos is not None:
            pr, pc = step.pivot_pos
            col_var = variable_html(pc, sub_size_px=11) if step.split_col is None or pc < step.split_col else "b"
            self.pivot_badge.setTextFormat(Qt.RichText)
            self.pivot_badge.setText(f"Pivote: Fila {pr + 1}, Columna {pc + 1} ({col_var})")
        else:
            self.pivot_badge.setText("")

        alert_rows, alert_message, critical = zero_row_alerts(step, self._alert_mode)
        if alert_message:
            color = COLOR_FEEDBACK_ERROR if critical else COLOR_ACCENT_WARNING
            self.alert_label.setStyleSheet(
                f"color: {color}; font-size: 15px; font-weight: 600; padding: 4px 2px;"
            )
            self.alert_label.setText(alert_message)
            self.alert_label.setVisible(True)
        else:
            self.alert_label.setVisible(False)

        self.prev_btn.setEnabled(curr > 0)
        self.next_btn.setEnabled(curr < total - 1)
        self._sync_slider()

        self.matrix_view.set_matrix(
            step.matrix,
            split_col=step.split_col,
            pivot=step.pivot_pos,
            mode=self._display_mode,
            actor_row=step.actor_row,
            affected_rows=step.affected_rows,
            animate=animate,
            alert_rows=alert_rows,
            highlight_cells=step.highlight_cells,
            show_headers=self._variable_headers,
        )
        self.stepChanged.emit(curr)
