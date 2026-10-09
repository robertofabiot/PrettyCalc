"""================================================================================
UNIVERSIDAD AMERICANA (UAM) - FIA | ÁLGEBRA LINEAL (MTM0120) - GRUPO 4
MÓDULO 3: Álgebra de Matrices e Inversa
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path
from typing import List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_matrices
except ImportError:
    calc_dir = Path(__file__).resolve().parent.parent
    parent_dir = calc_dir.parent
    for p in (str(calc_dir), str(parent_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_matrices
    except ImportError:
        from teoremas.resumen_teoremas import mostrar_teoremas_matrices



def parse_scalar(text: str) -> Fraction:
    """Convierte texto en Fraction exacta."""
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
    """Formatea una fracción para visualización limpia."""
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def read_scalar(prompt: str) -> Fraction:
    """Lectura robusta de escalares."""
    while True:
        try:
            return parse_scalar(input(prompt))
        except (ValueError, ZeroDivisionError) as exc:
            print(f"   ⚠️  Entrada inválida ({exc}). Intente de nuevo (ej. 2, -3/5, 0.25):")


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
    split_col: Optional[int] = None
) -> None:
    """Imprime una matriz formateada con alineación tabular."""
    if title:
        print(f"\n--- {title} ---")
    if not matrix or not matrix[0]:
        print("│ [Matriz vacía] │")
        return

    rows = len(matrix)
    cols = len(matrix[0])
    cells = [[fmt(matrix[r][c]) for c in range(cols)] for r in range(rows)]
    widths = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]

    for r in range(rows):
        if split_col is None:
            row_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(cols))
            print(f"│  {row_str}  │")
        else:
            left_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col))
            right_str = "  ".join(cells[r][c].rjust(widths[c]) for c in range(split_col, cols))
            print(f"│  {left_str}  │  {right_str}  │")


def read_matrix(rows: int, cols: int, name: str = "A") -> List[List[Fraction]]:
    """Lectura celda a celda de una matriz."""
    print(f"\nIngrese las entradas de la matriz {name} ({rows}×{cols}):")
    mat: List[List[Fraction]] = []
    for i in range(rows):
        row: List[Fraction] = []
        print(f"  Fila {i+1}:")
        for j in range(cols):
            val = read_scalar(f"     {name}[{i+1},{j+1}]: ")
            row.append(val)
        mat.append(row)
    return mat


def suma_resta_matrices_interactivo() -> None:
    """Operación 1: Suma y resta de matrices."""
    print("\n" + "-" * 60)
    print("SUMA Y RESTA DE MATRICES (A ± B)")
    print("-" * 60)
    rows = read_positive_int("Número de filas m: ")
    cols = read_positive_int("Número de columnas n: ")

    A = read_matrix(rows, cols, "A")
    B = read_matrix(rows, cols, "B")

    S = [[A[i][j] + B[i][j] for j in range(cols)] for i in range(rows)]
    R = [[A[i][j] - B[i][j] for j in range(cols)] for i in range(rows)]

    print_matrix(A, "Matriz A")
    print_matrix(B, "Matriz B")
    print_matrix(S, "Resultado: A + B")
    print_matrix(R, "Resultado: A - B")


def producto_escalar_interactivo() -> None:
    """Operación 2: Multiplicación por escalar k · A."""
    print("\n" + "-" * 60)
    print("MULTIPLICACIÓN DE MATRIZ POR ESCALAR (k · A)")
    print("-" * 60)
    rows = read_positive_int("Número de filas m: ")
    cols = read_positive_int("Número de columnas n: ")
    k = read_scalar("Escalar k: ")
    A = read_matrix(rows, cols, "A")

    scaled = [[k * A[i][j] for j in range(cols)] for i in range(rows)]

    print_matrix(A, "Matriz Original A")
    print_matrix(scaled, f"Resultado: ({fmt(k)}) · A")


def producto_matrices_interactivo() -> None:
    """Operación 3: Producto de matrices A_{m×n} · B_{n×p}."""
    print("\n" + "-" * 60)
    print("PRODUCTO MATRICIAL: A_{m×n} · B_{n×p} = C_{m×p}")
    print("-" * 60)
    m = read_positive_int("Filas de A (m): ")
    n = read_positive_int("Columnas de A / Filas de B (n): ")
    p = read_positive_int("Columnas de B (p): ")

    A = read_matrix(m, n, "A")
    B = read_matrix(n, p, "B")

    # Producto mediante 3 bucles anidados exactos
    C = []
    for i in range(m):
        row = []
        for j in range(p):
            cell_sum = sum(A[i][k_idx] * B[k_idx][j] for k_idx in range(n))
            row.append(cell_sum)
        C.append(row)

    print_matrix(A, f"Matriz A ({m}×{n})")
    print_matrix(B, f"Matriz B ({n}×{p})")
    print_matrix(C, f"Matriz Producto C = A · B ({m}×{p})")


def traspuesta_matriz_interactivo() -> None:
    """Operación 4: Traspuesta A^T y doble traspuesta (A^T)^T = A."""
    print("\n" + "-" * 60)
    print("TRASPUESTA Y DOBLE TRASPUESTA DE UNA MATRIZ (A^T) Y ((A^T)^T = A)")
    print("-" * 60)
    rows = read_positive_int("Número de filas m: ")
    cols = read_positive_int("Número de columnas n: ")
    A = read_matrix(rows, cols, "A")

    At = [[A[r][c] for r in range(rows)] for c in range(cols)]
    Att = [[At[r][c] for r in range(cols)] for c in range(rows)]

    print_matrix(A, f"Matriz Original A ({rows}×{cols})")
    print_matrix(At, f"Matriz Traspuesta A^T ({cols}×{rows})")
    print_matrix(Att, f"Matriz Doble Traspuesta (A^T)^T ({rows}×{cols})")

    holds = Att == A
    mark = "✓" if holds else "✗"
    print(f"\n{mark} Comprobación de identidad: (A^T)^T == A {'(Se verifica idénticamente)' if holds else '(Discrepancia)'}")


def inversa_matriz_interactivo() -> None:
    """Operación 5: Matriz inversa mediante Gauss-Jordan sobre [A | I_n]."""
    print("\n" + "-" * 60)
    print("CÁLCULO DE LA MATRIZ INVERSA POR GAUSS-JORDAN [A | I_n]")
    print("-" * 60)
    n = read_positive_int("Dimensión de la matriz cuadrada n: ")
    A = read_matrix(n, n, "A")

    # Construir [A | I_n]
    aug = []
    for i in range(n):
        row = [A[i][j] for j in range(n)]
        row.extend([Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n)])
        aug.append(row)

    print_matrix(aug, title="Matriz Aumentada Inicial [A | I_n]", split_col=n)

    mat = [[c for c in row] for row in aug]
    step = 1

    # Eliminación Gaussiana hacia adelante
    for col in range(n):
        pivot_r = None
        for r in range(col, n):
            if mat[r][col] != Fraction(0, 1):
                pivot_r = r
                break

        if pivot_r is None:
            print("\n🔴 RESULTADO: La matriz A NO ES INVERTIBLE (es SINGULAR).")
            print("   Se encontró una columna sin pivote en el bloque izquierdo.")
            print("   rango(A) < n, por lo tanto det(A) = 0 y no existe A⁻¹.")
            return

        if pivot_r != col:
            mat[col], mat[pivot_r] = mat[pivot_r], mat[col]
            print_matrix(
                mat,
                title=f"Paso {step}: Fila {col+1} ↔ Fila {pivot_r+1} (Intercambio)",
                split_col=n
            )
            step += 1

        piv_val = mat[col][col]
        for r in range(col + 1, n):
            if mat[r][col] != Fraction(0, 1):
                factor = - (mat[r][col] / piv_val)
                for c in range(2 * n):
                    mat[r][c] = mat[r][c] + (factor * mat[col][c])
                desc = f"f_{r+1} → f_{r+1} + ({fmt(factor)})·f_{col+1}"
                print_matrix(mat, title=f"Paso {step}: {desc}", split_col=n)
                step += 1

    # Eliminación hacia atrás (Gauss-Jordan) y normalización
    for col in range(n - 1, -1, -1):
        piv_val = mat[col][col]
        if piv_val != Fraction(1, 1):
            scale = Fraction(1, 1) / piv_val
            for c in range(2 * n):
                mat[col][c] = mat[col][c] * scale
            print_matrix(mat, title=f"Paso {step}: f_{col+1} → ({fmt(scale)})·f_{col+1}", split_col=n)
            step += 1

        for up_r in range(col - 1, -1, -1):
            if mat[up_r][col] != Fraction(0, 1):
                factor = - mat[up_r][col]
                for c in range(2 * n):
                    mat[up_r][c] = mat[up_r][c] + (factor * mat[col][c])
                desc = f"f_{up_r+1} → f_{up_r+1} + ({fmt(factor)})·f_{col+1}"
                print_matrix(mat, title=f"Paso {step}: {desc}", split_col=n)
                step += 1

    # Extraer A^-1 del bloque derecho
    inv = [[mat[i][j + n] for j in range(n)] for i in range(n)]

    print("\n🟢 RESULTADO: Matriz Invertible. Forma final [I_n | A⁻¹]:")
    print_matrix(mat, split_col=n)
    print_matrix(inv, title="Matriz Inversa A⁻¹")

    # Verificación A · A^-1 == I_n
    print("\nComprobación de Identidad (A · A⁻¹ == I_n):")
    is_identity = True
    for i in range(n):
        for j in range(n):
            val = sum(A[i][k_idx] * inv[k_idx][j] for k_idx in range(n))
            expected = Fraction(1, 1) if i == j else Fraction(0, 1)
            if val != expected:
                is_identity = False
    if is_identity:
        print("   ✓ Producto A · A⁻¹ comprobado exactamente igual a la matriz identidad I_n.")


def propiedades_distributivas_interactivo() -> None:
    """Operación 6: Propiedad distributiva A(B+C) = AB + AC y asociativa A(BC) = (AB)C."""
    print("\n" + "-" * 60)
    print("PROPIEDADES DISTRIBUTIVAS Y ASOCIATIVAS MATRICIALES")
    print("-" * 60)
    print(" 1. Distributiva izquierda: A · (B + C) = A · B + A · C")
    print(" 2. Distributiva derecha:   (A + B) · C = A · C + B · C")
    print(" 3. Asociativa:             A · (B · C) = (A · B) · C")
    opc = input("Seleccione una opción (1-3): ").strip()
    if opc == "1":
        m = read_positive_int("Filas de A (m): ")
        n = read_positive_int("Columnas de A / Filas de B y C (n): ")
        p = read_positive_int("Columnas de B y C (p): ")
        A = read_matrix(m, n, "A")
        B = read_matrix(n, p, "B")
        C = read_matrix(n, p, "C")
        B_plus_C = [[B[i][j] + C[i][j] for j in range(p)] for i in range(n)]
        lhs = [[sum(A[i][k] * B_plus_C[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        ab = [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        ac = [[sum(A[i][k] * C[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        rhs = [[ab[i][j] + ac[i][j] for j in range(p)] for i in range(m)]
        print_matrix(lhs, f"LHS: A · (B + C) ({m}×{p})")
        print_matrix(rhs, f"RHS: A·B + A·C ({m}×{p})")
        holds = lhs == rhs
        mark = "✓" if holds else "✗"
        print(f"\n{mark} Comprobación: A(B + C) == AB + AC {'(Se cumple la igualdad)' if holds else '(Discrepancia)'}")
    elif opc == "2":
        m = read_positive_int("Filas de A y B (m): ")
        n = read_positive_int("Columnas de A y B / Filas de C (n): ")
        p = read_positive_int("Columnas de C (p): ")
        A = read_matrix(m, n, "A")
        B = read_matrix(m, n, "B")
        C = read_matrix(n, p, "C")
        A_plus_B = [[A[i][j] + B[i][j] for j in range(n)] for i in range(m)]
        lhs = [[sum(A_plus_B[i][k] * C[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        ac = [[sum(A[i][k] * C[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        bc = [[sum(B[i][k] * C[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        rhs = [[ac[i][j] + bc[i][j] for j in range(p)] for i in range(m)]
        print_matrix(lhs, f"LHS: (A + B) · C ({m}×{p})")
        print_matrix(rhs, f"RHS: A·C + B·C ({m}×{p})")
        holds = lhs == rhs
        mark = "✓" if holds else "✗"
        print(f"\n{mark} Comprobación: (A + B)C == AC + BC {'(Se cumple la igualdad)' if holds else '(Discrepancia)'}")
    elif opc == "3":
        m = read_positive_int("Filas de A (m): ")
        n = read_positive_int("Columnas de A / Filas de B (n): ")
        p = read_positive_int("Columnas de B / Filas de C (p): ")
        q = read_positive_int("Columnas de C (q): ")
        A = read_matrix(m, n, "A")
        B = read_matrix(n, p, "B")
        C = read_matrix(p, q, "C")
        bc = [[sum(B[i][k] * C[k][j] for k in range(p)) for j in range(q)] for i in range(n)]
        lhs = [[sum(A[i][k] * bc[k][j] for k in range(n)) for j in range(q)] for i in range(m)]
        ab = [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(p)] for i in range(m)]
        rhs = [[sum(ab[i][k] * C[k][j] for k in range(p)) for j in range(q)] for i in range(m)]
        print_matrix(lhs, f"LHS: A · (B · C) ({m}×{q})")
        print_matrix(rhs, f"RHS: (A · B) · C ({m}×{q})")
        holds = lhs == rhs
        mark = "✓" if holds else "✗"
        print(f"\n{mark} Comprobación: A(BC) == (AB)C {'(Se cumple la igualdad)' if holds else '(Discrepancia)'}")
    else:
        print("   ⚠️  Opción no válida.")


def menu_matrices() -> None:
    """Menú principal del Módulo 3 con Logotipo ASCII requerido."""
    while True:
        print("\n" + "=" * 54)
        print(" [ A ][ B ] MÓDULO: ÁLGEBRA DE MATRICES")
        print(" [ C ][ D ] Operaciones, Traspuesta y Matriz Inversa")
        print("=" * 54)
        print(" 0. Ver Teoremas Clave del Módulo")
        print(" 1. Suma y Resta de Matrices (A ± B)")
        print(" 2. Multiplicación de Matriz por Escalar (k · A)")
        print(" 3. Multiplicación de Matrices (A · B)")
        print(" 4. Traspuesta y Doble Traspuesta ((A^T)^T = A)")
        print(" 5. Cálculo de Matriz Inversa por Gauss-Jordan (A⁻¹)")
        print(" 6. Propiedades Distributiva y Asociativa (A(B+C) = AB + AC, A(BC) = (AB)C)")
        print(" 7. Volver al Menú Principal")
        print("=" * 54)

        opc = input("Seleccione una opción (0-7): ").strip()

        if opc == "0":
            mostrar_teoremas_matrices()
            input("\nPresione ENTER para continuar...")
        elif opc == "1":
            suma_resta_matrices_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            producto_escalar_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "3":
            producto_matrices_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "4":
            traspuesta_matriz_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "5":
            inversa_matriz_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "6":
            propiedades_distributivas_interactivo()
            input("\nPresione ENTER para continuar...")
        elif opc == "7":
            break
        else:
            print("   ⚠️  Opción no reconocida. Ingrese un número entre 0 y 7.")


if __name__ == "__main__":
    menu_matrices()
