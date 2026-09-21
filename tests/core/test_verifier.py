"""Pruebas unitarias para SolutionVerifier."""

import unittest
from fractions import Fraction

from prettycalc.core.types import Matrix
from prettycalc.core.verifier import SolutionVerifier


class TestSolutionVerifier(unittest.TestCase):
    """Pruebas para verificación automática por sustitución."""

    def test_verify_valid_solution(self):
        # 2x + 3y = 8  -> 2(1) + 3(2) = 8 (OK)
        #  x -  y = -1 -> 1 - 2 = -1 (OK)
        aug = Matrix([[2, 3, 8], [1, -1, -1]])
        verifs = SolutionVerifier.verify(aug, [1, 2], split_col=2)

        self.assertEqual(len(verifs), 2)
        self.assertTrue(verifs[0].is_valid)
        self.assertEqual(verifs[0].lhs_value, Fraction(8, 1))
        self.assertEqual(verifs[0].rhs_value, Fraction(8, 1))

        self.assertTrue(verifs[1].is_valid)
        self.assertEqual(verifs[1].lhs_value, Fraction(-1, 1))
        self.assertEqual(verifs[1].rhs_value, Fraction(-1, 1))

    def test_verify_invalid_solution(self):
        aug = Matrix([[2, 3, 8], [1, -1, -1]])
        verifs = SolutionVerifier.verify(aug, [0, 0], split_col=2)
        self.assertFalse(verifs[0].is_valid)
        self.assertFalse(verifs[1].is_valid)

    def test_verify_mismatched_length(self):
        aug = Matrix([[2, 3, 8], [1, -1, -1]])
        with self.assertRaises(ValueError):
            SolutionVerifier.verify(aug, [1], split_col=2)


if __name__ == "__main__":
    unittest.main()
