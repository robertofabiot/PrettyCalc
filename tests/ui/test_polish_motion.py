"""Paneles que aparecen, pestañas, tarjetas de vectores y entrada del logotipo."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from prettycalc.ui import motion
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.navigation_bar import BrandMark
from prettycalc.ui.responsive import CurrentPageStack
from prettycalc.ui.vector_set_editor import VectorSetEditor


def _shown(qtbot, widget, w=600, h=400):
    qtbot.addWidget(widget)
    widget.resize(w, h)
    widget.show()
    qtbot.waitExposed(widget)
    return widget


def test_panel_fades_in_only_when_it_appears(qtbot):
    host = _shown(qtbot, QWidget())
    layout = QVBoxLayout(host)
    panel = QLabel("Pista")
    layout.addWidget(panel)
    panel.hide()
    motion.fade_when_shown(panel)
    panel.show()
    qtbot.waitUntil(lambda: panel.graphicsEffect() is not None, timeout=500)
    motion.finish_all()
    assert panel.graphicsEffect() is None
    panel.hide()
    assert not panel.isVisible()  # ocultar es inmediato


def test_mode_pages_fade_in_without_crossfading(qtbot):
    stack = _shown(qtbot, CurrentPageStack())
    first, second = QLabel("uno"), QLabel("dos")
    stack.addWidget(first)
    stack.addWidget(second)
    stack.setCurrentIndex(1)
    assert second.isVisible() and not first.isVisible()
    qtbot.waitUntil(lambda: second.graphicsEffect() is not None, timeout=500)
    motion.finish_all()
    assert second.graphicsEffect() is None


def test_vector_cards_fade_in_and_out(qtbot):
    editor = _shown(qtbot, VectorSetEditor("Conjunto", 3), 800, 400)
    count = editor.count()
    card = editor.add_vector()
    assert editor.count() == count + 1
    qtbot.waitUntil(lambda: card.graphicsEffect() is not None, timeout=500)
    motion.finish_all()
    assert card.graphicsEffect() is None
    editor.remove_vector(card, offer_undo=False)
    assert editor.count() == count
    layer = motion.layer_for(editor)
    assert layer._sprites  # la tarjeta quitada se desvanece por instantánea
    motion.finish_all()


def test_brand_mark_draws_itself_once(qtbot):
    mark = _shown(qtbot, BrandMark(40), 40, 40)
    assert mark.play_intro()
    assert mark.is_playing_intro()
    motion.finish_all()
    assert not mark.is_playing_intro()
    assert not mark.play_intro()


def test_brand_mark_is_still_with_reduce_motion(qtbot):
    motion.set_reduce_motion(True, persist=False)
    mark = _shown(qtbot, BrandMark(40), 40, 40)
    assert not mark.play_intro()
    assert not mark.is_playing_intro()


def test_window_plays_the_brand_intro_once(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1700, 900)
    window.show()
    qtbot.waitExposed(window)
    mark = window.nav_bar.brand_mark
    assert mark._intro_played
    motion.finish_all()
    window.set_module(3)
    window.set_module(0)
    assert not mark.is_playing_intro()


def test_results_tabs_fade_their_new_page(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1700, 900)
    window.show()
    qtbot.waitExposed(window)
    window.set_module(3)
    motion.finish_all()
    tabs = window.matrix_equations_view.results_tabs
    tabs.setCurrentIndex((tabs.currentIndex() + 1) % tabs.count())
    page = tabs.currentWidget()
    qtbot.waitUntil(lambda: page.graphicsEffect() is not None, timeout=500)
    motion.finish_all()
    assert page.graphicsEffect() is None
