"""Avisos, revelado de resultados, resultados desactualizados y vuelos entre widgets."""

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication, QWidget

from prettycalc.core.types import Matrix
from prettycalc.ui import choreography, motion
from prettycalc.ui.feedback import last_toast_message, show_toast, toast_for
from prettycalc.ui.main_window import MainWindow


def _window(qtbot, width=1700, height=950):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(width, height)
    window.show()
    qtbot.waitExposed(window)
    return window


def _layer(widget):
    return motion.layer_for(widget)


# ----------------------------------------------------------------- avisos


def test_toast_state_is_immediate_and_entrance_ends_at_rest(qtbot):
    host = QWidget()
    qtbot.addWidget(host)
    host.resize(800, 500)
    host.show()
    toast = show_toast(host, "Hola", kind="success")
    assert toast.isVisible()
    assert last_toast_message(host) == "Hola"
    motion.finish_all()
    assert toast._opacity.opacity() == 1.0
    assert toast.pos() == toast._resting_pos


def test_toast_replacement_keeps_it_open_and_dismiss_hides_at_once(qtbot):
    host = QWidget()
    qtbot.addWidget(host)
    host.resize(800, 500)
    host.show()
    show_toast(host, "Uno")
    motion.finish_all()
    toast = show_toast(host, "Dos", kind="warning")
    assert toast.isVisible() and toast.message() == "Dos"
    qtbot.keyClick(toast, Qt.Key_Escape)
    assert not toast.isVisible()
    motion.finish_all()
    assert not _layer(host).isVisible()


def test_undo_toast_shows_countdown_and_pauses_on_hover(qtbot):
    host = QWidget()
    qtbot.addWidget(host)
    host.resize(800, 500)
    host.show()
    toast = show_toast(host, "Se cargó el ejemplo", action_text="Deshacer", action=lambda: None, timeout_ms=4000)
    assert toast.has_countdown()
    assert 0.0 < toast.remaining_fraction() <= 1.0
    QApplication.sendEvent(toast, QEnterEvent(QPointF(5, 5), QPointF(5, 5), QPointF(5, 5)))
    assert toast.is_paused()
    assert not toast._timer.isActive()
    QApplication.sendEvent(toast, QEvent(QEvent.Leave))
    assert not toast.is_paused()
    assert toast._timer.isActive()
    toast.dismiss()
    assert not toast.has_countdown() or not toast.isVisible()


def test_many_toasts_in_a_row_do_not_queue(qtbot):
    host = QWidget()
    qtbot.addWidget(host)
    host.resize(800, 500)
    host.show()
    for index in range(8):
        show_toast(host, f"Aviso {index}")
    motion.finish_all()
    assert toast_for(host).message() == "Aviso 7"
    assert motion.running_count() == 0


def test_toast_without_motion_appears_still(qtbot):
    motion.set_reduce_motion(True, persist=False)
    host = QWidget()
    qtbot.addWidget(host)
    host.resize(800, 500)
    host.show()
    toast = show_toast(host, "Quieto", action_text="Deshacer", action=lambda: None)
    assert toast._entrance is None
    assert motion.running_count() == 0
    assert not toast._bar_timer.isActive()


# ----------------------------------------------- la matriz entra al carrusel


def test_solving_flies_the_matrix_into_the_procedure(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    book = view.stepper_carousel.matrix_view
    # El estado ya es el final: pasos, veredicto y matriz.
    assert book.matrix() == view.matrix_grid.get_matrix()
    assert view.dashboard_card.status_badge.text() == "Consistente determinado"
    assert book.transition_kind() == "arrival"
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    assert len(_layer(view)._flights) == 12
    motion.finish_all()
    assert not _layer(view).isVisible()
    assert not book.is_animating()


def test_recalculating_the_same_data_only_pulses_the_badge(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    motion.finish_all()
    view.solve_system()
    assert view.stepper_carousel.matrix_view.transition_kind() != "arrival"
    assert view.dashboard_card.same_verdict_as_before()
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    assert not _layer(view)._flights
    assert _layer(view)._marks


def test_flight_requires_the_grid_to_hold_exactly_the_shown_matrix(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    motion.finish_all()
    book = view.stepper_carousel.matrix_view
    assert choreography.grid_matches_book(view.matrix_grid, book)
    view.matrix_grid.cells[0][0].setText("9")
    assert not choreography.grid_matches_book(view.matrix_grid, book)
    assert choreography.fly_grid_into_book(view.matrix_grid, book) == 0


def test_changing_module_mid_flight_lands_everything(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    window.set_module(1)
    assert not _layer(view).isVisible()
    assert not view.stepper_carousel.matrix_view.is_animating()


def test_resizing_the_window_mid_flight_lands_everything(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    window.resize(1500, 900)
    qtbot.wait(10)
    assert not _layer(view).isVisible()


def test_final_step_sends_each_b_value_to_its_solution_line(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    qtbot.wait(30)  # las líneas nuevas del tablero se muestran en el bucle de eventos
    motion.finish_all()
    carousel = view.stepper_carousel
    carousel.go_to_step(len(carousel.steps()) - 2)
    motion.finish_all()
    carousel._gate.reset()
    carousel.next_step()
    layer = _layer(view)
    assert layer.is_active()
    analysis = view.dashboard_card.last_analysis
    assert len(layer._flights) == len(analysis.unique_solution)
    assert len(layer._marks) == len(analysis.unique_solution)
    final = carousel.steps()[-1].matrix
    split = carousel.steps()[-1].split_col
    values = sorted(final.get(r, split) for r in range(final.rows))
    assert values == sorted(analysis.unique_solution)
    motion.finish_all()
    assert not layer.isVisible()


def test_jumping_to_the_final_step_does_not_fly(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    motion.finish_all()
    carousel = view.stepper_carousel
    carousel.go_to_step(len(carousel.steps()) - 1)  # salto, no avance
    assert not _layer(view)._flights


def test_reduce_motion_solves_without_anything_in_flight(qtbot):
    motion.set_reduce_motion(True, persist=False)
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    qtbot.wait(30)
    assert not _layer(view).isVisible()
    assert not view.stepper_carousel.matrix_view.is_animating()
    assert motion.running_count() == 0


def test_dashboard_sections_end_without_effects(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case2()
    qtbot.wait(30)
    motion.finish_all()
    card = view.dashboard_card
    assert card.graphicsEffect() is None
    assert all(w.graphicsEffect() is None for w in card.findChildren(QWidget))


# --------------------------------------------------- veredictos de módulos


def test_explicit_action_reveals_and_same_result_pulses(qtbot):
    window = _window(qtbot)
    window.set_module(4)
    view = window.determinants_view
    view.load_session11_example()
    view.compute()
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    assert _layer(view)._sprites  # el veredicto nuevo se asienta
    motion.finish_all()
    view.compute()
    qtbot.waitUntil(lambda: _layer(view).is_active(), timeout=1000)
    assert _layer(view)._marks and not _layer(view)._sprites  # mismo veredicto: pulso


def test_action_decorator_ignores_signal_arguments(qtbot):
    window = _window(qtbot)
    window.set_module(1)
    ops = window.matrix_operations_view
    ops.load_compatible_product_sample()
    ops.compute(True)  # ``clicked(bool)`` no rompe la acción
    motion.finish_all()
    assert ops.badge.text()


def test_stale_result_fades_out_over_the_new_state(qtbot):
    window = _window(qtbot)
    window.set_module(3)
    view = window.matrix_equations_view
    view.load_sample()
    view.solve()
    motion.finish_all()
    view.grid_a.cells[0][0].setText("7")
    assert view.x_subtitle.text().startswith("Datos modificados")
    assert _layer(view).is_active()
    motion.finish_all()
    assert not _layer(view).isVisible()


def test_applications_panel_scrolls_smoothly_to_the_same_place(qtbot):
    window = _window(qtbot, 1366, 700)
    view = window.linear_systems_view
    view.toggle_applications()
    assert view.applications_panel.isVisible()
    qtbot.wait(20)
    motion.finish_all()
    target = view.left_scroll.verticalScrollBar().value()
    view.left_scroll.verticalScrollBar().setValue(0)
    view.left_scroll.ensureWidgetVisible(view.applications_panel, 0, 0)
    assert view.left_scroll.verticalScrollBar().value() == target
    assert view.applications_panel.graphicsEffect() is None
