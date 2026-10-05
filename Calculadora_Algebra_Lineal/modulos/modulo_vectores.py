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

# ------------------------------------------------------------------------------
# CONFIGURACIÓN DE CODIFICACIÓN EN CONSOLA
# ------------------------------------------------------------------------------
# Configura la salida estándar (stdout y stderr) para utilizar codificación UTF-8.
# Esto evita errores al imprimir símbolos especiales como "ℝ", "↔", "│", "💡", "⚠️".
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # Si la consola no soporta reconfiguración, continúa sin detener el programa

# ------------------------------------------------------------------------------
# IMPORTACIÓN DINÁMICA Y SEGURA DE MÓDULOS DE TEOREMAS
# ------------------------------------------------------------------------------
# Intenta importar el resumen de teoremas desde la estructura del proyecto.
# Si la ruta no está en sys.path, añade los directorios superiores para localizar la carpeta.
try:
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_vectores
except ImportError:
    calc_dir = Path(__file__).resolve().parent.parent  # Directorio padre inmediato
    parent_dir = calc_dir.parent                        # Directorio raíz del proyecto
    
    # Agrega los directorios a la lista de búsqueda de módulos en Python si no están presentes
    for p in (str(calc_dir), str(parent_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
            
    # Intenta nuevamente la importación tras ajustar las rutas de búsqueda
    try:
        from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_vectores
    except ImportError:
        from teoremas.resumen_teoremas import mostrar_teoremas_vectores


# ------------------------------------------------------------------------------
# FUNCIONES AUXILIARES: LECTURA, PARSEO Y FORMATO DE FRACCIONES
# ------------------------------------------------------------------------------

def parse_scalar(text: str) -> Fraction:
    """Convierte una cadena de texto ingresada por el usuario en una fracción exacta (Fraction).
    
    Soporta números enteros ("5"), decimales ("0.75") y fracciones ("3/4", "-1/2").
    Lanza excepciones de tipo ValueError o ZeroDivisionError si la entrada es inválida.
    """
    # Elimina espacios en blanco al inicio, final y entre caracteres
    cleaned = text.strip().replace(" ", "")
    
    if not cleaned:
        raise ValueError("Entrada vacía.")
    
    # Procesa texto en notación fraccionaria "numerador/denominador"
    if "/" in cleaned:
        parts = cleaned.split("/")
        if len(parts) != 2:
            raise ValueError("Formato de fracción inválido.")
        
        num, den = int(parts[0]), int(parts[1])
        if den == 0:
            raise ZeroDivisionError("El denominador no puede ser cero.")
        return Fraction(num, den)
    
    # Convierte enteros o decimales directamente a objeto Fraction
    return Fraction(cleaned)


def fmt(val: Fraction) -> str:
    """Da formato visual simplificado a las fracciones.
    
    Si el denominador es 1, retorna solo el entero (ej. '5' en lugar de '5/1').
    De lo contrario, retorna la representación en formato 'numerador/denominador'.
    """
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def read_scalar(prompt: str) -> Fraction:
    """Solicita al usuario una entrada numérica en consola.
    
    Mantiene un bucle interactivo hasta que la entrada sea parseada correctamente como Fraction.
    """
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            # Informa el error y vuelve a solicitar el dato
            print(f"   ⚠️  Entrada inválida ({exc}). Intente de nuevo (ej. 3, -1/2, 0.75):")


def read_positive_int(prompt: str) -> int:
    """Solicita al usuario un número entero estrictamente positivo (n > 0).
    
    Útil para validar dimensiones de vectores y cantidades de elementos.
    """
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val <= 0:
                print("   ⚠️  Debe ser un número entero positivo.")
                continue
            return val
        except ValueError:
            print("   ⚠️️  Entrada inválida. Ingrese un número entero.")


# ------------------------------------------------------------------------------
# FUNCIONES DE VISUALIZACIÓN DE MATRICES Y VECTORES
# ------------------------------------------------------------------------------

def print_matrix(
    matrix: List[List[Fraction]],
    title: str = "",
    split_col: Optional[int] = None,
    pivot_coords: Optional[Sequence[Tuple[int, int]]] = None
) -> None:
    """Imprime en consola una matriz formateada con alineación de columnas.
    
    - title: Título opcional descriptivo.
    - split_col: Índice de columna donde se dibuja una barra vertical '|' para matrices aumentadas.
    - pivot_coords: Lista de pares (fila, columna) de los pivotes para enmarcarlos con '[ ]'.
    """
    if title:
        print(f"\n--- {title} ---")
    if not matrix or not matrix[0]:
        print("│ [Matriz vacía] │")
        return

    rows = len(matrix)
    cols = len(matrix[0])
    
    # Convierte las coordenadas de pivotes a un conjunto para búsquedas rápidas O(1)
    piv_set = set(pivot_coords) if pivot_coords else set()

    # Prepara las cadenas formateadas para cada elemento de la matriz
    cells = []
    for r in range(rows):
        row_cells = []
        for c in range(cols):
            val_str = fmt(matrix[r][c])
            # Si el elemento actual es un pivote, se resalta entre corchetes
            if (r, c) in piv_set:
                row_cells.append(f"[{val_str}]")
            else:
                row_cells.append(val_str)
        cells.append(row_cells)

    # Determina el ancho máximo de texto en cada columna para alinear visualmente la tabla
    widths = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]

    # Imprime la matriz fila por fila
    for r in range(rows):
        if split_col is None:
            # Imprime una matriz estándar sin barra divisoria
            row_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(cols))
            print(f"│  {row_str}  │")
        else:
            # Imprime una matriz aumentada separando en la columna `split_col`
            left_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col))
            right_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col, cols))
            print(f"│  {left_str}  │  {right_str}  │")


def print_vector(v: Sequence[Fraction], name: str = "v") -> None:
    """Imprime un vector en notación horizontal con el símbolo de transposición: name = (v1, v2, ...)^T"""
    v_str = ", ".join(fmt(x) for x in v)
    print(f"   {name} = ({v_str})^T")


# ------------------------------------------------------------------------------
# ALGORITMOS MATEMÁTICOS DE REDUCCIÓN DE MATRICES
# ------------------------------------------------------------------------------

def build_homogeneous_system(vectors: List[List[Fraction]], dim_n: int) -> List[List[Fraction]]:
    """Construye la matriz aumentada [A | 0] del sistema homogéneo A·c = 0.
    
    Toma 'k' vectores de dimensión 'n' y los coloca como COLUMNAS de la matriz A,
    agregando una columna final de ceros.
    """
    k = len(vectors)
    augmented: List[List[Fraction]] = []
    
    for i in range(dim_n):
        # Toma la componente i-ésima de cada vector para formar la fila i de la matriz
        row = [vectors[j][i] for j in range(k)]
        row.append(Fraction(0, 1))  # Añade el término independiente 0 (sistema homogéneo)
        augmented.append(row)
        
    return augmented


def row_echelon_reduction(
    matrix: List[List[Fraction]],
    num_vars: int,
    verbose: bool = True
) -> Tuple[List[List[Fraction]], List[Tuple[int, int]]]:
    """Reduce la matriz a su Forma Escalonada por Filas (REF) mediante Eliminación Gaussiana.
    
    Devuelve:
    1. La matriz en forma REF.
    2. Una lista con las posiciones (fila, columna) de todos los pivotes encontrados.
    """
    # Crea una copia independiente (profunda) de la matriz de entrada para no modificar la original
    mat = [[c for c in row] for row in matrix]
    m = len(mat)
    pivot_row = 0
    pivots: List[Tuple[int, int]] = []
    step = 1

    # Recorre cada columna correspondiente a las variables del sistema
    for col in range(num_vars):
        if pivot_row >= m:
            break

        # Busca el primer elemento no nulo en o por debajo de pivot_row (pivote)
        selected_row = None
        for r in range(pivot_row, m):
            if mat[r][col] != Fraction(0, 1):
                selected_row = r
                break

        # Si no hay pivote en esta columna, la variable asociada es libre
        if selected_row is None:
            continue

        # Intercambia la fila actual con la fila del pivote seleccionado si es necesario
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
        pivots.append((pivot_row, col))  # Guarda las coordenadas del pivote encontrado

        # Elimina (hace cero) las entradas de la columna situadas debajo del pivote
        for r in range(pivot_row + 1, m):
            target_val = mat[r][col]
            if target_val != Fraction(0, 1):
                # Factor multiplicador para la operación elemental de fila: f_r -> f_r + factor * f_pivote
                factor = - (target_val / pivot_val)
                for c in range(len(mat[0])):
                    mat[r][c] = mat[r][c] + (factor * mat[pivot_row][c])

                if verbose:
                    desc = f"f_{r+1} → f_{r+1} + ({fmt(factor)})·f_{pivot_row+1}"
                    print_matrix(mat, title=f"Paso {step}: {desc}", split_col=num_vars)
                    step += 1

        pivot_row += 1  # Avanza a la siguiente fila pivote

    return mat, pivots


def back_substitution_rref(
    ref_matrix: List[List[Fraction]],
    pivots: List[Tuple[int, int]],
    num_vars: int
) -> List[List[Fraction]]:
    """Transforma una matriz en Forma Escalonada por Filas (REF) a Forma Escalonada Reducida (RREF).
    
    Aplica el algoritmo de Gauss-Jordan trabajando de abajo hacia arriba:
    1. Escala cada pivote para convertirlo en 1.
    2. Hace cero todas las entradas por ENCIMA de cada pivote.
    """
    mat = [[c for c in row] for row in ref_matrix]
    
    # Procesa los pivotes en orden inverso (de abajo hacia arriba)
    for r_idx, c_idx in reversed(pivots):
        pivot_val = mat[r_idx][c_idx]
        
        # Normaliza la fila multiplicando para que el pivote sea igual a 1
        if pivot_val != Fraction(1, 1):
            scale = Fraction(1, 1) / pivot_val
            for c in range(len(mat[0])):
                mat[r_idx][c] = mat[r_idx][c] * scale

        # Elimina todas las entradas por encima del pivote actual
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
    """Calcula una combinación lineal no trivial (coeficientes c ≠ 0) para el sistema A·c = 0.
    
    Se utiliza únicamente cuando el conjunto es Linealmente Dependiente (L.D.).
    Asigna valor 1 a la primera variable libre y calcula los coeficientes restantes.
    """
    pivot_cols = {col for _, col in pivots}
    # Identifica las variables libres (columnas que no contienen un pivote)
    free_vars = [c for c in range(num_vars) if c not in pivot_cols]
    
    if not free_vars:
        return None  # Si no hay variables libres, no existe solución no trivial

    # Selecciona la primera variable libre y le asigna un valor arbitrario distinto de cero (1)
    target_free = free_vars[0]
    weights = [Fraction(0, 1) for _ in range(num_vars)]
    weights[target_free] = Fraction(1, 1)

    # Despeja las variables básicas asociadas a partir de la matriz RREF
    for r_idx, piv_col in pivots:
        coeff = rref_matrix[r_idx][target_free]
        weights[piv_col] = - coeff

    return weights


# ------------------------------------------------------------------------------
# MÓDULOS DE EVALUACIÓN INTERACTIVA (OPCIONES DEL MENÚ)
# ------------------------------------------------------------------------------

def evaluar_independencia_interactivo() -> None:
    """Opción 1: Evalúa la Independencia o Dependencia Lineal (L.I. / L.D.) de 'k' vectores en ℝⁿ."""
    print("\n" + "=" * 65)
    print("EVALUACIÓN DE INDEPENDENCIA Y DEPENDENCIA LINEAL EN ℝⁿ")
    print("=" * 65)

    k = read_positive_int("Ingrese la cantidad de vectores (k): ")
    n = read_positive_int("Ingrese la dimensión del espacio (n para ℝⁿ): ")

    # Aplicación preliminar del Teorema de Dimensión
    if k > n:
        print(f"\n💡 [Observación Teórica]: Ha ingresado k = {k} vectores en ℝ^{n}.")
        print(f"   Por Teorema de Dimensión, como k ({k}) > n ({n}), el conjunto será")
        print("   necesariamente Linealmente Dependiente (L.D.). Se verificará por reducción.")

    # Captura interactiva de componentes de cada vector
    vectors: List[List[Fraction]] = []
    print(f"\nIngrese las componentes de los {k} vectores:")
    for j in range(k):
        print(f">> Vector v_{j+1} ∈ ℝ^{n}:")
        v: List[Fraction] = []
        for i in range(n):
            val = read_scalar(f"   v_{j+1}[{i+1}]: ")
            v.append(val)
        vectors.append(v)

    # Muestra en pantalla el conjunto de vectores ingresados
    print("\nConjunto ingresado:")
    for j, v in enumerate(vectors):
        print_vector(v, f"v_{j+1}")

    # Verifica si alguno de los vectores ingresados es el vector nulo (0)
    zero_idx = None
    for idx, v in enumerate(vectors):
        if all(x == Fraction(0, 1) for x in v):
            zero_idx = idx
            break

    # Construcción y reducción por filas de la matriz del sistema homogéneo [A | 0]
    aug = build_homogeneous_system(vectors, n)
    print_matrix(aug, title="Matriz Aumentada Inicial [A | 0] del Sistema Homogéneo", split_col=k)

    print("\n--- Reducción por Filas a Forma Escalonada (REF) ---")
    ref_mat, pivots = row_echelon_reduction(aug, num_vars=k, verbose=True)

    # Análisis del número de pivotes y variables libres
    num_pivots = len(pivots)
    pivot_cols = [c for _, c in pivots]
    free_vars = [c for c in range(k) if c not in pivot_cols]
    is_li = (num_pivots == k)  # Es L.I. únicamente si cada vector tiene su correspondiente pivote

    # Emisión del veredicto teórico final
    print("\n" + "=" * 65)
    print("                      VEREDICTO TEÓRICO                      ")
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

        # Muestra los teoremas específicos aplicables a la dependencia
        if k > n:
            print(f"   📌 Teorema Aplicado: k = {k} > n = {n}. En ℝⁿ ningún conjunto de más de n vectores puede ser L.I.")
        if zero_idx is not None:
            print(f"   📌 Teorema Aplicado: El vector v_{zero_idx+1} es el vector nulo 0. Todo conjunto con el 0 es L.D.")

        # Obtiene e imprime una combinación lineal no trivial explícita igual a cero
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
    """Opción 2: Determina si un vector 'b' se puede expresar como combinación lineal c₁v₁ + ... + cₖvₖ = b."""
    print("\n" + "-" * 65)
    print("EVALUACIÓN DE COMBINACIÓN LINEAL: c₁·v₁ + ... + cₖ·vₖ = b")
    print("-" * 65)

    k = read_positive_int("Cantidad de vectores generadores (k): ")
    n = read_positive_int("Dimensión del espacio (n para ℝⁿ): ")

    # Lectura del conjunto de vectores generadores
    vectors: List[List[Fraction]] = []
    for j in range(k):
        print(f"\nVector v_{j+1} ∈ ℝ^{n}:")
        v = [read_scalar(f"   v_{j+1}[{i+1}]: ") for i in range(n)]
        vectors.append(v)

    # Lectura del vector objetivo b
    print(f"\nVector objetivo b ∈ ℝ^{n}:")
    b = [read_scalar(f"   b[{i+1}]: ") for i in range(n)]

    # Construcción de la matriz aumentada [A | b] para el sistema no homogéneo
    aug = []
    for i in range(n):
        row = [vectors[j][i] for j in range(k)]
        row.append(b[i])
        aug.append(row)

    print_matrix(aug, title="Matriz Aumentada [A | b]", split_col=k)

    # Reducción de la matriz por el método de eliminación gaussiana
    ref_mat, pivots = row_echelon_reduction(aug, num_vars=k, verbose=True)

    # Verificación de inconsistencia del sistema (existencia de filas tipo [0 0 ... 0 | c] con c ≠ 0)
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
        # Lleva a forma RREF para despejar y mostrar los escalares c_i directamente
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
    """Opción 3: Calcula suma, resta, producto punto y normas cuadradas de dos vectores u y v en ℝⁿ."""
    print("\n" + "-" * 65)
    print("OPERACIONES BÁSICAS CON VECTORES EN ℝⁿ")
    print("-" * 65)
    n = read_positive_int("Dimensión de los vectores (n): ")

    # Captura de los dos vectores u y v
    print(f"\nIngrese vector u ∈ ℝ^{n}:")
    u = [read_scalar(f"   u[{i+1}]: ") for i in range(n)]

    print(f"\nIngrese vector v ∈ ℝ^{n}:")
    v = [read_scalar(f"   v[{i+1}]: ") for i in range(n)]

    # Operaciones elemento por elemento
    u_plus_v = [u[i] + v[i] for i in range(n)]       # Suma vectorial: u + v
    u_minus_v = [u[i] - v[i] for i in range(n)]      # Resta vectorial: u - v
    dot = sum(u[i] * v[i] for i in range(n))          # Producto punto (escalar): u · v
    norm_sq_u = sum(u[i] ** 2 for i in range(n))     # Norma de u al cuadrado: ||u||² = u · u
    norm_sq_v = sum(v[i] ** 2 for i in range(n))     # Norma de v al cuadrado: ||v||² = v · v

    # Presentación de resultados calculados
    print("\n--- Resultados ---")
    print_vector(u_plus_v, "u + v")
    print_vector(u_minus_v, "u - v")
    print(f"   • Producto Punto u · v = {fmt(dot)}")
    print(f"   • Norma al cuadrado ||u||² = {fmt(norm_sq_u)}")
    print(f"   • Norma al cuadrado ||v||² = {fmt(norm_sq_v)}")
    
    # Comprobación del criterio de ortogonalidad
    if dot == Fraction(0, 1):
        print("   💡 [Propiedad]: u y v son ORTOGONALES (u · v = 0).")


# ------------------------------------------------------------------------------
# MENÚ PRINCIPAL DEL MÓDULO
# ------------------------------------------------------------------------------

def menu_vectores() -> None:
    """Bucle del menú principal del programa interactivo."""
    while True:
        print("\n" + "=" * 54)
        print(" MÓDULO: VECTORES E INDEPENDENCIA LINEAL")
        print(" Combinaciones Lineales, L.I. y L.D.")
        print(" A x = 0")
        print("=" * 54)
        print(" 0. Ver Teoremas Clave del Módulo")
        print(" 1. Evaluar Independencia / Dependencia Lineal (L.I. o L.D.) en ℝⁿ")
        print(" 2. Evaluar Combinación Lineal (b = c₁v₁ + ... + cₖvₖ)")
        print(" 3. Operaciones Básicas en ℝⁿ (Suma, Resta, Producto Punto)")
        print(" 4. Volver al Menú Principal")
        print("=" * 54)

        opc = input("Seleccione una opción (0-4): ").strip()

        # Enrutamiento de la selección del usuario
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
            break  # Finaliza el bucle y sale del módulo
        else:
            print("   ⚠️  Opción no reconocida. Ingrese un número entre 0 y 4.")


# Punto de entrada de ejecución del script
if __name__ == "__main__":
    menu_vectores()