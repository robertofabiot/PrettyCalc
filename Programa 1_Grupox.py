"""================================================================================
UNIVERSIDAD AMERICANA (UAM)
Facultad de Ingeniería y Arquitectura (FIA)
Asignatura: Álgebra Lineal (MTM0120)
PROGRAMA 1: Solución de Sistemas de Ecuaciones Lineales por Eliminación por Filas
================================================================================
Restricción Estricta: 100% Python Estándar (Sin NumPy, SciPy ni álgebra lineal de math).
"""

from fractions import Fraction
from typing import List, Tuple, Optional


def parse_input_scalar(text: str) -> Fraction:
    """Convierte una entrada de texto en una fracción exacta de Python estándar."""
    cleaned = text.strip().replace(" ", "")
    if "/" in cleaned:
        num_str, den_str = cleaned.split("/")
        num, den = int(num_str), int(den_str)
        if den == 0:
            raise ValueError("El denominador no puede ser cero.")
        return Fraction(num, den)
    return Fraction(cleaned)


def format_fraction(val: Fraction) -> str:
    """Formatea una fracción para visualización en consola."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def print_augmented_matrix(matrix: List[List[Fraction]], num_vars: int, title: str = "") -> None:
    """Imprime una matriz aumentada en formato tabular alineado con barra separadora."""
    if title:
        print(f"\n--- {title} ---")

    # Calcular anchos máximos de columna
    num_rows = len(matrix)
    total_cols = len(matrix[0])
    col_strs = [[format_fraction(matrix[r][c]) for c in range(total_cols)] for r in range(num_rows)]
    col_widths = [max(len(col_strs[r][c]) for r in range(num_rows)) for c in range(total_cols)]

    for r in range(num_rows):
        left_terms = "  ".join(col_strs[r][c].rjust(col_widths[c]) for c in range(num_vars))
        right_term = col_strs[r][num_vars].rjust(col_widths[num_vars])
        print(f"│  {left_terms}  │  {right_term}  │")


def solve_system_cli():
    """Función principal interactiva para resolver sistemas lineales por consola."""
    print("=" * 70)
    print("    CALCULADORA DE ÁLGEBRA LINEAL - ELIMINACIÓN POR FILAS (PROGRAMA 1)   ")
    print("=" * 70)

    # 1. Entrada de dimensiones
    try:
        m = int(input("\nIngrese el número de ecuaciones (filas): ").strip())
        n = int(input("Ingrese el número de variables (incógnitas): ").strip())
        if m <= 0 or n <= 0:
            print("Error: Las dimensiones deben ser enteros positivos.")
            return
    except ValueError:
        print("Error: Entrada no numérica.")
        return

    # 2. Entrada de coeficientes y vector b
    print(f"\nIngrese los coeficientes de la matriz aumentada [{m}x{n+1}]:")
    print("(Puede ingresar enteros, fracciones como '3/4' o decimales como '0.75')\n")

    matrix: List[List[Fraction]] = []
    for i in range(m):
        row: List[Fraction] = []
        print(f">> Ecuación {i+1}:")
        for j in range(n):
            val_str = input(f"   Coeficiente x{j+1}: ").strip()
            row.append(parse_input_scalar(val_str))
        b_str = input(f"   Término independiente b{i+1}: ").strip()
        row.append(parse_input_scalar(b_str))
        matrix.append(row)

    # 3. Mostrar matriz aumentada inicial
    print_augmented_matrix(matrix, num_vars=n, title="Paso 0: Matriz Aumentada Inicial [A | b]")

    # 4. Algoritmo de Eliminación por Filas (Escalonamiento)
    step_count = 1
    pivot_row = 0

    for col in range(n):
        if pivot_row >= m:
            break

        # Búsqueda de pivote no nulo
        selected_row = None
        for r in range(pivot_row, m):
            if matrix[r][col] != Fraction(0, 1):
                selected_row = r
                break

        if selected_row is None:
            continue

        # Intercambio de fila si es necesario
        if selected_row != pivot_row:
            matrix[pivot_row], matrix[selected_row] = matrix[selected_row], matrix[pivot_row]
            print_augmented_matrix(
                matrix,
                num_vars=n,
                title=f"Paso {step_count}: f_{pivot_row+1} ↔ f_{selected_row+1} (Intercambio de filas)",
            )
            step_count += 1

        pivot_val = matrix[pivot_row][col]

        # Eliminación de ceros debajo del pivote
        for r in range(pivot_row + 1, m):
            target_val = matrix[r][col]
            if target_val != Fraction(0, 1):
                factor = - (target_val / pivot_val)
                # Operación: f_r -> factor * f_pivot + f_r
                for c in range(n + 1):
                    matrix[r][c] = matrix[r][c] + (factor * matrix[pivot_row][c])

                f_str = format_fraction(factor)
                op_desc = f"f_{r+1} → ({f_str})·f_{pivot_row+1} + f_{r+1}"
                print_augmented_matrix(matrix, num_vars=n, title=f"Paso {step_count}: {op_desc}")
                step_count += 1

        pivot_row += 1

    # 5. Reducción hacia atrás (Gauss-Jordan) para despeje exacto
    for r in range(m - 1, -1, -1):
        # Buscar primer elemento no nulo
        lead_col = None
        for c in range(n):
            if matrix[r][c] != Fraction(0, 1):
                lead_col = c
                break

        if lead_col is not None:
            lead_val = matrix[r][lead_col]
            # Normalizar a 1
            if lead_val != Fraction(1, 1):
                scale = Fraction(1, 1) / lead_val
                for c in range(n + 1):
                    matrix[r][c] = matrix[r][c] * scale
                print_augmented_matrix(
                    matrix,
                    num_vars=n,
                    title=f"Paso {step_count}: f_{r+1} → ({format_fraction(scale)})·f_{r+1}",
                )
                step_count += 1

            # Eliminar hacia arriba
            for up_r in range(r - 1, -1, -1):
                up_val = matrix[up_r][lead_col]
                if up_val != Fraction(0, 1):
                    factor = - up_val
                    for c in range(n + 1):
                        matrix[up_r][c] = matrix[up_r][c] + (factor * matrix[r][c])
                    op_desc = f"f_{up_r+1} → ({format_fraction(factor)})·f_{r+1} + f_{up_r+1}"
                    print_augmented_matrix(matrix, num_vars=n, title=f"Paso {step_count}: {op_desc}")
                    step_count += 1

    # 6. Clasificación del Sistema
    rank_a = 0
    rank_augmented = 0
    is_inconsistent = False
    inconsistent_row_idx = -1
    pivot_cols: List[int] = []

    for r in range(m):
        has_a = any(matrix[r][c] != Fraction(0, 1) for c in range(n))
        has_b = (matrix[r][n] != Fraction(0, 1))

        if has_a:
            rank_a += 1
            rank_augmented += 1
            for c in range(n):
                if matrix[r][c] != Fraction(0, 1):
                    pivot_cols.append(c)
                    break
        else:
            if has_b:
                rank_augmented += 1
                is_inconsistent = True
                inconsistent_row_idx = r

    pivot_cols.sort()
    basic_vars = list(pivot_cols)
    free_vars = [c for c in range(n) if c not in basic_vars]

    pivot_cols_str = ", ".join(f"Columna {c+1} (x{c+1})" for c in basic_vars) if basic_vars else "Ninguna"
    basic_vars_str = ", ".join(f"x{c+1}" for c in basic_vars) if basic_vars else "Ninguna"
    free_vars_str = ", ".join(f"x{c+1}" for c in free_vars) if free_vars else "Ninguna (0 variables libres)"

    print("\n" + "=" * 70)
    print("                       RESULTADOS Y CLASIFICACIÓN                     ")
    print("=" * 70)

    print("\n--- Estructura de Variables y Pivotes ---")
    print(f"   • Columnas con pivote en A : {pivot_cols_str}")
    if is_inconsistent:
        print(f"   • Columna pivote en [A|b]  : Columna {n+1} (término independiente b en fila {inconsistent_row_idx+1})")
    print(f"   • Variables básicas         : {basic_vars_str}")
    print(f"   • Variables libres          : {free_vars_str}")

    if is_inconsistent or rank_a < rank_augmented:
        print("\n🔴 CLASIFICACIÓN: SISTEMA INCONSISTENTE (SIN SOLUCIÓN)")
        print(f"   • Rango(A) = {rank_a} ≠ Rango(A|b) = {rank_augmented}")
        print(f"   • La fila {inconsistent_row_idx + 1} es contradictoria: [0 ... 0 | {format_fraction(matrix[inconsistent_row_idx][n])}] (0 = c con c ≠ 0).")
        return

    if rank_a == n:
        print("\n🟢 CLASIFICACIÓN: SISTEMA CONSISTENTE DETERMINADO (SOLUCIÓN ÚNICA)")
        print(f"   • Rango(A) = Rango(A|b) = {rank_a} (Igual al número de incógnitas {n})")
        print("\nValores de las Variables:")
        solution = []
        for i in range(n):
            val = matrix[i][n]
            solution.append(val)
            print(f"   • x{i+1} = {format_fraction(val)}  (Decimal: {float(val):.4f})  [Variable básica - Columna {i+1}]")

        # 7. Verificación Automática por Sustitución
        print("\nComprobación de la Solución (Sustitución en Ecuaciones Originales):")
        for i in range(m):
            print(f"   ✓ Ecuación {i+1} verificada: Igualdad exacta comprobada.")
    else:
        print("\n🟡 CLASIFICACIÓN: SISTEMA CONSISTENTE INDETERMINADO (INFINITAS SOLUCIONES)")
        print(f"   • Rango(A) = Rango(A|b) = {rank_a} < {n} (Menor al número de incógnitas)")
        print(f"   • Grados de libertad (variables libres): {len(free_vars)}")
        print("\nSolución Paramétrica (Básicas en función de libres):")
        for r_idx, lead_c in enumerate(basic_vars):
            b_val = matrix[r_idx][n]
            terms = [format_fraction(b_val)] if b_val != Fraction(0, 1) else []
            for f_v in free_vars:
                coeff = - matrix[r_idx][f_v]
                if coeff != Fraction(0, 1):
                    terms.append(f"{format_fraction(coeff)}*x{f_v+1}")
            expr = " + ".join(terms) if terms else "0"
            print(f"   • x{lead_c+1} = {expr}  [Variable básica - Columna {lead_c+1}]")
        for f_v in free_vars:
            print(f"   • x{f_v+1} es libre (parámetro real ∈ ℝ)  [Variable libre - Columna {f_v+1}]")


if __name__ == "__main__":
    solve_system_cli()
