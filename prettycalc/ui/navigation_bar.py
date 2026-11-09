"""Navegación lateral entre los módulos de PrettyCalc.

Con ocho módulos, la barra segmentada superior recortaba los rótulos
(«eterminant», «Ecuacione»). La barra lateral muestra cada módulo con su
marca tipográfica y su nombre completo; en ventanas de portátil se pliega a
un riel con la marca y el rótulo corto debajo (el nombre completo queda en
el tooltip), para dejarle el ancho al contenido.

Los elementos se dibujan con ``QPainter`` y los tokens del tema: así la
marca (en Fira Code) y el nombre (en Inter) conviven en un mismo botón y se
ven idénticos en Windows y en Linux.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

try:
    from PySide6.QtWidgets import (
        QButtonGroup,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import QRectF, QSize, Qt, Signal
    from PySide6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPen, QPixmap
    from PySide6.QtSvg import QSvgRenderer
except ImportError:
    QWidget = object  # type: ignore
    QPushButton = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.ui.theme import (
    COLOR_BG_BASE,
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
    ui_font,
)


# Marcas tipográficas (no emojis): los emojis se dibujan con Segoe UI Emoji en
# Windows y con Noto Color Emoji en Linux, y se veían distintos en cada sistema.
MODULE_TABS: Sequence[Tuple[str, str]] = (
    ("[A|b]", "Sistemas Lineales"),
    ("A·B", "Álgebra Matricial"),
    ("ℝⁿ", "Vectores en ℝⁿ"),
    ("Ax", "Ecuaciones Matriciales"),
    ("det", "Determinantes"),
    ("LU", "Factorización LU"),
    ("T(v)", "Transformaciones Lineales"),
    ("EV", "Espacios Vectoriales"),
)


#: Rótulos cortos: se muestran debajo de la marca en el riel plegado.
SHORT_LABELS: Sequence[str] = ("Sistemas", "Matrices", "Vectores", "Ecuaciones", "Determinantes", "LU", "Transform.", "Espacios")

#: Ancho de la barra desplegada y del riel plegado (px).
EXPANDED_WIDTH = 276
COMPACT_WIDTH = 96

_ITEM_HEIGHT = 40
_RAIL_ITEM_HEIGHT = 54
_RAIL_LABEL_PX = 11
_CHIP_W = 40
_CHIP_H = 24
_PAD_X = 10
_GAP = 12
_LABEL_PX = 14
_CHIP_PX = 12


class NavItem(QPushButton):
    """Elemento de la barra lateral: marca en una pastilla + nombre del módulo.

    ``text()`` devuelve el nombre completo (lo usan los lectores de pantalla y
    las pruebas); el dibujo lo hace ``paintEvent`` para combinar dos fuentes.
    """

    def __init__(
        self,
        glyph: str,
        label: str,
        short_label: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(label, parent)
        self.glyph = glyph
        self.short_label = short_label or label
        self._compact = False
        self._hovered = False
        self._keyboard_focus = False
        self.setObjectName("navItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setFixedHeight(_ITEM_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_Hover, True)
        self.setFont(ui_font(_LABEL_PX, weight=500))

    # -- geometría -------------------------------------------------------
    def label_rect(self) -> "QRectF":
        """Zona del nombre: lo que queda a la derecha de la marca."""
        left = _PAD_X + _CHIP_W + _GAP
        return QRectF(left, 0, max(0, self.width() - left - _PAD_X), self.height())

    def visible_label(self) -> str:
        """Rótulo que se dibuja: el nombre completo o, en el riel, el corto."""
        return self.short_label if self._compact else self.text()

    def label_fits(self) -> bool:
        """``True`` si el rótulo visible entra completo (sin elipsis)."""
        if self._compact:
            metrics = QFontMetrics(ui_font(_RAIL_LABEL_PX, weight=500))
            return metrics.horizontalAdvance(self.short_label) <= self.width() - 6
        metrics = QFontMetrics(self.font())
        return metrics.horizontalAdvance(self.text()) <= self.label_rect().width()

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        self.setFixedHeight(_RAIL_ITEM_HEIGHT if compact else _ITEM_HEIGHT)
        self.update()

    def sizeHint(self) -> "QSize":  # noqa: N802
        if self._compact:
            return QSize(COMPACT_WIDTH - 10, _RAIL_ITEM_HEIGHT)
        metrics = QFontMetrics(self.font())
        width = _PAD_X * 2 + _CHIP_W + _GAP + metrics.horizontalAdvance(self.text())
        return QSize(width, _ITEM_HEIGHT)

    def minimumSizeHint(self) -> "QSize":  # noqa: N802
        return QSize(_CHIP_W + 2 * _PAD_X, _ITEM_HEIGHT)

    # -- estados ---------------------------------------------------------
    def enterEvent(self, event) -> None:  # noqa: N802
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802
        # El anillo solo aparece al llegar con el teclado, no con el foco
        # inicial de la ventana ni con un clic.
        self._keyboard_focus = event.reason() in (Qt.TabFocusReason, Qt.BacktabFocusReason)
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        self._keyboard_focus = False
        super().focusOutEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        active = self.isChecked()

        if active:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(rgba_to_qcolor(COLOR_INTERACTIVE_IDLE, 0.16)))
            painter.drawRoundedRect(rect, 8, 8)
            # Pastilla de acento a la izquierda: dónde estoy, de un vistazo.
            if not self._compact:
                painter.setBrush(QColor(COLOR_INTERACTIVE_IDLE))
                painter.drawRoundedRect(QRectF(0, 10, 3, self.height() - 20), 1.5, 1.5)
        elif self._hovered or self.isDown():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(rgba_to_qcolor(COLOR_TEXT_PRIMARY, 0.06)))
            painter.drawRoundedRect(rect, 8, 8)

        if self.hasFocus() and self._keyboard_focus:
            painter.setPen(QPen(QColor(COLOR_TEXT_PRIMARY), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 7, 7)

        if self._compact:
            chip = QRectF((self.width() - _CHIP_W) / 2, 7, _CHIP_W, _CHIP_H)
        else:
            chip = QRectF(_PAD_X, (self.height() - _CHIP_H) / 2, _CHIP_W, _CHIP_H)
        painter.setPen(Qt.NoPen)
        if active:
            painter.setBrush(QColor(COLOR_INTERACTIVE_IDLE))
        else:
            painter.setBrush(QColor(rgba_to_qcolor(COLOR_INTERACTIVE_IDLE, 0.12)))
        painter.drawRoundedRect(chip, 6, 6)
        painter.setFont(ui_font(_CHIP_PX, mono=True, weight=600))
        painter.setPen(QColor(COLOR_BG_BASE if active else COLOR_INTERACTIVE_IDLE))
        painter.drawText(chip, Qt.AlignCenter, self.glyph)

        painter.setPen(QColor(COLOR_TEXT_PRIMARY if (active or self._hovered) else COLOR_TEXT_MUTED))
        if self._compact:
            font = ui_font(_RAIL_LABEL_PX, weight=600 if active else 500)
            painter.setFont(font)
            area = QRectF(2, chip.bottom() + 3, self.width() - 4, self.height() - chip.bottom() - 6)
            text = QFontMetrics(font).elidedText(self.short_label, Qt.ElideRight, int(area.width()))
            painter.drawText(area, Qt.AlignHCenter | Qt.AlignTop, text)
        else:
            painter.setFont(self.font())
            area = self.label_rect()
            text = QFontMetrics(self.font()).elidedText(self.text(), Qt.ElideRight, int(area.width()))
            painter.drawText(area, Qt.AlignVCenter | Qt.AlignLeft, text)
        painter.end()


def rgba_to_qcolor(hex_color: str, alpha: float) -> "QColor":
    """``QColor`` translúcido a partir de un token (equivalente a ``theme.rgba``)."""
    color = QColor(hex_color)
    color.setAlphaF(max(0.0, min(1.0, alpha)))
    return color


#: Logotipo sin el texto (para iconos y la barra lateral). El logotipo
#: completo, con «Pretty[Calc]», está en ``Docs/logo.svg``.
LOGO_MARK_PATH = Path(__file__).resolve().parent / "assets" / "logo-mark.svg"

_logo_renderer: Optional["QSvgRenderer"] = None


def _renderer() -> "QSvgRenderer":
    global _logo_renderer
    if _logo_renderer is None:
        _logo_renderer = QSvgRenderer(str(LOGO_MARK_PATH))
    return _logo_renderer


def paint_brand_mark(painter: "QPainter", rect: "QRectF") -> None:
    """Dibuja el logotipo en ``rect`` (barra lateral e icono de la ventana)."""
    _renderer().render(painter, rect)


class BrandMark(QWidget):
    """Logotipo de PrettyCalc: la matriz aumentada [A | b] con sus pivotes."""

    def __init__(self, size: int = 34, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAccessibleName("PrettyCalc")

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        paint_brand_mark(painter, QRectF(0, 0, self._size, self._size))
        painter.end()


def brand_icon() -> "QIcon":
    """Icono de la ventana y de la barra de tareas: el mismo logotipo, en varios tamaños."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        paint_brand_mark(painter, QRectF(0, 0, size, size))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def wordmark_html() -> str:
    """«Pretty[Calc]» como en el logotipo: Inter y, entre corchetes, Fira Code."""
    return (
        f"<span style='font-family:{FONT_FAMILY_SANS}; font-weight:600; color:{COLOR_TEXT_PRIMARY};'>Pretty</span>"
        f"<span style='font-family:{FONT_FAMILY_MONO}; font-weight:700; color:{COLOR_INTERACTIVE_IDLE};'>[Calc]</span>"
    )


class ModularNavigationBar(QFrame):
    """Barra lateral de módulos. Emite ``module_changed(int)`` al conmutar.

    Incluye la marca de la aplicación arriba y un pie con herramientas
    (``add_footer_item``). ``set_compact(True)`` la pliega a un riel.
    """

    module_changed = Signal(int)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        tabs: Sequence[Tuple[str, str]] = MODULE_TABS,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sideNav")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._buttons: List[NavItem] = []
        self._footer_items: List[NavItem] = []
        self._compact = False
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._setup_ui(tabs)
        self._group.idClicked.connect(self._on_id_clicked)
        self.setFixedWidth(EXPANDED_WIDTH)

    def _setup_ui(self, tabs: Sequence[Tuple[str, str]]) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 18, 8, 12)
        self._layout.setSpacing(2)

        brand = QWidget()
        brand_row = QHBoxLayout(brand)
        brand_row.setContentsMargins(10, 0, 6, 0)
        brand_row.setSpacing(12)
        self.brand_mark = BrandMark(40)
        brand_row.addWidget(self.brand_mark, 0, Qt.AlignVCenter)
        self._brand_text = QWidget()
        text_box = QVBoxLayout(self._brand_text)
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(0)
        self.title_label = QLabel(wordmark_html())
        self.title_label.setObjectName("appTitle")
        self.title_label.setTextFormat(Qt.RichText)
        self.title_label.setAccessibleName("PrettyCalc")
        self.title_label.setStyleSheet("font-size: 19px; letter-spacing: -0.01em; background: transparent;")
        caption = QLabel("Álgebra lineal")
        caption.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        text_box.addWidget(self.title_label)
        text_box.addWidget(caption)
        brand_row.addWidget(self._brand_text, 1, Qt.AlignVCenter)
        self._brand_row = brand_row
        self._layout.addWidget(brand)
        self._layout.addSpacing(22)

        self._section_caption = QLabel("MÓDULOS")
        self._section_caption.setObjectName("sideNavCaption")
        self._section_caption.setStyleSheet(
            f"font-size: 11px; font-weight: 600; letter-spacing: 0.12em; "
            f"color: {COLOR_TEXT_MUTED}; padding: 0 0 6px 12px;"
        )
        self._layout.addWidget(self._section_caption)

        for index, (glyph, label) in enumerate(tabs):
            short = SHORT_LABELS[index] if index < len(SHORT_LABELS) else label
            btn = NavItem(glyph, label, short)
            btn.setToolTip(f"{label}  (Ctrl+{index + 1})")
            btn.setAccessibleName(label)
            btn.setCheckable(True)
            self._group.addButton(btn, index)
            self._buttons.append(btn)
            self._layout.addWidget(btn)

        self._layout.addStretch(1)
        self._footer_rule = QFrame()
        self._footer_rule.setObjectName("sideNavRule")
        self._footer_rule.setFixedHeight(1)
        self._layout.addWidget(self._footer_rule)
        self._layout.addSpacing(8)

        if self._buttons:
            self._buttons[0].setChecked(True)

    def add_footer_item(self, glyph: str, label: str, short_label: Optional[str] = None) -> NavItem:
        """Agrega una herramienta al pie (atajos, apariencia…) y la devuelve."""
        item = NavItem(glyph, label, short_label)
        item.setAccessibleName(label)
        item.set_compact(self._compact)
        self._footer_items.append(item)
        self._layout.addWidget(item)
        return item

    def _on_id_clicked(self, index: int) -> None:
        self.module_changed.emit(index)

    def current_index(self) -> int:
        return self._group.checkedId()

    def set_current_index(self, index: int, emit: bool = True) -> None:
        """Selecciona el módulo `index` (0-based)."""
        if index < 0 or index >= len(self._buttons):
            return
        if self._buttons[index].isChecked() and not emit:
            return
        self._buttons[index].setChecked(True)
        if emit:
            self.module_changed.emit(index)

    def is_compact(self) -> bool:
        return self._compact

    def set_compact(self, compact: bool) -> None:
        """Riel con rótulos cortos cuando el ancho no alcanza: nunca un rótulo recortado."""
        if compact == self._compact:
            return
        self._compact = compact
        self._brand_text.setVisible(not compact)
        self._section_caption.setVisible(not compact)
        self._brand_row.setContentsMargins(0 if compact else 10, 0, 0 if compact else 6, 0)
        self._brand_row.setAlignment(self.brand_mark, Qt.AlignCenter if compact else Qt.AlignVCenter)
        side = 5 if compact else 8
        self._layout.setContentsMargins(side, 18, side, 12)
        for item in self._buttons + self._footer_items:
            item.set_compact(compact)
        self.setFixedWidth(COMPACT_WIDTH if compact else EXPANDED_WIDTH)

    @property
    def buttons(self) -> List[QPushButton]:
        return list(self._buttons)

    @property
    def footer_items(self) -> List[QPushButton]:
        return list(self._footer_items)
