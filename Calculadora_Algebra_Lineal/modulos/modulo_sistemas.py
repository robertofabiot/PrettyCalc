"""================================================================================
UNIVERSIDAD AMERICANA (UAM) - FIA | ÁLGEBRA LINEAL (MTM0120) - GRUPO 4
MÓDULO 1: Sistemas de Ecuaciones Lineales (SEL)
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path
from typing import List, Optional, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Soporte para imports relativos o absolutos sin depender de cómo se ejecute
try:
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_sistemas
except ImportError:
    calc_dir = Path(__file__).resolve().parent.parent
    parent_dir = calc_dir.parent
    for p in (str(calc_dir), str(parent_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_sistemas
    except ImportError:
        from teoremas.resumen_teoremas import mostrar_teoremas_sistemas



def parse_scalar(text: str) -> Fraction:
    """Convierte texto en una fracción exacta Fraction."""
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
    """Representación limpia de fracción irreducible."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def read_scalar(prompt: str) -> Fraction:
    """Lectura robusta de escalares con reintento."""
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   ⚠️  Entrada inválida ({exc}). Intente de nuevo (ej. 4, -2/3, 0.5):")


def read_positive_int(prompt: str) -> int:
    """Lectura de enteros positivos mayores a cero."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val <= 0:
                print("   ⚠️  Debe ser un entero positivo.")
                continue
            return val
        except ValueError:
            print("   ⚠️  Entrada inválida. Ingrese un número entero.")


def print_augmented_matrix(
    matrix: List[List[Fraction]],
    num_vars: int,
    title: str = ""
) -> None:
    """Imprime la matriz aumentada [A | b] con bordes limpios y separador."""
    if title:
        print(f"\n--- {title} ---")
    rows = len(matrix)
    cols = len(matrix[0])
    cells = [[fmt(matrix[r][c]) for c in range(cols)] for r in range(rows)]
    widths = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]

    for r in range(rows):
        left = "  ".join(cells[r][c].rjust(widths[c]) for c in range(num_vars))
        right = "  ".join(cells[r][c].rjust(widths[c]) for c in range(num_vars, cols))
        print(f"│  {left}  │  {right}  │")


def resolver_sel_interactivo() -> None:
    """Ejecuta la resolución completa de un sistema lineal con pasos y clasificación."""
    print("\n" + "-" * 65)
    print("RESOLUCIÓN DE SISTEMA LINEAL POR ELIMINACIÓN POR FILAS")
    print("-" * 65)

    m = read_positive_int("Ingrese el número de ecuaciones (filas m): ")
    n = read_positive_int("Ingrese el número de incógnitas (variables n): ")

    print(f"\nIngrese los coeficientes de la matriz aumentada [{m}×{n+1}]:")
    print("(Puede ingresar enteros, fracciones como '3/4' o decimales como '0.5')\n")

    matrix: List[List[Fraction]] = []
    for i in range(m):
        row: List[Fraction] = []
        print(f">> Ecuación {i+1}:")
        for j in range(n):
            val = read_scalar(f"   Coeficiente x{j+1}: ")
            row.append(val)
        b_val = read_scalar(f"   Término independiente b{i+1}: ")
        row.append(b_val)
        matrix.append(row)

    # Mostrar matriz inicial
    print_augmented_matrix(matrix, num_vars=n, title="Paso 0: Matriz Aumentada Inicial [A | b]")

    # Copia de trabajo
    mat = [[c for c in row] for row in matrix]
    step = 1
    pivot_row = 0

    # 1. Eliminación hacia adelante (Gauss)
    for col in range(n):
        if pivot_row >= m:
            break

        selected_row = None
        for r in range(pivot_row, m):
            if mat[r][col] != Fraction(0, 1):
                selected_row = r
                break

        if selected_row is None:
            continue

        if selected_row != pivot_row:
            mat[pivot_row], mat[selected_row] = mat[selected_row], mat[pivot_row]
            print_augmented_matrix(
                mat,
                num_vars=n,
                title=f"Paso {step}: Fila {pivot_row+1} ↔ Fila {selected_row+1} (Intercambio)"
            )
            step += 1

        pivot_val = mat[pivot_row][col]
        for r in range(pivot_row + 1, m):
            target_val = mat[r][col]
            if target_val != Fraction(0, 1):
                factor = - (target_val / pivot_val)
                for c in range(n + 1):
                    mat[r][c] = mat[r][c] + (factor * mat[pivot_row][c])

                desc = f"f_{r+1} → f_{r+1} + ({fmt(factor)})·f_{pivot_row+1}"
                print_augmented_matrix(mat, num_vars=n, title=f"Paso {step}: {desc}")
                step += 1

        pivot_row += 1

    # 2. Eliminación hacia atrás (Gauss-Jordan)
    for r in range(m - 1, -1, -1):
        lead_col = None
        for c in range(n):
            if mat[r][c] != Fraction(0, 1):
                lead_col = c
                break

        if lead_col is not None:
            lead_val = mat[r][lead_col]
            if lead_val != Fraction(1, 1):
                scale = Fraction(1, 1) / lead_val
                for c in range(n + 1):
                    mat[r][c] = mat[r][c] * scale
                print_augmented_matrix(
                    mat,
                    num_vars=n,
                    title=f"Paso {step}: f_{r+1} → ({fmt(scale)})·f_{r+1}"
                )
                step += 1

            for up_r in range(r - 1, -1, -1):
                up_val = mat[up_r][lead_col]
                if up_val != Fraction(0, 1):
                    factor = - up_val
                    for c in range(n + 1):
                        mat[up_r][c] = mat[up_r][c] + (factor * mat[r][c])
                    desc = f"f_{up_r+1} → f_{up_r+1} + ({fmt(factor)})·f_{r+1}"
                    print_augmented_matrix(mat, num_vars=n, title=f"Paso {step}: {desc}")
                    step += 1

    # 3. Clasificación según Rouché-Frobenius
    rank_a = 0
    rank_aug = 0
    is_inconsistent = False
    inconsistent_row = -1
    pivot_cols: List[int] = []

    for r in range(m):
        has_a = any(mat[r][c] != Fraction(0, 1) for c in range(n))
        has_b = (mat[r][n] != Fraction(0, 1))

        if has_a:
            rank_a += 1
            rank_aug += 1
            for c in range(n):
                if mat[r][c] != Fraction(0, 1):
                    pivot_cols.append(c)
                    break
        else:
            if has_b:
                rank_aug += 1
                is_inconsistent = True
                inconsistent_row = r

    pivot_cols.sort()
    basic_vars = list(pivot_cols)
    free_vars = [c for c in range(n) if c not in basic_vars]

    print("\n" + "=" * 65)
    print("                     DIAGNÓSTICO Y RESULTADOS                 ")
    print("=" * 65)
    print(f" • Rango de la matriz de coeficientes: rango(A) = {rank_a}")
    print(f" • Rango de la matriz aumentada:        rango([A|b]) = {rank_aug}")
    print(f" • Variables básicas ({len(basic_vars)}) : {[f'x{c+1}' for c in basic_vars] if basic_vars else 'Ninguna'}")
    print(f" • Variables libres  ({len(free_vars)}) : {[f'x{c+1}' for c in free_vars] if free_vars else 'Ninguna'}")

    if is_inconsistent or rank_a < rank_aug:
        print("\n🔴 CLASIFICACIÓN: SISTEMA INCONSISTENTE (SIN SOLUCIÓN)")
        print(f"   • Motivo: rango(A) = {rank_a} ≠ rango([A|b]) = {rank_aug}.")
        print(f"   • La fila {inconsistent_row+1} produce la contradicción: [0 ... 0 | {fmt(mat[inconsistent_row][n])}] (0 = c con c ≠ 0).")
    elif rank_a == n:
        print("\n🟢 CLASIFICACIÓN: SISTEMA CONSISTENTE DETERMINADO (SCD - SOLUCIÓN ÚNICA)")
        print(f"   • Motivo: rango(A) = rango([A|b]) = n = {n}.")
        print("\nSolución Única:")
        for i in range(n):
            val = mat[i][n]
            print(f"   • x{i+1} = {fmt(val)}  (Decimal: {float(val):.4f})")

        print("\nComprobación por Sustitución Directa:")
        for i in range(m):
            lhs = sum(matrix[i][j] * mat[j][n] for j in range(n))
            rhs = matrix[i][n]
            print(f"   ✓ Ecuación {i+1}: {fmt(lhs)} == {fmt(rhs)}  (Verificado)")
    else:
        print("\n🟡 CLASIFICACIÓN: SISTEMA CONSISTENTE INDETERMINADO (SCI - INFINITAS SOLUCIONES)")
        print(f"   • Motivo: rango(A) = rango([A|b]) = {rank_a} < n = {n}.")
        print(f"   • Grados de libertad (variables libres): {len(free_vars)}")
        print("\nSolución Paramétrica:")
        for r_idx, lead_c in enumerate(basic_vars):
            b_val = mat[r_idx][n]
            terms = [fmt(b_val)] if b_val != Fraction(0, 1) else []
            for f_v in free_vars:
                coeff = - mat[r_idx][f_v]
                if coeff != Fraction(0, 1):
                    terms.append(f"({fmt(coeff)})*x{f_v+1}")
            expr = " + ".join(terms) if terms else "0"
            print(f"   • x{lead_c+1} = {expr}")
        for f_v in free_vars:
            print(f"   • x{f_v+1} es variable libre (parámetro real ∈ ℝ)")


def menu_sistemas() -> None:
    """Menú principal interactivo del Módulo 1 con Logotipo ASCII requerido."""
    while True:
        print("\n" + "=" * 54)
        print(" [ [1 2 | 3] ] MÓDULO: SISTEMAS DE ECUACIONES (SEL)")
        print(" [ [0 1 | 5] ] Métodos: Gauss, Gauss-Jordan")
        print("=" * 54)
        print(" 0. Ver Teoremas Clave del Módulo")
        print(" 1. Resolver Sistema de Ecuaciones Lineales [A | b]")
        print(" 2. Volver al Menú Principal")
        print("=" * 54)

        opc = input("Seleccione una opción (0-2): ").strip()

        if opc == "0":
            mostrar_teoremas_sistemas()
            input("\nPresione ENTER para continuar...")
        elif opc == "1":
            resolver_sel_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            break
        else:
            print("   ⚠️  Opción no reconocida. Ingrese 0, 1 o 2.")


if __name__ == "__main__":
    menu_sistemas()
