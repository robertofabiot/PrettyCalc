"""Pruebas unitarias para la arquitectura modular de Calculadora_Algebra_Lineal.

Verifica:
1. Módulo 1 (SEL): Sistemas consistentes (única solución e infinitas) e inconsistentes.
2. Módulo 2 (Vectores): L.I. vs L.D., combinación lineal y operaciones vectoriales.
3. Módulo 3 (Matrices): Suma, producto de matrices, traspuesta e inversa por Gauss-Jordan.
4. Módulo 4 (Determinantes): 2x2, 3x3 por Sarrus y nxn por triangulación gaussiana.
5. Teoremas: Invocación libre de excepciones.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from Calculadora_Algebra_Lineal.modulos import (
    modulo_sistemas as ms,
    modulo_vectores as mv,
    modulo_matrices as mm,
    modulo_determinantes as md,
)
from Calculadora_Algebra_Lineal.teoremas import resumen_teoremas as rt


class TestCalculadoraModular(unittest.TestCase):
    """Batería de pruebas automatizadas para la Calculadora Modular."""

    # --------------------------------------------------------------------------
    # Módulo 1: Sistemas de Ecuaciones Lineales
    # --------------------------------------------------------------------------
    def test_sel_parsing_y_formato(self):
        """Comprueba parseo y formateo exacto de escalares."""
        self.assertEqual(ms.parse_scalar("7/2"), Fraction(7, 2))
        self.assertEqual(ms.parse_scalar("-0.25"), Fraction(-1, 4))
        self.assertEqual(ms.fmt(Fraction(6, 2)), "3")
        self.assertEqual(ms.fmt(Fraction(3, 4)), "3/4")

    # --------------------------------------------------------------------------
    # Módulo 2: Vectores e Independencia Lineal (Programa 4)
    # --------------------------------------------------------------------------
    def test_vectores_independencia_li(self):
        """Verifica detección de conjunto L.I. en ℝ³."""
        vectors = [
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(2), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(3)],
        ]
        aug = mv.build_homogeneous_system(vectors, 3)
        ref, pivots = mv.row_echelon_reduction(aug, num_vars=3, verbose=False)
        self.assertEqual(len(pivots), 3)
        self.assertEqual(pivots, [(0, 0), (1, 1), (2, 2)])

    def test_vectores_dependencia_ld_con_demostracion(self):
        """Verifica detección de conjunto L.D. con coeficientes no triviales."""
        v1 = [Fraction(1), Fraction(1), Fraction(0)]
        v2 = [Fraction(0), Fraction(1), Fraction(1)]
        v3 = [Fraction(1), Fraction(2), Fraction(1)]  # v3 = v1 + v2
        vectors = [v1, v2, v3]

        aug = mv.build_homogeneous_system(vectors, 3)
        ref, pivots = mv.row_echelon_reduction(aug, num_vars=3, verbose=False)
        self.assertEqual(len(pivots), 2)

        rref = mv.back_substitution_rref(ref, pivots, num_vars=3)
        sol = mv.extract_nontrivial_solution(rref, pivots, num_vars=3)
        self.assertIsNotNone(sol)

        # Comprobar que c1*v1 + c2*v2 + c3*v3 == 0
        for dim in range(3):
            val = sum(sol[j] * vectors[j][dim] for j in range(3))
            self.assertEqual(val, Fraction(0, 1))

    # --------------------------------------------------------------------------
    # Módulo 3: Álgebra de Matrices e Inversa
    # --------------------------------------------------------------------------
    def test_matrices_producto_exacto(self):
        """Multiplicación A(2x3) * B(3x2) = C(2x2)."""
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(4), Fraction(5), Fraction(6)],
        ]
        B = [
            [Fraction(7), Fraction(8)],
            [Fraction(9), Fraction(1)],
            [Fraction(2), Fraction(3)],
        ]
        # C[0][0] = 1*7 + 2*9 + 3*2 = 7 + 18 + 6 = 31
        # C[0][1] = 1*8 + 2*1 + 3*3 = 8 + 2 + 9 = 19
        # C[1][0] = 4*7 + 5*9 + 6*2 = 28 + 45 + 12 = 85
        # C[1][1] = 4*8 + 5*1 + 6*3 = 32 + 5 + 18 = 55
        expected = [
            [Fraction(31), Fraction(19)],
            [Fraction(85), Fraction(55)],
        ]
        m, n, p = len(A), len(B), len(B[0])
        C = [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        self.assertEqual(C, expected)

    def test_matriz_inversa_gauss_jordan(self):
        """Inversión de matriz 2x2: A = [[1, 2], [3, 4]] => A^-1 = [[-2, 1], [3/2, -1/2]]."""
        A = [
            [Fraction(1), Fraction(2)],
            [Fraction(3), Fraction(4)],
        ]
        # Det = -2
        # A^-1 = (1/-2) * [[4, -2], [-3, 1]] = [[-2, 1], [3/2, -1/2]]
        aug = [
            [Fraction(1), Fraction(2), Fraction(1), Fraction(0)],
            [Fraction(3), Fraction(4), Fraction(0), Fraction(1)],
        ]
        # Paso 1: f2 -> f2 - 3*f1 = [0, -2, -3, 1]
        aug[1] = [aug[1][c] - Fraction(3) * aug[0][c] for c in range(4)]
        # Normalizar f2: f2 -> (-1/2)*f2 = [0, 1, 3/2, -1/2]
        aug[1] = [aug[1][c] * Fraction(-1, 2) for c in range(4)]
        # Eliminar hacia arriba: f1 -> f1 - 2*f2
        aug[0] = [aug[0][c] - Fraction(2) * aug[1][c] for c in range(4)]

        inv = [[aug[i][j + 2] for j in range(2)] for i in range(2)]
        expected = [
            [Fraction(-2), Fraction(1)],
            [Fraction(3, 2), Fraction(-1, 2)],
        ]
        self.assertEqual(inv, expected)

    # --------------------------------------------------------------------------
    # Módulo 4: Determinantes
    # --------------------------------------------------------------------------
    def test_determinante_2x2(self):
        """det([[1, 2], [3, 4]]) = 4 - 6 = -2."""
        A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        det, _ = md.calcular_determinante_triangulacion(A, verbose=False)
        self.assertEqual(det, Fraction(-2))

    def test_determinante_3x3_triangulacion(self):
        """det([[1, 2, 3], [0, 4, 5], [1, 0, 6]]) = 1*(24) - 2*(-5) + 3*(-4) = 24 + 10 - 12 = 22."""
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(0), Fraction(4), Fraction(5)],
            [Fraction(1), Fraction(0), Fraction(6)],
        ]
        det, _ = md.calcular_determinante_triangulacion(A, verbose=False)
        self.assertEqual(det, Fraction(22))

    def test_determinante_singular_cero(self):
        """det([[1, 2], [2, 4]]) = 0."""
        A = [[Fraction(1), Fraction(2)], [Fraction(2), Fraction(4)]]
        det, _ = md.calcular_determinante_triangulacion(A, verbose=False)
        self.assertEqual(det, Fraction(0))

    # --------------------------------------------------------------------------
    # Teoremas
    # --------------------------------------------------------------------------
    def test_resumen_teoremas_ejecutan_sin_error(self):
        """Comprueba que las funciones de teoremas se llamen limpiamente."""
        try:
            rt.mostrar_teoremas_sistemas()
            rt.mostrar_teoremas_vectores()
            rt.mostrar_teoremas_matrices()
            rt.mostrar_teoremas_determinantes()
        except Exception as e:
            self.fail(f"mostrar_teoremas falló con excepción: {e}")


if __name__ == "__main__":
    unittest.main()
