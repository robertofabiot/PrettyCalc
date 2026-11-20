"""Carrusel de pasos con notación de libro: corchetes, fracciones apiladas y fórmulas.

Sprint 10:

- Barra de desplazamiento para saltar a cualquier paso y atajos de teclado
  (←/→, Inicio/Fin, RePág/AvPág) cuando el carrusel tiene el foco.
- Alertas automáticas de filas nulas: en una inversión señala el paso exacto
  en que el rango colapsa; en un sistema señala la fila [0 … 0 | c].
- Menú «Exportar» con el procedimiento completo en PDF, HTML, LaTeX o texto.

Sprint 11 (movimiento):

- Avanzar un paso reproduce la operación en el visor (ver ``BookMatrixWidget``);
  retroceder o saltar solo funde lo que cambió. En ráfaga (tecla mantenida o
  pulsada antes de que termine la secuencia) se usa siempre la versión corta.
- Al llegar a la forma final de un sistema, los pivotes se encienden en orden
  y las cabeceras quedan en verde (básicas) u ocre (libres).
- Reproducir el procedimiento: recorre los pasos con su coreografía y deja
  tiempo de lectura después de cada uno (0.5×, 1× o 2×; Espacio con el
  carrusel enfocado). Se detiene al final, ante cualquier interacción con el
  carrusel, al cambiar de módulo y si cambian los pasos.
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
    from PySide6.QtCore import QPointF, Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent, QPainter, QPolygonF
except ImportError:
    QFrame = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core import step_diff
from prettycalc.core.tracer import CalculationStep
from prettycalc.core.types import format_scalar
from prettycalc.ui import motion
from prettycalc.ui.book_matrix import (
    BookMatrixWidget,
    TRANSITION_BACK,
    TRANSITION_FORWARD,
    TRANSITION_JUMP,
    TRANSITION_SHORT,
)
from prettycalc.ui.mathtext import latex_to_book_html, prettify_step_text, variable_html
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
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


#: Velocidades de la reproducción, en el orden en que las recorre el botón.
PLAYBACK_SPEEDS = (1.0, 2.0, 0.5)
#: Tiempo de lectura base después de cada paso a 1×.
READING_BASE_MS = 1200


def reading_time_ms(text: str) -> int:
    """Tiempo de lectura de un paso a 1×: base más un poco por cada carácter extra."""
    plain = text or ""
    return int(min(4200, READING_BASE_MS + max(0, len(plain) - 60) * 18))


def speed_label(speed: float) -> str:
    """Rótulo corto de la velocidad (½× cabe en el botón; 0.5× no)."""
    return "½×" if speed == 0.5 else f"{speed:g}×"


class _PlaybackButton(QPushButton):
    """Reproducir / pausar, con el icono dibujado (sin depender de glifos)."""

    def __init__(self) -> None:
        super().__init__("")
        self._playing = False
        self.setObjectName("secondaryAction")
        self.setFixedWidth(36)
        self.setCursor(Qt.PointingHandCursor)
        self.set_playing(False)

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        name = "Pausar la reproducción del procedimiento" if playing else "Reproducir el procedimiento"
        self.setAccessibleName(name)
        self.setToolTip(f"{name} (Espacio)")
        self.update()

    def is_playing(self) -> bool:
        return self._playing

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        color = QColor(COLOR_TEXT_PRIMARY if self.isEnabled() else COLOR_TEXT_MUTED)
        painter.setBrush(color)
        cx, cy = self.width() / 2, self.height() / 2
        if self._playing:
            painter.drawRoundedRect(int(cx - 6), int(cy - 6), 4, 12, 1, 1)
            painter.drawRoundedRect(int(cx + 2), int(cy - 6), 4, 12, 1, 1)
        else:
            painter.drawPolygon(QPolygonF([QPointF(cx - 4, cy - 7), QPointF(cx - 4, cy + 7), QPointF(cx + 7, cy)]))
        painter.end()


class AlgorithmStepperCarousel(QFrame):
    """Stepper para navegar las transformaciones elementales del algoritmo."""

    #: Índice del paso visible (−1 sin pasos). Permite sincronizar diagramas externos.
    stepChanged = Signal(int)
    #: Índice y forma de llegar: ``forward``, ``short``, ``back``, ``jump`` o ``reset``.
    stepArrived = Signal(int, str)
    #: La reproducción empezó (``True``) o se detuvo (``False``).
    playbackChanged = Signal(bool)

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
        self._shown_step: Optional[CalculationStep] = None
        self._shown_alerts: Tuple[int, ...] = ()
        self._last_transition = ""
        self._gate = motion.BurstGate()
        self._autorepeat = False
        self._playing = False
        self._speed = 1.0
        self._play_timer = QTimer(self)
        self._play_timer.setSingleShot(True)
        self._play_timer.timeout.connect(self._play_tick)
        # El rótulo «Ir al paso» solo aparece si cabe: en columnas angostas
        # quedan el deslizador (con su nombre accesible) y la reproducción.
        self._caption_room = False
        self.setFocusPolicy(Qt.StrongFocus)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Fila de navegación: ‹ Anterior · posición · Siguiente ›. El interruptor
        # de fracciones y la exportación viven con el selector de paso, así el
        # carrusel cabe en columnas angostas sin recortar ningún botón.
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        self.prev_btn = QPushButton("‹  Anterior")
        self.prev_btn.setObjectName("stepNav")
        self.prev_btn.setToolTip("Paso anterior (←)")
        self.prev_btn.setAccessibleName("Paso anterior")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_step)
        nav_layout.addWidget(self.prev_btn)

        self.step_label = QLabel("Sin pasos")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setTextFormat(Qt.RichText)
        self.step_label.setStyleSheet(
            f"font-weight: 600; font-size: 17px; letter-spacing: 0.02em; color: {COLOR_TEXT_PRIMARY};"
        )
        nav_layout.addWidget(self.step_label, stretch=1)

        self.next_btn = QPushButton("Siguiente  ›")
        self.next_btn.setObjectName("stepNav")
        self.next_btn.setToolTip("Paso siguiente (→)")
        self.next_btn.setAccessibleName("Paso siguiente")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)

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
        self.step_slider.setMinimumWidth(60)
        self.step_slider.setToolTip("Arrastra para saltar a cualquier paso (Inicio/Fin: primero/último)")
        self.step_slider.setAccessibleName("Selector de paso del procedimiento")
        self.step_slider.valueChanged.connect(self._on_slider_moved)
        scrub_row.addWidget(self.step_slider, stretch=1)

        self.play_btn = _PlaybackButton()
        self.play_btn.clicked.connect(self.toggle_playback)
        scrub_row.addWidget(self.play_btn)
        self.speed_btn = QPushButton(speed_label(self._speed))
        self.speed_btn.setObjectName("secondaryAction")
        self.speed_btn.setFixedWidth(46)
        # Sin el relleno lateral del estilo secundario, «½×» cabe en 46 px.
        self.speed_btn.setStyleSheet("padding-left: 2px; padding-right: 2px;")
        self.speed_btn.setCursor(Qt.PointingHandCursor)
        self.speed_btn.setToolTip("Velocidad de la reproducción: 1×, 2× o ½×")
        self.speed_btn.setAccessibleName("Velocidad de la reproducción")
        self.speed_btn.clicked.connect(self.cycle_speed)
        scrub_row.addWidget(self.speed_btn)

        self.mode_btn = QPushButton("Fracciones")
        self.mode_btn.setObjectName("modeToggle")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.setToolTip("Interruptor: vista actual en fracciones o decimales")
        apply_widget_class(self.mode_btn, "modeToggle")
        scrub_row.addWidget(self.mode_btn)

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
        formula_box.setObjectName("stepFormulaBox")
        formula_box.setStyleSheet(f"""
            QFrame#stepFormulaBox {{
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
        heuristic_box.setObjectName("stepHeuristicBox")
        heuristic_box.setStyleSheet(f"""
            QFrame#stepHeuristicBox {{
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
        self.stop_playback()
        self._steps = steps
        self._current_index = 0
        self._shown_step = None
        self._gate.reset()
        self._update_view()

    def set_alert_mode(self, mode: str) -> None:
        self._alert_mode = mode
        self._update_view()

    def last_transition(self) -> str:
        """Cómo se llegó al paso visible (útil para pruebas y diagramas sincronizados)."""
        return self._last_transition

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
        """Salta al paso ``index`` (base 0), acotado al rango disponible.

        Un salto al paso siguiente cuenta como avanzar; cualquier otro salto
        solo funde lo que cambió.
        """
        self.stop_playback()
        self._go_to(index, jump_only=False)

    def _go_to(self, index: int, *, jump_only: bool) -> None:
        if not self._steps:
            return
        index = max(0, min(index, len(self._steps) - 1))
        if index == self._current_index:
            return
        if index == self._current_index + 1 and not jump_only:
            self._advance()
            return
        self._current_index = index
        self._gate.hit(motion.ms(motion.FAST))
        self._update_view(TRANSITION_JUMP)

    def first_alert_index(self) -> Optional[int]:
        """Primer paso con una fila nula crítica (singularidad o contradicción)."""
        for index, step in enumerate(self._steps):
            rows, _message, critical = zero_row_alerts(step, self._alert_mode)
            if rows and critical:
                return index
        return None

    def prev_step(self) -> None:
        self.stop_playback()
        if self._current_index > 0:
            self._current_index -= 1
            self._gate.hit(motion.ms(motion.FAST), autorepeat=self._autorepeat)
            self._update_view(TRANSITION_BACK)

    def next_step(self) -> None:
        self.stop_playback()
        self._advance()

    def _advance(self, *, from_playback: bool = False) -> bool:
        if self._current_index >= len(self._steps) - 1:
            return False
        self._current_index += 1
        burst = self._gate.hit(motion.ms(motion.SIGNATURE), autorepeat=self._autorepeat)
        self._update_view(TRANSITION_FORWARD if from_playback or not burst else TRANSITION_SHORT)
        return True

    # ------------------------------------------------------------------
    # Reproducción del procedimiento
    # ------------------------------------------------------------------

    def is_playing(self) -> bool:
        return self._playing

    def playback_speed(self) -> float:
        return self._speed

    def set_playback_speed(self, speed: float) -> None:
        if speed not in PLAYBACK_SPEEDS:
            return
        self._speed = speed
        self.speed_btn.setText(speed_label(speed))

    def cycle_speed(self) -> None:
        index = PLAYBACK_SPEEDS.index(self._speed) if self._speed in PLAYBACK_SPEEDS else 0
        self.set_playback_speed(PLAYBACK_SPEEDS[(index + 1) % len(PLAYBACK_SPEEDS)])

    def toggle_playback(self) -> None:
        if self._playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self) -> bool:
        """Recorre los pasos desde el actual (o desde el inicio si ya está al final)."""
        if len(self._steps) < 2:
            return False
        if self._current_index >= len(self._steps) - 1:
            self._current_index = 0
            self._update_view(TRANSITION_JUMP)
        self._playing = True
        self.play_btn.set_playing(True)
        self.playbackChanged.emit(True)
        self._play_timer.start(int(500 / self._speed))
        return True

    def stop_playback(self) -> None:
        self._play_timer.stop()
        if not self._playing:
            return
        self._playing = False
        self.play_btn.set_playing(False)
        self.playbackChanged.emit(False)

    def next_playback_delay(self) -> int:
        """Espera tras el paso visible: su coreografía más el tiempo de lectura."""
        step = self._steps[self._current_index] if self._steps else None
        reading = reading_time_ms(step.heuristic_text if step is not None else "")
        sequence = motion.ms(motion.SIGNATURE)
        return int(sequence + reading / self._speed)

    def _play_tick(self) -> None:
        if not self._playing:
            return
        if not self._advance(from_playback=True):
            self.stop_playback()
            return
        if self._current_index >= len(self._steps) - 1:
            self.stop_playback()
            return
        self._play_timer.start(self.next_playback_delay())

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_caption_room()

    def _update_caption_room(self) -> None:
        caption_w = self.jump_caption.sizeHint().width() + 10
        base = self.minimumSizeHint().width()
        if self.jump_caption.isVisible():
            base -= caption_w
        room = self.width() >= base + caption_w + (0 if self._caption_room else 24)
        if room != self._caption_room:
            self._caption_room = room
            self.jump_caption.setVisible(room and len(self._steps) > 2)

    def hideEvent(self, event) -> None:  # noqa: N802
        self.stop_playback()
        super().hideEvent(event)

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if not self._steps:
            super().keyPressEvent(event)
            return
        self._autorepeat = event.isAutoRepeat()
        try:
            if key in (Qt.Key_Right, Qt.Key_PageDown):
                self.next_step()
            elif key in (Qt.Key_Left, Qt.Key_PageUp):
                self.prev_step()
            elif key == Qt.Key_Home:
                self.stop_playback()
                self._go_to(0, jump_only=True)
            elif key == Qt.Key_End:
                self.stop_playback()
                self._go_to(len(self._steps) - 1, jump_only=True)
            elif key == Qt.Key_Space and event.modifiers() == Qt.NoModifier:
                if not event.isAutoRepeat():
                    self.toggle_playback()
            else:
                super().keyPressEvent(event)
                return
        finally:
            self._autorepeat = False
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
        # Diálogo de Qt (no el del sistema) para que se vea igual en Windows y
        # Linux; como instancia, para poder oscurecer su barra de título.
        from prettycalc.ui.platform_setup import apply_title_bar_theme
        from prettycalc.ui.theme import ACTIVE_THEME

        dialog = QFileDialog(
            self,
            "Guardar procedimiento",
            f"{safe.lower()}.pdf",
            "PDF (*.pdf);;Página web (*.html);;LaTeX (*.tex);;Texto (*.txt)",
        )
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        apply_title_bar_theme(dialog, dark=ACTIVE_THEME != "light")
        if not dialog.exec() or not dialog.selectedFiles():
            return None
        return self.save_steps(dialog.selectedFiles()[0])

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
        self.stop_playback()
        self._display_mode = "fraction" if checked else "decimal"
        self.mode_btn.setText("Fracciones" if checked else "Decimales")
        self._update_view()

    def _on_slider_moved(self, value: int) -> None:
        target = value - 1
        if target != self._current_index:
            self.stop_playback()
            # Arrastrar el deslizador es saltar: nunca dispara una secuencia por paso.
            self._go_to(target, jump_only=True)

    def _sync_slider(self) -> None:
        total = len(self._steps)
        self.scrub_host.setVisible(total > 0)
        self.jump_caption.setVisible(total > 2 and self._caption_room)
        self.step_slider.setVisible(total > 2)
        self.step_slider.blockSignals(True)
        self.step_slider.setMaximum(max(1, total))
        self.step_slider.setValue(self._current_index + 1)
        self.step_slider.setEnabled(total > 1)
        self.step_slider.blockSignals(False)
        self.play_btn.setVisible(total > 1)
        self.speed_btn.setVisible(total > 1)

    def _final_roles(self, step: CalculationStep, index: int) -> Tuple[Tuple[Tuple[int, int], ...], dict]:
        """Pivotes y papel de cada columna en la forma final de un sistema."""
        if self._alert_mode != ALERT_SYSTEM or index != len(self._steps) - 1 or step.split_col is None:
            return (), {}
        if not step_diff.is_echelon(step.matrix, step.split_col):
            return (), {}
        leads = step_diff.leading_entries(step.matrix, step.split_col)
        if not self._variable_headers:
            return leads, {}
        basic = {c for _r, c in leads}
        roles = {c: ("basic" if c in basic else "free") for c in range(step.split_col)}
        return leads, roles

    def _update_view(self, transition: str = "") -> None:
        self.export_btn.setEnabled(bool(self._steps))
        if not self._steps:
            self.step_label.setText(
                f"<span style='color:{COLOR_TEXT_MUTED}; font-weight:500; font-size:15px;'>Sin pasos</span>"
            )
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
            self._shown_step = None
            self._shown_alerts = ()
            self._last_transition = "reset"
            self.stepChanged.emit(-1)
            self.stepArrived.emit(-1, "reset")
            return

        total = len(self._steps)
        curr = self._current_index
        step = self._steps[curr]
        previous = self._shown_step
        previous_alerts = self._shown_alerts
        alert_was_visible = self.alert_label.isVisible()
        previous_alert_text = self.alert_label.text()

        position = f"{curr + 1}<span style='color:{COLOR_TEXT_MUTED}; font-weight:500;'> / {total}</span>"
        if curr == 0:
            position += f"<span style='color:{COLOR_TEXT_MUTED}; font-size:13px; font-weight:500;'>&nbsp;&nbsp;inicial</span>"
        elif curr == total - 1:
            position += f"<span style='color:{COLOR_TEXT_MUTED}; font-size:13px; font-weight:500;'>&nbsp;&nbsp;final</span>"
        self.step_label.setText(position)

        self.formula_label.setText(latex_to_book_html(step.latex_formula))
        self.heuristic_label.setText(prettify_step_text(step.heuristic_text))

        if step.pivot_pos is not None:
            pr, pc = step.pivot_pos
            col_var = variable_html(pc, sub_size_px=11) if step.split_col is None or pc < step.split_col else "b"
            self.pivot_badge.setTextFormat(Qt.RichText)
            self.pivot_badge.setText(f"Pivote: Fila {pr + 1}, Columna {pc + 1} ({col_var})")
        else:
            self.pivot_badge.setText("")

        alert_rows, alert_message, critical = zero_row_alerts(step, self._alert_mode)
        alert_color = COLOR_FEEDBACK_ERROR if critical else COLOR_ACCENT_WARNING
        if alert_message:
            self.alert_label.setStyleSheet(
                f"color: {alert_color}; font-size: 15px; font-weight: 600; padding: 4px 2px;"
            )
            self.alert_label.setText(alert_message)
            self.alert_label.setVisible(True)
        else:
            self.alert_label.setVisible(False)

        self.prev_btn.setEnabled(curr > 0)
        self.next_btn.setEnabled(curr < total - 1)
        self._sync_slider()

        leads, roles = self._final_roles(step, curr)
        contradictions = (
            step_diff.contradiction_rows(step.matrix, step.split_col) if self._alert_mode == ALERT_SYSTEM else ()
        )
        self.matrix_view.set_matrix(
            step.matrix,
            split_col=step.split_col,
            pivot=step.pivot_pos,
            mode=self._display_mode,
            actor_row=step.actor_row,
            affected_rows=step.affected_rows,
            animate=False,
            alert_rows=alert_rows,
            highlight_cells=step.highlight_cells,
            show_headers=self._variable_headers,
            header_roles=roles,
            contradiction_rows=contradictions,
        )
        self._shown_step = step
        self._shown_alerts = tuple(alert_rows)
        self._last_transition = transition or "reset"

        if transition and previous is not None and previous is not step:
            self.matrix_view.animate_from(
                previous.matrix,
                kind=transition,
                previous_pivot=previous.pivot_pos,
                previous_alert_rows=previous_alerts,
                alert_color=alert_color,
                base_matrix=self._steps[0].matrix,
                lead_cells=leads if transition == TRANSITION_FORWARD else (),
            )
            if transition != TRANSITION_SHORT:
                motion.fade_in(self.formula_label, motion.FAST)
                motion.fade_in(self.heuristic_label, motion.FAST)
                if alert_message and (not alert_was_visible or previous_alert_text != alert_message):
                    motion.fade_in(self.alert_label, motion.BASE)
        self.stepChanged.emit(curr)
        self.stepArrived.emit(curr, self._last_transition)
