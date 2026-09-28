"""================================================================================
UNIVERSIDAD AMERICANA (UAM) - FIA | ÁLGEBRA LINEAL (MTM0120) - GRUPO 4
MÓDULO 2: Vectores e Independencia Lineal
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# Import seguro de teoremas
try:
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_vectores
except ImportError:
    calc_dir = Path(__file__).resolve().parent.parent
    parent_dir = calc_dir.parent
    for p in (str(calc_dir), str(parent_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_vectores
    except ImportError:
        from teoremas.resumen_teoremas import mostrar_teoremas_vectores



def parse_scalar(text: str) -> Fraction:
    """Convierte texto en Fraction exacta."""
    cleaned = text.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("Entrada vacía.")
    if "/" in cleaned:
        parts = cleaned.split("/")
        if len(parts) != 2:
            raise ValueError("Formato de fracción inválido.")
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
            print(f"   ⚠️  Entrada inválida ({exc}). Intente de nuevo (ej. 3, -1/2, 0.75):")


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


def print_matrix(
    matrix: List[List[Fraction]],
    title: str = "",
    split_col: Optional[int] = None,
    pivot_coords: Optional[Sequence[Tuple[int, int]]] = None
) -> None:
    """Imprime una matriz formateada con alineación tabular."""
    if title:
        print(f"\n--- {title} ---")
    if not matrix or not matrix[0]:
        print("│ [Matriz vacía] │")
        return

    rows = len(matrix)
    cols = len(matrix[0])
    piv_set = set(pivot_coords) if pivot_coords else set()

    cells = []
    for r in range(rows):
        row_cells = []
        for c in range(cols):
            val_str = fmt(matrix[r][c])
            if (r, c) in piv_set:
                row_cells.append(f"[{val_str}]")
            else:
                row_cells.append(val_str)
        cells.append(row_cells)

    widths = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]

    for r in range(rows):
        if split_col is None:
            row_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(cols))
            print(f"│  {row_str}  │")
        else:
            left_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col))
            right_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col, cols))
            print(f"│  {left_str}  │  {right_str}  │")


def print_vector(v: Sequence[Fraction], name: str = "v") -> None:
    """Imprime un vector en notación columna y transpuesta."""
    v_str = ", ".join(fmt(x) for x in v)
    print(f"   {name} = ({v_str})^T")


# ------------------------------------------------------------------------------
# Algoritmos de Independencia Lineal (Núcleo Programa 4)
# ------------------------------------------------------------------------------

def build_homogeneous_system(vectors: List[List[Fraction]], dim_n: int) -> List[List[Fraction]]:
    """Construye [A | 0] con vectores como columnas y vector cero a la derecha."""
    k = len(vectors)
    augmented: List[List[Fraction]] = []
    for i in range(dim_n):
        row = [vectors[j][i] for j in range(k)]
        row.append(Fraction(0, 1))
        augmented.append(row)
    return augmented


def row_echelon_reduction(
    matrix: List[List[Fraction]],
    num_vars: int,
    verbose: bool = True
) -> Tuple[List[List[Fraction]], List[Tuple[int, int]]]:
    """Reduce la matriz a Forma Escalonada por Filas (REF) identificando pivotes."""
    mat = [[c for c in row] for row in matrix]
    m = len(mat)
    pivot_row = 0
    pivots: List[Tuple[int, int]] = []
    step = 1

    for col in range(num_vars):
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
            if verbose:
                print_matrix(
                    mat,
                    title=f"Paso {step}: Fila {pivot_row+1} ↔ Fila {selected_row+1} (Intercambio)",
                    split_col=num_vars
                )
                step += 1

        pivot_val = mat[pivot_row][col]
        pivots.append((pivot_row, col))

        for r in range(pivot_row + 1, m):
            target_val = mat[r][col]
            if target_val != Fraction(0, 1):
                factor = - (target_val / pivot_val)
                for c in range(len(mat[0])):
                    mat[r][c] = mat[r][c] + (factor * mat[pivot_row][c])

                if verbose:
                    desc = f"f_{r+1} → f_{r+1} + ({fmt(factor)})·f_{pivot_row+1}"
                    print_matrix(mat, title=f"Paso {step}: {desc}", split_col=num_vars)
                    step += 1

        pivot_row += 1

    return mat, pivots


def back_substitution_rref(
    ref_matrix: List[List[Fraction]],
    pivots: List[Tuple[int, int]],
    num_vars: int
) -> List[List[Fraction]]:
    """Lleva la matriz REF a RREF (Gauss-Jordan) para despejar dependencias exactas."""
    mat = [[c for c in row] for row in ref_matrix]
    for r_idx, c_idx in reversed(pivots):
        pivot_val = mat[r_idx][c_idx]
        if pivot_val != Fraction(1, 1):
            scale = Fraction(1, 1) / pivot_val
            for c in range(len(mat[0])):
                mat[r_idx][c] = mat[r_idx][c] * scale

        for up_r in range(r_idx - 1, -1, -1):
            up_val = mat[up_r][c_idx]
            if up_val != Fraction(0, 1):
                factor = - up_val
                for c in range(len(mat[0])):
                    mat[up_r][c] = mat[up_r][c] + (factor * mat[r_idx][c])
    return mat


def extract_nontrivial_solution(
    rref_matrix: List[List[Fraction]],
    pivots: List[Tuple[int, int]],
    num_vars: int
) -> Optional[List[Fraction]]:
    """Calcula coeficientes no triviales c ≠ 0 para A·c = 0 cuando es L.D."""
    pivot_cols = {col for _, col in pivots}
    free_vars = [c for c in range(num_vars) if c not in pivot_cols]
    if not free_vars:
        return None

    target_free = free_vars[0]
    weights = [Fraction(0, 1) for _ in range(num_vars)]
    weights[target_free] = Fraction(1, 1)

    for r_idx, piv_col in pivots:
        coeff = rref_matrix[r_idx][target_free]
        weights[piv_col] = - coeff

    return weights


def evaluar_independencia_interactivo() -> None:
    """Operación 1: Evaluación completa de Independencia y Dependencia Lineal."""
    print("\n" + "=" * 65)
    print("EVALUACIÓN DE INDEPENDENCIA Y DEPENDENCIA LINEAL EN ℝⁿ")
    print("=" * 65)

    k = read_positive_int("Ingrese la cantidad de vectores (k): ")
    n = read_positive_int("Ingrese la dimensión del espacio (n para ℝⁿ): ")

    if k > n:
        print(f"\n💡 [Observación Teórica]: Ha ingresado k = {k} vectores en ℝ^{n}.")
        print(f"   Por Teorema de Dimensión, como k ({k}) > n ({n}), el conjunto será")
        print("   necesariamente Linealmente Dependiente (L.D.). Se verificará por reducción.")

    vectors: List[List[Fraction]] = []
    print(f"\nIngrese las componentes de los {k} vectores:")
    for j in range(k):
        print(f">> Vector v_{j+1} ∈ ℝ^{n}:")
        v: List[Fraction] = []
        for i in range(n):
            val = read_scalar(f"   v_{j+1}[{i+1}]: ")
            v.append(val)
        vectors.append(v)

    print("\nConjunto ingresado:")
    for j, v in enumerate(vectors):
        print_vector(v, f"v_{j+1}")

    # Verificar vector nulo
    zero_idx = None
    for idx, v in enumerate(vectors):
        if all(x == Fraction(0, 1) for x in v):
            zero_idx = idx
            break

    # Construcción y reducción
    aug = build_homogeneous_system(vectors, n)
    print_matrix(aug, title="Matriz Aumentada Inicial [A | 0] del Sistema Homogéneo", split_col=k)

    print("\n--- Reducción por Filas a Forma Escalonada (REF) ---")
    ref_mat, pivots = row_echelon_reduction(aug, num_vars=k, verbose=True)

    num_pivots = len(pivots)
    pivot_cols = [c for _, c in pivots]
    free_vars = [c for c in range(k) if c not in pivot_cols]
    is_li = (num_pivots == k)

    print("\n" + "=" * 65)
    print("                       VEREDICTO TEÓRICO                      ")
    print("=" * 65)
    print_matrix(
        ref_mat,
        title="Forma Escalonada por Filas (REF) con Pivotes [entre corchetes]",
        split_col=k,
        pivot_coords=pivots
    )

    print(f"\n • Cantidad de vectores (k)       : {k}")
    print(f" • Dimensión del espacio (n)      : ℝ^{n}")
    print(f" • Número de pivotes (rango de A) : {num_pivots}")
    print(f" • Variables básicas              : {[f'c_{c+1}' for c in pivot_cols] if pivot_cols else 'Ninguna'}")
    print(f" • Variables libres               : {[f'c_{c+1}' for c in free_vars] if free_vars else 'Ninguna (0 libres)'}")

    if is_li:
        print("\n🟢 VEREDICTO: EL CONJUNTO ES LINEALMENTE INDEPENDIENTE (L.I.)")
        print("   " + "-" * 58)
        print("   Justificación Teórica:")
        print(f"   1. Número de pivotes = {num_pivots} coincide con el número de vectores (k = {k}).")
        print("   2. No existen variables libres en el sistema homogéneo A·c = 0.")
        print("   3. La única solución a c₁·v₁ + ... + cₖ·vₖ = 0 es la SOLUCIÓN TRIVIAL (c = 0).")
    else:
        print("\n🔴 VEREDICTO: EL CONJUNTO ES LINEALMENTE DEPENDIENTE (L.D.)")
        print("   " + "-" * 58)
        print("   Justificación Teórica:")
        print(f"   1. Número de pivotes = {num_pivots} < cantidad de vectores k = {k}.")
        print(f"   2. Existen {len(free_vars)} variable(s) libre(s): {[f'c_{c+1}' for c in free_vars]}.")
        print("   3. El sistema homogéneo admite SOLUCIONES NO TRIVIALES (c ≠ 0).")

        if k > n:
            print(f"   📌 Teorema Aplicado: k = {k} > n = {n}. En ℝⁿ ningún conjunto de más de n vectores puede ser L.I.")
        if zero_idx is not None:
            print(f"   📌 Teorema Aplicado: El vector v_{zero_idx+1} es el vector nulo 0. Todo conjunto con el 0 es L.D.")

        # Obtener y mostrar combinación no trivial
        rref = back_substitution_rref(ref_mat, pivots, num_vars=k)
        weights = extract_nontrivial_solution(rref, pivots, num_vars=k)
        if weights:
            print("\n--- Demostración de Combinación Lineal No Trivial Nula ---")
            terms = [f"({fmt(w)})·v_{i+1}" for i, w in enumerate(weights) if w != Fraction(0, 1)]
            print(f"   {' + '.join(terms)} = 0")
            print("   Verificación componente a componente:")
            for dim in range(n):
                acc = sum(weights[j] * vectors[j][dim] for j in range(k))
                print(f"      ✓ Componente {dim+1}: {fmt(acc)} (exactamente 0)")


def evaluar_combinacion_lineal_interactivo() -> None:
    """Operación 2: Determina si un vector b es combinación lineal de {v1, ..., vk}."""
    print("\n" + "-" * 65)
    print("EVALUACIÓN DE COMBINACIÓN LINEAL: c₁·v₁ + ... + cₖ·vₖ = b")
    print("-" * 65)

    k = read_positive_int("Cantidad de vectores generadores (k): ")
    n = read_positive_int("Dimensión del espacio (n para ℝⁿ): ")

    vectors: List[List[Fraction]] = []
    for j in range(k):
        print(f"\nVector v_{j+1} ∈ ℝ^{n}:")
        v = [read_scalar(f"   v_{j+1}[{i+1}]: ") for i in range(n)]
        vectors.append(v)

    print(f"\nVector objetivo b ∈ ℝ^{n}:")
    b = [read_scalar(f"   b[{i+1}]: ") for i in range(n)]

    # Construir [A | b]
    aug = []
    for i in range(n):
        row = [vectors[j][i] for j in range(k)]
        row.append(b[i])
        aug.append(row)

    print_matrix(aug, title="Matriz Aumentada [A | b]", split_col=k)

    # Reducción por filas
    ref_mat, pivots = row_echelon_reduction(aug, num_vars=k, verbose=True)

    # Inconsistencia
    is_inconsistent = False
    for r in range(n):
        all_zeros = all(ref_mat[r][c] == Fraction(0, 1) for c in range(k))
        if all_zeros and ref_mat[r][k] != Fraction(0, 1):
            is_inconsistent = True
            break

    if is_inconsistent:
        print("\n🔴 RESULTADO: El vector b NO ES COMBINACIÓN LINEAL del conjunto.")
        print("   El sistema A·c = b es INCONSISTENTE (fila [0 ... 0 | c ≠ 0]).")
    else:
        print("\n🟢 RESULTADO: El vector b SÍ ES COMBINACIÓN LINEAL del conjunto.")
        rref = back_substitution_rref(ref_mat, pivots, num_vars=k)
        print_matrix(rref, title="Forma Reducida [RREF | c*]", split_col=k)
        if len(pivots) == k:
            print("   Los coeficientes únicos son:")
            for idx, (_, col) in enumerate(pivots):
                val = rref[idx][k]
                print(f"      • c_{col+1} = {fmt(val)}")
        else:
            print("   Existen infinitas combinaciones lineales posibles (variables libres).")


def operaciones_basicas_vectores_interactivo() -> None:
    """Operación 3: Suma, resta, escalar y producto punto."""
    print("\n" + "-" * 65)
    print("OPERACIONES BÁSICAS CON VECTORES EN ℝⁿ")
    print("-" * 65)
    n = read_positive_int("Dimensión de los vectores (n): ")

    print(f"\nIngrese vector u ∈ ℝ^{n}:")
    u = [read_scalar(f"   u[{i+1}]: ") for i in range(n)]

    print(f"\nIngrese vector v ∈ ℝ^{n}:")
    v = [read_scalar(f"   v[{i+1}]: ") for i in range(n)]

    # Operaciones
    u_plus_v = [u[i] + v[i] for i in range(n)]
    u_minus_v = [u[i] - v[i] for i in range(n)]
    dot = sum(u[i] * v[i] for i in range(n))
    norm_sq_u = sum(u[i] ** 2 for i in range(n))
    norm_sq_v = sum(v[i] ** 2 for i in range(n))

    print("\n--- Resultados ---")
    print_vector(u_plus_v, "u + v")
    print_vector(u_minus_v, "u - v")
    print(f"   • Producto Punto u · v = {fmt(dot)}")
    print(f"   • Norma al cuadrado ||u||² = {fmt(norm_sq_u)}")
    print(f"   • Norma al cuadrado ||v||² = {fmt(norm_sq_v)}")
    if dot == Fraction(0, 1):
        print("   💡 [Propiedad]: u y v son ORTOGONALES (u · v = 0).")


def menu_vectores() -> None:
    """Menú principal del Módulo 2 con Logotipo ASCII requerido."""
    while True:
        print("\n" + "=" * 54)
        print(" MÓDULO: VECTORES E INDEPENDENCIA LINEAL")
        print(" Combinaciones Lineales, L.I. y L.D.")
        print(" 𝐴 𝑥 = 0")
        print("=" * 54)
        print(" 0. Ver Teoremas Clave del Módulo")
        print(" 1. Evaluar Independencia / Dependencia Lineal (L.I. o L.D.) en ℝⁿ")
        print(" 2. Evaluar Combinación Lineal (b = c₁v₁ + ... + cₖvₖ)")
        print(" 3. Operaciones Básicas en ℝⁿ (Suma, Resta, Producto Punto)")
        print(" 4. Volver al Menú Principal")
        print("=" * 54)

        opc = input("Seleccione una opción (0-4): ").strip()

        if opc == "0":
            mostrar_teoremas_vectores()
            input("\nPresione ENTER para continuar...")
        elif opc == "1":
            evaluar_independencia_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            evaluar_combinacion_lineal_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "3":
            operaciones_basicas_vectores_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "4":
            break
        else:
            print("   ⚠️  Opción no reconocida. Ingrese un número entre 0 y 4.")


if __name__ == "__main__":
    menu_vectores()
