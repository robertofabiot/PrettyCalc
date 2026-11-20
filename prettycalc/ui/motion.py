"""Sistema de movimiento de PrettyCalc: duraciones, curvas, interruptor y ayudantes.

Lo que ``theme.py`` es para el color, este módulo lo es para el movimiento.
Ningún módulo escribe duraciones ni curvas sueltas: todos importan estos
tokens y estos ayudantes.

Reglas que todos los ayudantes respetan:

- El estado de los widgets cambia de inmediato; la animación solo pinta la
  transición encima. Si una animación nunca corriera, la app se vería y se
  comportaría igual en su estado final.
- Ninguna animación bloquea la entrada ni se encola: un disparador nuevo lleva
  la anterior a su estado final y empieza la suya.
- Con «Reducir animaciones» no hay desplazamientos, vuelos ni escalonados:
  los ayudantes aplican el estado final al instante.
- Los efectos gráficos temporales se quitan al terminar, para que el render en
  reposo sea idéntico con y sin animaciones.
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import shiboken6
    from PySide6.QtCore import (
        QEasingCurve,
        QEvent,
        QObject,
        QPointF,
        QRect,
        QRectF,
        Qt,
        QTimer,
        QVariantAnimation,
        QAbstractAnimation,
    )
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import (
        QAbstractScrollArea,
        QApplication,
        QGraphicsOpacityEffect,
        QScrollArea,
        QWidget,
    )
except ImportError:  # pragma: no cover - entorno sin Qt
    QObject = object  # type: ignore
    QWidget = object  # type: ignore
    QVariantAnimation = object  # type: ignore


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

#: Hover, pistas, errores en línea y fundidos pequeños.
FAST = 120
#: Entrada de avisos, cambio de página, asentamiento de un badge.
BASE = 180
#: Intercambio simple, recorrido del pivote, desplazamiento suave.
SLOW = 260
#: Secuencias pedagógicas cortas (destello de la fila afectada).
EMPHASIS = 600
#: Coreografías de un paso o de un cálculo (solo con avance paso a paso,
#: acción explícita o reproducción; nunca en ráfaga).
SIGNATURE = 680
#: Retraso entre elementos de un revelado escalonado.
STAGGER = 50
#: Tope del escalonado completo: con muchos elementos el paso se acorta.
STAGGER_TOTAL = 300
#: Un ciclo de pulso repetido. 400 ms = 2.5 por segundo, bajo el límite
#: de 3 destellos por segundo (WCAG 2.3.1).
PULSE_CYCLE = 400

#: Curvas: entrar, salir, desplazarse y viajar.
CURVE_ENTER = "OutCubic"
CURVE_EXIT = "InCubic"
CURVE_MOVE = "InOutCubic"
CURVE_TRAVEL = "InOutCubic"
CURVE_LINEAR = "Linear"

_SETTINGS_KEY = "appearance/reduce_motion"


def curve(name: str) -> "QEasingCurve":
    """``QEasingCurve`` a partir del nombre de un token de curva."""
    return QEasingCurve(getattr(QEasingCurve.Type, name))


_CURVES: Dict[str, "QEasingCurve"] = {}


def ease(name: str, t: float) -> float:
    """Valor de la curva ``name`` en ``t`` ∈ [0, 1] (cacheado por nombre)."""
    t = 0.0 if t <= 0 else 1.0 if t >= 1 else t
    cached = _CURVES.get(name)
    if cached is None:
        cached = curve(name)
        _CURVES[name] = cached
    return float(cached.valueForProgress(t))


def local(t_ms: float, start_ms: float, dur_ms: float) -> float:
    """Progreso lineal de un tramo que empieza en ``start_ms`` y dura ``dur_ms``."""
    if dur_ms <= 0:
        return 1.0 if t_ms >= start_ms else 0.0
    return min(1.0, max(0.0, (t_ms - start_ms) / dur_ms))


def bell(t: float) -> float:
    """Pulso 0 → 1 → 0 (un solo ciclo)."""
    t = min(1.0, max(0.0, t))
    return math.sin(math.pi * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rect(a: "QRectF", b: "QRectF", t: float) -> "QRectF":
    return QRectF(
        lerp(a.x(), b.x(), t),
        lerp(a.y(), b.y(), t),
        lerp(a.width(), b.width(), t),
        lerp(a.height(), b.height(), t),
    )


def with_alpha(hex_color: str, alpha: float) -> "QColor":
    color = QColor(hex_color)
    color.setAlphaF(min(1.0, max(0.0, alpha)))
    return color


# ---------------------------------------------------------------------------
# Interruptor global y escala
# ---------------------------------------------------------------------------

_STATE: Dict[str, Optional[object]] = {"reduce": None, "scale": None}


def _env_flag(name: str) -> Optional[bool]:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return None
    return raw not in ("0", "false", "no", "off")


def system_prefers_reduced_motion(platform: Optional[str] = None) -> bool:
    """Preferencia del sistema operativo («mostrar animaciones» desactivado).

    Solo se consulta en Windows (``SPI_GETCLIENTAREAANIMATION``), que es una
    llamada barata. En cualquier otro sistema se devuelve ``False``.
    """
    platform = platform or sys.platform
    if not platform.startswith("win"):
        return False
    try:  # pragma: no cover - solo en Windows
        import ctypes

        enabled = ctypes.c_int(1)
        ok = ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0)
        return bool(ok) and not bool(enabled.value)
    except Exception:  # pragma: no cover - sin user32
        return False


def load_reduce_motion() -> bool:
    """«Reducir animaciones»: variable de entorno, luego lo guardado, luego el sistema.

    ``PRETTYCALC_REDUCE_MOTION=1`` fuerza la preferencia. Bajo pytest el valor
    por defecto es ``False`` (animaciones activas, pero deterministas: las
    pruebas llevan todo al final con :func:`finish_all`), salvo que la
    variable diga otra cosa.
    """
    env = _env_flag("PRETTYCALC_REDUCE_MOTION")
    if env is not None:
        return env
    if "pytest" in sys.modules:
        return False
    from prettycalc.ui.theme import _settings

    stored = stored_reduce_motion(_settings())
    if stored is not None:
        return stored
    return system_prefers_reduced_motion()


def stored_reduce_motion(settings) -> Optional[bool]:
    """Valor guardado en ``settings`` o ``None`` si el usuario nunca lo eligió."""
    if settings is None or not settings.contains(_SETTINGS_KEY):
        return None
    value = settings.value(_SETTINGS_KEY, False)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes")
    return bool(value)


def save_reduce_motion(flag: bool) -> bool:
    """Guarda la preferencia junto al tema (``appearance/reduce_motion``)."""
    from prettycalc.ui.theme import _settings

    settings = _settings()
    if settings is None:
        return False
    settings.setValue(_SETTINGS_KEY, bool(flag))
    settings.sync()
    return True


def reduce_motion() -> bool:
    """``True`` si el usuario pidió reducir animaciones. Se consulta al animar."""
    if _STATE["reduce"] is None:
        _STATE["reduce"] = load_reduce_motion()
    return bool(_STATE["reduce"])


def motion_enabled() -> bool:
    return not reduce_motion()


def set_reduce_motion(flag: bool, *, persist: bool = True) -> None:
    """Aplica la preferencia sin reiniciar. Al activarla, todo salta a su final."""
    _STATE["reduce"] = bool(flag)
    if persist:
        save_reduce_motion(flag)
    if flag:
        finish_all()


def motion_scale() -> float:
    """Factor de duración (``PRETTYCALC_MOTION_SCALE=4`` ralentiza todo para revisarlo)."""
    if _STATE["scale"] is None:
        raw = os.environ.get("PRETTYCALC_MOTION_SCALE", "").strip()
        try:
            value = float(raw) if raw else 1.0
        except ValueError:
            value = 1.0
        _STATE["scale"] = min(max(value, 0.1), 10.0)
    return float(_STATE["scale"])  # type: ignore[arg-type]


def reset_motion_state() -> None:
    """Olvida la preferencia y la escala en caché (útil en pruebas)."""
    _STATE["reduce"] = None
    _STATE["scale"] = None


def ms(base: float) -> int:
    """Duración efectiva de un token: 0 con movimiento reducido, escalada si no."""
    if reduce_motion():
        return 0
    return max(1, int(round(base * motion_scale())))


def stagger_step(count: int, step: int = STAGGER, total: int = STAGGER_TOTAL) -> int:
    """Retraso entre elementos para que ``count`` elementos no pasen de ``total``."""
    if count <= 1:
        return step
    return max(8, min(step, total // (count - 1)))


# ---------------------------------------------------------------------------
# Registro de animaciones en curso
# ---------------------------------------------------------------------------

_RUNNING: set = set()
_FINISHERS: List[Callable[[], None]] = []


def is_alive(obj: object) -> bool:
    """El objeto de C++ detrás de ``obj`` sigue existiendo."""
    if obj is None:
        return False
    try:
        return bool(shiboken6.isValid(obj))
    except Exception:
        return False


def _forget(anim: object) -> None:
    _RUNNING.discard(anim)


def track(anim: "QAbstractAnimation") -> "QAbstractAnimation":
    """Registra una animación para que :func:`finish_all` la alcance."""
    _RUNNING.add(anim)
    anim.finished.connect(lambda a=anim: _forget(a))
    anim.destroyed.connect(lambda _obj=None, a=anim: _forget(a))
    return anim


def finish(anim: Optional["QAbstractAnimation"]) -> None:
    """Lleva ``anim`` a su estado final al instante (emite ``finished``)."""
    if anim is None or not is_alive(anim):
        _forget(anim)
        return
    try:
        if anim.state() != QAbstractAnimation.State.Stopped:
            anim.setCurrentTime(anim.totalDuration())
            if anim.state() != QAbstractAnimation.State.Stopped:
                anim.stop()
    except RuntimeError:
        pass
    _forget(anim)


def register_finisher(callback: Callable[[], None]) -> None:
    """Rutina extra que :func:`finish_all` debe llamar (p. ej. temporizadores)."""
    if callback not in _FINISHERS:
        _FINISHERS.append(callback)


def finish_all() -> None:
    """Todas las animaciones saltan a su estado final. Las pruebas lo usan."""
    for _ in range(4):  # un final puede disparar otra transición corta
        pending = list(_RUNNING)
        if not pending:
            break
        for anim in pending:
            finish(anim)
    for callback in list(_FINISHERS):
        try:
            callback()
        except RuntimeError:
            pass


def running_count() -> int:
    alive = [a for a in list(_RUNNING) if is_alive(a)]
    for dead in set(_RUNNING) - set(alive):
        _RUNNING.discard(dead)
    return sum(1 for a in alive if a.state() == QAbstractAnimation.State.Running)


class Tween(QVariantAnimation):
    """Reloj lineal 0 → 1 que muere con su dueño.

    Los ayudantes aplican la curva de cada tramo a mano (``ease``), así una
    sola animación coordina una coreografía completa y no N animaciones.
    """

    def __init__(
        self,
        owner: "QObject",
        duration: int,
        on_value: Optional[Callable[[float], None]] = None,
        on_finish: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(owner)
        self._owner = owner
        self._on_value = on_value
        self._on_finish = on_finish
        self.setStartValue(0.0)
        self.setEndValue(1.0)
        self.setDuration(max(1, int(duration)))
        self.valueChanged.connect(self._value)
        self.finished.connect(self._done)

    def _value(self, value) -> None:
        if self._on_value is None or not is_alive(self._owner):
            return
        try:
            self._on_value(float(value))
        except RuntimeError:
            pass

    def _done(self) -> None:
        if self._on_finish is None or not is_alive(self._owner):
            return
        try:
            self._on_finish()
        except RuntimeError:
            pass


def run(
    owner: "QObject",
    duration: int,
    on_value: Optional[Callable[[float], None]] = None,
    on_finish: Optional[Callable[[], None]] = None,
) -> Optional[Tween]:
    """Arranca un :class:`Tween`. Con duración 0 aplica el final de inmediato."""
    if duration <= 0 or not is_alive(owner):
        if on_value is not None:
            on_value(1.0)
        if on_finish is not None:
            on_finish()
        return None
    tween = Tween(owner, duration, on_value, on_finish)
    track(tween)
    tween.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return tween


class BurstGate:
    """Detecta navegación en ráfaga: un disparador que llega con otro en curso.

    Mantener una flecha (autorrepetición) o pulsarla antes de que termine la
    secuencia anterior devuelve ``True``: la vista usa entonces la variante
    corta, para que navegar rápido se sienta tan ágil como sin animaciones.
    """

    def __init__(self) -> None:
        self._busy_until = 0.0

    def hit(self, duration_ms: int, *, autorepeat: bool = False) -> bool:
        now = time.monotonic()
        burst = autorepeat or now < self._busy_until
        self._busy_until = now + max(0, duration_ms) / 1000.0
        return burst

    def reset(self) -> None:
        self._busy_until = 0.0


# ---------------------------------------------------------------------------
# Fundidos con efecto temporal
# ---------------------------------------------------------------------------


def _effect_in_chain(widget: "QWidget") -> bool:
    """¿Este widget o algún ancestro tiene ya un efecto gráfico?"""
    node = widget
    while node is not None:
        if node.graphicsEffect() is not None:
            return True
        node = node.parentWidget()
    return False


def _has_effect_below(widget: "QWidget") -> bool:
    for child in widget.findChildren(QWidget):
        if child.graphicsEffect() is not None:
            return True
    return False


def fade_in(widget: Optional["QWidget"], duration: int = BASE, delay: int = 0) -> bool:
    """Fundido de entrada con un ``QGraphicsOpacityEffect`` que se quita al terminar.

    No hace nada si el widget no es visible, si se pidió reducir animaciones o
    si el widget, un ancestro o un descendiente ya tiene un efecto (Qt no
    admite efectos anidados).
    """
    if widget is None or not is_alive(widget) or not widget.isVisible():
        return False
    total = ms(duration)
    if total <= 0 or _effect_in_chain(widget) or _has_effect_below(widget):
        return False
    pause = ms(delay) if delay else 0
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    def step(t: float) -> None:
        if is_alive(effect):
            effect.setOpacity(ease(CURVE_ENTER, local(t * (pause + total), pause, total)))

    def done() -> None:
        if is_alive(widget) and widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)

    run(widget, pause + total, step, done)
    return True


def fade_in_sequence(widgets: Sequence[Optional["QWidget"]], duration: int = BASE, start: int = 0) -> int:
    """Revelado escalonado en orden de lectura. Devuelve cuántos se animaron."""
    live = [w for w in widgets if w is not None and is_alive(w) and w.isVisible()]
    step = stagger_step(len(live))
    count = 0
    for index, widget in enumerate(live):
        if fade_in(widget, duration, delay=start + index * step):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Desplazamiento suave
# ---------------------------------------------------------------------------


def _scroll_targets(area: "QScrollArea", child: "QWidget", xmargin: int, ymargin: int) -> Tuple[int, int]:
    """Mismo destino que ``QScrollArea.ensureWidgetVisible``."""
    content = area.widget()
    hbar = area.horizontalScrollBar()
    vbar = area.verticalScrollBar()
    h_value, v_value = hbar.value(), vbar.value()
    if content is None or child is None or not content.isAncestorOf(child):
        return h_value, v_value
    top_left = child.mapTo(content, child.rect().topLeft())
    focus = QRect(top_left, child.size())
    viewport = area.viewport()
    visible = QRect(-content.pos(), viewport.size())
    if visible.contains(focus):
        return h_value, v_value
    focus = focus.adjusted(-xmargin, -ymargin, xmargin, ymargin)
    if focus.width() > visible.width():
        h_value = focus.center().x() - viewport.width() // 2
    elif focus.right() > visible.right():
        h_value = focus.right() - viewport.width() + 1
    elif focus.left() < visible.left():
        h_value = focus.left()
    if focus.height() > visible.height():
        v_value = focus.center().y() - viewport.height() // 2
    elif focus.bottom() > visible.bottom():
        v_value = focus.bottom() - viewport.height() + 1
    elif focus.top() < visible.top():
        v_value = focus.top()
    h_value = max(hbar.minimum(), min(hbar.maximum(), h_value))
    v_value = max(vbar.minimum(), min(vbar.maximum(), v_value))
    return h_value, v_value


class _ScrollStopper(QObject):
    """La rueda o un clic del usuario detienen el desplazamiento en curso."""

    def __init__(self, area: "QAbstractScrollArea") -> None:
        super().__init__(area)
        self.tween: Optional[Tween] = None
        area.viewport().installEventFilter(self)
        for bar in (area.verticalScrollBar(), area.horizontalScrollBar()):
            bar.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() in (QEvent.Type.Wheel, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            tween = self.tween
            self.tween = None
            if tween is not None and is_alive(tween):
                tween.stop()
                _forget(tween)
        return False


def scroll_to(area: Optional["QAbstractScrollArea"], h_value: Optional[int] = None, v_value: Optional[int] = None) -> None:
    """Lleva las barras a ``h_value``/``v_value``; animado salvo movimiento reducido."""
    if area is None or not is_alive(area):
        return
    hbar, vbar = area.horizontalScrollBar(), area.verticalScrollBar()
    h_to = hbar.value() if h_value is None else h_value
    v_to = vbar.value() if v_value is None else v_value
    stopper = getattr(area, "_prettycalc_scroll_stopper", None)
    if stopper is None or not is_alive(stopper):
        stopper = _ScrollStopper(area)
        setattr(area, "_prettycalc_scroll_stopper", stopper)
    if stopper.tween is not None:
        finish(stopper.tween)
        stopper.tween = None
    h_from, v_from = hbar.value(), vbar.value()
    duration = ms(SLOW)
    distance = max(abs(h_to - h_from), abs(v_to - v_from))
    if duration <= 0 or distance <= 2:
        hbar.setValue(h_to)
        vbar.setValue(v_to)
        return

    def step(t: float) -> None:
        k = ease(CURVE_MOVE, t)
        hbar.setValue(int(round(lerp(h_from, h_to, k))))
        vbar.setValue(int(round(lerp(v_from, v_to, k))))

    def done() -> None:
        hbar.setValue(h_to)
        vbar.setValue(v_to)
        stopper.tween = None

    stopper.tween = run(area, duration, step, done)


def scroll_to_widget(
    area: Optional["QScrollArea"], child: Optional["QWidget"], xmargin: int = 50, ymargin: int = 50
) -> None:
    """Como ``ensureWidgetVisible``, pero la vista se desliza hasta el destino."""
    if area is None or child is None or not is_alive(area) or not is_alive(child):
        return
    h_value, v_value = _scroll_targets(area, child, xmargin, ymargin)
    scroll_to(area, h_value, v_value)


# ---------------------------------------------------------------------------
# Visibilidad en pantalla
# ---------------------------------------------------------------------------


def window_rect(widget: "QWidget", rect: Optional["QRect"] = None) -> "QRectF":
    """Rectángulo de ``widget`` (o de ``rect`` dentro de él) en coordenadas de ventana."""
    window = widget.window()
    rect = QRect(rect) if rect is not None else widget.rect()
    top_left = widget.mapTo(window, rect.topLeft())
    return QRectF(top_left.x(), top_left.y(), rect.width(), rect.height())


def on_screen(widget: Optional["QWidget"], rect: Optional["QRect"] = None, tolerance: int = 2) -> bool:
    """El widget (o una zona suya) se ve entero: no queda fuera de ningún viewport."""
    if widget is None or not is_alive(widget) or not widget.isVisible():
        return False
    target = QRect(rect) if rect is not None else widget.rect()
    if target.isEmpty():
        return False
    node = widget.parentWidget()
    while node is not None:
        if isinstance(node.parentWidget(), QAbstractScrollArea) and node is node.parentWidget().viewport():
            viewport = node
            top_left = widget.mapTo(viewport, target.topLeft())
            mapped = QRect(top_left, target.size())
            if not viewport.rect().adjusted(-tolerance, -tolerance, tolerance, tolerance).contains(mapped):
                return False
        node = node.parentWidget()
    window = widget.window()
    top_left = widget.mapTo(window, target.topLeft())
    return window.rect().adjusted(-tolerance, -tolerance, tolerance, tolerance).contains(QRect(top_left, target.size()))


def scroll_areas_of(widget: "QWidget") -> List["QAbstractScrollArea"]:
    areas = []
    node = widget.parentWidget() if widget is not None else None
    while node is not None:
        if isinstance(node, QAbstractScrollArea):
            areas.append(node)
        node = node.parentWidget()
    return areas


# ---------------------------------------------------------------------------
# Capa de coreografía de la ventana
# ---------------------------------------------------------------------------


@dataclass
class Flight:
    """Un objeto que viaja de ``src`` a ``dst`` (coordenadas de ventana)."""

    pixmap: "QPixmap"
    src: "QRectF"
    dst: "QRectF"
    start: float
    duration: float
    arc: float = 0.0
    fade_in: float = 0.12
    fade_out: float = 0.0
    opacity: float = 1.0
    curve: str = CURVE_TRAVEL


@dataclass
class Mark:
    """Anillo o tinte pintado encima de un widget (sin tocar su estilo)."""

    rect: "QRectF"
    color: str
    start: float
    duration: float
    fill: float = 0.0
    ring: float = 0.0
    radius: float = 6.0
    pulses: int = 1
    width: float = 2.0


@dataclass
class Sprite:
    """Instantánea fija que se desvanece (o aparece y se asienta) sobre su lugar.

    Con ``source`` y sin ``pixmap``, la instantánea se toma cuando empieza su
    tramo: así refleja la geometría final aunque el layout termine de
    asentarse después de programarla.
    """

    pixmap: Optional["QPixmap"]
    rect: "QRectF"
    start: float
    duration: float
    fade: str = "out"  # "out": 1 → 0;  "in": 0 → 1 con desplazamiento dy → 0
    dy: float = 0.0
    cover: Optional[str] = None
    source: Optional["QWidget"] = None


@dataclass
class Cover:
    """Tapa una zona con un color hasta ``until`` (el destino ya tiene el valor final).

    Con ``source``, la zona sigue al widget mientras espera.
    """

    rect: "QRectF"
    color: str
    until: float
    radius: float = 0.0
    source: Optional["QWidget"] = None


class ChoreographyLayer(QWidget):
    """Una sola capa por ventana para todo lo que viaja entre widgets distintos.

    Transparente al ratón y oculta mientras no hay nada en vuelo. Pinta en un
    único ``paintEvent`` todos los objetos (pixmaps cacheados al empezar), así
    que nunca hay un widget por objeto. Se cancela (todo salta al final) ante
    un redimensionamiento, un desplazamiento de las áreas que contienen el
    origen o el destino y un cambio de módulo.
    """

    def __init__(self, window: "QWidget") -> None:
        super().__init__(window)
        self.setObjectName("choreographyLayer")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._window = window
        self._flights: List[Flight] = []
        self._marks: List[Mark] = []
        self._sprites: List[Sprite] = []
        self._covers: List[Cover] = []
        self._total = 0.0
        self._now = 0.0
        self._base = 0.0
        self._started: set = set()
        self._tween: Optional[Tween] = None
        self._watched_bars: List[object] = []
        self._on_done: List[Callable[[], None]] = []
        self.hide()
        window.installEventFilter(self)

    # -- construcción ----------------------------------------------------

    @staticmethod
    def for_widget(widget: Optional["QWidget"]) -> Optional["ChoreographyLayer"]:
        if widget is None or not is_alive(widget):
            return None
        window = widget.window()
        if window is None:
            return None
        layer = getattr(window, "_prettycalc_choreography", None)
        if layer is not None and is_alive(layer) and layer.parent() is window:
            return layer
        layer = ChoreographyLayer(window)
        setattr(window, "_prettycalc_choreography", layer)
        return layer

    def is_active(self) -> bool:
        return self._tween is not None and is_alive(self._tween)

    def add_flight(self, flight: Flight) -> None:
        self._flights.append(flight)

    def add_mark(self, mark: Mark) -> None:
        self._marks.append(mark)

    def add_sprite(self, sprite: Sprite) -> None:
        self._sprites.append(sprite)

    def add_cover(self, cover: Cover) -> None:
        self._covers.append(cover)

    def watch(self, widgets: Iterable[Optional["QWidget"]]) -> None:
        """Un desplazamiento de cualquier área que contenga estos widgets cancela."""
        for widget in widgets:
            if widget is None or not is_alive(widget):
                continue
            for area in scroll_areas_of(widget):
                for bar in (area.verticalScrollBar(), area.horizontalScrollBar()):
                    if bar not in self._watched_bars:
                        bar.valueChanged.connect(self._on_scrolled)
                        self._watched_bars.append(bar)

    def on_done(self, callback: Callable[[], None]) -> None:
        self._on_done.append(callback)

    def _items(self) -> list:
        return [*self._flights, *self._marks, *self._sprites, *self._covers]

    def play(self) -> bool:
        """Arranca lo agregado desde el último ``play``. Devuelve si hay algo en vuelo.

        Si ya hay objetos en vuelo, lo nuevo se suma a partir del instante
        actual sin reiniciar lo anterior (nunca se encola).
        """
        items = self._items()
        fresh = [item for item in items if id(item) not in self._started]
        if self.is_active():
            offset = self._now
            for item in fresh:
                if isinstance(item, Cover):
                    item.until += offset
                else:
                    item.start += offset
        for item in fresh:
            self._started.add(id(item))
        ends = [f.start + f.duration for f in self._flights]
        ends += [m.start + m.duration for m in self._marks]
        ends += [s.start + s.duration for s in self._sprites]
        ends += [c.until for c in self._covers]
        total = max(ends) if ends else 0.0
        if total <= self._now:
            if not self.is_active():
                self.finish()
            return self.is_active()
        base = self._now if self.is_active() else 0.0
        if self._tween is not None and is_alive(self._tween):
            old = self._tween
            self._tween = None
            try:
                old.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            old.stop()
            _forget(old)
        self._base = base
        self._total = total
        self._now = base
        self.setGeometry(self._window.rect())
        self.show()
        self.raise_()
        self._tween = run(self, int(max(1.0, total - base)), self._step, self._finished)
        return True

    def _clear_items(self) -> None:
        self._flights = []
        self._marks = []
        self._sprites = []
        self._covers = []
        self._started = set()
        self._now = 0.0
        self._base = 0.0

    def finish(self) -> None:
        """Todo salta al estado final: la capa se vacía y se oculta."""
        tween = self._tween
        self._tween = None
        if tween is not None and is_alive(tween):
            try:
                tween.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            tween.stop()
        _forget(tween)
        self._finished()

    def _finished(self) -> None:
        self._tween = None
        self._clear_items()
        for bar in self._watched_bars:
            try:
                bar.valueChanged.disconnect(self._on_scrolled)
            except (RuntimeError, TypeError):
                pass
        self._watched_bars = []
        callbacks, self._on_done = self._on_done, []
        if is_alive(self):
            self.hide()
        for callback in callbacks:
            try:
                callback()
            except RuntimeError:
                pass

    def _on_scrolled(self, _value: int = 0) -> None:
        if self.is_active():
            self.finish()

    def _step(self, t: float) -> None:
        self._now = self._base + t * (self._total - self._base)
        for cover in self._covers:
            if cover.source is not None and is_alive(cover.source) and self._now < cover.until:
                cover.rect = window_rect(cover.source).adjusted(-1, -1, 1, 1)
        for sprite in self._sprites:
            if sprite.pixmap is None and self._now >= sprite.start:
                source = sprite.source
                if source is None or not is_alive(source) or not source.isVisible():
                    sprite.duration = 0.0
                    continue
                sprite.rect = window_rect(source)
                sprite.pixmap = source.grab()
        self.update()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self._window and event.type() == QEvent.Type.Resize:
            if self.is_active():
                self.finish()
            elif self.isVisible():
                self.setGeometry(self._window.rect())
        return False

    # -- pintado ---------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        now = self._now
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        for cover in self._covers:
            if now < cover.until:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(cover.color))
                painter.drawRoundedRect(cover.rect, cover.radius, cover.radius)

        for sprite in self._sprites:
            if sprite.pixmap is None:
                continue
            t = local(now, sprite.start, sprite.duration)
            if sprite.fade == "out":
                if t >= 1.0:
                    continue
                alpha = 1.0 - ease(CURVE_EXIT, t) if now >= sprite.start else 1.0
                offset = 0.0
            else:
                if t >= 1.0:
                    continue
                k = ease(CURVE_ENTER, t)
                alpha = k
                offset = sprite.dy * (1.0 - k)
                if sprite.cover:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(sprite.cover))
                    painter.drawRect(sprite.rect.adjusted(-1, -1, 1, 1))
            painter.setOpacity(alpha)
            target = QRectF(sprite.rect).translated(0, offset)
            painter.drawPixmap(target, sprite.pixmap, QRectF(sprite.pixmap.rect()))
            painter.setOpacity(1.0)

        for mark in self._marks:
            t = local(now, mark.start, mark.duration)
            if t <= 0.0 or t >= 1.0:
                continue
            pulses = max(1, mark.pulses)
            phase = (t * pulses) % 1.0
            strength = bell(phase)
            painter.setBrush(Qt.NoBrush)
            if mark.fill > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(with_alpha(mark.color, mark.fill * strength))
                painter.drawRoundedRect(mark.rect, mark.radius, mark.radius)
            if mark.ring > 0:
                pen = QPen(with_alpha(mark.color, mark.ring * strength), mark.width)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(mark.rect, mark.radius, mark.radius)

        for flight in self._flights:
            t = local(now, flight.start, flight.duration)
            if now < flight.start or t >= 1.0:
                continue
            k = ease(flight.curve, t)
            rect = lerp_rect(flight.src, flight.dst, k)
            if flight.arc:
                dx = flight.dst.center().x() - flight.src.center().x()
                dy = flight.dst.center().y() - flight.src.center().y()
                length = math.hypot(dx, dy) or 1.0
                bump = flight.arc * bell(k)
                rect.translate(-dy / length * bump, dx / length * bump)
            alpha = flight.opacity
            if flight.fade_in > 0:
                alpha *= min(1.0, t / flight.fade_in)
            if flight.fade_out > 0 and t > 1.0 - flight.fade_out:
                alpha *= max(0.0, (1.0 - t) / flight.fade_out)
            painter.setOpacity(alpha)
            pix = flight.pixmap
            ratio = pix.devicePixelRatio() or 1.0
            w, h = pix.width() / ratio, pix.height() / ratio
            center = rect.center()
            painter.drawPixmap(QPointF(center.x() - w / 2, center.y() - h / 2), pix)
            painter.setOpacity(1.0)
        painter.end()


def layer_for(widget: Optional["QWidget"]) -> Optional[ChoreographyLayer]:
    return ChoreographyLayer.for_widget(widget)


def finish_layer(widget: Optional["QWidget"]) -> None:
    """Termina al instante lo que vuela en la ventana de ``widget``."""
    if widget is None or not is_alive(widget):
        return
    layer = getattr(widget.window(), "_prettycalc_choreography", None)
    if layer is not None and is_alive(layer):
        layer.finish()


def grab_pixmap(widget: "QWidget", rect: Optional["QRect"] = None) -> "QPixmap":
    return widget.grab(rect) if rect is not None else widget.grab()


def text_pixmap(
    text: str,
    color: str,
    font,
    size: Tuple[int, int],
    painter_fn: Optional[Callable[["QPainter", "QRect"], None]] = None,
    device_ratio: float = 1.0,
) -> "QPixmap":
    """Pinta una sola vez un texto (o lo que dibuje ``painter_fn``) en un pixmap."""
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    pix = QPixmap(int(w * device_ratio), int(h * device_ratio))
    pix.setDevicePixelRatio(device_ratio)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    rect = QRect(0, 0, w, h)
    if painter_fn is not None:
        painter_fn(painter, rect)
    else:
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(rect, Qt.AlignCenter, text)
    painter.end()
    return pix


def device_ratio(widget: Optional["QWidget"]) -> float:
    try:
        return float(widget.devicePixelRatioF()) if widget is not None else 1.0
    except (AttributeError, RuntimeError):
        return 1.0


def crossfade_out(widget: Optional["QWidget"], duration: int = FAST) -> bool:
    """Instantánea del aspecto actual que se desvanece mientras debajo ya cambió.

    Se llama *antes* de cambiar el widget: el estado cambia al instante y el
    aspecto anterior se retira encima, sin tocar el layout.
    """
    if widget is None or not is_alive(widget) or not widget.isVisible():
        return False
    total = ms(duration)
    if total <= 0:
        return False
    layer = layer_for(widget)
    if layer is None:
        return False
    rect = window_rect(widget)
    if rect.isEmpty():
        return False
    layer.add_sprite(Sprite(widget.grab(), rect, 0.0, float(total), fade="out"))
    layer.watch([widget])
    return layer.play()


def settle(widget: Optional["QWidget"], cover: str, *, dy: float = 6.0, duration: int = BASE, delay: int = 0) -> bool:
    """El widget se asienta: aparece con un fundido y un desplazamiento mínimo.

    ``cover`` es el color de la superficie de debajo, que tapa el widget real
    mientras su instantánea entra (el widget ya tiene su aspecto final).
    """
    if widget is None or not is_alive(widget) or not widget.isVisible():
        return False
    total = ms(duration)
    if total <= 0:
        return False
    layer = layer_for(widget)
    if layer is None:
        return False
    rect = window_rect(widget)
    if rect.isEmpty():
        return False
    start = float(ms(delay)) if delay else 0.0
    layer.add_cover(Cover(rect.adjusted(-1, -1, 1, 1), cover, start + 1.0, source=widget))
    layer.add_sprite(Sprite(None, rect, start, float(total), fade="in", dy=dy, cover=cover, source=widget))
    layer.watch([widget])
    return layer.play()


def pulse(
    widget: Optional["QWidget"],
    color: str,
    *,
    fill: float = 0.16,
    ring: float = 0.0,
    duration: int = EMPHASIS,
    delay: int = 0,
    pulses: int = 1,
    rect: Optional["QRect"] = None,
    radius: float = 6.0,
    margin: int = 0,
) -> bool:
    """Pulso pintado encima del widget (o de ``rect`` dentro de él), sin tocar su QSS."""
    if widget is None or not is_alive(widget) or not widget.isVisible():
        return False
    total = ms(duration)
    if total <= 0:
        return False
    layer = layer_for(widget)
    if layer is None:
        return False
    area = window_rect(widget, rect).adjusted(-margin, -margin, margin, margin)
    layer.add_mark(
        Mark(area, color, float(ms(delay)) if delay else 0.0, float(total), fill=fill, ring=ring, radius=radius, pulses=pulses)
    )
    layer.watch([widget])
    return layer.play()


def defer(owner: "QObject", callback: Callable[[], None], delay: int = 0) -> None:
    """Corre ``callback`` cuando el layout ya se asentó (o tras ``delay`` ms)."""

    def safe() -> None:
        if is_alive(owner):
            try:
                callback()
            except RuntimeError:
                pass

    QTimer.singleShot(delay, owner, safe)


# ---------------------------------------------------------------------------
# Revelado del veredicto tras una acción explícita
# ---------------------------------------------------------------------------


def _resolve(owner: object, path: str):
    node = owner
    for part in path.split("."):
        node = getattr(node, part, None)
        if node is None:
            return None
    return node


def verdict_signature(badge) -> Optional[Tuple[str, str]]:
    if badge is None or not is_alive(badge):
        return None
    return (badge.text(), badge.styleSheet())


def reveal_verdict(
    badge,
    before: Optional[Tuple[str, str]],
    *,
    sections: Sequence["QWidget"] = (),
    cover: Optional[str] = None,
    delay: int = 0,
) -> None:
    """El badge se asienta y las secciones entran; si nada cambió, el badge pulsa.

    Sin pulso, recalcular lo mismo parecería no haber hecho nada (Nielsen #1).
    """
    if badge is None or not is_alive(badge) or not motion_enabled():
        return
    from prettycalc.ui.theme import COLOR_SURFACE_ELEVATED, COLOR_TEXT_PRIMARY

    same = before is not None and before == verdict_signature(badge)
    live = [w for w in sections if w is not None and is_alive(w)]

    def play() -> None:
        if not badge.isVisible():
            return
        host = badge.parentWidget()
        if host is not None and host.layout() is not None:
            host.layout().activate()  # geometría final antes de la instantánea
        if same:
            pulse(badge, COLOR_TEXT_PRIMARY, fill=0.22, duration=EMPHASIS, delay=delay, radius=4)
            return
        settle(badge, cover or COLOR_SURFACE_ELEVATED, delay=delay)
        fade_in_sequence(live, BASE, start=delay + BASE)

    defer(badge, play)


def reveals(badge_path: str, sections_path: Optional[str] = None):
    """Decora una acción explícita (Calcular, Resolver…) para revelar su veredicto.

    ``badge_path`` y ``sections_path`` son atributos (con puntos) de la vista:
    el badge del veredicto y, opcionalmente, el layout cuyas filas entran
    escalonadas (una marca ✓ / ✗ por widget).
    """
    import functools
    import inspect

    def decorate(fn):
        try:
            params = [
                p for p in inspect.signature(fn).parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
            positional = max(0, len(params) - 1)
        except (TypeError, ValueError):
            positional = 0

        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            before = verdict_signature(_resolve(self, badge_path))
            # Las señales de Qt pueden pasar argumentos (``checked``) que la acción no usa.
            result = fn(self, *args[:positional], **kwargs)
            sections: List["QWidget"] = []
            layout = _resolve(self, sections_path) if sections_path else None
            if layout is not None:
                for index in range(layout.count()):
                    widget = layout.itemAt(index).widget()
                    if widget is not None:
                        sections.append(widget)
            reveal_verdict(_resolve(self, badge_path), before, sections=sections)
            return result

        return wrapper

    return decorate


# ---------------------------------------------------------------------------
# Paneles que aparecen y páginas que cambian
# ---------------------------------------------------------------------------


class _RevealOnShow(QObject):
    """Un panel que se muestra (``setVisible(True)``) entra con un fundido.

    Solo reacciona a ``ShowToParent``: el panel mismo pasó de oculto a
    visible. Mostrar la ventana o cambiar de módulo no lo dispara. El
    layout ya es el final; al ocultarse, el panel desaparece sin más.
    """

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.ShowToParent and isinstance(watched, QWidget):
            window = watched.window()
            if window is not None and window.isVisible():
                defer(watched, lambda w=watched: fade_in(w, BASE))
        return False


_REVEAL_FILTER: Dict[str, object] = {}


def fade_when_shown(*widgets: Optional["QWidget"]) -> None:
    """Registra paneles que entran con un fundido cada vez que aparecen."""
    app = QApplication.instance()
    if app is None:
        return
    reveal = _REVEAL_FILTER.get("filter")
    if reveal is None or not is_alive(reveal):
        reveal = _RevealOnShow(app)
        _REVEAL_FILTER["filter"] = reveal
    for widget in widgets:
        if widget is not None and is_alive(widget):
            widget.installEventFilter(reveal)


def fade_page_changes(tabs) -> None:
    """Al cambiar de pestaña, el contenido nuevo entra con un fundido corto."""

    def changed(_index: int) -> None:
        page = tabs.currentWidget()
        if page is not None:
            defer(page, lambda: fade_in(page, FAST))

    tabs.currentChanged.connect(changed)
