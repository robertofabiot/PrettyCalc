"""Sprint 10: las celdas inválidas explican qué carácter falló."""

import pytest

from prettycalc.core.determinants import determinant_triangulation
from prettycalc.core.classifier import classify_system
from prettycalc.core.input_diagnostics import decimal_hint, diagnose_scalar_text
from prettycalc.core.types import Matrix


@pytest.mark.parametrize("text", ["3", "-1/2", "0.75", ".5", "+7", "", "  4  ", "1e5"])
def test_valid_inputs_pass(text):
    assert diagnose_scalar_text(text).is_valid


def test_empty_can_be_required():
    diagnosis = diagnose_scalar_text("", allow_empty=False)
    assert not diagnosis.is_valid
    assert diagnosis.suggestion == "0"


@pytest.mark.parametrize(
    "text, fragment, suggestion",
    [
        ("2,5", "coma decimal", "2.5"),
        ("1O", "letra O", "10"),
        ("l2", "letra l", "12"),
        ("3/0", "divide entre cero", None),
        ("3/", "Falta el denominador", None),
        ("1/2/3", "más de una barra", None),
        ("1.5/2", "mezcla fracción y decimal", None),
        ("1..2", "más de un punto", None),
        ("3-2", "signo fuera de lugar", None),
        ("abc", "«a»", None),
    ],
)
def test_invalid_inputs_are_explained(text, fragment, suggestion):
    diagnosis = diagnose_scalar_text(text)
    assert not diagnosis.is_valid
    assert fragment in diagnosis.message
    assert diagnosis.suggestion == suggestion


def test_decimal_hint_only_for_fractions():
    assert decimal_hint("3/2") == "≈ 1.5"
    assert decimal_hint("4/2") == "= 2"
    assert decimal_hint("1/3") == "≈ 0.333333"
    assert decimal_hint("2") == ""
    assert decimal_hint("x/2") == ""


def test_triangulation_closes_with_explicit_diagonal_product():
    result = determinant_triangulation(Matrix([[0, 1], [2, 3]]))
    last = result.tracer[-1]
    assert "(-1) \\cdot (2)(1) = -2" in last.latex_formula
    assert last.highlight_cells == ((0, 0), (1, 1))


def test_inconsistent_system_keeps_the_contradiction_value():
    analysis = classify_system(Matrix([[1, 2, 4], [2, 4, 9]]), split_col=2)
    assert analysis.inconsistent_value == 1
