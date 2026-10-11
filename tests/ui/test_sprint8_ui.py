"""Interfaz de norma, TMI, propiedades del determinante y PLU."""

from prettycalc.core.types import Matrix, Vector
from prettycalc.ui.modules.determinants_view import DeterminantsView
from prettycalc.ui.modules.lu_factorization_view import LUFactorizationView
from prettycalc.ui.modules.matrix_operations_view import MatrixOperationsView
from prettycalc.ui.modules.vectors_view import VectorsView
from prettycalc.ui.theme import COLOR_FEEDBACK_SUCCESS


def test_vectors_view_shows_the_class_norm_distance_and_outer_product(qtbot):
    view = VectorsView()
    qtbot.addWidget(view)

    view.load_norm_sample()
    assert "‖u‖ = 5" in view.metric_summary.text()
    assert view.metric_stepper._steps

    view.load_distance_sample()
    assert "d(u, v) = 5" in view.metric_summary.text()

    view.load_outer_product_sample()
    assert view.metric_result._matrix == Matrix([
        [1, -2, 3],
        [-2, 4, -6],
        [3, -6, 9],
    ])
    assert "3×3" in view.metric_summary.text()


def test_tmi_panel_marks_the_invertible_and_singular_examples(qtbot):
    view = MatrixOperationsView()
    qtbot.addWidget(view)

    view.load_tmi_invertible_sample()
    assert view.pages.currentIndex() == 5
    checklist = view.tmi_checklist.text()
    assert "Cumple" in checklist
    assert "*c" in checklist
    assert "*e" in checklist
    assert "*h" in checklist
    assert "No cumple" not in checklist
    assert COLOR_FEEDBACK_SUCCESS in view.badge.styleSheet()

    view.load_tmi_singular_sample()
    singular = view.tmi_checklist.text()
    assert "No cumple" in singular
    assert "*c" in singular
    assert view.tmi_stepper._steps


def test_inverse_identities_panel_checks_the_three_laws(qtbot):
    view = MatrixOperationsView()
    qtbot.addWidget(view)
    view.load_inverse_identities_sample()

    assert view.pages.currentIndex() == 6
    text = view.identity_checklist.text()
    assert "(A⁻¹)⁻¹ = A" in text
    assert "(AB)⁻¹ = B⁻¹ A⁻¹" in text
    assert "(Aᵀ)⁻¹ = (A⁻¹)ᵀ" in text
    assert "✓" in text
    assert view.identity_stepper._steps


def test_determinant_properties_panel_uses_the_session11_product(qtbot):
    view = DeterminantsView()
    qtbot.addWidget(view)
    view.load_properties_example()

    assert view.last_properties is not None
    assert view.last_properties.det_A == 9
    assert view.last_properties.det_B == 5
    assert view.last_properties.det_AB == 45
    text = view.properties_checklist.text()
    assert "det(AB) = 45" in text
    assert "det(Aᵀ)" in text
    assert "det(kA)" in text
    assert "✓" in text
    assert view.stepper._steps


def test_lu_view_solves_the_session12_permutation_example(qtbot):
    view = LUFactorizationView()
    qtbot.addWidget(view)
    view.grid.set_matrix(Matrix([
        [0, 1, 2],
        [1, 0, 3],
        [4, -3, 8],
    ]))
    view.b_grid.set_matrix(Matrix([[3], [4], [9]]))
    view.decompose()
    view.solve()

    assert view.last_factorization is not None
    assert view.last_factorization.permutation_count == 1
    assert view.last_factorization.P == Matrix([
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ])
    assert "P · A = L · U" in view.checklist_label.text()
    assert "No se requirieron" not in view.permutation_note.text()
    assert view.last_solution is not None
    assert view.last_solution.x_solution == Vector([1, 1, 1])
    assert view.last_solution.permuted_b == Vector([4, 3, 9])
    assert "Pb" in view.pb_label.text()
    assert "A · x = b" in view.ax_label.text()
    assert COLOR_FEEDBACK_SUCCESS in view.ax_label.styleSheet()
