"""Formularios de química, Leontief, dieta y tráfico en Sistemas Lineales."""

from fractions import Fraction

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.theme import COLOR_ACCENT_WARNING, COLOR_FEEDBACK_ERROR, COLOR_FEEDBACK_SUCCESS


def _panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    view = window.linear_systems_view
    return view, view.applications_panel


def test_chemical_form_balances_propane_and_loads_the_matrix(qtbot):
    view, panel = _panel(qtbot)
    assert not panel.isVisible()
    view.applications_toggle.click()
    assert panel.isVisible()
    panel.balance_btn.click()

    assert panel.last_chemical is not None
    assert panel.last_chemical.stoichiometric_coefficients == [1, 5, 3, 4]
    assert "1" in panel.result_label.text()
    assert "C3H8" in panel.result_label.text()
    assert COLOR_ACCENT_WARNING in panel.result_label.text()
    assert COLOR_FEEDBACK_SUCCESS in panel.result_label.styleSheet()
    assert view.matrix_grid.get_matrix() == Matrix([
        [3, 0, -1, 0, 0],
        [8, 0, 0, -2, 0],
        [0, 2, -2, -1, 0],
    ])
    assert view.last_applied is panel.last_chemical
    assert view.stepper_carousel._steps
    assert "enteros positivos mínimos" in view.stepper_carousel._steps[-1].heuristic_text


def test_invalid_formula_stays_on_the_panel(qtbot):
    view, panel = _panel(qtbot)
    panel.reactants_edit.setText("2H2")
    panel.products_edit.setText("H2O")
    panel.balance_btn.click()

    assert panel.last_chemical is None
    assert "coeficiente" in panel.result_label.text()
    assert COLOR_FEEDBACK_ERROR in panel.result_label.styleSheet()
    assert view.last_applied is None


def test_leontief_example_shows_exact_relative_prices(qtbot):
    view, panel = _panel(qtbot)
    panel.show_mode(1)
    panel.leontief_example_btn.click()

    assert panel.last_leontief is not None
    assert panel.last_leontief.equilibrium_price_vector == Vector([
        Fraction(31, 33), Fraction(28, 33), 1,
    ])
    assert "31/33" in panel.result_label.text()
    assert "0.94" in panel.result_label.text()
    assert view.matrix_grid.get_matrix().shape == (3, 4)
    assert view.dashboard_card.parametric_solution is not None


def test_cambridge_diet_reports_the_slide_grams(qtbot):
    view, panel = _panel(qtbot)
    panel.show_mode(2)
    panel.diet_btn.click()

    assert panel.last_nutrition is not None
    assert panel.last_nutrition.is_feasible
    assert "27.7 g" in panel.result_label.text()
    assert "39.2 g" in panel.result_label.text()
    assert "23.3 g" in panel.result_label.text()
    assert view.matrix_grid.get_matrix().shape == (3, 4)
    assert COLOR_FEEDBACK_SUCCESS in panel.result_label.styleSheet()


def test_baltimore_panel_lists_the_one_way_ranges(qtbot):
    view, panel = _panel(qtbot)
    panel.show_mode(3)
    panel.traffic_btn.click()

    assert panel.last_network is not None
    assert panel.last_network.parameter_range == (Fraction(0), Fraction(500))
    assert "x5 ∈ [0, 500]" in panel.result_label.text()
    assert "x1 ∈ [100, 600]" in panel.result_label.text()
    assert view.matrix_grid.get_matrix() == panel.last_network.augmented_matrix
    assert view._solver == "gauss"
