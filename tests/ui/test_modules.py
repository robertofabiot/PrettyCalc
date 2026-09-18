"""Pruebas de integración del shell multi-módulo (Sprint 2)."""

from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.theme import COLOR_FEEDBACK_ERROR, COLOR_FEEDBACK_SUCCESS
from prettycalc.core.types import Matrix


def test_navigation_bar_has_four_modules(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert len(window.nav_bar.buttons) == 4
    assert window.module_stack.count() == 4
    assert "Sistemas Lineales" in window.nav_bar.buttons[0].text()
    assert "Álgebra Matricial" in window.nav_bar.buttons[1].text()
    assert "Vectores" in window.nav_bar.buttons[2].text()
    assert "Ecuaciones" in window.nav_bar.buttons[3].text()


def test_set_module_switches_stacked_widget_and_subtitle(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.set_module(1)
    assert window.module_stack.currentIndex() == 1
    assert window.nav_bar.current_index() == 1
    assert "Álgebra matricial" in window.subtitle_lbl.text()

    window.set_module(2)
    assert window.module_stack.currentIndex() == 2
    assert "Vectores" in window.subtitle_lbl.text()

    window.set_module(3)
    assert window.module_stack.currentIndex() == 3
    assert "Ecuaciones" in window.subtitle_lbl.text()

    window.set_module(0)
    assert window.module_stack.currentWidget() is window.linear_systems_view


def test_clicking_nav_segment_changes_module(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.nav_bar.buttons[2].click()
    assert window.module_stack.currentIndex() == 2
    assert window.module_stack.currentWidget() is window.vectors_view


def test_keyboard_shortcuts_ctrl_1_to_4(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    shortcuts = {action.shortcut().toString(): action for action in window.actions()}
    assert "Ctrl+1" in shortcuts
    assert "Ctrl+4" in shortcuts
    shortcuts["Ctrl+3"].trigger()
    assert window.module_stack.currentIndex() == 2
    shortcuts["Ctrl+1"].trigger()
    assert window.module_stack.currentIndex() == 0


def test_matrix_operations_compatible_badge_and_inspector(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view
    view.load_compatible_product_sample()

    assert view.compute_btn.isEnabled()
    assert "compatibles" in view.badge.text().lower()
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()
    assert view._result is not None
    assert view._result == Matrix([[58, 64], [139, 154]])

    view._on_result_cell_clicked(0, 0)
    assert "C_1,1" in view.inspector_label.text()
    assert view.grid_a._highlight_rows == {0}
    assert view.grid_b._highlight_cols == {0}


def test_matrix_operations_incompatible_disables_compute(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view
    view.load_incompatible_sample()

    assert not view.compute_btn.isEnabled()
    assert "incompatibles" in view.badge.text().lower()
    assert "Columnas de A (3)" in view.badge.text()
    assert COLOR_FEEDBACK_ERROR in view.badge.styleSheet()


def test_vectors_combination_scd_sample(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(2)
    view = window.vectors_view
    view.load_combination_scd_sample()
    assert "ÚNICA" in view.combo_badge.text()
    assert COLOR_FEEDBACK_SUCCESS in view.combo_badge.styleSheet()
    assert "c1 = 2" in view.combo_summary.text()


def test_vectors_combination_si_sample(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(2)
    view = window.vectors_view
    view.load_combination_si_sample()
    assert "NO ES COMBINACIÓN" in view.combo_badge.text()
    assert COLOR_FEEDBACK_ERROR in view.combo_badge.styleSheet()


def test_matrix_equations_sample_solves_and_verifies(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)
    view = window.matrix_equations_view
    view.load_sample()
    assert "Consistente determinado" in view.dashboard.status_badge.text()
    assert "igualdad exacta" in view.product_label.text()
    assert "✓" in view.product_label.text()


def test_module_state_persists_when_switching(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.linear_systems_view.matrix_grid.cells[0][0].setText("9")
    window.set_module(1)
    window.set_module(0)
    assert window.matrix_grid.cells[0][0].text() == "9"
