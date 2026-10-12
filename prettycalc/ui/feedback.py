"""Retroalimentación transversal: avisos flotantes (toasts) y estado de carga.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10. Heurísticas de Nielsen #1 (visibilidad del estado) y #3 (control y
libertad): cada acción destructiva o masiva confirma lo que hizo y ofrece
deshacerla sin un diálogo modal que interrumpa el trabajo.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator, Optional

try:
    from PySide6.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QWidget,
        QGraphicsOpacityEffect,
    )
    from PySide6.QtCore import QEvent, QObject, QTimer, Qt
except ImportError:  # pragma: no cover - entorno sin Qt
    QFrame = object  # type: ignore
    QObject = object  # type: ignore

from prettycalc.ui.theme import repolish

_KINDS = ("info", "success", "warning", "error")
_ICONS = {"info": "i", "success": "✓", "warning": "!", "error": "✕"}


class Toast(QFrame):
    """Aviso no modal anclado al pie de la ventana, con acción opcional."""

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._host = host
        self._action: Optional[Callable[[], None]] = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(12)
        self.icon_label = QLabel("")
        self.icon_label.setObjectName("toastIcon")
        self.icon_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        layout.addWidget(self.icon_label)
        self.message_label = QLabel("")
        self.message_label.setObjectName("toastMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setTextFormat(Qt.PlainText)
        layout.addWidget(self.message_label, stretch=1)
        self.action_btn = QPushButton("")
        self.action_btn.setObjectName("toastAction")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.clicked.connect(self._run_action)
        self.action_btn.hide()
        layout.addWidget(self.action_btn)
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("toastClose")
        self.close_btn.setToolTip("Cerrar aviso (Esc)")
        self.close_btn.setFixedWidth(30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.dismiss)
        layout.addWidget(self.close_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)
        self.hide()
        host.installEventFilter(self)

    def show_message(
        self,
        message: str,
        *,
        kind: str = "info",
        action_text: Optional[str] = None,
        action: Optional[Callable[[], None]] = None,
        timeout_ms: int = 4500,
    ) -> None:
        kind = kind if kind in _KINDS else "info"
        self.setProperty("kind", kind)
        repolish(self)
        self.icon_label.setText(_ICONS[kind])
        self.message_label.setText(message)
        self._action = action
        if action_text and action is not None:
            self.action_btn.setText(action_text)
            self.action_btn.show()
        else:
            self.action_btn.hide()
        self._reposition()
        self.show()
        self.raise_()
        if timeout_ms > 0:
            self._timer.start(timeout_ms)
        else:
            self._timer.stop()

    def message(self) -> str:
        return self.message_label.text()

    def dismiss(self) -> None:
        self._timer.stop()
        self.hide()

    def _run_action(self) -> None:
        action = self._action
        self.dismiss()
        if action is not None:
            action()

    def _reposition(self) -> None:
        host = self._host
        width = min(640, max(320, host.width() - 80))
        self.setFixedWidth(width)
        self.adjustSize()
        x = (host.width() - width) // 2
        y = host.height() - self.height() - 24
        self.move(max(8, x), max(8, y))

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is self._host and event.type() == QEvent.Type.Resize and self.isVisible():
            self._reposition()
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self.dismiss()
            return
        super().keyPressEvent(event)


def _toast_host(widget: QWidget) -> QWidget:
    window = widget.window() if widget is not None else None
    return window if window is not None else widget


def toast_for(widget: QWidget) -> Toast:
    """Toast único de la ventana que contiene ``widget`` (lo crea si hace falta)."""
    host = _toast_host(widget)
    existing = getattr(host, "_prettycalc_toast", None)
    if existing is not None:
        try:
            existing.objectName()
            if existing.parent() is host:
                return existing
        except RuntimeError:
            pass
    toast = Toast(host)
    setattr(host, "_prettycalc_toast", toast)
    return toast


def show_toast(
    widget: QWidget,
    message: str,
    *,
    kind: str = "info",
    action_text: Optional[str] = None,
    action: Optional[Callable[[], None]] = None,
    timeout_ms: int = 4500,
) -> Toast:
    """Muestra un aviso no modal en la ventana de ``widget``."""
    toast = toast_for(widget)
    toast.show_message(
        message,
        kind=kind,
        action_text=action_text,
        action=action,
        timeout_ms=timeout_ms,
    )
    return toast


def last_toast_message(widget: QWidget) -> str:
    """Texto del último aviso de la ventana (útil para pruebas y accesibilidad)."""
    host = _toast_host(widget)
    toast = getattr(host, "_prettycalc_toast", None)
    if toast is None:
        return ""
    try:
        return toast.message()
    except RuntimeError:
        return ""


@contextmanager
def busy(button: Optional[QPushButton] = None, text: str = "Calculando…") -> Iterator[None]:
    """Estado de carga visible mientras corre un cálculo síncrono.

    Deshabilita el botón, cambia su rótulo y muestra el cursor de espera. Al
    terminar (o si hay excepción) restaura todo. Así la interfaz nunca parece
    congelada sin explicación en matrices grandes con fracciones densas.
    """
    app = QApplication.instance()
    previous_text = button.text() if button is not None else ""
    previous_enabled = button.isEnabled() if button is not None else True
    if button is not None:
        button.setEnabled(False)
        button.setText(text)
    if app is not None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        app.processEvents()
    try:
        yield
    finally:
        if app is not None:
            QApplication.restoreOverrideCursor()
        if button is not None:
            try:
                button.setText(previous_text)
                button.setEnabled(previous_enabled)
            except RuntimeError:
                pass
