from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

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


def test_vector_checks_stay_large_and_module_can_scroll(qtbot):
    from PySide6.QtWidgets import QLabel, QScrollArea

    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(980, 420)
    window.show()
    window.set_module(2)
    view = window.vectors_view
    view.load_combination_scd_sample()
    qtbot.wait(30)

    checks = [lbl for lbl in view.findChildren(QLabel) if "componente" in lbl.text()]
    assert checks
    for lbl in checks:
        assert "24px" in lbl.styleSheet()

    page = view.tabs.currentWidget()
    scroll = page.findChild(QScrollArea)
    assert scroll is not None
    assert scroll.widgetResizable() is True


def test_matrix_transpose_mode_updates_shape_and_properties(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view
    view.transpose_mode_btn.click()
    view.grid_transpose.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
    view.identity_scalar_edit.setText("2")
    view.compute()

    assert view.compute_btn.isEnabled()
    assert view._result == Matrix([[1, 4], [2, 5], [3, 6]])
    assert "Aᵀ es 3×2" in view.badge.text()
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()
    text = view.properties_label.text()
    assert "rectangular" in text
    assert "(Aᵀ)ᵀ = A" in text
    assert "No aplica: la matriz no es cuadrada." in text


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


def test_vectors_independence_li_sample(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(2)
    view = window.vectors_view
    view.load_independence_li_sample()
    assert "INDEPENDIENTE (L.I.)" in view.indep_badge.text()
    assert COLOR_FEEDBACK_SUCCESS in view.indep_badge.styleSheet()
    assert "k = 3 en ℝ^3" in view.indep_summary.text()
    assert "solución trivial" in view.indep_summary.text()


def test_vectors_independence_ld_sample(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(2)
    view = window.vectors_view
    view.load_independence_ld_sample()
    assert "DEPENDIENTE (L.D.)" in view.indep_badge.text()
    assert COLOR_FEEDBACK_ERROR in view.indep_badge.styleSheet()
    assert "infinitas soluciones no triviales" in view.indep_summary.text()
    assert view.indep_checklist.count() > 0


def test_vectors_independence_dim_sample(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(2)
    view = window.vectors_view
    view.load_independence_dim_sample()
    assert "DEPENDIENTE (L.D.)" in view.indep_badge.text()
    assert "k = 4 > n = 3" in view.indep_summary.text()


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


def test_matrix_equations_scroll_and_tabs(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)
    view = window.matrix_equations_view

    # Verify scroll area exists and is resizable
    assert hasattr(view, "scroll_area")
    assert view.scroll_area.widgetResizable() is True

    # Verify tab widget has 2 tabs
    assert hasattr(view, "results_tabs")
    assert view.results_tabs.count() == 2
    assert "Comprobación" in view.results_tabs.tabText(0)
    assert "Procedimiento" in view.results_tabs.tabText(1)

    # Test tab switching
    view.results_tabs.setCurrentIndex(1)
    assert view.results_tabs.currentIndex() == 1
    view.results_tabs.setCurrentIndex(0)
    assert view.results_tabs.currentIndex() == 0


def test_matrix_equations_samples_and_reset(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)
    view = window.matrix_equations_view

    # Test SCI sample (Infinitas soluciones)
    view.load_sample_sci()
    assert "indeterminado" in view.dashboard.status_badge.text().lower() or "infinitas" in view.dashboard.status_badge.text().lower()

    # Test SI sample (Sin solución / inconsistente)
    view.load_sample_si()
    assert "inconsistente" in view.dashboard.status_badge.text().lower() or "sin solución" in view.dashboard.status_badge.text().lower()
    assert "No hay vector x" in view.product_label.text()

    # Test Reset
    view.reset()
    assert view.grid_a.data_shape() == (3, 3)
    assert view.vec_b.grid.num_rows == 3
    assert view.results_tabs.currentIndex() == 0


def test_matrix_operations_transpose_and_double_transpose(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view

    view.transpose_mode_btn.click()
    assert view._is_transpose_mode() is True

    from prettycalc.core.types import Matrix
    mat_a = Matrix([[1, 2, 3], [4, 5, 6]])
    view.grid_transpose.set_matrix(mat_a)
    view.compute()

    # Transpose result must be 3x2
    assert view.transpose_result_view.matrix() == Matrix([[1, 4], [2, 5], [3, 6]])
    # Double transpose result must equal original A (2x3)
    assert view.double_transpose_result_view.matrix() == mat_a
    assert "(Aᵀ)ᵀ = A" in view.inspector_label.text()
    assert "(Aᵀ)ᵀ = A" in view.properties_label.text()
    assert "font-size:22px" in view.properties_label.text()


def test_matrix_operations_distributive_left_and_right_and_assoc(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view

    # 1. Left distributive: A(B + C) = AB + AC
    view.load_distributive_matrix_sample()
    assert view._is_distributive_mode() is True
    assert view.dist_lhs_view.matrix() is not None
    assert view.dist_rhs_view.matrix() is not None
    assert view.dist_lhs_view.matrix() == view.dist_rhs_view.matrix()
    assert "A · (B + C)" in view.dist_comparison_label.text()
    assert "22px" in view.dist_comparison_label.text()
    assert "Distributiva izquierda" in view.dist_comparison_label.text()

    # 2. Right distributive: (A + B)C = AC + BC
    view.dist_right_btn.click()
    view.compute()
    assert view.dist_lhs_view.matrix() == view.dist_rhs_view.matrix()
    assert "(A + B) · C" in view.dist_comparison_label.text()
    assert "22px" in view.dist_comparison_label.text()
    assert "Distributiva derecha" in view.dist_comparison_label.text()

    # 3. Associative: A(BC) = (AB)C
    view.dist_assoc_btn.click()
    view.compute()
    assert view.dist_lhs_view.matrix() == view.dist_rhs_view.matrix()
    assert "A · (B · C)" in view.dist_comparison_label.text()
    assert "22px" in view.dist_comparison_label.text()
    assert "Asociativa" in view.dist_comparison_label.text()


def test_matrix_operations_distributive_incompatible(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view

    view.load_distributive_matrix_sample()
    from prettycalc.core.types import Matrix
    # Set C with incompatible dimension (3x2 instead of 2x2 for B+C)
    view.grid_dist_c.set_matrix(Matrix([[1, 2], [3, 4], [5, 6]]))
    ok, msg = view._compatibility_state()
    assert ok is False
    assert "incompatibles" in msg.lower()
    assert view.compute_btn.isEnabled() is False


def test_all_verification_font_sizes_are_large_and_rich(qtbot):
    """Verifica que las comprobaciones nunca se muestren en chiquito (≥22px) ni en texto plano."""
    window = MainWindow()
    qtbot.addWidget(window)

    # 1. SEL Module (Dashboard)
    window.set_module(0)
    window.linear_systems_view.load_sample_case1()
    dash = window.linear_systems_view.dashboard_card
    assert dash.checklist_container.count() > 0
    first_check = dash.checklist_container.itemAt(0).widget()
    labels = first_check.findChildren(QLabel)
    assert any("22px" in lbl.text() or "24px" in lbl.text() for lbl in labels)

    # 2. Vectors View (Linear combination checklist)
    window.set_module(2)
    window.vectors_view.load_combination_scd_sample()
    assert window.vectors_view.combo_checklist.count() > 0
    row_label = window.vectors_view.combo_checklist.itemAt(0).widget()
    assert "font-size: 24px" in row_label.styleSheet()

    # 3. Matrix Equations View (A x = b checklist)
    window.set_module(3)
    window.matrix_equations_view.load_sample()
    eq_lbl = window.matrix_equations_view.product_label
    assert eq_lbl.textFormat() == Qt.RichText
    assert "22px" in eq_lbl.text()

    # 4. Matrix-Vector Properties View (A(u+v) checklist and steps)
    prop_view = window.matrix_equations_view.properties_view
    prop_view.load_distributive_sample()
    assert prop_view.checklist_label.textFormat() == Qt.RichText
    assert "22px" in prop_view.checklist_label.text()
    assert prop_view.steps_text.textFormat() == Qt.RichText



