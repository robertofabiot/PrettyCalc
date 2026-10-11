"""Interfaz de la factorización LU y las dos sustituciones."""

from fractions import Fraction

from PySide6.QtCore import Qt

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.theme import COLOR_FEEDBACK_ERROR, COLOR_FEEDBACK_SUCCESS


def test_lu_tab_is_the_sixth_module(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(5)
    assert window.module_stack.currentWidget() is window.lu_view
    assert "Factorización LU" in window.nav_bar.buttons[5].text()
    assert "Factorización LU" in window.subtitle_lbl.text()


def test_session12_example1_shows_factors_and_both_stages(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.set_module(5)
    view = window.lu_view
    view.load_example_1()

    assert view.last_factorization is not None
    assert view.last_factorization.L == Matrix([
        [1, 0, 0],
        [-1, 1, 0],
        [2, -5, 1],
    ])
    assert view.last_factorization.U == Matrix([
        [3, -7, -2],
        [0, -2, -1],
        [0, 0, -1],
    ])
    assert view.last_solution is not None
    assert view.last_solution.y_intermediate == Vector([-7, -2, 6])
    assert view.last_solution.x_solution == Vector([3, 4, -6])
    assert view.last_solution.verification_passed
    assert "L · U = A" in view.checklist_label.text()
    assert COLOR_FEEDBACK_SUCCESS in view.checklist_label.styleSheet()
    assert "A · x = b" in view.ax_label.text()
    assert COLOR_FEEDBACK_SUCCESS in view.ax_label.styleSheet()
    assert "y = [-7, -2, 6]ᵀ" in view.y_label.text()
    assert "x = [3, 4, -6]ᵀ" in view.x_label.text()
    assert "-1" in view.l_readout.text()
    assert view.factor_stepper._steps
    assert view.forward_stepper._steps
    assert view.backward_stepper._steps
    rendered_steps = view.forward_steps_label.text()
    assert "y<sub>1</sub> = b<sub>1</sub> = -7." in rendered_steps
    assert view.forward_steps_label.textFormat() == Qt.TextFormat.RichText
    assert view.solve_btn.isEnabled()


def test_session12_example2_four_by_four(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.lu_view
    view.load_example_2()

    assert view.last_solution is not None
    assert view.last_solution.y_intermediate == Vector([-9, -4, 5, 1])
    assert view.last_solution.x_solution == Vector([3, 4, -6, -1])
    assert "4 × 4" in view.shape_label.text()
    assert view.grid.get_matrix().shape == (4, 4)


def test_session12_rectangular_example_disables_the_unique_solve(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.lu_view
    view.load_example_3()

    assert view.last_factorization is not None
    assert view.last_factorization.is_valid
    assert view.last_factorization.U.shape == (4, 5)
    assert view.last_solution is None
    assert not view.solve_btn.isEnabled()
    assert "4×5" in view.badge.text()
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()
    assert any("no tiene pivote" in step.heuristic_text for step in view.factor_stepper._steps)


def test_zero_pivot_factors_with_a_permutation_matrix(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.lu_view
    view.grid.set_matrix(Matrix([
        [0, 1],
        [1, 1],
    ]))
    view.decompose()

    assert view.last_factorization is not None
    assert view.last_factorization.permutation_count == 1
    assert view.last_factorization.is_valid
    assert "P · A = L · U" in view.checklist_label.text()
    assert "permutación" in view.badge.text()
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()
    assert view.factor_stepper._steps
    assert view.solve_btn.isEnabled()


def test_singular_factorization_explains_the_missing_unique_solution(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.lu_view
    view.grid.set_matrix(Matrix([
        [1, 2],
        [2, 4],
    ]))
    view.decompose()

    assert view.last_factorization is not None
    assert view.last_factorization.is_valid
    assert "pivote diagonal nulo" in view.badge.text()
    assert COLOR_FEEDBACK_ERROR in view.badge.styleSheet()
    assert not view.solve_btn.isEnabled()


def test_second_load_reuses_the_same_factors(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.lu_view
    view.load_example_1()
    factors = view.last_factorization
    view.b_grid.set_matrix(Matrix([[0], [0], [0]]))
    assert view.last_solution is None
    assert view.last_factorization is factors

    view.solve()
    assert view.last_factorization is factors
    assert view.last_solution is not None
    assert view.last_solution.x_solution == Vector([Fraction(0), Fraction(0), Fraction(0)])
    assert view.last_solution.verification_passed
