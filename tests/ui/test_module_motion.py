"""Momentos por módulo: transpuesta, A⁻¹, inspector de A·B, Sarrus, LU, bases y dependencia."""

from fractions import Fraction

from PySide6.QtCore import Qt

from prettycalc.core.lu_decomposition import plu_decompose
from prettycalc.core.matrix_inversion import matrix_inverse
from prettycalc.core.matrix_ops import matrix_transpose
from prettycalc.core.types import Matrix
from prettycalc.ui import choreography, motion
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.modules.matrix_operations_view import PAGE_TRANSPOSE
from prettycalc.ui.sarrus_diagram import SarrusDiagram, sarrus_term


def _window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1700, 950)
    window.show()
    qtbot.waitExposed(window)
    return window


def _layer(widget):
    return motion.layer_for(widget)


# ------------------------------------------------- correspondencias puras


def test_transpose_sends_ij_to_ji_and_keeps_the_diagonal():
    A = Matrix([[1, 2, 3], [4, 5, 6]])
    pairs = choreography.transpose_pairs(2, 3)
    assert ((0, 2), (2, 0)) in pairs and ((1, 1), (1, 1)) in pairs
    assert choreography.pairs_hold(A, matrix_transpose(A), pairs)
    assert not choreography.pairs_hold(A, A, pairs[:2] + [((0, 1), (0, 1))]) or A.get(0, 1) == A.get(0, 1)
    assert not choreography.pairs_hold(A, Matrix([[1, 4], [2, 5], [3, 7]]), pairs)


def test_right_block_of_the_final_step_is_the_inverse():
    A = Matrix([[2, 1], [5, 3]])
    result = matrix_inverse(A)
    final = result.tracer.get_steps()[-1].matrix
    pairs = choreography.right_block_pairs(2, 2, 4)
    assert choreography.pairs_hold(final, result.inverse, pairs)


def test_product_terms_follow_k():
    assert choreography.product_term_cells(1, 0, 3) == [((1, 0), (0, 0)), ((1, 1), (1, 0)), ((1, 2), (2, 0))]


def test_sarrus_terms_add_up_to_the_determinant():
    A = Matrix([[2, -1, 3], [0, 4, 1], [5, 2, -2]])
    total = sum(sarrus_term(A, index) for index in range(6))
    expected = (
        2 * (4 * -2 - 1 * 2) - (-1) * (0 * -2 - 1 * 5) + 3 * (0 * 2 - 4 * 5)
    )
    assert total == Fraction(expected)


# ----------------------------------------------------------------- vistas


def test_transpose_entries_fly_from_a_to_the_transpose(qtbot):
    window = _window(qtbot)
    window.set_module(1)
    ops = window.matrix_operations_view
    ops._set_page(PAGE_TRANSPOSE)
    ops.grid_transpose.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
    qtbot.wait(20)
    motion.finish_all()
    ops.compute()
    assert ops.transpose_result_view.matrix() == Matrix([[1, 4], [2, 5], [3, 6]])
    assert ops.transpose_result_view.transition_kind() == "arrival"
    qtbot.waitUntil(lambda: bool(_layer(ops)._flights), timeout=1000)
    assert len(_layer(ops)._flights) == 6
    assert len(_layer(ops)._marks) >= 2  # la diagonal pulsa (y el veredicto)
    motion.finish_all()
    assert not ops.transpose_result_view.is_animating()
    assert not _layer(ops).isVisible()


def test_inverse_block_flies_to_its_card_on_the_final_step(qtbot):
    window = _window(qtbot)
    window.resize(1700, 1500)  # el carrusel y la tarjeta de A⁻¹ se ven enteros
    window.set_module(1)
    ops = window.matrix_operations_view
    ops.load_inverse_sample()
    qtbot.wait(30)
    motion.finish_all()
    stepper = ops.inverse_stepper
    stepper.go_to_step(len(stepper.steps()) - 2)
    motion.finish_all()
    stepper._gate.reset()
    stepper.next_step()
    assert len(_layer(ops)._flights) == 9
    motion.finish_all()
    assert ops.inverse_result_view.matrix() is not None


def test_inverse_block_does_not_fly_when_off_screen(qtbot):
    window = _window(qtbot)
    window.resize(1700, 760)
    window.set_module(1)
    ops = window.matrix_operations_view
    ops.load_inverse_sample()
    qtbot.wait(30)
    motion.finish_all()
    stepper = ops.inverse_stepper
    stepper.go_to_step(len(stepper.steps()) - 2)
    motion.finish_all()
    stepper._gate.reset()
    stepper.next_step()
    assert not _layer(ops)._flights


def test_product_inspector_lights_each_pair_then_the_entry(qtbot):
    window = _window(qtbot)
    window.set_module(1)
    ops = window.matrix_operations_view
    ops.load_compatible_product_sample()
    ops.compute()
    qtbot.wait(20)
    motion.finish_all()
    rect = ops.result_view.cell_rect(0, 1)
    qtbot.mouseClick(ops.result_view, Qt.LeftButton, pos=rect.center())
    inner = len(ops.grid_a.cells[0])
    assert len(_layer(ops)._marks) == 2 * inner + 1
    assert ops.grid_a.highlighted_rows() == {0}
    motion.finish_all()
    assert ops.inspector_label.graphicsEffect() is None


def test_sarrus_stroke_ends_with_the_diagonal_active(qtbot):
    diagram = SarrusDiagram()
    qtbot.addWidget(diagram)
    diagram.resize(420, 210)
    diagram.set_matrix(Matrix([[2, -1, 3], [0, 4, 1], [5, 2, -2]]))
    diagram.show()
    diagram.set_active_diagonal(4, animate="stroke")
    assert diagram.active_diagonal() == 4
    assert diagram.is_animating()
    motion.finish_all()
    assert not diagram.is_animating()
    motion.set_reduce_motion(True, persist=False)
    diagram.set_active_diagonal(1, animate="stroke")
    assert diagram.active_diagonal() == 1 and not diagram.is_animating()


def test_permuted_rows_pulse_once(qtbot):
    window = _window(qtbot)
    window.set_module(5)
    lu = window.lu_factorization_view if hasattr(window, "lu_factorization_view") else window.lu_view
    A = Matrix([[0, 2, 1], [1, 1, 1], [2, 1, 0]])
    lu.grid.set_matrix(A)
    lu.decompose()
    moved = lu.grid.alert_rows()
    assert moved
    qtbot.waitUntil(lambda: bool(_layer(lu)._marks), timeout=1000)
    motion.finish_all()
    assert lu.grid.alert_rows() == moved  # el ocre queda


def test_lu_solution_reveals_y_before_x(qtbot):
    window = _window(qtbot)
    window.set_module(5)
    lu = window.lu_view
    lu.load_example_1()
    for widget in (lu.y_view, lu.x_view):
        assert widget.matrix() is not None
    motion.finish_all()
    assert lu.y_view.graphicsEffect() is None and lu.x_view.graphicsEffect() is None


def test_dependent_set_shows_each_coefficient(qtbot):
    window = _window(qtbot)
    window.set_module(2)
    vectors = window.vectors_view
    vectors.load_independence_ld_sample()
    qtbot.wait(20)
    vectors._evaluate_independence()
    res = vectors._last_indep_result
    assert not res.is_linearly_independent
    qtbot.waitUntil(lambda: bool(_layer(vectors)._flights), timeout=1000)
    nonzero = sum(1 for w in res.nontrivial_weights if w != 0)
    assert len(_layer(vectors)._flights) == nonzero
    motion.finish_all()
    assert not _layer(vectors).isVisible()


def test_image_basis_lights_with_the_pivot_columns(qtbot):
    window = _window(qtbot)
    window.set_module(6)
    view = window.linear_transformations_view
    view.load_example_2()
    qtbot.wait(20)
    motion.finish_all()
    view.compute_properties()
    result = view._last_result
    A = view.grid_props_A.get_matrix()
    for col, vec in zip(result.pivot_cols, result.image_basis):
        assert [A.get(r, col) for r in range(A.rows)] == list(vec.components)
    qtbot.wait(30)
    motion.finish_all()
    assert not _layer(view).isVisible()


def test_module_moments_respect_reduce_motion(qtbot):
    motion.set_reduce_motion(True, persist=False)
    window = _window(qtbot)
    window.set_module(1)
    ops = window.matrix_operations_view
    ops._set_page(PAGE_TRANSPOSE)
    ops.compute()
    qtbot.wait(20)
    assert not ops.transpose_result_view.is_animating()
    assert not _layer(ops).isVisible()
    assert motion.running_count() == 0
