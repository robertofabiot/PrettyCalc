"""Sprint 10: Módulos 5 (determinantes) y 6 (LU) al estándar 10/10."""

from fractions import Fraction

from prettycalc.core.determinants import (
    best_expansion_line,
    determinant_laplace_expansion,
    determinant_sarrus_3x3,
    scaling_breakdown,
)
from prettycalc.core.types import Matrix
from prettycalc.ui.feedback import last_toast_message, toast_for
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.modules.determinants_view import DeterminantsView
from prettycalc.ui.modules.lu_factorization_view import LUFactorizationView, permuted_rows


def _det(qtbot):
    view = DeterminantsView()
    qtbot.addWidget(view)
    return view


def _lu(qtbot):
    view = LUFactorizationView()
    qtbot.addWidget(view)
    return view


# ---------------------------------------------------------------- núcleo
def test_sarrus_records_one_step_per_diagonal():
    steps = determinant_sarrus_3x3(Matrix([[2, -1, 0], [-2, 3, 4], [-5, 1, 6]])).tracer.get_steps()
    diagonal_steps = steps[1:7]
    assert [step.highlight_cells for step in diagonal_steps][1] == ((0, 1), (1, 2), (2, 0))
    assert "se resta" in diagonal_steps[4].heuristic_text and "= 8" in diagonal_steps[4].heuristic_text


def test_best_expansion_line_prefers_most_zeros():
    assert best_expansion_line(Matrix([[1, 0, 2], [0, 0, 3], [4, 5, 6]])) == ("row", 1, 2)
    assert best_expansion_line(Matrix([[1, 0], [2, 0]])) == ("col", 1, 2)


def test_laplace_highlights_the_expansion_line():
    steps = determinant_laplace_expansion(Matrix([[1, 2], [3, 4]]), along="col", index=1).tracer.get_steps()
    assert steps[1].highlight_cells == ((0, 1), (1, 1))


def test_scaling_breakdown_spells_out_the_power():
    assert scaling_breakdown(Fraction(2), 2, Fraction(9)) == "kⁿ = 2² = 4 ⇒ 4 · 9 = 36"


# --------------------------------------------------------- determinantes
def test_order_spinbox_jumps_directly(qtbot):
    view = _det(qtbot)
    view.size_control.rows_spin.setValue(7)
    assert view.grid.data_shape() == (7, 7)
    assert view.expansion_index.maximum() == 7


def test_sarrus_on_wrong_order_offers_adjustment(qtbot):
    view = _det(qtbot)
    view.size_control.set_size(4, 4)
    view.sarrus_mode_btn.click()
    assert not view.compute_btn.isEnabled()
    assert not view.sarrus_fix_btn.isHidden()
    assert "Sarrus" in last_toast_message(view)
    view.sarrus_fix_btn.click()
    assert view.grid.data_shape() == (3, 3)
    assert view.compute_btn.isEnabled()
    assert view.sarrus_fix_btn.isHidden()


def test_sarrus_diagram_follows_the_carousel(qtbot):
    view = _det(qtbot)
    view.load_sarrus_example()
    assert view.sarrus_diagram.matrix() is not None
    view.stepper.go_to_step(4)
    assert view.sarrus_diagram.active_diagonal() == 3
    view.stepper.go_to_step(0)
    assert view.sarrus_diagram.active_diagonal() is None


def test_laplace_highlights_line_and_suggests_zeros(qtbot):
    view = _det(qtbot)
    view.grid.set_matrix(Matrix([[1, 0, 2], [0, 0, 3], [4, 5, 6]]))
    view.laplace_mode_btn.click()
    assert view.grid.highlighted_rows() == {0}
    assert "fila 2 (2 ceros)" in view.laplace_suggest_btn.text()
    view.apply_expansion_suggestion()
    assert view.expansion_index.value() == 2
    assert view.grid.highlighted_rows() == {1}
    assert view.laplace_suggest_btn.isHidden()
    view.laplace_col_btn.click()
    assert view.grid.highlighted_cols() == {1}
    view.triangulation_mode_btn.click()
    assert view.grid.highlighted_rows() == set() and view.grid.highlighted_cols() == set()


def test_adjugate_is_tabbed_and_inverse_can_be_reused(qtbot):
    view = _det(qtbot)
    view.load_session11_example()
    assert view.adjugate_tabs.count() == 4
    assert view.use_inverse_btn.isEnabled()
    original = view.grid.get_matrix()
    view.use_inverse_as_input()
    assert view.last_adjugate.inverse_via_adjugate == original
    toast_for(view).action_btn.click()
    assert view.grid.get_matrix() == original


def test_singular_adjugate_disables_inverse_actions(qtbot):
    view = _det(qtbot)
    view.adjugate_mode_btn.click()
    view.grid.set_matrix(Matrix([[1, 2], [2, 4]]))
    view.compute()
    assert not view.use_inverse_btn.isEnabled()
    assert not view.send_inverse_btn.isEnabled()


def test_inverse_can_be_sent_to_module_2(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(4)
    window.determinants_view.load_session11_example()
    window.determinants_view.send_inverse_btn.click()
    assert window.module_stack.currentWidget() is window.matrix_operations_view
    ops = window.matrix_operations_view
    assert ops.pages.currentIndex() == 4
    assert ops.inverse_result_view.matrix() == Matrix([[1, 3, -3], [2, 0, 1], [-1, 4, -2]])


def test_properties_show_b_beside_a_and_power_breakdown(qtbot):
    view = _det(qtbot)
    view.resize(1400, 800)
    view.show()
    view.load_properties_example()
    qtbot.wait(20)
    assert not view.inputs_row.is_vertical()
    assert "kⁿ = 2² = 4 ⇒ 4 · 9 = 36" in view.properties_checklist.text()
    view.scalar_k.setText("1/0")
    assert not view.compute_btn.isEnabled()
    assert "Escalar k" in view.badge.text()


def test_invalid_cell_is_located_without_modal(qtbot):
    view = _det(qtbot)
    view.grid.cells[1][0].setText("2,5")
    assert view.badge.text().startswith("A, fila 2, columna 1")
    view.size_control.rows_spin.setValue(3)
    assert view.grid.data_shape() == (3, 3)


# -------------------------------------------------------------------- LU
def test_lu_size_spinboxes_set_any_shape(qtbot):
    view = _lu(qtbot)
    view.size_control.set_size(5, 5)
    assert view.grid.data_shape() == (5, 5)
    assert view.b_grid.data_shape() == (5, 1)
    assert "5 × 5" in view.shape_label.text()


def test_permuted_rows_are_marked_on_a(qtbot):
    assert permuted_rows(Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])) == [0, 1]
    view = _lu(qtbot)
    view.grid.set_matrix(Matrix([[0, 2, 1], [1, 1, 1], [2, 1, 0]]))
    view.decompose()
    assert view.grid.alert_rows() == {0, 1}
    assert not view.swap_legend.isHidden()
    view.grid.cells[2][2].setText("5")
    assert view.grid.alert_rows() == set()


def test_stages_live_in_tabs(qtbot):
    view = _lu(qtbot)
    view.grid.set_matrix(Matrix([[0, 2, 1], [1, 1, 1], [2, 1, 0]]))
    view.b_grid.set_matrix(Matrix([[3], [3], [3]]))
    view.decompose()
    view.solve()
    assert view.stage_tabs.count() == 3
    assert view.stage_tabs.tabText(0) == "Etapa 1 · Ly = Pb"


def test_singular_u_offers_classification(qtbot):
    view = _lu(qtbot)
    view.grid.set_matrix(Matrix([[1, 2], [2, 4]]))
    view.b_grid.set_matrix(Matrix([[3], [6]]))
    view.decompose()
    assert not view.solve_btn.isEnabled()
    assert view.classify_btn.isEnabled()
    view.classify()
    assert "indeterminado" in view.dashboard.status_badge.text().lower()
    assert view.stage_tabs.currentIndex() == 2

    view.b_grid.set_matrix(Matrix([[3], [7]]))
    view.classify()
    assert "inconsistente" in view.dashboard.status_badge.text().lower()
