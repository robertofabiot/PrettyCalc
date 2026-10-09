from fractions import Fraction
import pytest

from prettycalc.core.clipboard import (
    matrix_to_tsv,
    parse_matrix_text,
    parse_matrix_to_matrix,
)
from prettycalc.core.types import Matrix


def test_matrix_to_tsv_fraction_mode():
    mat = Matrix([[Fraction(1, 2), Fraction(-3, 1)], [Fraction(5, 4), Fraction(0, 1)]])
    tsv = matrix_to_tsv(mat, mode="fraction")
    assert tsv == "1/2\t-3\n5/4\t0"


def test_matrix_to_tsv_decimal_mode():
    mat = Matrix([[Fraction(1, 2), Fraction(-3, 1)], [Fraction(5, 4), Fraction(0, 1)]])
    tsv = matrix_to_tsv(mat, mode="decimal")
    assert tsv == "0.5\t-3\n1.25\t0"


def test_matrix_to_tsv_from_nested_list():
    raw = [["1", "2"], ["3", "4"]]
    tsv = matrix_to_tsv(raw)
    assert tsv == "1\t2\n3\t4"


def test_parse_matrix_text_tsv():
    text = "1\t2\t3\n4\t5\t6"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(1), Fraction(2), Fraction(3)],
        [Fraction(4), Fraction(5), Fraction(6)],
    ]


def test_parse_matrix_text_csv():
    text = "1, 2, 3\n4, 5, 6"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(1), Fraction(2), Fraction(3)],
        [Fraction(4), Fraction(5), Fraction(6)],
    ]


def test_parse_matrix_text_semicolon():
    text = "1; 2; 3\n4; 5; 6"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(1), Fraction(2), Fraction(3)],
        [Fraction(4), Fraction(5), Fraction(6)],
    ]


def test_parse_matrix_text_spaces():
    text = "1  2   3\n4  5   6"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(1), Fraction(2), Fraction(3)],
        [Fraction(4), Fraction(5), Fraction(6)],
    ]


def test_parse_matrix_text_python_nested_list():
    text = "[[1, -2/3], [4.5, 0]]"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(1), Fraction(-2, 3)],
        [Fraction(9, 2), Fraction(0)],
    ]


def test_parse_matrix_text_python_flat_list():
    text = "[1, 2, 3]"
    grid = parse_matrix_text(text)
    assert grid == [[Fraction(1), Fraction(2), Fraction(3)]]


def test_parse_matrix_text_latex():
    text = r"\begin{pmatrix} 1 & \frac{1}{2} \\ -3 & -\frac{3}{4} \end{pmatrix}"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(1), Fraction(1, 2)],
        [Fraction(-3), Fraction(-3, 4)],
    ]


def test_parse_matrix_text_unicode_minus():
    text = "−1\t−2\n−3/4\t5"
    grid = parse_matrix_text(text)
    assert grid == [
        [Fraction(-1), Fraction(-2)],
        [Fraction(-3, 4), Fraction(5)],
    ]


def test_parse_matrix_text_single_scalar():
    text = "  42  "
    grid = parse_matrix_text(text)
    assert grid == [[Fraction(42)]]


def test_parse_matrix_text_empty_or_invalid():
    assert parse_matrix_text("") is None
    assert parse_matrix_text("   \n   ") is None
    assert parse_matrix_text("abc\tdef") is None
    # Irregular matrix (ragged lines)
    assert parse_matrix_text("1\t2\t3\n4\t5") is None


def test_parse_matrix_to_matrix():
    mat = parse_matrix_to_matrix("1\t2\n3\t4")
    assert mat is not None
    assert mat.rows == 2
    assert mat.cols == 2
    assert mat.get(0, 0) == Fraction(1)
    assert mat.get(1, 1) == Fraction(4)

    assert parse_matrix_to_matrix("not_a_matrix") is None
