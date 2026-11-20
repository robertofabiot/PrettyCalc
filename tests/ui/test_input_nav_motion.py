"""Cuadrícula de entrada y navegación: crecimiento, destello, celda inválida e indicador."""

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication

from prettycalc.ui import motion
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.matrix_grid import DynamicMatrixGrid


def _grid(qtbot, **kwargs):
    grid = DynamicMatrixGrid(**kwargs)
    qtbot.addWidget(grid)
    grid.resize(500, 300)
    grid.show()
    qtbot.waitExposed(grid)
    return grid


def test_new_column_grows_from_the_old_brackets(qtbot):
    grid = _grid(qtbot)
    grid.add_column()
    assert grid.is_growing()
    # En [A | b] la variable nueva entra antes de b.
    assert grid._grow_cells == {(0, 2), (1, 2)}
    assert grid.data_shape() == (2, 4)
    motion.finish_all()
    assert not grid.is_growing() and not grid._grow_cells


def test_new_row_and_plain_matrix_cells_are_found_by_index(qtbot):
    grid = _grid(qtbot, augmented=False)
    grid.add_row()
    assert grid._grow_cells == {(2, 0), (2, 1)}
    motion.finish_all()
    qtbot.wait(10)  # las celdas nuevas se muestran en el bucle de eventos
    grid.add_column()
    assert grid._grow_cells == {(0, 2), (1, 2), (2, 2)}


def test_removing_a_row_contracts_without_new_cells(qtbot):
    grid = _grid(qtbot)
    grid.add_row()
    motion.finish_all()
    qtbot.wait(10)
    grid.remove_row(2)
    assert grid.is_growing() and not grid._grow_cells
    motion.finish_all()


def test_flash_is_painted_and_keeps_its_api(qtbot):
    grid = _grid(qtbot)
    grid.flash()
    assert grid.is_flashing()
    assert not grid.cells[0][0].property("flash")
    motion.finish_all()
    assert not grid.is_flashing()
    assert grid._flash_strength == 0.0


def test_flash_without_motion_uses_the_static_tint(qtbot):
    grid = _grid(qtbot)
    motion.set_reduce_motion(True, persist=False)
    grid.flash()
    assert grid.cells[0][0].property("flash") is True
    assert motion.running_count() == 0


def test_rebuilding_the_grid_mid_animation_is_safe(qtbot):
    grid = _grid(qtbot)
    grid.flash()
    grid.add_column()
    grid.resize_to(4, 5)
    grid.undo()
    grid.set_matrix(grid.get_matrix())
    motion.finish_all()
    assert motion.running_count() == 0


def test_blocked_submit_pulses_the_invalid_cell_twice(qtbot):
    grid = _grid(qtbot)
    grid.cells[1][0].setText("abc")
    layer = motion.layer_for(grid)
    assert not layer.is_active()  # el error aparece sin movimiento al escribir
    assert grid.focus_first_invalid()
    mark = layer._marks[-1]
    assert mark.pulses == 2
    # Dos ciclos en 800 ms: menos de 3 destellos por segundo.
    assert mark.duration / mark.pulses >= 1000 / 3
    motion.finish_all()


def _window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1700, 900)
    window.show()
    qtbot.waitExposed(window)
    return window


def test_active_indicator_slides_to_the_new_module(qtbot):
    window = _window(qtbot)
    window.set_module(4)
    nav = window.nav_bar
    assert nav.is_sliding()
    assert nav.buttons[4].isChecked()
    assert nav.buttons[4].indicator_external
    motion.finish_all()
    assert not nav.is_sliding()
    assert not nav.buttons[4].indicator_external


def test_clicking_a_module_slides_and_changes_page(qtbot):
    window = _window(qtbot)
    qtbot.mouseClick(window.nav_bar.buttons[2], Qt.LeftButton)
    assert window.module_stack.currentIndex() == 2
    assert window.nav_bar.is_sliding()


def test_rapid_module_switching_never_queues(qtbot):
    window = _window(qtbot)
    for index in (0, 4, 1, 7, 2, 9, 3):
        window.set_module(index)
    layer = motion.layer_for(window)
    assert len(layer._sprites) <= 2  # solo la última página y su encabezado
    motion.finish_all()
    assert window.module_stack.currentIndex() == 3
    assert window.nav_bar.buttons[3].isChecked()
    assert not layer.isVisible()


def test_module_change_crossfades_without_effects_on_pages(qtbot):
    window = _window(qtbot)
    window.set_module(1)
    assert motion.layer_for(window)._sprites
    assert window.module_stack.currentWidget().graphicsEffect() is None


def test_nav_hover_tint_fades_in(qtbot):
    window = _window(qtbot)
    item = window.nav_bar.buttons[3]
    QApplication.sendEvent(item, QEnterEvent(QPointF(4, 4), QPointF(4, 4), QPointF(4, 4)))
    motion.finish_all()
    assert item.hover_strength() == 1.0
    QApplication.sendEvent(item, QEvent(QEvent.Leave))
    motion.finish_all()
    assert item.hover_strength() == 0.0


def test_navigation_without_motion_is_instant(qtbot):
    motion.set_reduce_motion(True, persist=False)
    window = _window(qtbot)
    window.set_module(5)
    assert not window.nav_bar.is_sliding()
    assert not motion.layer_for(window).isVisible()
