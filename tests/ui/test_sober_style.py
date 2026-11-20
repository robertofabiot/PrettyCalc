"""Riel con cajón, tablas en flujo horizontal, contenedores por elevación y acento primario."""

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication, QTableWidget

from prettycalc.ui import motion
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.modules.numerical_methods_view import _BisectionTab
from prettycalc.ui.navigation_bar import COMPACT_WIDTH, DRAWER_WIDTH
from prettycalc.ui.tables import align_decimals, fit_columns, is_number
from prettycalc.ui.theme import (
    COLOR_ACCENT_PRIMARY,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_SURFACE_INNER,
    PALETTES,
    badge_style,
    contrast_ratio,
    get_global_stylesheet,
)


def _window(qtbot, width=1500, height=860):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(width, height)
    window.show()
    qtbot.waitExposed(window)
    return window


# ------------------------------------------------------------------ tablas


def test_decimal_points_line_up_when_right_aligned():
    column = align_decimals(["2", "2.5", "2.0944824", "—"])
    assert column[-1] == "—"
    numbers = column[:3]
    assert len({len(text) for text in numbers}) == 1
    assert {len(text) - text.index(".") for text in numbers if "." in text} == {8}
    assert numbers[0].rstrip() == "2"  # el valor no cambia: solo se rellena con espacios


def test_scientific_notation_does_not_widen_the_column():
    column = align_decimals(["-1", "-0.00894165", "-8.95647e-05"])
    assert column[1] == "-0.00894165"
    assert column[0] == "-1" + " " * 9
    assert column[2] == "-8.95647e-05"


def test_is_number():
    assert is_number("−0.5") and is_number("16") and is_number("1e-05")
    assert not is_number("—") and not is_number("No definido")


def _bisection(qtbot, width):
    window = _window(qtbot, width, 800)
    window.set_module(8)
    qtbot.wait(20)
    tab = window.numerical_methods_view.findChildren(_BisectionTab)[0]
    tab._calculate()
    qtbot.wait(30)
    return window, tab._table


def test_bisection_table_is_borderless_and_right_aligned(qtbot):
    _window_, table = _bisection(qtbot, 1500)
    assert not table.showGrid()
    assert not table.alternatingRowColors()
    for col in range(table.columnCount()):
        assert table.item(0, col).textAlignment() & Qt.AlignRight
        assert table.horizontalHeaderItem(col).textAlignment() & Qt.AlignRight


def test_bisection_columns_fit_without_horizontal_scroll(qtbot):
    for width in (1080, 1366, 1920):
        _window_, table = _bisection(qtbot, width)
        widths = sum(table.columnWidth(c) for c in range(table.columnCount()))
        assert widths <= table.viewport().width()
        assert table.horizontalScrollBar().maximum() == 0


def test_column_alignment_is_decided_per_column(qtbot):
    _window_, table = _bisection(qtbot, 1366)
    delegate = table.itemDelegate()
    # A 1366 px todas las columnas caben alineadas por el punto decimal.
    assert delegate.raw_columns == set()
    _window_, narrow = _bisection(qtbot, 1080)
    raw = narrow.itemDelegate().raw_columns
    assert raw  # en la ventana mínima algunas columnas se muestran sin relleno
    assert 0 not in raw  # el índice k nunca se encoge


def test_table_rules_have_no_vertical_lines():
    qss = get_global_stylesheet()
    assert "gridline-color: transparent" in qss
    assert "QTableView::item" in qss and "border-bottom: 1px solid" in qss


# --------------------------------------------- contenedores y acento


def test_cards_are_borderless():
    qss = get_global_stylesheet()
    block = qss[qss.index('QFrame[class="elevated-card"]'):]
    block = block[: block.index("}")]
    assert "border: none" in block


def test_badges_are_passive():
    style = badge_style(COLOR_FEEDBACK_SUCCESS)
    assert f"background-color: {COLOR_SURFACE_INNER}" in style
    assert f"border-left: 4px solid {COLOR_FEEDBACK_SUCCESS}" in style
    assert COLOR_ACCENT_PRIMARY not in style


def test_primary_accent_is_legible_and_visible_in_every_theme():
    for name, palette in PALETTES.items():
        accent, on_accent = palette["accent_primary"], palette["on_accent"]
        assert contrast_ratio(on_accent, accent) >= 4.5, name
        # El botón se distingue de la tarjeta y del lienzo (WCAG 1.4.11).
        assert contrast_ratio(accent, palette["surface_elevated"]) >= 3.0, name
        assert accent != palette["feedback_success"], name


def test_cards_read_by_tone_in_every_theme():
    for name, palette in PALETTES.items():
        assert palette["surface_elevated"] != palette["bg_base"], name
        assert contrast_ratio(palette["surface_elevated"], palette["bg_base"]) >= 1.2, name


def test_bisection_summary_does_not_use_the_accent(qtbot):
    window, _table = _bisection(qtbot, 1500)
    tab = window.numerical_methods_view.findChildren(_BisectionTab)[0]
    assert COLOR_ACCENT_PRIMARY not in tab._badge.styleSheet()
    assert COLOR_SURFACE_INNER in tab._badge.styleSheet()


# --------------------------------------------------------------- cajón


def _hover(widget):
    QApplication.sendEvent(widget, QEnterEvent(QPointF(10, 10), QPointF(10, 10), QPointF(10, 10)))


def test_navigation_is_an_icon_rail_at_every_width(qtbot):
    for width in (1080, 1920):
        window = _window(qtbot, width, 768)
        assert window.nav_bar.is_compact()
        assert window.nav_bar.width() == COMPACT_WIDTH
        assert window.nav_rail_space.width() == COMPACT_WIDTH
        for item in window.nav_bar.buttons:
            assert item.toolTip()


def test_hover_opens_a_drawer_over_the_canvas(qtbot):
    window = _window(qtbot)
    nav = window.nav_bar
    content_before = window.module_stack.geometry()
    chip_before = nav.buttons[3].mapTo(window, nav.buttons[3].rect().topLeft())
    _hover(nav)
    qtbot.waitUntil(nav.is_drawer_open, timeout=1000)
    motion.finish_all()
    assert nav.width() == DRAWER_WIDTH
    assert nav.graphicsEffect() is not None  # sombra sobre el lienzo
    # Superpuesto: el contenido no se movió ni cambió de tamaño.
    assert window.module_stack.geometry() == content_before
    # Las marcas no se mueven al abrir: solo aparece el nombre.
    assert nav.buttons[3].mapTo(window, nav.buttons[3].rect().topLeft()).y() == chip_before.y()
    QApplication.sendEvent(nav, QEvent(QEvent.Leave))
    qtbot.waitUntil(lambda: not nav.is_drawer_open(), timeout=1000)
    motion.finish_all()
    assert nav.width() == COMPACT_WIDTH
    assert nav.graphicsEffect() is None


def test_keyboard_focus_opens_the_drawer_and_escape_closes_it(qtbot):
    window = _window(qtbot)
    nav = window.nav_bar
    nav.buttons[2].setFocus(Qt.TabFocusReason)
    qtbot.waitUntil(nav.is_drawer_open, timeout=1000)
    qtbot.keyClick(nav, Qt.Key_Escape)
    assert not nav.is_drawer_open()


def test_drawer_without_motion_opens_instantly(qtbot):
    motion.set_reduce_motion(True, persist=False)
    window = _window(qtbot)
    window.nav_bar.open_drawer()
    assert window.nav_bar.width() == DRAWER_WIDTH
    window.nav_bar.close_drawer()
    assert window.nav_bar.width() == COMPACT_WIDTH
    assert motion.running_count() == 0


def test_choosing_a_module_from_the_drawer_switches_page(qtbot):
    window = _window(qtbot)
    window.nav_bar.open_drawer()
    motion.finish_all()
    qtbot.mouseClick(window.nav_bar.buttons[4], Qt.LeftButton)
    assert window.module_stack.currentIndex() == 4
