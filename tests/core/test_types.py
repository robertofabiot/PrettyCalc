"""Pruebas unitarias para tipos de datos escalares y estructura Matrix."""

import unittest
from fractions import Fraction

from prettycalc.core.types import (
    parse_scalar,
    format_scalar,
    Matrix,
)


class TestScalarParser(unittest.TestCase):
    """Pruebas para el parser de escalares numéricos."""

    def test_parse_integers(self):
        self.assertEqual(parse_scalar(0), Fraction(0, 1))
        self.assertEqual(parse_scalar(5), Fraction(5, 1))
        self.assertEqual(parse_scalar(-12), Fraction(-12, 1))
        self.assertEqual(parse_scalar("42"), Fraction(42, 1))
        self.assertEqual(parse_scalar("-7"), Fraction(-7, 1))
        self.assertEqual(parse_scalar("+15"), Fraction(15, 1))

    def test_parse_fractions(self):
        self.assertEqual(parse_scalar("3/4"), Fraction(3, 4))
        self.assertEqual(parse_scalar("-1/2"), Fraction(-1, 2))
        self.assertEqual(parse_scalar("6/8"), Fraction(3, 4))
        self.assertEqual(parse_scalar("  -5 / 10  "), Fraction(-1, 2))
        self.assertEqual(parse_scalar(Fraction(2, 3)), Fraction(2, 3))

    def test_parse_decimals(self):
        self.assertEqual(parse_scalar(0.75), Fraction(3, 4))
        self.assertEqual(parse_scalar(-0.5), Fraction(-1, 2))
        self.assertEqual(parse_scalar("0.25"), Fraction(1, 4))
        self.assertEqual(parse_scalar("-1.5"), Fraction(-3, 2))

    def test_parse_invalid_values(self):
        with self.assertRaises(ValueError):
            parse_scalar("")
        with self.assertRaises(ValueError):
            parse_scalar("abc")
        with self.assertRaises(ValueError):
            parse_scalar("3/0")  # División por cero
        with self.assertRaises(ValueError):
            parse_scalar("1/2/3")
        with self.assertRaises(TypeError):
            parse_scalar([1, 2])


class TestScalarFormatter(unittest.TestCase):
    """Pruebas para el formateo de escalares."""

    def test_format_fraction_mode(self):
        self.assertEqual(format_scalar(Fraction(5, 1), mode="fraction"), "5")
        self.assertEqual(format_scalar(Fraction(3, 4), mode="fraction"), "3/4")
        self.assertEqual(format_scalar(Fraction(-1, 2), mode="fraction"), "-1/2")

    def test_format_decimal_mode(self):
        self.assertEqual(format_scalar(Fraction(5, 1), mode="decimal"), "5")
        self.assertEqual(format_scalar(Fraction(1, 2), mode="decimal"), "0.5")
        self.assertEqual(format_scalar(Fraction(3, 4), mode="decimal"), "0.75")

    def test_format_latex_mode(self):
        self.assertEqual(format_scalar(Fraction(5, 1), mode="latex"), "5")
        self.assertEqual(format_scalar(Fraction(3, 4), mode="latex"), "\\frac{3}{4}")
        self.assertEqual(format_scalar(Fraction(-1, 2), mode="latex"), "-\\frac{1}{2}")


class TestMatrixStructure(unittest.TestCase):
    """Pruebas para la clase Matrix."""

    def test_matrix_creation_and_shape(self):
        m = Matrix([[1, "2/3"], [-4, 0.5]])
        self.assertEqual(m.rows, 2)
        self.assertEqual(m.cols, 2)
        self.assertEqual(m.shape, (2, 2))
        self.assertEqual(m.get(0, 0), Fraction(1, 1))
        self.assertEqual(m.get(0, 1), Fraction(2, 3))
        self.assertEqual(m.get(1, 0), Fraction(-4, 1))
        self.assertEqual(m.get(1, 1), Fraction(1, 2))

    def test_matrix_zeros_and_identity(self):
        z = Matrix.zeros(2, 3)
        self.assertEqual(z.shape, (2, 3))
        self.assertTrue(all(z[r, c] == Fraction(0, 1) for r in range(2) for c in range(3)))

        ident = Matrix.identity(3)
        self.assertEqual(ident.shape, (3, 3))
        self.assertEqual(ident[0, 0], Fraction(1, 1))
        self.assertEqual(ident[1, 1], Fraction(1, 1))
        self.assertEqual(ident[2, 2], Fraction(1, 1))
        self.assertEqual(ident[0, 1], Fraction(0, 1))

    def test_matrix_from_flat_list(self):
        m = Matrix.from_flat_list([1, 2, 3, 4, 5, 6], 2, 3)
        self.assertEqual(m.shape, (2, 3))
        self.assertEqual(m.get_row(0), [Fraction(1, 1), Fraction(2, 1), Fraction(3, 1)])
        self.assertEqual(m.get_row(1), [Fraction(4, 1), Fraction(5, 1), Fraction(6, 1)])

    def test_matrix_copy_independence(self):
        m1 = Matrix([[1, 2], [3, 4]])
        m2 = m1.copy()
        m2.set(0, 0, 99)
        self.assertEqual(m1.get(0, 0), Fraction(1, 1))
        self.assertEqual(m2.get(0, 0), Fraction(99, 1))

    def test_matrix_get_set_rows_cols(self):
        m = Matrix([[1, 2], [3, 4]])
        self.assertEqual(m.get_col(0), [Fraction(1, 1), Fraction(3, 1)])
        self.assertEqual(m.get_col(1), [Fraction(2, 1), Fraction(4, 1)])

        m.set_row(1, [7, 8])
        self.assertEqual(m.get_row(1), [Fraction(7, 1), Fraction(8, 1)])

    def test_matrix_augment_and_split(self):
        a = Matrix([[1, 2], [3, 4]])
        b = [5, 6]
        aug = a.augment(b)
        self.assertEqual(aug.shape, (2, 3))
        self.assertEqual(aug.get_col(2), [Fraction(5, 1), Fraction(6, 1)])

        left, right = aug.split_augmented(2)
        self.assertEqual(left, a)
        self.assertEqual(right.shape, (2, 1))
        self.assertEqual(right.get_col(0), [Fraction(5, 1), Fraction(6, 1)])

    def test_matrix_latex_and_str(self):
        m = Matrix([[1, "1/2"], [3, 4]])
        latex = m.to_latex()
        self.assertIn("\\begin{bmatrix}", latex)
        self.assertIn("\\frac{1}{2}", latex)
        self.assertIn("\\end{bmatrix}", latex)

        aug_latex = m.to_latex(split_col=1)
        self.assertIn("\\begin{array}{c|c}", aug_latex)

        s = str(m)
        self.assertIn("│", s)

    def test_matrix_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            Matrix([])
        with self.assertRaises(ValueError):
            Matrix([[]])
        with self.assertRaises(ValueError):
            Matrix([[1, 2], [3]])


if __name__ == "__main__":
    unittest.main()
