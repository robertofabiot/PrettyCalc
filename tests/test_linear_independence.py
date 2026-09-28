"""Pruebas unitarias para el evaluador de Independencia y Dependencia Lineal en ℝⁿ.

Verifica:
1. Conjunto L.I. canónico en ℝ³ (base estándar).
2. Conjunto L.I. no trivial con matrices invertibles y fracciones.
3. Conjunto L.D. con combinación lineal evidente (v3 = v1 + v2).
4. Conjunto L.D. por Teorema Fundamental de Dimensión (k > n).
5. Conjunto L.D. con presencia del vector nulo.
6. Conjunto L.I. con menos vectores que dimensión (k < n).
7. Parsing exacto de escalares y fracciones.
"""

import importlib.util
import sys
import unittest
from fractions import Fraction
from pathlib import Path

# Cargar dinámicamente Programa 4_Grupo4.py desde la raíz
script_path = Path(__file__).resolve().parent.parent / "Programa 4_Grupo4.py"
spec = importlib.util.spec_from_file_location("programa_4", script_path)
p4 = importlib.util.module_from_spec(spec)
sys.modules["programa_4"] = p4
spec.loader.exec_module(p4)


class TestLinearIndependence(unittest.TestCase):
    """Batería de pruebas exhaustiva para Programa 4."""

    def test_parse_scalar(self):
        """Verifica la conversión exacta a Fraction."""
        self.assertEqual(p4.parse_scalar("3"), Fraction(3, 1))
        self.assertEqual(p4.parse_scalar("-5"), Fraction(-5, 1))
        self.assertEqual(p4.parse_scalar("3/4"), Fraction(3, 4))
        self.assertEqual(p4.parse_scalar("-2/6"), Fraction(-1, 3))
        self.assertEqual(p4.parse_scalar("0.5"), Fraction(1, 2))
        self.assertEqual(p4.parse_scalar("-0.75"), Fraction(-3, 4))

        with self.assertRaises(ZeroDivisionError):
            p4.parse_scalar("4/0")

    def test_canonico_linealmente_independiente_r3(self):
        """Caso 1: Vectores de la base estándar en ℝ³ (e1, e2, e3)."""
        vectors = [
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(1)],
        ]
        res = p4.evaluate_linear_independence(vectors, dim_n=3, verbose=False)

        self.assertEqual(res["k"], 3)
        self.assertEqual(res["n"], 3)
        self.assertEqual(res["num_pivots"], 3)
        self.assertEqual(len(res["free_vars"]), 0)
        self.assertTrue(res["is_linearly_independent"])
        self.assertIsNone(res["nontrivial_solution"])

    def test_linealmente_independiente_general(self):
        """Caso 2: Tres vectores L.I. con números enteros y fracciones."""
        vectors = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(4), Fraction(5), Fraction(6)],
            [Fraction(7), Fraction(8), Fraction(10)],  # det ≠ 0
        ]
        res = p4.evaluate_linear_independence(vectors, dim_n=3, verbose=False)

        self.assertEqual(res["num_pivots"], 3)
        self.assertEqual(len(res["free_vars"]), 0)
        self.assertTrue(res["is_linearly_independent"])

    def test_linealmente_dependiente_combinacion_directa(self):
        """Caso 3: v3 = v1 + v2 => v1 + v2 - v3 = 0 (L.D.)."""
        v1 = [Fraction(1), Fraction(2), Fraction(3)]
        v2 = [Fraction(4), Fraction(5), Fraction(6)]
        v3 = [Fraction(5), Fraction(7), Fraction(9)]
        vectors = [v1, v2, v3]

        res = p4.evaluate_linear_independence(vectors, dim_n=3, verbose=False)

        self.assertEqual(res["num_pivots"], 2)
        self.assertEqual(res["free_vars"], [2])
        self.assertFalse(res["is_linearly_independent"])
        self.assertIsNotNone(res["nontrivial_solution"])

        # Comprobar que c1*v1 + c2*v2 + c3*v3 == 0
        c = res["nontrivial_solution"]
        for dim in range(3):
            val = sum(c[j] * vectors[j][dim] for j in range(3))
            self.assertEqual(val, Fraction(0))

    def test_teorema_k_mayor_que_n(self):
        """Caso 4: k = 4 vectores en ℝ³ (necesariamente L.D.)."""
        vectors = [
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(1)],
        ]
        res = p4.evaluate_linear_independence(vectors, dim_n=3, verbose=False)

        self.assertTrue(res["theorem_k_greater_n"])
        self.assertFalse(res["is_linearly_independent"])
        self.assertEqual(res["num_pivots"], 3)
        self.assertEqual(len(res["free_vars"]), 1)
        self.assertEqual(res["free_vars"], [3])

    def test_vector_nulo_es_ld(self):
        """Caso 5: Un conjunto que contiene al vector nulo es siempre L.D."""
        vectors = [
            [Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(1), Fraction(2), Fraction(3)],
        ]
        res = p4.evaluate_linear_independence(vectors, dim_n=3, verbose=False)

        self.assertEqual(res["zero_vector_index"], 0)
        self.assertFalse(res["is_linearly_independent"])
        self.assertEqual(len(res["free_vars"]), 1)

    def test_k_menor_que_n_linealmente_independiente(self):
        """Caso 6: k = 2 vectores no paralelos en ℝ³ (L.I.)."""
        vectors = [
            [Fraction(1), Fraction(0), Fraction(2)],
            [Fraction(0), Fraction(1), Fraction(-1)],
        ]
        res = p4.evaluate_linear_independence(vectors, dim_n=3, verbose=False)

        self.assertEqual(res["k"], 2)
        self.assertEqual(res["n"], 3)
        self.assertEqual(res["num_pivots"], 2)
        self.assertEqual(len(res["free_vars"]), 0)
        self.assertTrue(res["is_linearly_independent"])


if __name__ == "__main__":
    unittest.main()
