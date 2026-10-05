"""Pruebas de la transpuesta, la traza y el inspector de propiedades."""

from fractions import Fraction
from pathlib import Path

import pytest

from prettycalc.core.matrix_properties import (
    analyze_matrix,
    describe_matrix_kind,
    format_property_lines,
    is_skew_symmetric,
    is_symmetric,
    matrix_trace,
)
from prettycalc.core.types import DimensionMismatchError, Matrix


def _status(checks, name: str) -> str:
    match = next(check for check in checks if check.name == name)
    return match.status


def test_kinds_cover_square_rectangular_and_vectors():
    assert "cuadrada" in describe_matrix_kind(Matrix.identity(2))
    assert describe_matrix_kind(Matrix([[1, 2, 3], [4, 5, 6]])).startswith("rectangular")
    assert describe_matrix_kind(Matrix([[1, 2, 3]])).startswith("vector fila")
    assert describe_matrix_kind(Matrix([[1], [2]])).startswith("vector columna")
    assert "1×1" in describe_matrix_kind(Matrix([[7]]))


def test_identity_and_zero_report_expected_properties():
    identity = analyze_matrix(Matrix.identity(3), scalar=2)
    assert _status(identity, "Matriz identidad") == "cumple"
    assert _status(identity, "Matriz diagonal") == "cumple"
    assert _status(identity, "Matriz escalar") == "cumple"
    assert _status(identity, "Triangular superior") == "cumple"
    assert _status(identity, "Triangular inferior") == "cumple"
    assert _status(identity, "Simétrica") == "cumple"
    assert _status(identity, "Antisimétrica") == "no_cumple"
    assert _status(identity, "Matriz nula") == "no_cumple"
    assert any(check.detail == "tr(A) = 3." for check in identity)
    assert _status(identity, "(k · A)ᵀ = k · Aᵀ") == "cumple"

    zero = analyze_matrix(Matrix.zeros(2, 2))
    assert _status(zero, "Matriz nula") == "cumple"
    assert _status(zero, "Simétrica") == "cumple"
    assert _status(zero, "Antisimétrica") == "cumple"
    assert _status(zero, "Matriz identidad") == "no_cumple"
    assert any(check.detail == "tr(A) = 0." for check in zero)


def test_upper_triangular_symmetric_and_skew_examples():
    upper = Matrix([[1, 2], [0, 3]])
    report = analyze_matrix(upper)
    assert _status(report, "Triangular superior") == "cumple"
    assert _status(report, "Triangular inferior") == "no_cumple"
    assert _status(report, "Simétrica") == "no_cumple"
    assert matrix_trace(upper) == Fraction(4, 1)

    symmetric = Matrix([[1, "1/2"], ["1/2", 3]])
    assert is_symmetric(symmetric)
    assert not is_skew_symmetric(symmetric)

    skew = Matrix([[0, 2], [-2, 0]])
    assert is_skew_symmetric(skew)
    assert matrix_trace(skew) == Fraction(0, 1)


def test_rectangular_matrix_marks_square_properties_as_not_applicable():
    report = analyze_matrix(Matrix([[1, 2, 3], [4, 5, 6]]))
    assert _status(report, "Tipo") == "dato"
    for name in ("Matriz identidad", "Simétrica", "Traza", "Matriz diagonal"):
        assert _status(report, name) == "no_aplica"
    assert _status(report, "(Aᵀ)ᵀ = A") == "cumple"


def test_transpose_identities_hold_or_explain_why_they_do_not_apply():
    left = Matrix([[1, 2], [3, 4]])
    right = Matrix([[0, 1], [1, 0]])
    incompatible = Matrix([[1, 2, 3]])
    report = analyze_matrix(left, right, scalar="1/2")
    assert _status(report, "(Aᵀ)ᵀ = A") == "cumple"
    assert _status(report, "(A + B)ᵀ = Aᵀ + Bᵀ") == "cumple"
    assert _status(report, "(k · A)ᵀ = k · Aᵀ") == "cumple"
    assert _status(report, "(A · B)ᵀ = Bᵀ · Aᵀ") == "cumple"

    blocked = analyze_matrix(left, incompatible, scalar=None)
    assert _status(blocked, "(A + B)ᵀ = Aᵀ + Bᵀ") == "no_aplica"
    assert _status(blocked, "(A · B)ᵀ = Bᵀ · Aᵀ") == "no_aplica"
    assert _status(blocked, "(k · A)ᵀ = k · Aᵀ") == "no_aplica"

    lines = format_property_lines(report)
    assert any(line.startswith("✓  (Aᵀ)ᵀ = A") for line in lines)


def test_trace_rejects_non_square_matrix():
    with pytest.raises(DimensionMismatchError, match="cuadradas"):
        matrix_trace(Matrix([[1, 2, 3]]))


def test_core_modules_do_not_call_print_or_input():
    root = Path(__file__).resolve().parents[2] / "prettycalc" / "core"
    for path in root.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "print(" not in source, path.name
        assert "input(" not in source, path.name
