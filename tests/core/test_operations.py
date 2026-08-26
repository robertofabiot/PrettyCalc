"""Pruebas unitarias para operaciones elementales de fila y metadatos de transformación."""

import unittest
from fractions import Fraction

from prettycalc.core.types import Matrix
from prettycalc.core.operations import (
    swap_rows,
    scale_row,
    add_row_multiple,
    get_swap_metadata,
    get_scale_metadata,
    get_add_multiple_metadata,
)


class TestElementaryRowOperations(unittest.TestCase):
    """Pruebas para las 3 operaciones elementales de fila."""

    def setUp(self):
        self.matrix = Matrix([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ])

    def test_swap_rows(self):
        swapped = swap_rows(self.matrix, 0, 1)
        self.assertEqual(swapped.get_row(0), [Fraction(4, 1), Fraction(5, 1), Fraction(6, 1)])
        self.assertEqual(swapped.get_row(1), [Fraction(1, 1), Fraction(2, 1), Fraction(3, 1)])
        self.assertEqual(swapped.get_row(2), [Fraction(7, 1), Fraction(8, 1), Fraction(9, 1)])
        # Inmutabilidad de la original
        self.assertEqual(self.matrix.get_row(0), [Fraction(1, 1), Fraction(2, 1), Fraction(3, 1)])

    def test_swap_same_row(self):
        same = swap_rows(self.matrix, 1, 1)
        self.assertEqual(same, self.matrix)

    def test_swap_out_of_bounds(self):
        with self.assertRaises(IndexError):
            swap_rows(self.matrix, 0, 5)

    def test_scale_row(self):
        scaled = scale_row(self.matrix, 1, "1/5")
        self.assertEqual(
            scaled.get_row(1),
            [Fraction(4, 5), Fraction(1, 1), Fraction(6, 5)]
        )
        self.assertEqual(self.matrix.get_row(1), [Fraction(4, 1), Fraction(5, 1), Fraction(6, 1)])

    def test_scale_row_by_zero_error(self):
        with self.assertRaises(ValueError):
            scale_row(self.matrix, 0, 0)

    def test_add_row_multiple(self):
        # f2 -> -4*f1 + f2
        # Fila 1: [1, 2, 3] -> -4*[1, 2, 3] = [-4, -8, -12]
        # Fila 2: [4, 5, 6] -> [-4+4, -8+5, -12+6] = [0, -3, -6]
        result = add_row_multiple(self.matrix, target_r=1, source_r=0, scalar=-4)
        self.assertEqual(
            result.get_row(1),
            [Fraction(0, 1), Fraction(-3, 1), Fraction(-6, 1)]
        )
        self.assertEqual(result.get_row(0), self.matrix.get_row(0))

    def test_add_row_multiple_same_row_error(self):
        with self.assertRaises(ValueError):
            add_row_multiple(self.matrix, target_r=0, source_r=0, scalar=2)


class TestOperationMetadata(unittest.TestCase):
    """Pruebas para los metadatos LaTeX y heurísticas descriptivas."""

    def test_swap_metadata(self):
        latex, heuristic = get_swap_metadata(0, 2)
        self.assertEqual(latex, "f_{1} \\leftrightarrow f_{3}")
        self.assertIn("Fila 1", heuristic)
        self.assertIn("Fila 3", heuristic)

    def test_scale_metadata(self):
        latex, heuristic = get_scale_metadata(1, "1/2")
        self.assertIn("f_{2}", latex)
        self.assertIn("\\frac{1}{2}", latex)
        self.assertIn("Fila 2", heuristic)
        self.assertIn("1/2", heuristic)

    def test_add_multiple_metadata(self):
        latex, heuristic = get_add_multiple_metadata(target_r=1, source_r=0, scalar=-3)
        self.assertIn("f_{2}", latex)
        self.assertIn("f_{1}", latex)
        self.assertIn("Fila 1", heuristic)
        self.assertIn("Fila 2", heuristic)


if __name__ == "__main__":
    unittest.main()
