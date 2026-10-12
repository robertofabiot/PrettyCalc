"""Sprint 10: brechas de la auditoría UI/UX cerradas en los componentes y módulos 1 y 2."""

from fractions import Fraction

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from prettycalc.core.types import Matrix
from prettycalc.ui.feedback import last_toast_message
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.scalar_field import ScalarField, ScalarInput
from prettycalc.ui.stepper_carousel import ALERT_SYSTEM, AlgorithmStepperCarousel
from prettycalc.ui.theme import (
    COLOR_FEEDBACK_ERROR,
    COLOR_INTERACTIVE_DISABLED,
    COLOR_SURFACE_ELEVATED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    PALETTES,
    contrast_ratio,
)


def _window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window


# ---------------------------------------------------------------------------
# Módulo 7: componentes transversales
# ---------------------------------------------------------------------------

def test_muted_text_meets_wcag_aa_on_cards_in_every_theme():
    assert contrast_ratio(COLOR_TEXT_MUTED, COLOR_SURFACE_ELEVATED) >= 4.5
    for palette in PALETTES.values():
        assert contrast_ratio(palette["text_primary"], palette["surface_elevated"]) >= 4.5
        assert contrast_ratio(palette["text_muted"], palette["surface_elevated"]) >= 4.5


def test_grid_explains_the_invalid_cell_inline(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2)
    qtbot.addWidget(grid)
    grid.cells[1][2].setText("2,5")
    message = grid.validation_message()
    assert message.startswith("Fila 2, columna b")
    assert "coma decimal" in message
    assert not grid.hint_label.isHidden()
    assert "coma decimal" in grid.cells[1][2].toolTip()
    grid.cells[1][2].setText("2.5")
    assert grid.hint_label.isHidden()


def test_blank_cell_becomes_zero_when_focus_leaves(qtbot):
    grid = DynamicMatrixGrid(initial_rows=1, initial_cols=1, augmented=False)
    qtbot.addWidget(grid)
    grid.show()
    cell = grid.cells[0][0]
    cell.setText("")
    from PySide6.QtCore import QCoreApplication, QEvent, Qt
    from PySide6.QtGui import QFocusEvent

    QCoreApplication.sendEvent(cell, QFocusEvent(QEvent.FocusOut, Qt.TabFocusReason))
    assert cell.text() == "0"


def test_grid_undo_and_redo_restore_bulk_changes(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2, augmented=False)
    qtbot.addWidget(grid)
    grid.set_matrix(Matrix([[1, 2], [3, 4]]))
    grid.set_matrix(Matrix([[9]]))
    assert grid.data_shape() == (1, 1)
    assert grid.undo()
    assert grid.get_matrix() == Matrix([[1, 2], [3, 4]])
    assert grid.redo()
    assert grid.get_matrix() == Matrix([[9]])


def test_keyboard_deletes_active_row_and_column(qtbot):
    grid = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=False)
    qtbot.addWidget(grid)
    grid.show()
    grid.set_matrix(Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
    qtbot.keyClick(grid.cells[1][0], Qt.Key_Delete, Qt.ControlModifier)
    assert grid.get_matrix() == Matrix([[1, 2, 3], [7, 8, 9]])
    qtbot.keyClick(grid.cells[0][2], Qt.Key_Delete, Qt.ControlModifier | Qt.ShiftModifier)
    assert grid.get_matrix() == Matrix([[1, 2], [7, 8]])


def test_ctrl_enter_requests_a_computation(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2)
    qtbot.addWidget(grid)
    with qtbot.waitSignal(grid.submitRequested, timeout=1000):
        qtbot.keyClick(grid.cells[0][0], Qt.Key_Return, Qt.ControlModifier)


def test_resize_to_keeps_entries_and_b_column(qtbot):
    grid = DynamicMatrixGrid(initial_rows=2, initial_cols=2)
    qtbot.addWidget(grid)
    grid.set_matrix(Matrix([[1, 2, 5], [3, 4, 6]]))
    grid.resize_to(3, 4)
    assert grid.get_matrix() == Matrix([[1, 2, 0, 5], [3, 4, 0, 6], [0, 0, 0, 0]])


def test_paste_confirms_with_an_undoable_toast(qtbot):
    from prettycalc.ui.clipboard import copy_matrix_to_clipboard

    window = _window(qtbot)
    grid = window.linear_systems_view.matrix_grid
    copy_matrix_to_clipboard(Matrix([[1, 2, 3], [4, 5, 6]]))
    assert grid.paste_from_clipboard()
    assert "pegada" in last_toast_message(grid)
    assert grid.undo()
    assert grid.data_shape() == (2, 3)
    assert grid.get_matrix() == Matrix.zeros(2, 3)


def test_scalar_field_marks_errors_and_shows_decimal_hint(qtbot):
    field = ScalarField("3/2")
    scalar_input = ScalarInput(field, presets=(("−1", "-1", "opuesta"),))
    qtbot.addWidget(scalar_input)
    assert field.is_valid()
    assert scalar_input.hint_text() == "≈ 1.5"
    field.setText("2,5")
    assert not field.is_valid()
    assert field.property("invalid") is True
    assert "coma decimal" in scalar_input.hint_text()
    scalar_input.chip_buttons[0].click()
    assert field.text() == "-1"
    assert field.value() == Fraction(-1)


def test_carousel_jumps_and_flags_contradictions(qtbot):
    from prettycalc.core.elimination import gauss_jordan_elimination

    carousel = AlgorithmStepperCarousel(alert_mode=ALERT_SYSTEM)
    qtbot.addWidget(carousel)
    _rref, tracer = gauss_jordan_elimination(Matrix([[1, 2, 4], [2, 4, 9]]), split_col=2)
    carousel.set_steps(tracer.get_steps())
    alert = carousel.first_alert_index()
    assert alert is not None
    carousel.go_to_step(alert)
    assert "Contradicción en la fila 2: 0 = 1" in carousel.alert_label.text()
    assert 1 in carousel.matrix_view.alert_rows()
    carousel.go_to_step(0)
    qtbot.keyClick(carousel, Qt.Key_End)
    assert carousel.current_index() == len(carousel.steps()) - 1


def test_carousel_exports_text_latex_and_pdf(qtbot, tmp_path):
    from prettycalc.ui.export import steps_to_latex, steps_to_text
    from prettycalc.core.elimination import gauss_jordan_elimination

    _rref, tracer = gauss_jordan_elimination(Matrix([[1, 1, 2], [1, -1, 0]]), split_col=2)
    steps = tracer.get_steps()
    text = steps_to_text(steps, "Sistema")
    assert "Paso inicial" in text and "Paso 2" in text
    latex = steps_to_latex(steps, "Sistema")
    assert latex.startswith("\\documentclass") and "\\end{document}" in latex
    carousel = AlgorithmStepperCarousel()
    qtbot.addWidget(carousel)
    carousel.set_steps(steps)
    written = carousel.save_steps(str(tmp_path / "informe.pdf"))
    assert written and (tmp_path / "informe.pdf").read_bytes().startswith(b"%PDF")
    assert carousel.save_steps(str(tmp_path / "informe.html"))
    assert "<table class=\"matrix\">" in (tmp_path / "informe.html").read_text(encoding="utf-8")


def test_navigation_has_help_and_appearance_entries(qtbot):
    window = _window(qtbot)
    assert window.shortcuts_btn.toolTip().endswith("(F1)")
    assert "Ctrl+," in window.appearance_btn.toolTip()
    window.resize(1366, 768)
    qtbot.wait(20)
    texts = [button.text() for button in window.nav_bar.buttons]
    for button in window.nav_bar.buttons:
        assert button.fontMetrics().horizontalAdvance(button.text()) < button.width()
    assert len(texts) == 6


# ---------------------------------------------------------------------------
# Módulo 1: Sistemas lineales
# ---------------------------------------------------------------------------

def test_size_control_sets_dimensions_in_one_step(qtbot):
    view = _window(qtbot).linear_systems_view
    view.size_control.set_size(5, 5)
    assert view.matrix_grid.data_shape() == (5, 6)
    assert view.size_control.rows_spin.value() == 5
    view.matrix_grid.add_row()
    assert view.size_control.rows_spin.value() == 6


def test_reset_is_undoable(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_sample_case1()
    view.reset_matrix()
    assert view.matrix_grid.data_shape() == (2, 3)
    assert "se puede recuperar" in last_toast_message(view)
    view.undo_last_load()
    assert view.matrix_grid.data_shape() == (3, 4)


def test_preset_replacing_user_data_offers_undo(qtbot):
    view = _window(qtbot).linear_systems_view
    view.matrix_grid.cells[0][0].setText("7")
    view.load_sample_case3()
    assert view.active_preset == "case3"
    assert view.preset_buttons["case3"].isChecked()
    assert "Deshacer" == view.window()._prettycalc_toast.action_btn.text()
    view.undo_last_load()
    assert view.matrix_grid.cells[0][0].text() == "7"
    assert view.active_preset is None


def test_editing_clears_the_active_preset_marker(qtbot):
    view = _window(qtbot).linear_systems_view
    view.load_sample_case2()
    assert view.preset_buttons["case2"].isChecked()
    view.matrix_grid.cells[0][0].setText("5")
    assert view.active_preset is None
    assert not view.preset_buttons["case2"].isChecked()


def test_cramer_is_blocked_with_guidance_for_rectangular_systems(qtbot):
    view = _window(qtbot).linear_systems_view
    view.matrix_grid.set_matrix(Matrix([[1, 2, 3, 4], [0, 1, 2, 3]]))
    assert not view.cramer_method_btn.isEnabled()
    assert "Requiere matriz cuadrada" in view.cramer_method_btn.toolTip()
    view.matrix_grid.set_matrix(Matrix([[1, 2, 3], [0, 1, 2]]))
    view.cramer_method_btn.click()
    view.matrix_grid.resize_to(2, 4)
    assert view.method_hint.isVisibleTo(view)
    assert not view.solve_btn.isEnabled()
    view.make_system_square()
    assert view.matrix_grid.data_shape() == (3, 4)
    assert view.solve_btn.isEnabled()


def test_singular_cramer_offers_gauss_jordan(qtbot):
    view = _window(qtbot).linear_systems_view
    view.cramer_method_btn.click()
    view.matrix_grid.set_matrix(Matrix([[1, 2, 3], [2, 4, 6]]))
    view.solve_system()
    dashboard = view.dashboard_card
    assert dashboard.notice_action_btn.isVisibleTo(dashboard)
    dashboard.notice_action_btn.click()
    assert view._solver == "gauss"
    assert "indeterminado" in dashboard.status_badge.text().lower()


def test_inconsistent_dashboard_names_row_and_value(qtbot):
    view = _window(qtbot).linear_systems_view
    view.load_sample_case3()
    texts = " ".join(label.text() for label in view.dashboard_card.findChildren(QLabel))
    assert "0 = 1" in texts
    assert view.dashboard_card.copy_results_btn.isEnabled()


def test_leontief_grid_reports_column_sums(qtbot):
    view = _window(qtbot).linear_systems_view
    panel = view.applications_panel
    assert "cada columna suma 1" in panel.column_sums_label.text()
    panel.consumption_grid.cells[0][0].setText("0.5")
    assert "no suma 1" in panel.column_sums_label.text()


def test_custom_diet_and_network_are_editable(qtbot):
    view = _window(qtbot).linear_systems_view
    panel = view.applications_panel
    panel.diet_grid.set_matrix(Matrix([[1, 0, 2], [0, 1, 3]]))
    panel.solve_cambridge_diet()
    assert panel.last_nutrition is not None
    assert panel.last_nutrition.amounts == [2, 3]
    assert "Mezcla exacta de la dieta." in panel.result_label.text()
    panel.traffic_grid.set_matrix(Matrix([[1, -1, 0], [0, 1, 50]]))
    panel.solve_baltimore()
    assert panel.last_network is not None
    assert view.matrix_grid.get_matrix() == Matrix([[1, -1, 0], [0, 1, 50]])


# ---------------------------------------------------------------------------
# Módulo 2: Álgebra matricial
# ---------------------------------------------------------------------------

def _ops(qtbot):
    window = _window(qtbot)
    window.set_module(1)
    return window.matrix_operations_view


def test_single_compute_button(qtbot):
    view = _ops(qtbot)
    assert view.header_compute_btn is view.compute_btn


def test_inspector_badge_names_the_inspected_cell(qtbot):
    view = _ops(qtbot)
    view.load_compatible_product_sample()
    view._on_result_cell_clicked(1, 0)
    assert view.inspected_cell() == (1, 0)
    assert view.inspect_badge.text() == "Inspeccionando C₂,₁"
    view.grid_a.cells[0][0].setText("2")
    assert view.inspected_cell() is None


def test_fix_dimensions_shortcut_after_switching_to_sum(qtbot):
    view = _ops(qtbot)
    view.load_compatible_product_sample()
    view.add_btn.click()
    assert not view.compute_btn.isEnabled()
    assert view.fix_dims_btn.isVisibleTo(view)
    assert view.fix_dims_btn.text() == "Ajustar B a 2×3"
    view.fix_dims_btn.click()
    assert view.grid_b.data_shape() == (2, 3)
    assert view.compute_btn.isEnabled()


def test_scalar_field_shows_red_border_and_presets(qtbot):
    view = _ops(qtbot)
    view.scalar_mode_btn.click()
    view.scalar_edit.setText("abc")
    assert view.scalar_edit.property("invalid") is True
    assert not view.compute_btn.isEnabled()
    view.scalar_input.chip_buttons[0].click()
    view.grid_scalar.set_matrix(Matrix([[1, -2], [0, 3]]))
    view.compute()
    assert view._result == Matrix([[-1, 2], [0, -3]])
    assert "opuesta" in view.inspector_label.text()


def test_transpose_partner_b_is_visible_and_editable(qtbot):
    view = _ops(qtbot)
    view.transpose_mode_btn.click()
    view.grid_transpose.set_matrix(Matrix([[1, 2], [3, 4]]))
    view.include_b_btn.click()
    assert view.transpose_b_card.isVisibleTo(view)
    view.grid_transpose_b.set_matrix(Matrix([[1, 0], [0, 1]]))
    view.compute()
    text = view.properties_label.text()
    assert "(A + B)ᵀ = Aᵀ + Bᵀ" in text


def test_every_ternary_property_has_a_sample_and_intermediates(qtbot):
    view = _ops(qtbot)
    for loader, expected in (
        (view.load_distributive_matrix_sample, "B + C"),
        (view.load_distributive_right_sample, "A + B"),
        (view.load_associative_sample, "BC"),
    ):
        loader()
        steps = view.dist_stepper.steps()
        assert len(steps) >= 4
        assert expected in steps[0].latex_formula
        assert view.dist_lhs_view.matrix() == view.dist_rhs_view.matrix()


def test_singular_inverse_jumps_to_the_zero_row(qtbot):
    view = _ops(qtbot)
    view.load_singular_inverse_sample()
    assert view._result is None
    index = view.inverse_stepper.current_index()
    assert index > 0
    assert view.inverse_stepper.matrix_view.alert_rows()
    assert "Rango deficiente" in view.inverse_stepper.alert_label.text()
    assert f"paso {index + 1}" in view.inverse_check_label.text()


def test_reuse_inverse_checks_double_inverse(qtbot):
    view = _ops(qtbot)
    view.load_inverse_sample()
    original = view.grid_inverse.get_matrix()
    view.use_inverse_as_input()
    assert view.inverse_result_view.matrix() == original


def test_tmi_key_card_and_filters(qtbot):
    view = _ops(qtbot)
    view.load_tmi_singular_sample()
    assert view.tmi_key_card.isVisibleTo(view)
    assert "*c" in view.tmi_key_card.text()
    view.tmi_filter_buttons["key"].click()
    keyed = view.tmi_checklist.text()
    assert "*e" in keyed and "   a   " not in keyed
    view.tmi_filter_buttons["failed"].click()
    assert "Cumple " not in view.tmi_checklist.text().replace("No cumple", "")
    view.load_tmi_invertible_sample()
    assert "Todas las caracterizaciones se cumplen" in view.tmi_checklist.text()


def test_identities_show_both_sides_and_the_wrong_order(qtbot):
    view = _ops(qtbot)
    view.load_inverse_identities_sample()
    assert view.identity_compare_row.isVisibleTo(view)
    assert view.id_ab_inverse_view.matrix() == view.id_ba_product_view.matrix()
    assert view.id_wrong_order_view.matrix() != view.id_ab_inverse_view.matrix()
    assert view.id_wrong_connector.text() == "≠"
