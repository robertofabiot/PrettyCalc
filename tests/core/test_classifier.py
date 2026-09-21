"""Pruebas unitarias para el clasificador de sistemas lineales y Teorema de Rouché-Frobenius."""

import unittest
from fractions import Fraction

from prettycalc.core.types import Matrix
from prettycalc.core.classifier import classify_system, SystemType


class TestSystemClassifier(unittest.TestCase):
    """Pruebas para clasificación canónica (SCD, SCI, SI)."""

    def test_consistent_determined_scd(self):
        # Caso 1: Solución Única
        # 2x + y - z = 8
        # -3x - y + 2z = -11
        # -2x + y + 2z = -3
        # Solución: x=2, y=3, z=-1
        aug = Matrix([
            [2, 1, -1, 8],
            [-3, -1, 2, -11],
            [-2, 1, 2, -3],
        ])
        analysis = classify_system(aug, split_col=3)
        self.assertEqual(analysis.system_type, SystemType.CONSISTENT_DETERMINED)
        self.assertEqual(analysis.rank_a, 3)
        self.assertEqual(analysis.rank_augmented, 3)
        self.assertEqual(analysis.unique_solution, [Fraction(2, 1), Fraction(3, 1), Fraction(-1, 1)])
        self.assertEqual(len(analysis.free_variables), 0)
        self.assertEqual(analysis.pivot_columns, [0, 1, 2])
        self.assertEqual(analysis.pivot_columns_1based, [1, 2, 3])
        self.assertEqual(analysis.basic_variables_names, ["x1", "x2", "x3"])
        self.assertEqual(analysis.free_variables_names, [])
        self.assertFalse(analysis.has_augmented_pivot)

    def test_consistent_indetermined_sci(self):
        # Caso 2: Infinitas Soluciones
        # x + 2y - z = 4
        # 2x + 4y - 2z = 8
        # 0 = 0
        aug = Matrix([
            [1, 2, -1, 4],
            [2, 4, -2, 8],
        ])
        analysis = classify_system(aug, split_col=3)
        self.assertEqual(analysis.system_type, SystemType.CONSISTENT_INDETERMINED)
        self.assertEqual(analysis.rank_a, 1)
        self.assertEqual(analysis.rank_augmented, 1)
        self.assertEqual(analysis.basic_variables, [0])  # x1 básica
        self.assertEqual(analysis.free_variables, [1, 2])  # x2, x3 libres
        self.assertEqual(analysis.pivot_columns, [0])
        self.assertEqual(analysis.pivot_columns_1based, [1])
        self.assertEqual(analysis.basic_variables_names, ["x1"])
        self.assertEqual(analysis.free_variables_names, ["x2", "x3"])
        self.assertFalse(analysis.has_augmented_pivot)

        # x1 = 4 - 2*x2 + x3
        expr_x1 = analysis.parametric_solutions[0]
        self.assertEqual(expr_x1.constant, Fraction(4, 1))
        self.assertEqual(expr_x1.free_var_coeffs[1], Fraction(-2, 1))
        self.assertEqual(expr_x1.free_var_coeffs[2], Fraction(1, 1))

    def test_inconsistent_si(self):
        # Caso 3: Inconsistente (Sin Solución)
        # x + y = 2
        # x + y = 5
        aug = Matrix([
            [1, 1, 2],
            [1, 1, 5],
        ])
        analysis = classify_system(aug, split_col=2)
        self.assertEqual(analysis.system_type, SystemType.INCONSISTENT)
        self.assertEqual(analysis.rank_a, 1)
        self.assertEqual(analysis.rank_augmented, 2)
        self.assertIsNone(analysis.unique_solution)
        self.assertIsNotNone(analysis.inconsistent_row)
        self.assertEqual(analysis.pivot_columns, [0])
        self.assertEqual(analysis.pivot_columns_1based, [1])
        self.assertEqual(analysis.basic_variables, [0])
        self.assertEqual(analysis.free_variables, [1])
        self.assertTrue(analysis.has_augmented_pivot)


if __name__ == "__main__":
    unittest.main()
