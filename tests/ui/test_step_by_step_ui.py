"""Los carruseles muestran los procedimientos completos en la interfaz."""

from PySide6.QtWidgets import QAbstractScrollArea

from prettycalc.ui.main_window import MainWindow


def _window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1366, 768)
    window.show()
    qtbot.waitExposed(window)
    return window


def test_matrix_product_has_a_carousel_that_follows_the_inspector(qtbot):
    window = _window(qtbot)
    window.set_module(1)
    view = window.matrix_operations_view
    view.load_compatible_product_sample()
    view.compute()
    assert view.ops_steps_card.isVisible()
    assert len(view.ops_stepper.steps()) == 2 + 4
    view.ops_stepper.go_to_step(3)  # c₁₂
    assert view.grid_a._highlight_rows == {0}
    assert view.grid_b._highlight_cols == {1}
    assert "C<sub>1,2</sub>" in view.inspector_label.text()


def test_scalar_and_transpose_pages_also_have_steps(qtbot):
    window = _window(qtbot)
    view = window.matrix_operations_view
    window.set_module(1)
    view.scalar_mode_btn.click()
    view.compute()
    assert view.ops_steps_card.isVisible() and view.ops_stepper.steps()
    view.transpose_mode_btn.click()
    view.compute()
    assert view.ops_stepper.steps()[1].heuristic_text.startswith("La fila 1 de A")
    view.inverse_mode_btn.click()
    assert not view.ops_steps_card.isVisible()


def test_adjugate_mode_shows_the_adjugate_procedure(qtbot):
    window = _window(qtbot)
    window.set_module(4)
    view = window.determinants_view
    view.load_session11_example()
    view.adjugate_mode_btn.click()
    view.compute()
    texts = [step.heuristic_text for step in view.stepper.steps()]
    assert sum(text.startswith("Menor ") for text in texts) == 9
    assert texts[-1].startswith("A⁻¹ = (1/det A)·adj(A)")


def test_laplace_controls_do_not_push_the_toolbar_off_screen(qtbot):
    window = _window(qtbot)
    window.set_module(4)
    view = window.determinants_view
    view.load_session11_example()
    view.laplace_mode_btn.click()
    view.compute()
    qtbot.wait(30)
    assert view.laplace_box.isVisible()
    overflow = [
        area.horizontalScrollBar().maximum()
        for area in view.findChildren(QAbstractScrollArea)
        if area.isVisible() and area.horizontalScrollBar().isVisible()
    ]
    assert overflow == []
    assert any("M₂₁ = ad − bc" in s.heuristic_text or "M₁₁ = ad − bc" in s.heuristic_text for s in view.stepper.steps())


def test_cramer_carousel_develops_each_determinant(qtbot):
    window = _window(qtbot)
    view = window.linear_systems_view
    view.load_cramer_sample()
    view.solve_system()
    qtbot.waitUntil(lambda: bool(view.stepper_carousel.steps()), timeout=2000)
    texts = [step.heuristic_text for step in view.stepper_carousel.steps()]
    assert any("det(A₁(b))" in text and "=" in text for text in texts)
    assert any(text.startswith("x₁ = det(A₁(b)) / det(A)") for text in texts)
