"""Pruebas unitarias para algoritmos de eliminación Gaussiana y Gauss-Jordan."""

import unittest
from fractions import Fraction

from prettycalc.core.types import Matrix
from prettycalc.core.elimination import gaussian_elimination, gauss_jordan_elimination


class TestElimination(unittest.TestCase):
    """Pruebas para eliminación hacia adelante y reducción completa."""

    def test_gaussian_elimination_simple_system(self):
        # Sistema 2x2:
        #  x + 2y = 5
        # 3x + 4y = 11
        # Matriz aumentada [A | b]:
        # [1, 2, 5]
        # [3, 4, 11]
        aug = Matrix([[1, 2, 5], [3, 4, 11]])
        ref, tracer = gaussian_elimination(aug, split_col=2)

        # En la fila 2 debe quedar: [0, -2, -4]
        self.assertEqual(ref.get_row(0), [Fraction(1, 1), Fraction(2, 1), Fraction(5, 1)])
        self.assertEqual(ref.get_row(1), [Fraction(0, 1), Fraction(-2, 1), Fraction(-4, 1)])
        self.assertTrue(len(tracer) >= 2)

    def test_gaussian_elimination_with_row_swap(self):
        # Matriz donde el primer pivote es 0:
        # [0, 2, 4]
        # [3, 1, 7]
        aug = Matrix([[0, 2, 4], [3, 1, 7]])
        ref, tracer = gaussian_elimination(aug, split_col=2)

        self.assertEqual(ref.get_row(0), [Fraction(3, 1), Fraction(1, 1), Fraction(7, 1)])
        self.assertEqual(ref.get_row(1), [Fraction(0, 1), Fraction(2, 1), Fraction(4, 1)])

    def test_gauss_jordan_elimination(self):
        # Sistema 2x2 con solución única x=1, y=2:
        #  x + 2y = 5
        # 3x + 4y = 11
        aug = Matrix([[1, 2, 5], [3, 4, 11]])
        rref, tracer = gauss_jordan_elimination(aug, split_col=2)

        # RREF debe ser:
        # [1, 0, 1]
        # [0, 1, 2]
        self.assertEqual(rref.get_row(0), [Fraction(1, 1), Fraction(0, 1), Fraction(1, 1)])
        self.assertEqual(rref.get_row(1), [Fraction(0, 1), Fraction(1, 1), Fraction(2, 1)])

    def test_gauss_jordan_3x3_system(self):
        # 2x + y - z = 8
        # -3x - y + 2z = -11
        # -2x + y + 2z = -3
        # Solución: x=2, y=3, z=-1
        aug = Matrix([
            [2, 1, -1, 8],
            [-3, -1, 2, -11],
            [-2, 1, 2, -3],
        ])
        rref, tracer = gauss_jordan_elimination(aug, split_col=3)

        self.assertEqual(rref.get(0, 3), Fraction(2, 1))
        self.assertEqual(rref.get(1, 3), Fraction(3, 1))
        self.assertEqual(rref.get(2, 3), Fraction(-1, 1))


if __name__ == "__main__":
    unittest.main()
