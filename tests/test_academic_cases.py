"""Pruebas de validación formal para los 3 Casos Académicos de la Tarea 1.

Requisitos de la Rúbrica Universitaria:
- Caso 1: Sistema con Solución Única (Consistente Determinado).
- Caso 2: Sistema con Infinitas Soluciones (Consistente Indeterminado).
- Caso 3: Sistema Sin Solución (Inconsistente).
"""

import unittest
from fractions import Fraction

from prettycalc.core.types import Matrix
from prettycalc.core.elimination import gaussian_elimination, gauss_jordan_elimination
from prettycalc.core.classifier import classify_system, SystemType
from prettycalc.core.verifier import SolutionVerifier


class TestAcademicCasesTarea1(unittest.TestCase):
    """Casos de prueba evaluativos oficiales del silabo universitario."""

    def test_caso_1_solucion_unica_scd(self):
        """Caso 1: Sistema 3x3 con solución única.

        Ecuaciones:
          x +  y +  z = 4
         2x -  y +  z = 4
          x + 2y -  z = 3

        Solución analítica:
          x = 2, y = 1, z = 1
        """
        augmented = Matrix([
            [1, 1, 1, 4],
            [2, -1, 1, 4],
            [1, 2, -1, 3],
        ])

        # 1. Eliminación y trazado
        ref, tracer = gaussian_elimination(augmented, split_col=3)
        self.assertTrue(len(tracer) >= 3)

        # 2. Clasificación
        analysis = classify_system(augmented, split_col=3)
        self.assertEqual(analysis.system_type, SystemType.CONSISTENT_DETERMINED)
        self.assertEqual(analysis.rank_a, 3)
        self.assertEqual(analysis.rank_augmented, 3)
        self.assertEqual(analysis.unique_solution, [Fraction(2, 1), Fraction(1, 1), Fraction(1, 1)])

        # 3. Verificación automática por sustitución
        verifications = SolutionVerifier.verify(augmented, analysis.unique_solution, split_col=3)
        self.assertEqual(len(verifications), 3)
        self.assertTrue(all(v.is_valid for v in verifications))

    def test_caso_2_infinitas_soluciones_sci(self):
        """Caso 2: Sistema con infinitas soluciones y variables libres.

        Ecuaciones:
          x + 2y + 3z = 6
         2x + 4y + 6z = 12
         3x + 6y + 9z = 18
        """
        augmented = Matrix([
            [1, 2, 3, 6],
            [2, 4, 6, 12],
            [3, 6, 9, 18],
        ])

        # 1. Clasificación
        analysis = classify_system(augmented, split_col=3)
        self.assertEqual(analysis.system_type, SystemType.CONSISTENT_INDETERMINED)
        self.assertEqual(analysis.rank_a, 1)
        self.assertEqual(analysis.rank_augmented, 1)
        self.assertEqual(analysis.basic_variables, [0])  # x1
        self.assertEqual(analysis.free_variables, [1, 2])  # x2, x3

        # Expresión paramétrica: x1 = 6 - 2*x2 - 3*x3
        expr = analysis.parametric_solutions[0]
        self.assertEqual(expr.constant, Fraction(6, 1))
        self.assertEqual(expr.free_var_coeffs[1], Fraction(-2, 1))
        self.assertEqual(expr.free_var_coeffs[2], Fraction(-3, 1))

        # Comprobar solución particular (x2=0, x3=0 -> x1=6)
        sol_particular = analysis.unique_solution
        self.assertEqual(sol_particular, [Fraction(6, 1), Fraction(0, 1), Fraction(0, 1)])

        verifications = SolutionVerifier.verify(augmented, sol_particular, split_col=3)
        self.assertTrue(all(v.is_valid for v in verifications))

    def test_caso_3_sin_solucion_si(self):
        """Caso 3: Sistema inconsistente con fila contradictoria.

        Ecuaciones:
          x + 2y = 4
         2x + 4y = 9
        """
        augmented = Matrix([
            [1, 2, 4],
            [2, 4, 9],
        ])

        analysis = classify_system(augmented, split_col=2)
        self.assertEqual(analysis.system_type, SystemType.INCONSISTENT)
        self.assertEqual(analysis.rank_a, 1)
        self.assertEqual(analysis.rank_augmented, 2)
        self.assertIsNone(analysis.unique_solution)
        self.assertIsNotNone(analysis.inconsistent_row)


if __name__ == "__main__":
    unittest.main()
