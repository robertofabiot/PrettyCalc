"""================================================================================
UNIVERSIDAD AMERICANA (UAM)
Facultad de Ingeniería y Arquitectura (FIA)
Asignatura: Álgebra Lineal (MTM0120)
PROGRAMA 4: Independencia y Dependencia Lineal en ℝⁿ
Grupo 4
================================================================================
Restricción estricta del Contrato Didáctico:
    100% Python estándar. Prohibido NumPy, SciPy y álgebra lineal de math.
    Toda la aritmética se realiza con fractions.Fraction (exacta, sin redondeo).

Fundamento algebraico:
    1. Un conjunto de vectores {v₁, v₂, ..., vₖ} en ℝⁿ es Linealmente Independiente (L.I.)
       si y solo si la ecuación vectorial homogénea:
           c₁·v₁ + c₂·v₂ + ... + cₖ·vₖ = 0
       admite ÚNICAMENTE la solución trivial:
           c₁ = c₂ = ... = cₖ = 0.
    2. Si existe al menos una solución no trivial (donde al menos un cᵢ ≠ 0),
       el conjunto es Linealmente Dependiente (L.D.).
    3. Construcción del Sistema Homogéneo:
       Se forma la ecuación matricial A·c = 0, donde las columnas de A (dimensión n × k)
       son los vectores v₁, v₂, ..., vₖ. La matriz aumentada del sistema homogéneo es [A | 0].
    4. Reducción a Forma Escalonada por Filas (REF):
       - Sea r el número de pivotes de la matriz A (r = rango(A)).
       - Total de incógnitas = k (número de vectores).
       - Variables básicas = r (columnas con pivote).
       - Variables libres = k - r (columnas sin pivote).
    5. Criterio de Decisión:
       - Si r == k: Cada columna tiene pivote (0 variables libres).
         El sistema homogéneo solo tiene la solución trivial → CONJUNTO L.I.
       - Si r < k: Hay al menos una variable libre (k - r ≥ 1).
         El sistema homogéneo tiene infinitas soluciones no triviales → CONJUNTO L.D.
    6. Teorema de Dimensión:
       - Si k > n (más vectores que la dimensión del espacio ℝⁿ),
         el número máximo de pivotes es r ≤ min(n, k) = n < k.
         Por ende, el conjunto es necesariamente L.D.
================================================================================
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple


# ------------------------------------------------------------------------------
# Utilidades de Entrada y Salida (Aritmética Exacta)
# ------------------------------------------------------------------------------

def parse_scalar(text: str) -> Fraction:
    """Convierte texto en una fracción exacta Fraction (enteros, a/b o decimales)."""
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
    """Formatea una fracción para visualización limpia en consola."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def read_scalar(prompt: str) -> Fraction:
    """Lee un escalar de consola con reintento automático ante entrada errónea."""
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   ⚠️  Entrada inválida ({exc}). Intente de nuevo (ej. 3, -4, 2/5, 0.75):")


def read_positive_int(prompt: str) -> int:
    """Lee un entero estrictamente positivo."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val <= 0:
                print("   ⚠️  Debe ser un número entero positivo mayor que cero.")
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
    """Imprime una matriz formateada con alineación y separador opcional de matriz aumentada."""
    if title:
        print(f"\n--- {title} ---")
    if not matrix or not matrix[0]:
        print("│ [Matriz vacía] │")
        return

    rows = len(matrix)
    cols = len(matrix[0])
    piv_set = set(pivot_coords) if pivot_coords else set()

    # Formateo de celdas destacando pivotes si se proporcionan
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


def print_vector_set(vectors: List[List[Fraction]], dim_n: int) -> None:
    """Muestra el conjunto de vectores ingresados en formato columna."""
    k = len(vectors)
    print(f"\nConjunto de {k} vectores en ℝ^{dim_n}:")
    for j, v in enumerate(vectors):
        v_str = ", ".join(fmt(x) for x in v)
        print(f"   v_{j+1} = ({v_str})^T")


# ------------------------------------------------------------------------------
# Algoritmos Algebraicos: Reducción por Filas y Análisis de Independencia
# ------------------------------------------------------------------------------

def build_homogeneous_system(vectors: List[List[Fraction]], dim_n: int) -> List[List[Fraction]]:
    """Construye la matriz aumentada [A | 0] del sistema homogéneo A·c = 0.
    
    A es de tamaño n × k, donde la columna j es el vector v_j.
    La columna aumentada k contiene el vector cero (0, ..., 0)^T.
    """
    k = len(vectors)
    augmented: List[List[Fraction]] = []
    for i in range(dim_n):
        row = [vectors[j][i] for j in range(k)]
        row.append(Fraction(0, 1))  # Vector cero del sistema homogéneo
        augmented.append(row)
    return augmented


def row_echelon_reduction(
    matrix: List[List[Fraction]],
    num_vars: int,
    verbose: bool = True
) -> Tuple[List[List[Fraction]], List[Tuple[int, int]]]:
    """Reduce la matriz a su Forma Escalonada por Filas (REF) mediante Eliminación Gaussiana.
    
    Parámetros:
        matrix: Matriz aumentada [A | 0] de tamaño m × (n_vars + 1).
        num_vars: Cantidad de incógnitas / columnas de la matriz de coeficientes A.
        verbose: Si True, imprime cada operación elemental de fila realizada.
        
    Retorna:
        (ref_matrix, pivots): Matriz en REF y lista de tuplas (fila, columna) con los pivotes.
    """
    # Copia profunda para no mutar el original
    mat = [[cell for cell in row] for row in matrix]
    m = len(mat)
    pivot_row = 0
    pivots: List[Tuple[int, int]] = []
    step = 1

    for col in range(num_vars):
        if pivot_row >= m:
            break

        # 1. Búsqueda de elemento pivote no nulo en la columna actual
        selected_row: Optional[int] = None
        for r in range(pivot_row, m):
            if mat[r][col] != Fraction(0, 1):
                selected_row = r
                break

        if selected_row is None:
            # Columna sin pivote (variable libre)
            continue

        # 2. Intercambio de filas si el pivote no está en pivot_row
        if selected_row != pivot_row:
            mat[pivot_row], mat[selected_row] = mat[selected_row], mat[pivot_row]
            if verbose:
                print_matrix(
                    mat,
                    title=f"Paso {step}: Fila {pivot_row + 1} ↔ Fila {selected_row + 1} (Intercambio de filas)",
                    split_col=num_vars
                )
                step += 1

        pivot_val = mat[pivot_row][col]
        pivots.append((pivot_row, col))

        # 3. Eliminación hacia adelante (hacer ceros debajo del pivote)
        for r in range(pivot_row + 1, m):
            target_val = mat[r][col]
            if target_val != Fraction(0, 1):
                factor = - (target_val / pivot_val)
                # Operación elemental: f_r -> f_r + factor * f_pivot
                for c in range(len(mat[0])):
                    mat[r][c] = mat[r][c] + (factor * mat[pivot_row][c])

                if verbose:
                    factor_str = fmt(factor)
                    op_desc = f"f_{r+1} → f_{r+1} + ({factor_str})·f_{pivot_row+1}"
                    print_matrix(
                        mat,
                        title=f"Paso {step}: {op_desc}",
                        split_col=num_vars
                    )
                    step += 1

        pivot_row += 1

    return mat, pivots


def back_substitution_rref(
    ref_matrix: List[List[Fraction]],
    pivots: List[Tuple[int, int]],
    num_vars: int,
    verbose: bool = False
) -> List[List[Fraction]]:
    """Convierte la matriz REF a Forma Escalonada Reducida por Filas (RREF) mediante Gauss-Jordan.
    
    Se utiliza para obtener los coeficientes canónicos de las variables básicas
    en función de las variables libres y explicitar la combinación no trivial.
    """
    mat = [[cell for cell in row] for row in ref_matrix]
    step = 1

    for r_idx, c_idx in reversed(pivots):
        pivot_val = mat[r_idx][c_idx]
        # 1. Normalizar el pivote a 1
        if pivot_val != Fraction(1, 1):
            scale = Fraction(1, 1) / pivot_val
            for c in range(len(mat[0])):
                mat[r_idx][c] = mat[r_idx][c] * scale
            if verbose:
                print_matrix(
                    mat,
                    title=f"Gauss-Jordan {step}: f_{r_idx+1} → ({fmt(scale)})·f_{r_idx+1}",
                    split_col=num_vars
                )
                step += 1

        # 2. Hacer ceros por encima del pivote
        for up_r in range(r_idx - 1, -1, -1):
            up_val = mat[up_r][c_idx]
            if up_val != Fraction(0, 1):
                factor = - up_val
                for c in range(len(mat[0])):
                    mat[up_r][c] = mat[up_r][c] + (factor * mat[r_idx][c])
                if verbose:
                    op_desc = f"f_{up_r+1} → f_{up_r+1} + ({fmt(factor)})·f_{r_idx+1}"
                    print_matrix(
                        mat,
                        title=f"Gauss-Jordan {step}: {op_desc}",
                        split_col=num_vars
                    )
                    step += 1

    return mat


def extract_nontrivial_relation(
    rref_matrix: List[List[Fraction]],
    pivots: List[Tuple[int, int]],
    num_vars: int
) -> Optional[List[Fraction]]:
    """Encuentra una solución no trivial c ≠ 0 para A·c = 0 cuando el conjunto es L.D.
    
    Asigna 1 a la primera variable libre y resuelve las básicas correspondientes.
    """
    pivot_cols = {col for _, col in pivots}
    free_vars = [c for c in range(num_vars) if c not in pivot_cols]
    if not free_vars:
        return None

    # Elegimos la primera variable libre y le asignamos 1 (resto de libres en 0)
    target_free = free_vars[0]
    weights = [Fraction(0, 1) for _ in range(num_vars)]
    weights[target_free] = Fraction(1, 1)

    for r_idx, piv_col in pivots:
        # En RREF: c_{piv_col} + sum(mat[r][f] * c_f) = 0 => c_{piv_col} = - mat[r][target_free]
        coeff = mat_val = rref_matrix[r_idx][target_free]
        weights[piv_col] = - coeff

    return weights


# ------------------------------------------------------------------------------
# Función de Evaluación y Diagnóstico Teórico Completo
# ------------------------------------------------------------------------------

def evaluate_linear_independence(
    vectors: List[List[Fraction]],
    dim_n: int,
    verbose: bool = True
) -> dict:
    """Evalúa la independencia lineal del conjunto de vectores en ℝⁿ.
    
    Retorna un diccionario completo con:
        - k: Cantidad de vectores
        - n: Dimensión del espacio
        - initial_matrix: Matriz aumentada inicial [A | 0]
        - ref_matrix: Matriz en Forma Escalonada por Filas
        - rref_matrix: Matriz en Forma Escalonada Reducida por Filas
        - pivots: Lista de posiciones pivote (fila, columna)
        - num_pivots: Cantidad de pivotes (rango de A)
        - basic_vars: Índices de variables básicas (0-indexed)
        - free_vars: Índices de variables libres (0-indexed)
        - is_linearly_independent: Booleano True si L.I., False si L.D.
        - theorem_k_greater_n: Booleano True si k > n
        - zero_vector_index: Índice del vector nulo si existe
        - nontrivial_solution: Coeficientes c_i no triviales si es L.D.
    """
    k = len(vectors)

    # 1. Comprobaciones teóricas preliminares
    zero_vector_idx: Optional[int] = None
    for idx, v in enumerate(vectors):
        if all(x == Fraction(0, 1) for x in v):
            zero_vector_idx = idx
            break

    k_greater_n = (k > dim_n)

    # 2. Construcción del sistema homogéneo [A | 0]
    aug_system = build_homogeneous_system(vectors, dim_n)

    if verbose:
        print_matrix(
            aug_system,
            title="Matriz Aumentada Inicial del Sistema Homogéneo [A | 0]",
            split_col=k
        )

    # 3. Reducción por filas a Forma Escalonada por Filas (REF)
    if verbose:
        print("\n" + "=" * 70)
        print("          PROCESO DE REDUCCIÓN POR FILAS A FORMA ESCALONADA (REF)     ")
        print("=" * 70)

    ref_mat, pivots = row_echelon_reduction(aug_system, num_vars=k, verbose=verbose)

    num_pivots = len(pivots)
    pivot_cols = [c for _, c in pivots]
    free_vars = [c for c in range(k) if c not in pivot_cols]
    is_li = (num_pivots == k)

    # 4. RREF y obtención de solución no trivial si es L.D.
    rref_mat = back_substitution_rref(ref_mat, pivots, num_vars=k, verbose=False)
    nontrivial_weights = extract_nontrivial_relation(rref_mat, pivots, num_vars=k) if not is_li else None

    return {
        "k": k,
        "n": dim_n,
        "initial_matrix": aug_system,
        "ref_matrix": ref_mat,
        "rref_matrix": rref_mat,
        "pivots": pivots,
        "num_pivots": num_pivots,
        "basic_vars": pivot_cols,
        "free_vars": free_vars,
        "is_linearly_independent": is_li,
        "theorem_k_greater_n": k_greater_n,
        "zero_vector_index": zero_vector_idx,
        "nontrivial_solution": nontrivial_weights,
    }


def display_results(results: dict, vectors: List[List[Fraction]]) -> None:
    """Muestra el reporte detallado con veredicto teórico explícito."""
    k = results["k"]
    n = results["n"]
    pivots = results["pivots"]
    num_pivots = results["num_pivots"]
    basic_vars = results["basic_vars"]
    free_vars = results["free_vars"]
    is_li = results["is_linearly_independent"]
    ref_mat = results["ref_matrix"]

    print("\n" + "=" * 70)
    print("                       INFORME Y VEREDICTO TEÓRICO                    ")
    print("=" * 70)

    # Matriz reducida final
    print_matrix(
        ref_mat,
        title="Forma Escalonada por Filas (REF) de [A | 0] (Pivotes entre corchetes)",
        split_col=k,
        pivot_coords=pivots
    )

    print("\n--- Métricas del Sistema Homogéneo ---")
    print(f"   • Cantidad de vectores (columnas k)     : {k}")
    print(f"   • Dimensión del espacio vectorial (ℝⁿ)  : n = {n}")
    print(f"   • Número de pivotes encontrados (rango) : {num_pivots}")
    print(f"   • Posiciones pivote (fila, col)         : {[(r+1, c+1) for r, c in pivots] if pivots else 'Ninguno'}")
    print(f"   • Columnas con pivote (variables básicas): {[f'c_{c+1}' for c in basic_vars] if basic_vars else 'Ninguna'}")
    print(f"   • Columnas sin pivote (variables libres) : {[f'c_{c+1}' for c in free_vars] if free_vars else 'Ninguna (0 libres)'}")
    print(f"   • Total de variables libres             : {len(free_vars)}")

    print("\n--- Veredicto Teórico Explícito ---")
    if is_li:
        print("🟢 EL CONJUNTO DE VECTORES ES LINEALMENTE INDEPENDIENTE (L.I.)")
        print("   " + "-" * 62)
        print("   Fundamentación teórica:")
        print(f"   1. El número de pivotes ({num_pivots}) coincide exactamente con la cantidad")
        print(f"      de vectores (k = {k}). Por ende, toda columna contiene una posición pivote.")
        print("   2. No existen variables libres en el sistema homogéneo A·c = 0.")
        print("   3. La única solución posible a la combinación lineal nula:")
        print("          c₁·v₁ + c₂·v₂ + ... + cₖ·vₖ = 0")
        print("      es la SOLUCIÓN TRIVIAL (c₁ = c₂ = ... = cₖ = 0).")
        print("   4. Ningún vector del conjunto puede expresarse como combinación lineal")
        print("      de los vectores restantes.")
    else:
        print("🔴 EL CONJUNTO DE VECTORES ES LINEALMENTE DEPENDIENTE (L.D.)")
        print("   " + "-" * 62)
        print("   Fundamentación teórica:")
        print(f"   1. El número de pivotes ({num_pivots}) es estrictamente MENOR que la cantidad")
        print(f"      de vectores (k = {k}).")
        print(f"   2. Existen {len(free_vars)} variable(s) libre(s): {[f'c_{c+1}' for c in free_vars]}.")
        print("   3. La presencia de variables libres demuestra que el sistema homogéneo A·c = 0")
        print("      posee INFINITAS SOLUCIONES (admite soluciones no triviales c ≠ 0).")
        print("   4. Al menos uno de los vectores puede escribirse como combinación lineal")
        print("      de los demás.")

        # Notas teóricas especiales
        if results["theorem_k_greater_n"]:
            print("\n   📌 Teorema Fundamental Aplicado (k > n):")
            print(f"      El conjunto tiene k = {k} vectores en ℝ^{n}. Dado que k > n,")
            print("      es imposible tener k pivotes en solo n filas (a lo sumo n pivotes).")
            print("      Por teorema, cualquier conjunto de k vectores en ℝⁿ con k > n es L.D.")

        if results["zero_vector_index"] is not None:
            z_idx = results["zero_vector_index"]
            print(f"\n   📌 Presencia del Vector Nulo:")
            print(f"      El vector v_{z_idx+1} es el vector cero 0. Todo conjunto que contenga")
            print("      al vector nulo es automáticamente Linealmente Dependiente.")

        # Demostración de combinación no trivial
        weights = results["nontrivial_solution"]
        if weights:
            print("\n--- Demostración con Solución No Trivial (c ≠ 0) ---")
            sol_terms = [f"({fmt(w)})·v_{i+1}" for i, w in enumerate(weights) if w != Fraction(0, 1)]
            print("   Combinación lineal no trivial que produce el vector cero:")
            print(f"   {' + '.join(sol_terms)} = 0")
            print("   Valores asignados a los coeficientes cᵢ:")
            for i, w in enumerate(weights):
                print(f"      • c_{i+1} = {fmt(w)} ({float(w):.4f})")

            # Verificación celda a celda
            print("\n   Comprobación exacta de la suma componente a componente:")
            for dim_idx in range(n):
                acc = sum(weights[j] * vectors[j][dim_idx] for j in range(k))
                print(f"      ✓ Componente {dim_idx+1}: suma = {fmt(acc)} (idéntico a 0)")


# ------------------------------------------------------------------------------
# Interfaz de Consola Interactiva (CLI)
# ------------------------------------------------------------------------------

def mostrar_teoremas_modulo() -> None:
    """Despliega los teoremas y propiedades analizadas en clase para este módulo."""

    print("\n" + "=" * 65)
    print(" 📖 TEOREMAS CLAVE — VECTORES E INDEPENDENCIA LINEAL")
    print("=" * 65)
    print("""
1. DEFINICIÓN FUNDAMENTAL DE INDEPENDENCIA LINEAL (L.I.):
   Un conjunto de k vectores {v₁, v₂, ..., vₖ} en ℝⁿ es L.I. si y solo si
   la única solución a la ecuación vectorial homogénea:
       c₁·v₁ + c₂·v₂ + ... + cₖ·vₖ = 0
   es la SOLUCIÓN TRIVIAL (c₁ = c₂ = ... = cₖ = 0).

2. DEFINICIÓN DE DEPENDENCIA LINEAL (L.D.):
   El conjunto es L.D. si existen escalares no todos nulos tales que
   c₁·v₁ + ... + cₖ·vₖ = 0. Al menos un vector es combinación lineal
   de los demás.

3. CONEXIÓN CON LA FORMA ESCALONADA POR FILAS (REF) DE A·c = 0:
   Siendo A = [ v₁  v₂ ... vₖ ] (matriz de n × k):
   • Si número de pivotes r = k: Cero variables libres.
     → Solución única (trivial) → LINEALMENTE INDEPENDIENTE (L.I.).
   • Si número de pivotes r < k: Existen (k - r) variables libres.
     → Infinitas soluciones no triviales → LINEALMENTE DEPENDIENTE (L.D.).

4. TEOREMA DE LA DIMENSIÓN (k > n):
   Cualquier conjunto de k vectores en ℝⁿ con k > n es necesariamente L.D.,
   pues en n filas el número máximo de pivotes es r ≤ n < k.

5. TEOREMA DEL VECTOR NULO:
   Cualquier conjunto de vectores que contenga al vector cero 0 es L.D.
""")
    print("=" * 65)


def linear_independence_cli():
    """Función principal interactiva con Logotipo ASCII requerido y opción de teoremas."""
    while True:
        print("\n" + "=" * 54)
        print(" MÓDULO: VECTORES E INDEPENDENCIA LINEAL")
        print(" Combinaciones Lineales, L.I. y L.D.")
        print(" 𝐴 𝑥 = 0")
        print("=" * 54)
        print(" 0. Ver Teoremas Clave del Módulo")
        print(" 1. Evaluar Independencia / Dependencia Lineal (L.I. o L.D.) en ℝⁿ")
        print(" 2. Salir")
        print("=" * 54)

        opc = input("Seleccione una opción (0-2): ").strip()

        if opc == "0":
            mostrar_teoremas_modulo()
            input("\nPresione ENTER para continuar...")
        elif opc == "1":
            print("\n" + "-" * 75)
            print("PASO 1: Dimensiones del Problema")
            print("-" * 75)
            k = read_positive_int("Ingrese la cantidad de vectores (k): ")
            n = read_positive_int("Ingrese la dimensión del espacio (n para ℝⁿ): ")

            if k > n:
                print(f"\n💡 [Observación Teórica Preliminar]: Ha ingresado k = {k} vectores en ℝ^{n}.")
                print(f"   Por teorema fundamental, como k ({k}) > n ({n}), el conjunto será")
                print("   necesariamente Linealmente Dependiente (L.D.). Se verificará por reducción.\n")

            print("\n" + "-" * 75)
            print("PASO 2: Ingreso de Vectores Columna")
            print("(Puede ingresar enteros, fracciones como '3/4' o decimales como '0.5')")
            print("-" * 75)

            vectors: List[List[Fraction]] = []
            for j in range(k):
                print(f"\n>> Vector v_{j+1} ∈ ℝ^{n}:")
                v: List[Fraction] = []
                for i in range(n):
                    val = read_scalar(f"   Componente v_{j+1}[{i+1}]: ")
                    v.append(val)
                vectors.append(v)

            print_vector_set(vectors, dim_n=n)

            print("\n" + "-" * 75)
            print("PASO 3: Construcción del Sistema Homogéneo A·c = 0 y Reducción por Filas")
            print("-" * 75)

            results = evaluate_linear_independence(vectors, dim_n=n, verbose=True)
            display_results(results, vectors)
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            print("\n¡Gracias por utilizar PrettyCalc - Álgebra Lineal Grupo 4! Sesión finalizada.\n")
            break
        else:
            print("   ⚠️  Opción no válida. Ingrese 0, 1 o 2.")



if __name__ == "__main__":
    linear_independence_cli()
