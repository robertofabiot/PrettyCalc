"""Sprint 10: Módulo 4 (A · x = b y propiedades de A · x) al estándar 10/10."""

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.feedback import last_toast_message, toast_for
from prettycalc.ui.modules.matrix_equations_view import MatrixEquationsView
from prettycalc.ui.modules.matrix_vector_properties_view import MatrixVectorPropertiesView


def _equations(qtbot):
    view = MatrixEquationsView()
    qtbot.addWidget(view)
    return view


def _properties(qtbot):
    view = MatrixVectorPropertiesView()
    qtbot.addWidget(view)
    return view


def test_single_primary_action_for_solving(qtbot):
    view = _equations(qtbot)
    assert view.header_solve_btn is view.solve_btn


def test_sci_marks_x_as_particular_solution(qtbot):
    view = _equations(qtbot)
    view.load_sample_sci()
    assert not view.x_badge.isHidden()
    assert "Solución particular" in view.x_badge.text()
    assert "x₂" in view.x_badge.text() and "x₃" in view.x_badge.text()
    assert view.x_view.highlight_cells() == ((1, 0), (2, 0))
    assert "x₁ = 4 − 2x₂ + x₃" in view.x_badge.toolTip()

    view.load_sample()
    assert view.x_badge.isHidden()
    assert "única" in view.x_subtitle.text()


def test_si_names_the_contradictory_row(qtbot):
    view = _equations(qtbot)
    view.load_sample_si()
    assert "No hay vector x" in view.product_label.text()
    assert "0 = " in view.product_label.text() and "imposible" in view.product_label.text()


def test_make_square_is_offered_for_rectangular_a_and_can_be_undone(qtbot):
    view = _equations(qtbot)
    view.size_control.set_size(2, 4)
    assert not view.make_square_btn.isHidden()
    view.make_square()
    assert view.grid_a.data_shape() == (4, 4)
    assert view.vec_b.grid.num_rows == 4
    assert view.make_square_btn.isHidden()
    toast_for(view).action_btn.click()
    assert view.grid_a.data_shape() == (2, 4)


def test_invalid_cells_are_explained_inline(qtbot):
    view = _equations(qtbot)
    view.grid_a.cells[1][2].setText("3/0")
    assert not view.solve_btn.isEnabled()
    assert view.badge.text().startswith("✕ A, fila 2, columna 3")
    view.grid_a.cells[1][2].setText("3")
    view.vec_b.grid.cells[0][0].setText("2,5")
    assert "b, componente 1" in view.badge.text()


def test_b_mismatch_offers_a_fix(qtbot):
    view = _equations(qtbot)
    view.vec_b.set_vector(Vector([1, 2]))
    assert not view.solve_btn.isEnabled()
    assert not view.fix_b_btn.isHidden()
    view.fix_b_btn.click()
    assert view.vec_b.grid.num_rows == 3
    assert view.solve_btn.isEnabled()


def test_editing_after_solving_marks_result_stale(qtbot):
    view = _equations(qtbot)
    view.load_sample()
    view.vec_b.grid.cells[0][0].setText("9")
    assert view.x_view.matrix() is None
    assert "vuelve a resolver" in view.x_subtitle.text()


def test_reset_can_be_undone(qtbot):
    view = _equations(qtbot)
    view.load_sample()
    view.reset()
    assert "restablecieron" in last_toast_message(view)
    toast_for(view).action_btn.click()
    assert view.grid_a.get_matrix() == Matrix([[1, 1, 1], [2, -1, 1], [1, 2, -1]])
    assert view.vec_b.get_vector() == Vector([4, 4, 3])


def test_linked_dimensions_follow_the_columns_of_a(qtbot):
    view = _properties(qtbot)
    assert view.link_dims_chk.isChecked()
    view.spin_n.setValue(5)
    assert view.vec_u_dist.grid.num_rows == 5
    assert view.vec_v_dist.grid.num_rows == 5
    assert view.vec_u_homo.grid.num_rows == 5
    assert view.verify_btn.isEnabled()

    view.link_dims_chk.setChecked(False)
    view.spin_n.setValue(2)
    assert view.vec_u_dist.grid.num_rows == 5
    assert not view.verify_btn.isEnabled()
    assert not view.sync_btn.isHidden()
    view.link_dims_chk.setChecked(True)
    assert view.vec_u_dist.grid.num_rows == 2


def test_rhs_reads_in_one_row(qtbot):
    view = _properties(qtbot)
    view.load_distributive_sample()
    assert view.rhs_view1.matrix() is not None and view.rhs_view2.matrix() is not None
    assert view.rhs_view2_box.parentWidget() is view.rhs_final_view.parentWidget().parentWidget()


def test_scalar_c_shows_decimal_hint_and_chips(qtbot):
    view = _properties(qtbot)
    view.btn_mode_homo.click()
    view.input_c.setText("3/2")
    assert view.input_c_widget.hint_text() == "≈ 1.5"
    view.input_c.setText("2/0")
    assert not view.verify_btn.isEnabled()
    assert "Escalar c" in view.badge.text()


def test_c_zero_is_explained(qtbot):
    view = _properties(qtbot)
    view.btn_mode_homo.click()
    view.input_c.setText("0")
    assert not view.c_zero_note.isHidden()
    view.load_zero_scalar_sample()
    assert not view.zero_note.isHidden()
    assert "vector nulo" in view.zero_note.text()
    assert "HOMOGENEIDAD DEMOSTRADA" in view.equality_banner.text()


def test_properties_result_goes_stale_after_edit(qtbot):
    view = _properties(qtbot)
    view.load_distributive_sample()
    view.vec_u_dist.grid.cells[0][0].setText("7")
    assert "vuelve a verificar" in view.equality_banner.text()
    assert view.lhs_final_view.matrix() is None


def test_properties_reset_can_be_undone(qtbot):
    view = _properties(qtbot)
    view.load_distributive_sample()
    view.reset()
    toast_for(view).action_btn.click()
    assert view.grid_a.get_matrix() == Matrix([[2, -1, 3], [1, 0, -2]])
    assert view.vec_u_dist.get_vector() == Vector([1, 2, -1])
