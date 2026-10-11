"""Sesión 8: balanceo químico, Leontief, dieta y redes de flujo."""

from fractions import Fraction

import pytest

from prettycalc.core.applied_models import (
    AppliedModelError,
    ChemicalFormulaError,
    analyze_network_flow,
    balance_chemical_equation,
    balance_chemical_reaction,
    baltimore_traffic_network,
    cambridge_diet,
    coal_electric_steel_consumption,
    integer_balanced_coefficients,
    leontief_prices_reproduce_zero,
    parse_chemical_equation,
    parse_chemical_formula,
    parse_chemical_side,
    solve_leontief_exchange,
    solve_nutrition_mix,
)
from prettycalc.core.matrix_vector_ops import matrix_vector_multiply
from prettycalc.core.theorems import all_theorem_texts
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector


def test_integer_coefficients_clear_denominators_and_flip_sign():
    assert integer_balanced_coefficients([
        Fraction(1, 4), Fraction(5, 4), Fraction(3, 4), 1,
    ]) == [1, 5, 3, 4]
    assert integer_balanced_coefficients([
        Fraction(-1, 4), Fraction(-5, 4), Fraction(-3, 4), -1,
    ]) == [1, 5, 3, 4]


def test_integer_coefficients_reject_a_direction_that_changes_sign():
    with pytest.raises(ValueError):
        integer_balanced_coefficients([1, -1])


def test_formula_parser_counts_groups():
    assert parse_chemical_formula("C3H8") == {"C": 3, "H": 8}
    assert parse_chemical_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_formula("2H2")


def test_propane_balances_to_the_session_integers():
    result = balance_chemical_equation("C3H8 + O2 → CO2 + H2O")

    assert result.is_valid
    assert result.elements == ["C", "H", "O"]
    assert result.stoichiometric_coefficients == [1, 5, 3, 4]
    assert result.balanced_equation_text == "1 C3H8 + 5 O2 → 3 CO2 + 4 H2O"
    assert result.augmented_matrix == Matrix([
        [3, 0, -1, 0, 0],
        [8, 0, 0, -2, 0],
        [0, 2, -2, -1, 0],
    ])
    assert result.tracer.total_steps >= 2
    assert "1 C3H8" in result.summary


def test_aluminum_oxide_and_phosphate_reactions_are_minimal_integers():
    aluminum = balance_chemical_equation("Al2O3 + C → Al + CO2")
    assert aluminum.is_valid
    assert aluminum.stoichiometric_coefficients == [2, 3, 4, 3]

    phosphate = balance_chemical_equation("Ca(OH)2 + H3PO4 → Ca3(PO4)2 + H2O")
    assert phosphate.is_valid
    assert phosphate.stoichiometric_coefficients == [3, 2, 1, 6]


def test_impossible_atom_swap_has_no_positive_balance():
    result = balance_chemical_equation("C → H")
    assert not result.is_valid
    assert result.stoichiometric_coefficients == []


def test_coal_electricity_steel_prices_are_exact_relative_to_steel():
    result = solve_leontief_exchange(coal_electric_steel_consumption())

    assert result.columns_sum_to_one
    assert result.degrees_of_freedom == 1
    assert result.equilibrium_price_vector == Vector([Fraction(31, 33), Fraction(28, 33), 1])
    assert leontief_prices_reproduce_zero(result)
    assert result.system_matrix == Matrix([
        [1, Fraction(-2, 5), Fraction(-3, 5)],
        [Fraction(-3, 5), Fraction(9, 10), Fraction(-1, 5)],
        [Fraction(-2, 5), Fraction(-1, 2), Fraction(4, 5)],
    ])
    assert f"{float(result.equilibrium_price_vector[0]):.2f}" == "0.94"
    assert f"{float(result.equilibrium_price_vector[1]):.2f}" == "0.85"


def test_leontief_rejects_a_rectangular_consumption_matrix():
    with pytest.raises(ValueError, match="cuadrada"):
        solve_leontief_exchange(Matrix([[1, 0, 0], [0, 1, 0]]))


def test_open_exchange_with_identity_only_has_the_zero_price():
    result = solve_leontief_exchange(Matrix.zeros(2, 2))
    assert not result.columns_sum_to_one
    assert result.degrees_of_freedom == 0
    assert result.equilibrium_price_vector == Vector([0, 0])


def test_cambridge_diet_matches_the_rounded_slide_and_the_exact_requirements():
    composition, requirements = cambridge_diet()
    result = solve_nutrition_mix(
        composition,
        requirements,
        ingredient_names=["leche descremada", "harina de soya", "suero de leche"],
        nutrient_names=["proteínas", "carbohidratos", "grasa"],
    )

    assert result.is_feasible
    assert result.amounts == [
        Fraction(42933, 154868),
        Fraction(15174, 38717),
        Fraction(1290, 5531),
    ]
    assert [f"{float(amount):.3f}" for amount in result.amounts] == ["0.277", "0.392", "0.233"]
    assert [f"{float(grams):.1f}" for grams in result.gram_amounts] == ["27.7", "39.2", "23.3"]
    image = matrix_vector_multiply(composition, Vector(result.amounts))
    assert image == requirements


def test_negative_ingredient_is_not_a_feasible_diet():
    result = solve_nutrition_mix(Matrix([[1, 0], [0, 1]]), Vector([1, -2]))
    assert not result.is_feasible
    assert result.failure_reason is not None
    assert "negativa" in result.failure_reason


def test_baltimore_traffic_keeps_every_street_one_way():
    result = analyze_network_flow(baltimore_traffic_network())

    assert result.is_feasible
    assert result.bounds_are_exact
    assert result.general_flow_solution["x1"] == "600 - x5"
    assert result.general_flow_solution["x2"] == "200 + x5"
    assert result.general_flow_solution["x3"] == "400"
    assert result.general_flow_solution["x4"] == "500 - x5"
    assert result.general_flow_solution["x5"] == "x5"
    assert result.parameter_range == (Fraction(0), Fraction(500))
    assert result.valid_ranges["x1"] == (Fraction(100), Fraction(600))
    assert result.valid_ranges["x2"] == (Fraction(200), Fraction(700))
    assert result.valid_ranges["x3"] == (Fraction(400), Fraction(400))
    assert result.valid_ranges["x4"] == (Fraction(0), Fraction(500))
    assert result.valid_ranges["x5"] == (Fraction(0), Fraction(500))
    assert "x5" in result.summary


def test_capacity_on_the_free_street_shrinks_the_interval():
    result = analyze_network_flow(baltimore_traffic_network(), capacities={4: 100})

    assert result.is_feasible
    assert result.parameter_range == (Fraction(0), Fraction(100))
    assert result.valid_ranges["x5"] == (Fraction(0), Fraction(100))
    assert result.valid_ranges["x1"] == (Fraction(500), Fraction(600))
    assert result.valid_ranges["x4"] == (Fraction(400), Fraction(500))


def test_unique_negative_flow_is_infeasible():
    result = analyze_network_flow(Matrix([[1, -3]]))
    assert not result.is_feasible
    assert result.bounds_are_exact
    assert result.valid_ranges["x1"] == (Fraction(-3), Fraction(-3))


def test_formula_and_integer_edge_cases():
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_formula("   ")
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_formula("Ca(OH")
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_formula("Ca)OH")
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_formula("C*")
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_formula("()")
    assert parse_chemical_formula("Ca(OH)") == {"Ca": 1, "O": 1, "H": 1}
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_side(" + ")
    with pytest.raises(ChemicalFormulaError):
        parse_chemical_equation("C3H8 + O2")
    with pytest.raises(ValueError):
        integer_balanced_coefficients([])
    with pytest.raises(ValueError):
        integer_balanced_coefficients([0, 0])


def test_water_balance_builds_labels_from_the_atom_counts():
    result = balance_chemical_reaction([{"H": 2}, {"O": 2}], [{"H": 2, "O": 1}])
    assert result.is_valid
    assert result.stoichiometric_coefficients == [2, 1, 2]
    assert result.reactants == ["H2", "O2"]
    assert result.products == ["H2O"]


def test_reaction_with_two_free_directions_is_not_a_single_balance():
    result = balance_chemical_reaction(
        [{"X": 1}],
        [{"X": 1}, {"X": 1}],
        reactant_labels=["A"],
        product_labels=["B", "C"],
    )
    assert not result.is_valid
    assert "direcciones libres" in result.summary


def test_mixed_sign_nullspace_is_not_a_positive_balance():
    result = balance_chemical_reaction(
        [{"A": 1}, {"B": 1}],
        [{"A": 1, "B": -1}],
        reactant_labels=["P", "Q"],
        product_labels=["R"],
    )
    assert not result.is_valid
    assert result.stoichiometric_coefficients == []


def test_empty_formulas_and_a_missing_side_are_rejected():
    with pytest.raises(ChemicalFormulaError):
        balance_chemical_reaction([{}], [{}])
    with pytest.raises(ChemicalFormulaError):
        balance_chemical_reaction([], [{"H": 2}])


def test_nutrition_rejects_a_bad_table_and_an_inconsistent_mix():
    with pytest.raises(DimensionMismatchError):
        solve_nutrition_mix(Matrix([[1, 0]]), Vector([1, 2]))
    with pytest.raises(AppliedModelError):
        solve_nutrition_mix(Matrix([[1]]), Vector([1]), portion_grams=0)
    with pytest.raises(AppliedModelError):
        solve_nutrition_mix(
            Matrix([[1, 0], [0, 1]]),
            Vector([1, 1]),
            ingredient_names=["solo uno"],
        )
    inconsistent = solve_nutrition_mix(Matrix([[0]]), Vector([1]))
    assert not inconsistent.is_feasible
    plain = solve_nutrition_mix(Matrix([[1, 0], [0, 1]]), Vector([2, 3]))
    assert plain.is_feasible
    assert plain.ingredient_names == ["alimento 1", "alimento 2"]
    assert plain.nutrient_names == ["nutriente 1", "nutriente 2"]


def test_network_rejects_bad_input_and_reports_an_open_ray():
    with pytest.raises(AppliedModelError):
        analyze_network_flow(Matrix([[1]]))
    with pytest.raises(AppliedModelError):
        analyze_network_flow(Matrix([[1, 1, 0]]), capacities={5: 1})
    with pytest.raises(AppliedModelError):
        analyze_network_flow(Matrix([[1, 1, 0]]), capacities={0: -1})

    inconsistent = analyze_network_flow(Matrix([[0, 1]]))
    assert not inconsistent.is_feasible
    assert inconsistent.general_flow_solution == {}

    open_ray = analyze_network_flow(Matrix([[1, -1, 0]]))
    assert open_ray.is_feasible
    assert open_ray.parameter_range is not None
    assert open_ray.parameter_range[1] is None
    assert "∞" in open_ray.summary

    blocked = analyze_network_flow(Matrix([[1, 0, -1]]))
    assert not blocked.is_feasible
    assert blocked.valid_ranges == {}

    over_capacity = analyze_network_flow(Matrix([[1, -1, 10]]), capacities={0: 5})
    assert not over_capacity.is_feasible
    assert over_capacity.valid_ranges == {}


def test_several_free_flows_can_make_the_particular_solution_negative():
    result = analyze_network_flow(Matrix([[1, 1, 0, -1]]))
    assert not result.bounds_are_exact
    assert not result.is_feasible
    assert "negativo" in result.summary


def test_theorem_compendium_covers_applications_and_lu():
    chapters = all_theorem_texts()
    assert len(chapters) == 6
    joined = "\n".join(chapters)
    assert "ROUCHE-FROBENIUS" in joined
    assert "LEONTIEF" in joined
    assert "FACTORIZACION LU" in joined


def test_two_free_flows_keep_the_general_solution_without_claiming_tight_bounds():
    network = Matrix([
        [1, 1, 0, 0, 1],
        [0, 0, 1, 1, 1],
    ])
    result = analyze_network_flow(network)
    assert not result.bounds_are_exact
    assert result.general_flow_solution
    assert result.valid_ranges == {}
