"""Sprint 10: Módulo 3 (vectores en ℝⁿ) al estándar 10/10."""

from PySide6.QtGui import QGuiApplication

from prettycalc.core.types import Matrix, Vector
from prettycalc.core.vector_ops import trace_vector_scale, trace_vector_sum
from prettycalc.ui.feedback import last_toast_message, toast_for
from prettycalc.ui.modules.vectors_view import VectorsView


def _view(qtbot):
    view = VectorsView()
    qtbot.addWidget(view)
    return view


def test_core_traces_each_component_of_u_minus_v():
    result = trace_vector_sum(Vector([1, 2]), Vector([4, -5]), subtract=True)
    steps = result.tracer.get_steps()
    assert result.vector == Vector([-3, 7])
    assert len(steps) == 3
    assert "Componente 2: 2 − (-5) = 7." == steps[2].heuristic_text
    assert steps[2].highlight_cells == ((1, 0), (1, 1), (1, 2))


def test_core_scale_by_zero_explains_the_null_vector():
    steps = trace_vector_scale(Vector([3, 4]), "0").tracer.get_steps()
    assert "vector cero" in steps[-1].heuristic_text


def test_basic_operation_shows_operator_and_component_steps(qtbot):
    view = _view(qtbot)
    view.load_basic_sample()
    assert view.basic_result.matrix() == Matrix([[5], [-2], [2]])
    assert view.basic_op_lbl.text() == "+"
    assert len(view.basic_stepper.steps()) == 4

    view.basic_sub_btn.click()
    assert view.basic_op_lbl.text() == "−"
    assert view.basic_result.matrix() is None  # los cambios invalidan el resultado anterior


def test_swap_turns_u_minus_v_into_v_minus_u_and_can_be_undone(qtbot):
    view = _view(qtbot)
    view.vec_u.set_vector(Vector([1, 2, 3]))
    view.vec_v.set_vector(Vector([4, 5, 6]))
    view.basic_sub_btn.click()
    view.swap_basic_operands()
    view._compute_basic()
    assert view.basic_result.matrix() == Matrix([[3], [3], [3]])
    assert "intercambiaron" in last_toast_message(view)
    toast_for(view).action_btn.click()
    assert view.vec_u.get_vector() == Vector([1, 2, 3])


def test_scale_mode_uses_scalar_field_with_chips(qtbot):
    view = _view(qtbot)
    view.basic_scale_btn.click()
    assert view.vec_u.isHidden() and not view.scale_card.isHidden()
    view.basic_k.setText("3/2")
    assert view.basic_k_input.hint_text() == "≈ 1.5"
    view.basic_k.setText("1/0")
    assert not view.basic_compute_btn.isEnabled()
    assert "Escalar k" in view.basic_badge.text()
    view.basic_k_input.chip_buttons[0].click()
    assert view.basic_k.text() == "-1"
    assert view.basic_compute_btn.isEnabled()


def test_invalid_component_is_named_in_the_badge(qtbot):
    view = _view(qtbot)
    view.vec_v.grid.cells[1][0].setText("2,5")
    assert "Vector v, componente 2" in view.basic_badge.text()
    assert "coma decimal" in view.basic_badge.text()


def test_metrics_use_one_selector_and_one_compute_button(qtbot):
    view = _view(qtbot)
    view.metric_u.set_vector(Vector([3, 4]))
    view.metric_u_dim.setValue(2)
    view.norm_u_btn.click()
    view.metric_compute_btn.click()
    assert "‖u‖ = 5" in view.metric_summary.text()

    view.metric_v_dim.setValue(3)
    view.distance_btn.click()
    assert not view.metric_compute_btn.isEnabled()
    assert "misma dimensión" in view.metric_badge.text()
    assert not view.metric_fix_dims_btn.isHidden()
    view.metric_fix_dims_btn.click()
    assert view.metric_v_dim.value() == 2
    assert view.metric_compute_btn.isEnabled()


def test_outer_product_inspector_highlights_u_row_and_v_column(qtbot):
    view = _view(qtbot)
    view.load_outer_product_sample()
    view._on_outer_cell_clicked(1, 2)
    assert view.inspected_cell() == (1, 2)
    assert view.metric_u.grid.highlighted_rows() == {1}
    assert view.metric_v.grid.highlighted_rows() == {2}
    assert "(-2) · (3) = -6" in view.metric_inspector.text()
    view.metric_u.grid.cells[0][0].setText("5")
    assert view.inspected_cell() is None


def test_combination_si_names_the_contradiction_row_and_value(qtbot):
    view = _view(qtbot)
    view.load_combination_si_sample()
    texts = [view.combo_checklist.itemAt(i).widget().text() for i in range(view.combo_checklist.count())]
    assert any("fila 3" in t and "0 = 1" in t for t in texts)
    assert not view.combo_contradiction_btn.isHidden()
    view.show_combination_contradiction()
    assert view.combo_stepper.isVisibleTo(view)
    assert view.combo_stepper.current_index() == view.combo_stepper.first_alert_index()


def test_combination_sci_sample_is_available(qtbot):
    view = _view(qtbot)
    view.load_combination_sci_sample()
    assert "SCI" in view.combo_badge.text()


def test_combination_warns_before_evaluating_when_k_exceeds_n(qtbot):
    view = _view(qtbot)
    view.combo_set.add_vector()
    assert view.combo_set.crowded_text() == ""
    view.combo_set.add_vector()
    assert "k = 4 > n = 3" in view.combo_set.crowded_text()


def test_combination_validation_is_inline_not_modal(qtbot):
    view = _view(qtbot)
    view.combo_set.editors[1].grid.cells[0][0].setText("abc")
    assert not view.combo_btn.isEnabled()
    assert "v₂, componente 1" in view.combo_set.error_lbl.text()
    view.target_editor.grid.cells[2][0].setText("1O")
    assert "Vector objetivo" in view.combo_input_hint.text()


def test_editing_after_evaluation_marks_the_verdict_as_stale(qtbot):
    view = _view(qtbot)
    view.load_combination_scd_sample()
    view.target_editor.grid.cells[0][0].setText("7")
    assert "vuelve a evaluar" in view.combo_badge.text()
    assert view.combo_checklist.count() == 0


def test_paste_matrix_loads_columns_as_vectors_and_b(qtbot):
    view = _view(qtbot)
    QGuiApplication.clipboard().setText("1\t0\t2\n0\t1\t3\n0\t0\t0\n0\t0\t0")
    assert view.paste_augmented_combination()
    assert view.combo_dim.value() == 4
    assert view.combo_set.count() == 2
    assert view.target_editor.get_vector() == Vector([2, 3, 0, 0])
    toast_for(view).action_btn.click()
    assert view.combo_set.count() == 2 and view.combo_dim.value() == 3


def test_independence_paste_columns_and_undo_removal(qtbot):
    view = _view(qtbot)
    QGuiApplication.clipboard().setText("1 2 3 4\n5 6 7 8")
    assert view.indep_set.paste_columns_from_clipboard()
    assert view.indep_set.count() == 4 and view.indep_dim.value() == 2
    assert "k = 4 > n = 2" in view.indep_set.crowded_text()

    view.indep_set.remove_vector(view.indep_set.editors[0])
    assert view.indep_set.count() == 3
    assert view.indep_set.editors[0].title() == "v₁"
    toast_for(view).action_btn.click()
    assert view.indep_set.count() == 4
    assert view.indep_set.editors[0].get_vector() == Vector([1, 5])


def test_last_vector_cannot_be_removed(qtbot):
    view = _view(qtbot)
    while view.indep_set.count() > 1:
        view.indep_set.remove_vector(view.indep_set.editors[-1], offer_undo=False)
    assert not view.indep_set.editors[0].delete_btn.isEnabled()


def test_theorems_dialog_belongs_to_module_3(qtbot):
    view = _view(qtbot)
    assert "Módulo 3" in view.THEOREMS_TITLE
    assert "Módulo 3" in view.theorems_html()
    assert "Módulo 2" not in view.theorems_html()


def test_independence_lists_free_variables_without_python_syntax(qtbot):
    view = _view(qtbot)
    view.load_independence_ld_sample()
    assert "['" not in view.indep_summary.text()
    assert "c₃" in view.indep_summary.text()
