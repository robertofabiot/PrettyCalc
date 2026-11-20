"""Módulo 10: Jacobi y Gauss-Seidel en la interfaz."""

from prettycalc.core.iterative_methods import IterationStatus, IterativeMethod
from prettycalc.core.types import Matrix
from prettycalc.ui.feedback import last_toast_message
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.modules.iterative_methods_view import FIRST_ITERATION_STEP


def _view(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1366, 768)
    window.show()
    qtbot.waitExposed(window)
    window.set_module(9)
    return window, window.iterative_view


def test_ctrl_0_opens_the_module(qtbot):
    window, view = _view(qtbot)
    window.set_module(0)
    window.set_module(9)
    assert window.module_stack.currentWidget() is view
    assert "Métodos Iterativos" in window.subtitle_lbl.text()


def test_dominant_example_fills_steps_tables_plot_and_comparison(qtbot):
    _window, view = _view(qtbot)
    view.load_example("dominant")
    jac = view.results[IterativeMethod.JACOBI]
    gs = view.results[IterativeMethod.GAUSS_SEIDEL]
    assert jac.converged and gs.converged
    assert gs.iteration_count < jac.iteration_count
    for method, result in view.results.items():
        panel = view.panels[method]
        assert len(panel.stepper.steps()) == len(result.tracer)
        assert panel.table.rowCount() == len(result.iterations)
        assert panel.stepper._display_mode == "decimal"
    assert len(view.plot.series()) == 2
    assert view.compare_table.rowCount() > 0
    assert "Ambos convergen" in view.compare_summary.text()
    assert view.tabs.currentIndex() == 2
    assert "Jacobi converge en" in view.badge.text()


def test_diagnosis_updates_live_with_dominance_and_gauges(qtbot):
    _window, view = _view(qtbot)
    view.load_example("gs_only")
    assert "✗" in view.dominance_label.text()
    assert view.jacobi_gauge.radius() > 1
    assert view.gs_gauge.radius() < 1
    assert view.results[IterativeMethod.JACOBI].status is IterationStatus.DIVERGED


def test_table_and_carousel_follow_each_other(qtbot):
    _window, view = _view(qtbot)
    view.load_example("dominant")
    panel = view.panels[IterativeMethod.JACOBI]
    panel.table.selectRow(2)
    assert panel.stepper.current_index() == FIRST_ITERATION_STEP + 2
    panel.stepper.go_to_step(FIRST_ITERATION_STEP + 5)
    assert panel.table.currentRow() == 5


def test_single_method_only_runs_that_method(qtbot):
    _window, view = _view(qtbot)
    view.load_example("dominant")
    view.gs_btn.click()
    view.iterate()
    assert list(view.results) == [IterativeMethod.GAUSS_SEIDEL]
    assert view.panels[IterativeMethod.JACOBI].stepper.steps() == []
    assert view.tabs.currentIndex() == 1


def test_divergent_system_offers_reordering_and_then_converges(qtbot):
    _window, view = _view(qtbot)
    view.load_example("neither")
    assert all(r.status is IterationStatus.DIVERGED for r in view.results.values())
    assert "reordenándolas" in last_toast_message(view)
    view.reorder_rows()
    assert view.grid.get_matrix() == Matrix([[7, -1, 6], [1, -5, -4]])
    view.iterate()
    assert all(r.converged for r in view.results.values())
    view.grid.undo()
    assert view.grid.get_matrix() == Matrix([[1, -5, -4], [7, -1, 6]])


def test_zero_diagonal_shows_the_reason_in_the_carousel(qtbot):
    _window, view = _view(qtbot)
    view.grid.set_matrix(Matrix([[0, 1, 1], [1, 2, 3]]))
    view.iterate()
    assert view.results == {}
    assert "aᵢᵢ = 0" in view.badge.text()
    steps = view.panels[IterativeMethod.JACOBI].stepper.steps()
    assert steps and steps[-1].alert_rows == (0,)


def test_changing_parameters_clears_stale_results(qtbot):
    _window, view = _view(qtbot)
    view.load_example("dominant")
    view.max_iter_spin.setValue(10)
    assert view.results == {}
    assert view.plot.series() == []


def test_x0_follows_the_order_of_the_system(qtbot):
    _window, view = _view(qtbot)
    view.size_control.set_size(5, 5)
    assert view.x0_grid.data_shape() == (1, 5)
