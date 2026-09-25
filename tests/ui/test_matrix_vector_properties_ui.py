"""Pruebas de interfaz para la vista de propiedades del producto matriz-vector A · x."""

from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.theme import COLOR_FEEDBACK_ERROR, COLOR_FEEDBACK_SUCCESS
from prettycalc.core.types import Matrix, Vector


def test_properties_tab_exists_in_matrix_equations_view(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    eq_view = window.matrix_equations_view
    assert hasattr(eq_view, "tabs")
    assert eq_view.tabs.count() == 2
    assert "Ecuación" in eq_view.tabs.tabText(0)
    assert "Propiedades" in eq_view.tabs.tabText(1)
    assert hasattr(eq_view, "properties_view")


def test_distributive_sample_verifies_and_displays(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    prop_view = window.matrix_equations_view.properties_view
    window.matrix_equations_view.tabs.setCurrentIndex(1)

    prop_view.load_distributive_sample()

    assert prop_view._last_distributive_result is not None
    assert prop_view._last_distributive_result.is_equal is True
    assert prop_view.verify_btn.isEnabled() is True

    # Comprobación de textos en la interfaz
    banner_text = prop_view.equality_banner.text()
    assert "DISTRIBUTIVA DEMOSTRADA" in banner_text
    assert COLOR_FEEDBACK_SUCCESS in prop_view.equality_banner.styleSheet()

    chk_text = prop_view.checklist_label.text()
    assert "Componente 1" in chk_text
    assert "Componente 2" in chk_text

    steps = prop_view.steps_text.text()
    assert "PROPIEDAD DISTRIBUTIVA" in steps
    assert "LADO IZQUIERDO" in steps
    assert "LADO DERECHO" in steps


def test_homogeneity_sample_verifies_and_displays(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    prop_view = window.matrix_equations_view.properties_view
    window.matrix_equations_view.tabs.setCurrentIndex(1)

    prop_view.load_homogeneity_sample()

    assert prop_view._mode == "homogeneity"
    assert prop_view._last_homogeneity_result is not None
    assert prop_view._last_homogeneity_result.is_equal is True
    assert prop_view.verify_btn.isEnabled() is True

    banner_text = prop_view.equality_banner.text()
    assert "HOMOGENEIDAD DEMOSTRADA" in banner_text
    assert COLOR_FEEDBACK_SUCCESS in prop_view.equality_banner.styleSheet()

    chk_text = prop_view.checklist_label.text()
    assert "Componente 1" in chk_text

    steps = prop_view.steps_text.text()
    assert "HOMOGENEIDAD" in steps


def test_incompatible_dimensions_disables_button_and_shows_error(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    prop_view = window.matrix_equations_view.properties_view
    window.matrix_equations_view.tabs.setCurrentIndex(1)

    prop_view.load_incompatible_sample()

    assert prop_view.verify_btn.isEnabled() is False
    badge_text = prop_view.badge.text().lower()
    assert "no conformable" in badge_text or "incompatible" in badge_text
    assert COLOR_FEEDBACK_ERROR in prop_view.badge.styleSheet()


def test_reset_clears_results(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    prop_view = window.matrix_equations_view.properties_view
    window.matrix_equations_view.tabs.setCurrentIndex(1)

    prop_view.load_distributive_sample()
    assert prop_view._last_distributive_result is not None

    prop_view.reset()
    assert prop_view.grid_a.data_shape() == (2, 3)
    assert prop_view.vec_u_dist.grid.num_rows == 3
    assert prop_view.vec_v_dist.grid.num_rows == 3
    assert prop_view.results_tabs.currentIndex() == 0


def test_mode_toggle_switches_visible_controls(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    prop_view = window.matrix_equations_view.properties_view

    # Conmutar a homogeneidad
    prop_view.btn_mode_homo.click()
    assert prop_view._mode == "homogeneity"
    assert prop_view.vector_controls_stack.currentIndex() == 1
    assert "c·u" in prop_view.formula_lbl.text()

    # Conmutar de vuelta a distributiva
    prop_view.btn_mode_dist.click()
    assert prop_view._mode == "distributive"
    assert prop_view.vector_controls_stack.currentIndex() == 0
    assert "u + v" in prop_view.formula_lbl.text()


def test_dimension_spinners_and_sync(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_module(3)

    prop_view = window.matrix_equations_view.properties_view

    prop_view.spin_m.setValue(4)
    prop_view.spin_n.setValue(2)
    assert prop_view.grid_a.data_shape() == (4, 2)

    # Forzar desincronización
    prop_view.spin_dim_u.setValue(5)
    assert prop_view.verify_btn.isEnabled() is False

    # Sincronizar
    prop_view.sync_dimensions()
    assert prop_view.spin_dim_u.value() == 2
    assert prop_view.spin_dim_v.value() == 2
    assert prop_view.verify_btn.isEnabled() is True
