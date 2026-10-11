"""================================================================================
UNIVERSIDAD AMERICANA (UAM) - FIA | ÁLGEBRA LINEAL (MTM0120) - GRUPO 4
MÓDULO 4: Determinantes y Propiedades
================================================================================

DEPRECADO: el cálculo vive en ``prettycalc.core.determinants``.
Este menú de consola solo lee datos, imprime el desglose y delega en el core.
"""

from __future__ import annotations

import sys
import warnings
from fractions import Fraction
from pathlib import Path
from typing import List, Optional, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_determinantes
except ImportError:
    calc_dir = Path(__file__).resolve().parent.parent
    parent_dir = calc_dir.parent
    for p in (str(calc_dir), str(parent_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_determinantes
    except ImportError:
        from teoremas.resumen_teoremas import mostrar_teoremas_determinantes



def parse_scalar(text: str) -> Fraction:
    """Convierte texto a Fraction exacta."""
    cleaned = text.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("Entrada vacía.")
    if "/" in cleaned:
        parts = cleaned.split("/")
        if len(parts) != 2:
            raise ValueError("Formato de fracción no válido.")
        num, den = int(parts[0]), int(parts[1])
        if den == 0:
            raise ZeroDivisionError("El denominador no puede ser cero.")
        return Fraction(num, den)
    return Fraction(cleaned)


def fmt(val: Fraction) -> str:
    """Formateo limpio de fracciones."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def read_scalar(prompt: str) -> Fraction:
    """Lectura robusta de escalares."""
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   ⚠️  Entrada inválida ({exc}). Intente de nuevo (ej. 5, -1/3, 0.5):")


def read_positive_int(prompt: str) -> int:
    """Lectura de enteros positivos."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val <= 0:
                print("   ⚠️  Debe ser un número entero positivo.")
                continue
            return val
        except ValueError:
            print("   ⚠️  Entrada inválida. Ingrese un número entero.")


def print_matrix(matrix: List[List[Fraction]], title: str = "") -> None:
    """Imprime una matriz alineada."""
    if title:
        print(f"\n--- {title} ---")
    rows = len(matrix)
    cols = len(matrix[0])
    cells = [[fmt(matrix[r][c]) for c in range(cols)] for r in range(rows)]
    widths = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]
    for r in range(rows):
        row_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(cols))
        print(f"│  {row_str}  │")


def read_square_matrix(n: int, name: str = "A") -> List[List[Fraction]]:
    """Lee una matriz cuadrada n×n."""
    print(f"\nIngrese las entradas de la matriz cuadrada {name} ({n}×{n}):")
    mat: List[List[Fraction]] = []
    for i in range(n):
        row: List[Fraction] = []
        print(f"  Fila {i+1}:")
        for j in range(n):
            row.append(read_scalar(f"     {name}[{i+1},{j+1}]: "))
        mat.append(row)
    return mat


def _core_matrix(matrix: List[List[Fraction]]):
    """Importa el core en el momento de uso para no acoplar el arranque del menú."""
    from prettycalc.core.types import Matrix

    return Matrix(matrix)


def calcular_determinante_triangulacion(
    matrix: List[List[Fraction]],
    verbose: bool = True
) -> Tuple[Fraction, List[List[Fraction]]]:
    """Delegado deprecado de ``prettycalc.core.determinants.determinant_triangulation``.

    Se conserva la firma (determinante, matriz triangular como listas) para el
    menú de consola y las pruebas históricas. El algoritmo ya no vive aquí.
    """
    warnings.warn(
        "calcular_determinante_triangulacion está deprecado; "
        "use prettycalc.core.determinants.determinant_triangulation.",
        DeprecationWarning,
        stacklevel=2,
    )
    from prettycalc.core.determinants import determinant_triangulation

    result = determinant_triangulation(_core_matrix(matrix))
    triangular = result.triangular_matrix
    triangular_rows = triangular.to_list() if triangular is not None else [
        [cell for cell in row] for row in matrix
    ]
    if verbose:
        for step in result.tracer:
            print_matrix(
                step.matrix.to_list(),
                title=f"Paso {step.step_number}: {step.heuristic_text}",
            )
    return result.value, triangular_rows


def determinante_2x2_interactivo() -> None:
    """Operación 1: Determinante 2×2 directo."""
    print("\n" + "-" * 60)
    print("DETERMINANTE DE MATRIZ 2×2: det(A) = a·d - b·c")
    print("-" * 60)
    A = read_square_matrix(2, "A")
    print_matrix(A, "Matriz A (2×2)")

    from prettycalc.core.determinants import determinant_2x2

    result = determinant_2x2(_core_matrix(A))
    print("\nCálculo Detallado:")
    for line in result.step_descriptions:
        print(f"   {line}")
    print(f"   (Decimal: {float(result.value):.4f})")
    mostrar_diagnostico_singularidad(result.value)


def determinante_3x3_interactivo() -> None:
    """Operación 2: Determinante 3×3 por Regla de Sarrus."""
    print("\n" + "-" * 60)
    print("DETERMINANTE DE MATRIZ 3×3 (REGLA DE SARRUS)")
    print("-" * 60)
    A = read_square_matrix(3, "A")
    print_matrix(A, "Matriz A (3×3)")

    from prettycalc.core.determinants import determinant_sarrus_3x3

    result = determinant_sarrus_3x3(_core_matrix(A))
    print("\nCálculo por Regla de Sarrus:")
    for line in result.step_descriptions:
        print(f"   {line}")
    print(f"   (Decimal: {float(result.value):.4f})")
    mostrar_diagnostico_singularidad(result.value)


def determinante_nxn_interactivo() -> None:
    """Operación 3: Determinante n×n por Triangulación Gaussiana."""
    print("\n" + "-" * 60)
    print("DETERMINANTE DE MATRIZ n×n (MÉTODO DE TRIANGULACIÓN GAUSSIANA)")
    print("-" * 60)
    n = read_positive_int("Dimensión n de la matriz cuadrada: ")
    A = read_square_matrix(n, "A")
    print_matrix(A, f"Matriz Inicial A ({n}×{n})")

    print("\n--- Proceso de Triangulación Paso a Paso ---")
    det, triangular = calcular_determinante_triangulacion(A, verbose=True)

    print("\n" + "=" * 60)
    print("                     RESULTADO DEL DETERMINANTE                ")
    print("=" * 60)
    print_matrix(triangular, f"Matriz Triangular Superior Resultante U")

    diag_terms = [f"({fmt(triangular[i][i])})" for i in range(n)]
    print(f"\n   det(A) = (±1) · [{' · '.join(diag_terms)}]")
    print(f"   det(A) = {fmt(det)}  (Decimal: {float(det):.4f})")
    mostrar_diagnostico_singularidad(det)


def mostrar_diagnostico_singularidad(det: Fraction) -> None:
    """Imprime el análisis de invertibilidad derivado del determinante."""
    print("\n--- Diagnóstico de Invertibilidad y Rango ---")
    if det != Fraction(0, 1):
        print(f"   🟢 det(A) ≠ 0 ({fmt(det)})")
        print("      • La matriz A es NO SINGULAR (INVERTIBLE). Existe A⁻¹.")
        print("      • Las filas y columnas de A son LINEALMENTE INDEPENDIENTES.")
        print("      • El sistema homogéneo A·x = 0 tiene únicamente la solución trivial x = 0.")
        print("      • Rango(A) = n (Rango completo).")
    else:
        print("   🔴 det(A) = 0")
        print("      • La matriz A es SINGULAR (NO INVERTIBLE). No existe A⁻¹.")
        print("      • Las filas y columnas de A son LINEALMENTE DEPENDIENTES.")
        print("      • El sistema homogéneo A·x = 0 admite soluciones no triviales (infinitas soluciones).")
        print("      • Rango(A) < n.")


def menu_determinantes() -> None:
    """Menú principal del Módulo 4 con Logotipo ASCII."""
    warnings.warn(
        "El menú de consola de determinantes está deprecado. "
        "Use la pestaña Determinantes de PrettyCalc o prettycalc.core.determinants.",
        DeprecationWarning,
        stacklevel=2,
    )
    while True:
        print("\n" + "=" * 54)
        print(" | A |   det(A)   MÓDULO: DETERMINANTES Y PROPIEDADES")
        print(" | a  b | c  d |  Métodos: Triangulación y Cofactores")
        print("=" * 54)
        print(" 0. Ver Teoremas Clave del Módulo")
        print(" 1. Determinante de Matriz 2×2 (Fórmula Directa)")
        print(" 2. Determinante de Matriz 3×3 (Regla de Sarrus)")
        print(" 3. Determinante de Matriz n×n (Triangulación Gaussiana)")
        print(" 4. Volver al Menú Principal")
        print("=" * 54)

        opc = input("Seleccione una opción (0-4): ").strip()

        if opc == "0":
            mostrar_teoremas_determinantes()
            input("\nPresione ENTER para continuar...")
        elif opc == "1":
            determinante_2x2_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            determinante_3x3_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "3":
            determinante_nxn_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "4":
            break
        else:
            print("   ⚠️  Opción no válida. Ingrese un número entre 0 y 4.")


if __name__ == "__main__":
    menu_determinantes()
