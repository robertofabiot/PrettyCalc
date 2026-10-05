"""================================================================================
UNIVERSIDAD AMERICANA (UAM)
Facultad de Ingeniería y Arquitectura (FIA)
Asignatura: Álgebra Lineal (MTM0120)
PROGRAMA 3: Operaciones en ℝⁿ, Combinación Lineal y Ecuaciones Matriciales
Grupo 4
================================================================================
Restricción estricta del Contrato Didáctico:
    100% Python estándar. Prohibido NumPy, SciPy y álgebra lineal de math.
    Toda la aritmética se realiza con fractions.Fraction (exacta, sin redondeo).

Fundamento algebraico (equivalencias usadas en este programa):
    1. Vectores en ℝⁿ  →  listas de n fracciones; suma/resta componente a componente.
    2. Combinación lineal  Σ cᵢ vᵢ = b  →  sistema A c = b, columnas de A = vᵢ.
    3. Producto A_{m×n} · B_{n×p}  →  tres bucles anidados:
           C[i][j] = sum(A[i][k] * B[k][j] for k in range(n))
    4. Ecuación matricial A x = b  →  matriz aumentada [A | b] y Gauss-Jordan.
================================================================================
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple


# ------------------------------------------------------------------------------
# Utilidades de entrada / salida (sin librerías externas)
# ------------------------------------------------------------------------------

def parse_scalar(text: str) -> Fraction:
    """Convierte texto a Fraction exacta (enteros, a/b o decimales).

    Equivalente algebraico: inmersión de ℚ en el cuerpo de trabajo. No se usa
    float para calcular, solo para interpretar decimales de entrada.
    """
    cleaned = text.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("Entrada vacía.")
    if "/" in cleaned:
        num_str, den_str = cleaned.split("/")
        num, den = int(num_str), int(den_str)
        if den == 0:
            raise ValueError("El denominador no puede ser cero.")
        return Fraction(num, den)
    return Fraction(cleaned)


def fmt(val: Fraction) -> str:
    """Representación textual de una fracción irreducible."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def read_scalar(prompt: str) -> Fraction:
    """Lee un escalar del teclado con reintento ante formato inválido."""
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   Entrada inválida ({exc}). Intente de nuevo.")


def read_positive_int(prompt: str) -> int:
    """Lee un entero positivo."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value <= 0:
                print("   Debe ser un entero positivo.")
                continue
            return value
        except ValueError:
            print("   No es un entero.")


def print_vector(vector: Sequence[Fraction], title: str = "") -> None:
    """Imprime un vector columna con corchetes de libro."""
    if title:
        print(f"\n{title}")
    width = max(len(fmt(v)) for v in vector)
    for v in vector:
        print(f"  │  {fmt(v).rjust(width)}  │")


def print_matrix(matrix: List[List[Fraction]], title: str = "", split_col: Optional[int] = None) -> None:
    """Imprime una matriz alineada; si split_col está definido, dibuja [A | b]."""
    if title:
        print(f"\n--- {title} ---")
    rows = len(matrix)
    cols = len(matrix[0])
    cells = [[fmt(matrix[r][c]) for c in range(cols)] for r in range(rows)]
    widths = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]
    for r in range(rows):
        if split_col is None:
            body = "  ".join(cells[r][c].rjust(widths[c]) for c in range(cols))
            print(f"│  {body}  │")
        else:
            left = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col))
            right = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col, cols))
            print(f"│  {left}  │  {right}  │")


def read_vector(n: int, name: str) -> List[Fraction]:
    """Lee las n componentes de un vector en ℝⁿ."""
    print(f"\nComponentes de {name} ∈ ℝ^{n}:")
    return [read_scalar(f"   {name}[{i + 1}]: ") for i in range(n)]


def read_matrix(rows: int, cols: int, name: str) -> List[List[Fraction]]:
    """Lee una matriz m×n celda a celda."""
    print(f"\nEntradas de {name} ({rows}×{cols}):")
    data: List[List[Fraction]] = []
    for i in range(rows):
        row: List[Fraction] = []
        print(f"  Fila {i + 1}:")
        for j in range(cols):
            row.append(read_scalar(f"     {name}[{i + 1},{j + 1}]: "))
        data.append(row)
    return data


# ------------------------------------------------------------------------------
# Módulo 1 — Operaciones vectoriales en ℝⁿ
# ------------------------------------------------------------------------------

def vector_add(u: Sequence[Fraction], v: Sequence[Fraction]) -> List[Fraction]:
    """Suma (u+v)_i = u_i + v_i. Exige dim(u) = dim(v)."""
    if len(u) != len(v):
        raise ValueError(
            f"Dimensiones incompatibles: dim(u)={len(u)} ≠ dim(v)={len(v)}. "
            "La suma en ℝⁿ exige la misma n."
        )
    return [u[i] + v[i] for i in range(len(u))]


def vector_sub(u: Sequence[Fraction], v: Sequence[Fraction]) -> List[Fraction]:
    """Resta (u−v)_i = u_i − v_i. Exige dim(u) = dim(v)."""
    if len(u) != len(v):
        raise ValueError(
            f"Dimensiones incompatibles: dim(u)={len(u)} ≠ dim(v)={len(v)}. "
            "La resta en ℝⁿ exige la misma n."
        )
    return [u[i] - v[i] for i in range(len(u))]


def vector_scale(v: Sequence[Fraction], k: Fraction) -> List[Fraction]:
    """Producto por escalar (k·v)_i = k · v_i (distributivo en cada componente)."""
    return [k * v[i] for i in range(len(v))]


def menu_vectores() -> None:
    """Menú interactivo de suma, resta y escalado en ℝⁿ."""
    print("\n" + "=" * 70)
    print("  1. OPERACIONES CON VECTORES EN ℝⁿ")
    print("=" * 70)
    n = read_positive_int("Dimensión n: ")
    print("Operación:  1) u + v    2) u − v    3) k · v")
    op = input("Elija 1, 2 o 3: ").strip()
    if op == "3":
        v = read_vector(n, "v")
        k = read_scalar("Escalar k: ")
        result = vector_scale(v, k)
        print_vector(result, title=f"Resultado  ({fmt(k)}) · v =")
        return
    u = read_vector(n, "u")
    v = read_vector(n, "v")
    try:
        result = vector_add(u, v) if op == "1" else vector_sub(u, v)
    except ValueError as exc:
        print(f"\n✕ {exc}")
        return
    symbol = "+" if op == "1" else "−"
    print_vector(result, title=f"Resultado  u {symbol} v =")


# ------------------------------------------------------------------------------
# Eliminación de Gauss-Jordan (reutilizada por combinación lineal y Ax = b)
# ------------------------------------------------------------------------------

def gauss_jordan(matrix: List[List[Fraction]], num_vars: int) -> List[List[Fraction]]:
    """Reduce [A | b] a forma escalonada reducida (RREF) por operaciones elementales.

    Equivalente algebraico: secuencia de E_i (intercambio, escalado, combinación)
    que no altera el conjunto solución del sistema lineal.
    """
    m = len(matrix)
    total_cols = len(matrix[0])
    work = [[cell for cell in row] for row in matrix]
    pivot_row = 0

    # Fase hacia adelante: ceros debajo de cada pivote.
    for col in range(num_vars):
        if pivot_row >= m:
            break
        selected = None
        for r in range(pivot_row, m):
            if work[r][col] != 0:
                selected = r
                break
        if selected is None:
            continue
        if selected != pivot_row:
            work[pivot_row], work[selected] = work[selected], work[pivot_row]
        pivot_val = work[pivot_row][col]
        for r in range(pivot_row + 1, m):
            if work[r][col] != 0:
                factor = -(work[r][col] / pivot_val)
                for c in range(total_cols):
                    work[r][c] = work[r][c] + factor * work[pivot_row][c]
        pivot_row += 1

    # Fase hacia atrás: pivotes = 1 y ceros encima.
    for r in range(m - 1, -1, -1):
        lead = None
        for c in range(num_vars):
            if work[r][c] != 0:
                lead = c
                break
        if lead is None:
            continue
        scale = Fraction(1, 1) / work[r][lead]
        for c in range(total_cols):
            work[r][c] *= scale
        for up in range(r):
            if work[up][lead] != 0:
                factor = -work[up][lead]
                for c in range(total_cols):
                    work[up][c] = work[up][c] + factor * work[r][c]
    return work


def classify_rref(rref: List[List[Fraction]], num_vars: int) -> Tuple[str, Optional[List[Fraction]], str]:
    """Clasifica SCD / SCI / SI a partir de la RREF (Rouché-Frobenius).

    Returns:
        (tipo, solución particular o única, mensaje)
    """
    m = len(rref)
    rank_a = 0
    rank_aug = 0
    inconsistent = False
    pivot_cols: List[int] = []
    pivot_row_of: dict = {}

    for r in range(m):
        lead = None
        for c in range(num_vars):
            if rref[r][c] != 0:
                lead = c
                break
        b_nz = rref[r][num_vars] != 0
        if lead is not None:
            rank_a += 1
            rank_aug += 1
            if lead not in pivot_cols:
                pivot_cols.append(lead)
                pivot_row_of[lead] = r
        elif b_nz:
            rank_aug += 1
            inconsistent = True

    if inconsistent or rank_a < rank_aug:
        return (
            "SI",
            None,
            f"Inconsistente: Rango(A)={rank_a} ≠ Rango(A|b)={rank_aug} (aparece 0 = c, c≠0).",
        )

    free = [c for c in range(num_vars) if c not in pivot_cols]
    solution = [Fraction(0, 1)] * num_vars
    for var in pivot_cols:
        solution[var] = rref[pivot_row_of[var]][num_vars]

    if rank_a == num_vars:
        return ("SCD", solution, "Consistente determinado: solución única.")

    parts = []
    for i in range(num_vars):
        if i in free:
            parts.append(f"x{i + 1} libre")
        else:
            row = pivot_row_of[i]
            terms = [fmt(rref[row][num_vars])]
            for fvar in free:
                coeff = -rref[row][fvar]
                if coeff != 0:
                    terms.append(f"{fmt(coeff)}*x{fvar + 1}")
            parts.append(f"x{i + 1} = " + " + ".join(terms))
    return ("SCI", solution, "Consistente indeterminado. " + "; ".join(parts))


# ------------------------------------------------------------------------------
# Módulo 2 — Combinación lineal  Σ cᵢ vᵢ = b
# ------------------------------------------------------------------------------

def menu_combinacion() -> None:
    """Decide si b es combinación lineal de {v₁,…,vₖ} resolviendo A c = b.

    Construcción: cada vⱼ se coloca como columna j de A. El sistema A c = b
    es exactamente  c₁ v₁ + … + cₖ vₖ = b.
    """
    print("\n" + "=" * 70)
    print("  2. EVALUACIÓN DE COMBINACIÓN LINEAL  (Σ cᵢ vᵢ = b)")
    print("=" * 70)
    n = read_positive_int("Dimensión n de ℝⁿ: ")
    k = read_positive_int("Número de vectores generadores k: ")
    vectors: List[List[Fraction]] = [read_vector(n, f"v{j + 1}") for j in range(k)]
    target = read_vector(n, "b")

    # Matriz aumentada [v1 | v2 | … | vk | b]
    augmented: List[List[Fraction]] = []
    for i in range(n):
        row = [vectors[j][i] for j in range(k)]
        row.append(target[i])
        augmented.append(row)

    print_matrix(augmented, title="Matriz aumentada [v1 … vk | b]", split_col=k)
    rref = gauss_jordan(augmented, num_vars=k)
    print_matrix(rref, title="RREF (Gauss-Jordan)", split_col=k)
    kind, weights, message = classify_rref(rref, num_vars=k)

    print("\n" + "-" * 70)
    if kind == "SI":
        print("🔴  NO ES COMBINACIÓN LINEAL (sistema inconsistente).")
        print(f"    {message}")
        return
    if kind == "SCD":
        print("🟢  SÍ ES COMBINACIÓN LINEAL ÚNICA (SCD).")
    else:
        print("🟡  SÍ ES COMBINACIÓN LINEAL CON INFINITAS COMBINACIONES (SCI).")
    print(f"    {message}")
    if weights is not None:
        terms = [f"({fmt(weights[j])})·v{j + 1}" for j in range(k)]
        print("    b = " + " + ".join(terms))
        print("    Pesos:")
        for j, c in enumerate(weights):
            print(f"      c{j + 1} = {fmt(c)}")

        # Verificación componente a componente: Σ cᵢ vᵢ ≟ b
        print("\n    Comprobación componente a componente:")
        reconstructed = [Fraction(0, 1)] * n
        for j in range(k):
            for i in range(n):
                reconstructed[i] += weights[j] * vectors[j][i]
        for i in range(n):
            ok = reconstructed[i] == target[i]
            mark = "✓" if ok else "✗"
            print(f"      {mark}  componente {i + 1}:  {fmt(reconstructed[i])} = {fmt(target[i])}")


# ------------------------------------------------------------------------------
# Módulo 3 — Álgebra matricial (incl. producto con bucles anidados)
# ------------------------------------------------------------------------------

def matrix_add(A: List[List[Fraction]], B: List[List[Fraction]]) -> List[List[Fraction]]:
    """C_ij = A_ij + B_ij. Exige las mismas dimensiones m×n."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(
            f"No se pueden sumar: A es {len(A)}×{len(A[0])} y B es {len(B)}×{len(B[0])}."
        )
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def matrix_sub(A: List[List[Fraction]], B: List[List[Fraction]]) -> List[List[Fraction]]:
    """C_ij = A_ij − B_ij. Exige las mismas dimensiones m×n."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(
            f"No se pueden restar: A es {len(A)}×{len(A[0])} y B es {len(B)}×{len(B[0])}."
        )
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def matrix_scale(A: List[List[Fraction]], k: Fraction) -> List[List[Fraction]]:
    """C_ij = k · A_ij (producto escalar-matriz)."""
    return [[k * A[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def matrix_multiply(
    A: List[List[Fraction]],
    B: List[List[Fraction]],
    verbose: bool = True,
) -> List[List[Fraction]]:
    """Producto C = A · B mediante TRES BUCLES ANIDADOS en Python puro.

    Conformabilidad: columnas(A) = filas(B). Si A es m×n y B es n×p, C es m×p.

    Fundamento: la entrada C_ij es el producto punto de la fila i de A con la
    columna j de B:

        C[i][j] = 0
        for k in range(n):          # índice compartido (columnas de A / filas de B)
            C[i][j] += A[i][k] * B[k][j]

    El bucle externo i recorre las filas del resultado; el medio j recorre las
    columnas; el interno k realiza la contracción del índice n.
    """
    m = len(A)
    n = len(A[0])
    n_b = len(B)
    p = len(B[0])
    if n != n_b:
        raise ValueError(
            f"Producto no conformable: columnas de A ({n}) ≠ filas de B ({n_b}). "
            "Se requiere A m×n y B n×p."
        )

    C: List[List[Fraction]] = [[Fraction(0, 1) for _ in range(p)] for _ in range(m)]
    if verbose:
        print("\nDesglose pedagógico del producto (bucles i, j, k):")

    for i in range(m):
        for j in range(p):
            accum = Fraction(0, 1)
            terms = []
            for k in range(n):
                prod = A[i][k] * B[k][j]
                accum += prod
                terms.append(f"({fmt(A[i][k])})·({fmt(B[k][j])})")
            C[i][j] = accum
            if verbose:
                print(f"  C[{i + 1},{j + 1}] = " + " + ".join(terms) + f" = {fmt(accum)}")
    return C


def menu_matrices() -> None:
    """Suma, resta, escalado y producto con validación dimensional."""
    print("\n" + "=" * 70)
    print("  3. OPERACIONES MATRICIALES")
    print("=" * 70)
    print("  1) A + B     2) A − B     3) k · A     4) A · B (con desglose)")
    op = input("Elija 1-4: ").strip()

    if op == "3":
        m = read_positive_int("Filas de A: ")
        n = read_positive_int("Columnas de A: ")
        A = read_matrix(m, n, "A")
        k = read_scalar("Escalar k: ")
        print_matrix(matrix_scale(A, k), title=f"({fmt(k)}) · A")
        return

    if op == "4":
        m = read_positive_int("Filas de A (m): ")
        n_a = read_positive_int("Columnas de A (n_A): ")
        n_b = read_positive_int("Filas de B (n_B): ")
        p = read_positive_int("Columnas de B (p): ")
        A = read_matrix(m, n_a, "A")
        B = read_matrix(n_b, p, "B")
        try:
            C = matrix_multiply(A, B, verbose=True)
        except ValueError as exc:
            print(f"\n✕ {exc}")
            return
        print_matrix(C, title=f"C = A · B   ({m}×{p})")
        return

    m = read_positive_int("Filas (m): ")
    n = read_positive_int("Columnas (n): ")
    A = read_matrix(m, n, "A")
    B = read_matrix(m, n, "B")
    try:
        C = matrix_add(A, B) if op == "1" else matrix_sub(A, B)
    except ValueError as exc:
        print(f"\n✕ {exc}")
        return
    print_matrix(C, title="A + B" if op == "1" else "A − B")


# ------------------------------------------------------------------------------
# Módulo 4 — Ecuación matricial A x = b
# ------------------------------------------------------------------------------

def menu_ecuacion() -> None:
    """Resuelve A x = b por Gauss-Jordan y comprueba el producto A · x."""
    print("\n" + "=" * 70)
    print("  4. ECUACIÓN MATRICIAL  A x = b")
    print("=" * 70)
    m = read_positive_int("Filas de A (y dimensión de b): ")
    n = read_positive_int("Columnas de A (y dimensión de x): ")
    A = read_matrix(m, n, "A")
    b = read_vector(m, "b")

    augmented = [A[i] + [b[i]] for i in range(m)]
    print_matrix(augmented, title="[A | b]", split_col=n)
    rref = gauss_jordan(augmented, num_vars=n)
    print_matrix(rref, title="RREF", split_col=n)
    kind, x, message = classify_rref(rref, num_vars=n)
    print("\n" + "-" * 70)
    print(f"Clasificación: {kind}. {message}")

    if x is None:
        print("No existe x tal que A x = b.")
        return

    print_vector(x, title="Vector solución x (única o particular):")

    # Comprobación formal: (A · x)_i ≟ b_i  usando el mismo producto de 3 bucles.
    x_col = [[x[i]] for i in range(n)]
    Ax = matrix_multiply(A, x_col, verbose=False)
    print("\nComprobación A · x ≟ b:")
    all_ok = True
    for i in range(m):
        got = Ax[i][0]
        ok = got == b[i]
        all_ok = all_ok and ok
        mark = "✓" if ok else "✗"
        print(f"  {mark}  (A x)_{i + 1} = {fmt(got)}    b_{i + 1} = {fmt(b[i])}")
    if all_ok:
        print("Igualdad matricial exacta verificada.")


def menu_propiedades_ax() -> None:
    """Verificación de las propiedades del producto matriz-vector A · x."""
    print("\n" + "=" * 70)
    print("  5. PROPIEDADES DEL PRODUCTO MATRIZ-VECTOR (A · x)")
    print("=" * 70)
    print("  1) Propiedad Distributiva:  A(u + v) = A·u + A·v")
    print("  2) Propiedad de Homogeneidad: A(c·u) = c·(A·u)")
    prop = input("Elija 1 o 2: ").strip()

    if prop not in ("1", "2"):
        print("Opción inválida.")
        return

    m = read_positive_int("Número de filas de A (m): ")
    n = read_positive_int("Número de columnas de A (n): ")
    A = read_matrix(m, n, "A")

    if prop == "1":
        print(f"\nIngrese dos vectores u y v en ℝ^{n} (compatibles con las {n} columnas de A):")
        u = read_vector(n, "u")
        v = read_vector(n, "v")

        # LHS: A · (u + v)
        u_plus_v = vector_add(u, v)
        upv_col = [[u_plus_v[i]] for i in range(n)]
        lhs = matrix_multiply(A, upv_col, verbose=False)
        lhs_vec = [lhs[i][0] for i in range(m)]

        # RHS: A·u + A·v
        u_col = [[u[i]] for i in range(n)]
        v_col = [[v[i]] for i in range(n)]
        Au = matrix_multiply(A, u_col, verbose=False)
        Av = matrix_multiply(A, v_col, verbose=False)
        Au_vec = [Au[i][0] for i in range(m)]
        Av_vec = [Av[i][0] for i in range(m)]
        rhs_vec = vector_add(Au_vec, Av_vec)

        print("\n" + "-" * 70)
        print("DEMOSTRACIÓN DE LA PROPIEDAD DISTRIBUTIVA: A(u + v) = A·u + A·v")
        print("-" * 70)
        print_vector(u_plus_v, title="Paso 1 (LHS) - Suma intermedia (u + v):")
        print_vector(lhs_vec, title="Paso 2 (LHS) - Resultado A · (u + v):")
        print_vector(Au_vec, title="Paso 1 (RHS) - Producto A · u:")
        print_vector(Av_vec, title="Paso 2 (RHS) - Producto A · v:")
        print_vector(rhs_vec, title="Paso 3 (RHS) - Suma final (A·u) + (A·v):")

        print("\nComprobación de igualdad componente a componente:")
        all_equal = True
        for i in range(m):
            eq = lhs_vec[i] == rhs_vec[i]
            all_equal = all_equal and eq
            mark = "✓" if eq else "✗"
            print(f"  {mark}  Fila {i + 1}:  LHS = {fmt(lhs_vec[i])}  ==  RHS = {fmt(rhs_vec[i])}")

        if all_equal:
            print("\n🟢  ¡Propiedad Distributiva verificada exitosamente! Ambos lados son idénticos.")
        else:
            print("\n🔴  Discrepancia encontrada.")

    elif prop == "2":
        print(f"\nIngrese el vector u en ℝ^{n} (compatible con las {n} columnas de A):")
        u = read_vector(n, "u")
        c = read_scalar("Ingrese el escalar c: ")

        # LHS: A · (c · u)
        cu = vector_scale(u, c)
        cu_col = [[cu[i]] for i in range(n)]
        lhs = matrix_multiply(A, cu_col, verbose=False)
        lhs_vec = [lhs[i][0] for i in range(m)]

        # RHS: c · (A · u)
        u_col = [[u[i]] for i in range(n)]
        Au = matrix_multiply(A, u_col, verbose=False)
        Au_vec = [Au[i][0] for i in range(m)]
        rhs_vec = vector_scale(Au_vec, c)

        print("\n" + "-" * 70)
        print("DEMOSTRACIÓN DE LA PROPIEDAD DE HOMOGENEIDAD: A(c·u) = c·(A·u)")
        print("-" * 70)
        print_vector(cu, title=f"Paso 1 (LHS) - Vector escalado ({fmt(c)}) · u:")
        print_vector(lhs_vec, title="Paso 2 (LHS) - Resultado A · (c·u):")
        print_vector(Au_vec, title="Paso 1 (RHS) - Producto A · u:")
        print_vector(rhs_vec, title=f"Paso 2 (RHS) - Escalado final ({fmt(c)}) · (A·u):")

        print("\nComprobación de igualdad componente a componente:")
        all_equal = True
        for i in range(m):
            eq = lhs_vec[i] == rhs_vec[i]
            all_equal = all_equal and eq
            mark = "✓" if eq else "✗"
            print(f"  {mark}  Fila {i + 1}:  LHS = {fmt(lhs_vec[i])}  ==  RHS = {fmt(rhs_vec[i])}")

        if all_equal:
            print("\n🟢  ¡Propiedad de Homogeneidad verificada exitosamente! Ambos lados son idénticos.")
        else:
            print("\n🔴  Discrepancia encontrada.")


# ------------------------------------------------------------------------------
# Menú principal
# ------------------------------------------------------------------------------

def main() -> None:
    """Bucle del menú de consola del Programa 3."""
    while True:
        print("\n" + "=" * 70)
        print("  PROGRAMA 3 — Álgebra Lineal  (Grupo 4, MTM0120)")
        print("=" * 70)
        print("  1. Operaciones con vectores en ℝⁿ")
        print("  2. Evaluación de combinación lineal  (Σ cᵢ vᵢ = b)")
        print("  3. Operaciones matriciales  (A ± B, k·A, A·B)")
        print("  4. Ecuaciones matriciales  (A x = b)")
        print("  5. Propiedades del producto matriz-vector  (A · x)")
        print("  0. Salir")
        choice = input("\nSeleccione una opción: ").strip()
        if choice == "0":
            print("Hasta luego.")
            return
        handlers = {
            "1": menu_vectores,
            "2": menu_combinacion,
            "3": menu_matrices,
            "4": menu_ecuacion,
            "5": menu_propiedades_ax,
        }
        action = handlers.get(choice)
        if action is None:
            print("Opción no válida.")
            continue
        try:
            action()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrumpido.")
            return
        except Exception as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()

