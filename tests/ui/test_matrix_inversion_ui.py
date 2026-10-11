"""Interfaz de la inversa A⁻¹ y de la forma vectorial paramétrica."""

from fractions import Fraction

from PySide6.QtWidgets import QLabel, QWidget

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.theme import COLOR_FEEDBACK_ERROR, COLOR_FEEDBACK_SUCCESS


def _labels_text(root: QWidget) -> str:
    return " ".join(label.text() for label in root.findChildren(QLabel))


def test_inverse_sample_shows_inverse_and_identity_check(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view
    view.load_inverse_sample()

    assert view.pages.currentIndex() == 4
    assert view.compute_btn.isEnabled()
    assert view._result == Matrix([
        [Fraction(-9, 2), 7, Fraction(-3, 2)],
        [-2, 4, -1],
        [Fraction(3, 2), -2, Fraction(1, 2)],
    ])
    assert "A · A⁻¹ = I_3" in view.inverse_check_label.text()
    assert "A⁻¹ · A = I_3" in view.inverse_check_label.text()
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()
    assert view.inverse_stepper._steps
    assert view.inverse_stepper._steps[0].split_col == 3
    assert "I_n" in view.inverse_stepper._steps[0].latex_formula


def test_inverse_nonsquare_disables_compute(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view
    view.inverse_mode_btn.click()
    view.grid_inverse.set_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))

    assert view.pages.currentIndex() == 4
    assert not view.compute_btn.isEnabled()
    assert not view.header_compute_btn.isEnabled()
    assert "cuadradas" in view.badge.text()
    assert "n×n" in view.badge.text()
    assert COLOR_FEEDBACK_ERROR in view.badge.styleSheet()


def test_inverse_singular_renders_error_badge(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(1)
    view = window.matrix_operations_view
    view.inverse_mode_btn.click()
    view.grid_inverse.set_matrix(Matrix([
        [2, 3, 4],
        [2, 3, 4],
        [2, 3, 4],
    ]))
    view.compute()

    assert "singular" in view.badge.text().lower()
    assert "Teorema de la Matriz Invertible" in view.badge.text()
    assert COLOR_FEEDBACK_ERROR in view.badge.styleSheet()
    assert view._result is None
    assert view.inverse_stepper._steps
    assert "singular" in view.inverse_check_label.text().lower()


def test_sci_dashboard_renders_parametric_column_vectors(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.linear_systems_view
    view.matrix_grid.set_matrix(Matrix([
        [3, 5, -4, 0],
        [-3, -2, 4, 0],
        [6, 1, -8, 0],
    ]))
    view.solve_system()

    dashboard = view.dashboard_card
    solution = dashboard.parametric_solution
    assert solution is not None
    assert solution.particular_vector == Vector([0, 0, 0])
    assert solution.null_basis_vectors[2] == Vector([Fraction(4, 3), 0, 1])
    text = _labels_text(dashboard)
    assert "Forma vectorial paramétrica" in text
    assert "4/3" in text
    assert "particular p" in text
    assert dashboard.findChild(QWidget, "parametricVectorForm") is not None


def test_determined_system_does_not_show_parametric_form(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_sample_case1()

    dashboard = window.dashboard_card
    assert dashboard.parametric_solution is None
    assert "Forma vectorial paramétrica" not in _labels_text(dashboard)
