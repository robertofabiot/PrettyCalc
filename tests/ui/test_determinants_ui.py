"""Interfaz de determinantes, adjunta y Regla de Cramer."""

from fractions import Fraction

from PySide6.QtWidgets import QLabel

from prettycalc.core.determinants import DeterminantMethod
from prettycalc.core.types import Matrix
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.theme import COLOR_FEEDBACK_ERROR, COLOR_FEEDBACK_SUCCESS


def _session11() -> Matrix:
    return Matrix([
        [1, 3, -3],
        [2, 0, 1],
        [-1, 4, -2],
    ])


def _labels_text(root) -> str:
    return " ".join(label.text() for label in root.findChildren(QLabel))


def test_determinants_tab_is_the_fifth_module(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(4)
    assert window.module_stack.currentWidget() is window.determinants_view
    assert "Determinantes" in window.nav_bar.buttons[4].text()


def test_session11_example_shows_cofactors_and_adjugate(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.set_module(4)
    view = window.determinants_view
    view.load_session11_example()

    assert view.last_determinant is not None
    assert view.last_determinant.value == Fraction(-19)
    assert view.last_adjugate is not None
    assert view.last_adjugate.det_A == Fraction(-19)
    assert view.last_adjugate.cofactors_matrix == Matrix([
        [-4, 3, 8],
        [-6, -5, -7],
        [3, -7, -6],
    ])
    assert view.last_adjugate.adjugate_matrix == Matrix([
        [-4, -6, 3],
        [3, -5, -7],
        [8, -7, -6],
    ])
    assert view.last_adjugate.inverse_via_adjugate is not None
    assert view.adjugate_section.isVisible()
    assert "det(A) = -19" in view.det_value_label.text()
    assert "-4" in view.cofactors_readout.text()
    assert "-6" in view.adjugate_readout.text()
    assert "4/19" in view.inverse_readout.text()
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()
    assert view.stepper._steps


def test_sarrus_example_and_rejection_on_2x2(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(4)
    view = window.determinants_view
    view.load_sarrus_example()
    assert view.last_determinant is not None
    assert view.last_determinant.method is DeterminantMethod.SARRUS_3X3
    assert view.last_determinant.value == Fraction(36)

    view.grid.set_matrix(Matrix.identity(2))
    view.sarrus_mode_btn.click()
    assert not view.compute_btn.isEnabled()
    assert "3×3" in view.badge.text()
    assert COLOR_FEEDBACK_ERROR in view.badge.styleSheet()


def test_laplace_column_matches_triangulation(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.set_module(4)
    view = window.determinants_view
    view.grid.set_matrix(_session11())
    view.triangulation_mode_btn.click()
    view.compute()
    assert view.last_determinant is not None
    assert view.last_determinant.method is DeterminantMethod.TRIANGULATION
    assert view.last_determinant.value == Fraction(-19)
    assert view.stepper._steps[-1].matrix is not None

    view.laplace_mode_btn.click()
    view.laplace_col_btn.click()
    view.expansion_index.setValue(3)
    view.compute()
    assert view.last_determinant.method is DeterminantMethod.LAPLACE_COL
    assert view.last_determinant.value == Fraction(-19)
    assert view.laplace_box.isVisible()


def test_singular_determinant_uses_error_badge(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(4)
    view = window.determinants_view
    view.triangulation_mode_btn.click()
    view.grid.set_matrix(Matrix([[1, 2], [2, 4]]))
    view.compute()
    assert view.last_determinant is not None
    assert view.last_determinant.is_singular is True
    assert "det(A) = 0" in view.det_value_label.text()
    assert "singular" in view.badge.text().lower()
    assert COLOR_FEEDBACK_ERROR in view.badge.styleSheet()


def test_cramer_sample_shows_column_quotients(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.linear_systems_view
    view.load_cramer_sample()

    assert view._solver == "cramer"
    assert view.last_cramer is not None
    assert view.last_cramer.det_A == Fraction(6)
    assert view.last_cramer.solution == [Fraction(4), Fraction(-2), Fraction(3)]
    dashboard = view.dashboard_card
    assert dashboard.cramer_result is view.last_cramer
    text = _labels_text(dashboard)
    assert "det(A) = 6" in text
    assert "24 / 6 = 4" in text
    assert "-12 / 6 = -2" in text
    assert "18 / 6 = 3" in text
    assert dashboard.findChild(QLabel, "cramerComponent0") is not None
    assert view.stepper_carousel._steps


def test_cramer_plan_2x2_from_the_grid(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.linear_systems_view
    view.cramer_method_btn.click()
    view.matrix_grid.set_matrix(Matrix([
        [3, -2, 7],
        [2, 5, 11],
    ]))
    view.solve_system()
    assert view.last_cramer is not None
    assert view.last_cramer.solution == [Fraction(3), Fraction(1)]
    assert "57 / 19 = 3" in _labels_text(view.dashboard_card)


def test_cramer_singular_and_nonsquare_do_not_crash(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    view = window.linear_systems_view
    view.cramer_method_btn.click()
    view.matrix_grid.set_matrix(Matrix([
        [1, 2, 3],
        [2, 4, 6],
    ]))
    view.solve_system()
    assert view.last_cramer is None
    singular_text = _labels_text(view.dashboard_card)
    assert "det(A) = 0" in singular_text
    assert COLOR_FEEDBACK_ERROR in view.dashboard_card.status_badge.styleSheet()

    view.matrix_grid.set_matrix(Matrix([
        [1, 2, 3, 4],
        [0, 1, 2, 3],
    ]))
    view.solve_system()
    assert view.last_cramer is None
    assert "n×n" in _labels_text(view.dashboard_card)
