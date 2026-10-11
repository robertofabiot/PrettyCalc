"""Compendio de teoremas de Álgebra Lineal MTM0120.

El texto vive en el motor para que la consola y cualquier otra capa lo impriman
sin copiarlo. No hay entrada interactiva aquí: quien muestra el texto decide
cómo pausar.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional

from prettycalc.core.classifier import SystemType, classify_system
from prettycalc.core.determinants import matrix_determinant
from prettycalc.core.matrix_inversion import (
    NonSquareMatrixError,
    SingularMatrixError,
    matrix_inverse,
)
from prettycalc.core.matrix_ops import matrix_multiply, matrix_transpose
from prettycalc.core.matrix_properties import PropertyCheck
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import Matrix, Vector, format_scalar
from prettycalc.core.elimination import gauss_jordan_elimination


def theorem_block(title: str, body: str) -> str:
    """Bloque de pantalla: título, cuerpo y cierre, igual que la consola histórica."""
    rule = "=" * 75
    return f"\n{rule}\n [TEOREMAS CLAVE] -- {title}\n{rule}\n{body}\n{rule}"


def text_linear_systems() -> str:
    """Rouché-Frobenius, clasificación SCD/SCI/SI y operaciones elementales."""
    return theorem_block(
        "MODULO 1: SISTEMAS DE ECUACIONES LINEALES (SEL)",
        """
1. TEOREMA DE ROUCHE-FROBENIUS (Existencia y Unicidad de Soluciones):
   Dado un sistema lineal A*x = b con m ecuaciones y n incognitas, y su matriz
   aumentada [A | b]:
   * El sistema es CONSISTENTE (tiene solucion) si y solo si:
         rango(A) = rango([A | b])
   * Si rango(A) < rango([A | b]), el sistema es INCONSISTENTE (Sin solucion).
     Aparece una fila contradictoria del tipo [ 0  0 ... 0 | c ] con c != 0.

2. CLASIFICACION DE SISTEMAS CONSISTENTES:
   Sea r = rango(A) = rango([A | b]):
   * Si r = n (rango igual al numero de incognitas):
     SISTEMA CONSISTENTE DETERMINADO (SCD) --> Posee SOLUCION UNICA.
     (Cero variables libres; cada columna de A tiene un pivote).
   * Si r < n (rango menor al numero de incognitas):
     SISTEMA CONSISTENTE INDETERMINADO (SCI) --> Posee INFINITAS SOLUCIONES.
     Existen exactamente (n - r) VARIABLES LIBRES (grados de libertad).

3. PROPIEDADES DE LAS OPERACIONES ELEMENTALES POR FILA:
   Las tres operaciones elementales preservan exactamente el conjunto solucion:
   a) Intercambio de dos filas: f_i <--> f_j
   b) Multiplicacion de una fila por un escalar k != 0: f_i --> k * f_i
   c) Suma a una fila de un multiplo de otra: f_i --> f_i + k * f_j
""",
    )


def text_vectors() -> str:
    """Independencia lineal, dimensión y vector nulo."""
    return theorem_block(
        "MODULO 2: VECTORES E INDEPENDENCIA LINEAL",
        """
1. DEFINICION FUNDAMENTAL DE INDEPENDENCIA LINEAL (L.I.):
   Un conjunto de k vectores {v_1, v_2, ..., v_k} en R^n es Linealmente Independiente
   si y solo si la unica solucion a la ecuacion vectorial homogenea:
       c_1*v_1 + c_2*v_2 + ... + c_k*v_k = 0
   es la SOLUCION TRIVIAL: c_1 = c_2 = ... = c_k = 0.

2. DEFINICION DE DEPENDENCIA LINEAL (L.D.):
   El conjunto es Linealmente Dependiente si existen escalares c_1, ..., c_k NO TODOS
   NULOS tales que c_1*v_1 + ... + c_k*v_k = 0.
   Equivalencia geometrica: Al menos un vector puede escribirse como combinacion lineal
   de los demas vectores del conjunto.

3. CONEXION CON LA FORMA ESCALONADA POR FILAS (REF) DE A*c = 0:
   Construyendo la matriz A = [ v_1  v_2 ... v_k ] de tamano n x k:
   * Si numero de pivotes r = k:
     Todas las columnas tienen pivote (0 variables libres).
     --> Unica solucion trivial --> CONJUNTO LINEALMENTE INDEPENDIENTE (L.I.).
   * Si numero de pivotes r < k:
     Existen (k - r) variables libres en el sistema homogeneo A*c = 0.
     --> Infinitas soluciones no triviales --> CONJUNTO LINEALMENTE DEPENDIENTE (L.D.).

4. TEOREMA DE LA DIMENSION (k > n):
   Si un conjunto contiene k vectores en R^n con k > n (mas vectores que la dimension
   del espacio), entonces el conjunto es NECESARIAMENTE LINEALMENTE DEPENDIENTE.
   (Motivo: En n filas solo puede haber como maximo n pivotes, por lo que r <= n < k).

5. TEOREMA DEL VECTOR NULO:
   Cualquier conjunto que contenga al vector cero 0 es LINEALMENTE DEPENDIENTE,
   ya que 1*0 + 0*v_2 + ... + 0*v_k = 0 es una solucion no trivial con c_1 = 1 != 0.

6. TEOREMA DE DOS VECTORES:
   Un conjunto de dos vectores {v_1, v_2} es L.D. si y solo si uno es multiplo escalar
   del otro (son paralelos o colineales).

7. NORMA, DISTANCIA Y PRODUCTO EXTERIOR:
   ||v||^2 = v · v = Σ v_i^2 es un racional exacto. La norma se escribe como
   radical simplificado a√b / c, sin pasar por punto flotante.
   d(u, v) = ||u - v||.
   El producto exterior u v^T es la matriz m×n con entradas u_i v_j.
""",
    )


def text_matrices() -> str:
    """Producto, transpuesta y teorema de la matriz invertible."""
    return theorem_block(
        "MODULO 3: ALGEBRA DE MATRICES Y MATRIZ INVERSA",
        """
1. CONFORMABILIDAD Y MULTIPLICACION:
   * La suma y resta A +- B solo estan definidas si A y B tienen el mismo tamano m x n.
   * El producto A*B esta definido si y solo si el numero de columnas de A coincide
     con el numero de filas de B:
         A_{m x n} * B_{n x p} = C_{m x p}
   * IMPORTANTE: El producto matricial NO es conmutativo en general (A*B != B*A).

2. PROPIEDADES DE LA TRASPUESTA:
   * (A^T)^T = A
   * (A + B)^T = A^T + B^T
   * (k * A)^T = k * A^T
   * (A * B)^T = B^T * A^T  (Inversion del orden en el producto)

3. TEOREMA DE LA MATRIZ INVERTIBLE (Para A cuadrada de n x n):
   Las siguientes afirmaciones son logicamente equivalentes:
   a) A es invertible (no singular, existe A^-1 tal que A*A^-1 = A^-1*A = I_n).
   b) A es equivalente por filas a la matriz identidad I_n.
   c) A tiene exactamente n posiciones pivote (rango(A) = n).
   d) La ecuacion A*x = 0 tiene unicamente la solucion trivial x = 0.
   e) Las columnas de A forman un conjunto Linealmente Independiente en R^n.
   f) Las columnas de A generan a R^n.
   g) det(A) != 0.

4. CALCULO DE LA MATRIZ INVERSA MEDIANTE GAUSS-JORDAN:
   Se construye la matriz aumentada [ A | I_n ]. Se aplican operaciones elementales
   hasta llevar el bloque izquierdo a la identidad:
       [ A | I_n ]  --(Gauss-Jordan)-->  [ I_n | A^-1 ]
   Si en el bloque izquierdo aparece una fila de ceros, A no tiene rango completo
   y por ende NO es invertible (es singular).
""",
    )


def text_determinants() -> str:
    """Determinante, operaciones elementales, Cramer y adjunta."""
    return theorem_block(
        "MODULO 4: DETERMINANTES Y PROPIEDADES",
        """
1. DEFINICION Y CRITERIO DE INVERTIBILIDAD:
   El determinante es una funcion escalar det: M_{n x n} --> R tal que:
   * Una matriz A es INVERTIBLE si y solo si det(A) != 0.
   * Si det(A) = 0, la matriz es SINGULAR (no invertible, columnas L.D.).

2. EFECTO DE LAS OPERACIONES ELEMENTALES SOBRE EL DETERMINANTE:
   a) Si se intercambian dos filas de A: det(A_nueva) = - det(A).
   b) Si se multiplica una fila de A por un escalar k: det(A_nueva) = k * det(A).
   c) Si se suma a una fila un multiplo de otra fila: det(A_nueva) = det(A)  (Invariante).

3. DETERMINANTE DE MATRICES TRIANGULARES:
   Si A es triangular superior, triangular inferior o diagonal, su determinante
   es simplemente el PRODUCTO DE LOS ELEMENTOS DE SU DIAGONAL PRINCIPAL:
       det(A) = a_11 * a_22 * ... * a_nn
   (Este teorema es la base del metodo de triangulacion por eliminacion gaussiana).

4. PROPIEDADES MULTIPLICATIVAS FUNDAMENTALES:
   * det(A * B) = det(A) * det(B)
   * det(A^T) = det(A)
   * Si A es invertible: det(A^-1) = 1 / det(A)
   * det(k * A_{n x n}) = k^n * det(A)

5. CASOS DONDE det(A) = 0 AUTOMATICAMENTE:
   * Si A tiene una fila o columna completamente de ceros.
   * Si dos filas (o columnas) de A son identicas.
   * Si dos filas (o columnas) de A son linealmente dependientes (multiplos escalares).

6. REGLA DE CRAMER Y MATRIZ ADJUNTA:
   Si A es n x n y det(A) != 0, la componente i de la solucion de A*x = b es
       x_i = det(A_i(b)) / det(A),
   donde A_i(b) es A con la columna i reemplazada por b.
   La adjunta es la transpuesta de la matriz de cofactores, y
       A^-1 = (1 / det(A)) * adj(A).
""",
    )


def text_applications() -> str:
    """Leontief, balanceo químico, dieta y redes de flujo."""
    return theorem_block(
        "MODULO 5: APLICACIONES DE SISTEMAS LINEALES",
        """
1. MODELO CERRADO DE INTERCAMBIO DE LEONTIEF:
   La columna j de C reparte la produccion del sector j. En el modelo cerrado
   cada columna suma 1. Los precios de equilibrio cumplen
       (I - C) p = 0.
   El sistema es homogeneo. Hay al menos un grado de libertad: los precios son
   relativos. Se normaliza la ultima variable libre en 1.

2. BALANCEO QUIMICO:
   Cada elemento da una ecuacion homogenea: atomos en reactivos menos atomos
   en productos igual a cero. La solucion del nucleo, llevada a enteros positivos
   minimos (mcm de los denominadores y luego mcd), es el conjunto de coeficientes
   estequiometricos.

3. DIETA O MEZCLA:
   Si las columnas de A son los nutrientes de cada alimento y b es el requerimiento,
       A x = b.
   Una solucion con alguna componente negativa no es realizable.

4. REDES DE FLUJO:
   En cada nodo, flujo que entra = flujo que sale. En calles de un solo sentido
   cada variable cumple x_i >= 0. Con una variable libre, esas desigualdades
   recortan un intervalo cerrado para el parametro.
""",
    )


def text_factorization() -> str:
    """Factorización A = LU y las dos sustituciones."""
    return theorem_block(
        "MODULO 6: FACTORIZACION LU",
        """
1. FACTORIZACION A = LU:
   L es triangular inferior con unos en la diagonal y los multiplicadores de la
   eliminacion debajo. U es la forma escalonada de A. Esta factorizacion no
   intercambia filas. Si un pivote es cero y debajo hay una entrada distinta de
   cero, A = LU no existe.

2. FACTORIZACION P A = L U:
   P empieza como I. Cuando el pivote es cero y hay una entrada no nula debajo,
   se intercambian esas filas en U, en P y en los multiplicadores ya guardados
   en L. La identidad que se comprueba es P A = L U.

3. RESOLUCION EN DOS ETAPAS:
   Si no hubo permutacion y la diagonal de U es distinta de cero:
   a) L y = b.
   b) U x = y.
   Si hubo permutacion:
   a) L y = P b.
   b) U x = y.
   Los factores se reutilizan con varios vectores de carga b.
""",
    )


@dataclass(frozen=True)
class TMICheckItem:
    """Una caracterización del Teorema de la Matriz Invertible."""

    code: str
    statement: str
    holds: bool
    evidence: str


@dataclass(frozen=True)
class InvertibleMatrixTheoremResult:
    """Diagnóstico del TMI: las caracterizaciones, el veredicto y la traza."""

    matrix: Matrix
    is_invertible: bool
    checks: List[TMICheckItem]
    tracer: StepTracer
    determinant: Fraction
    pivot_count: int


@dataclass(frozen=True)
class InverseIdentitiesResult:
    """Checklist de (A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹A⁻¹ y (Aᵀ)⁻¹ = (A⁻¹)ᵀ."""

    A: Matrix
    B: Optional[Matrix]
    checks: List[PropertyCheck]
    tracer: StepTracer


def _require_square_matrix(matrix: Matrix, operation: str) -> int:
    if matrix.rows != matrix.cols:
        raise NonSquareMatrixError(
            f"No se puede {operation}: la matriz es {matrix.rows}×{matrix.cols}. "
            "Esta caracterización está definida para matrices cuadradas (n×n)."
        )
    return matrix.rows


def _rref_pivot_columns(reduced: Matrix) -> List[int]:
    """Columnas 0-based con pivote en una RREF."""
    pivots: List[int] = []
    column = 0
    for row_index in range(reduced.rows):
        while column < reduced.cols:
            if reduced.get(row_index, column) != 0:
                pivots.append(column)
                column += 1
                break
            column += 1
    return pivots


def _cell_comparison(left: Matrix, right: Matrix) -> str:
    """Dice si dos matrices coinciden y, si no, qué celdas difieren."""
    if left.shape != right.shape:
        return f"los tamaños {left.rows}×{left.cols} y {right.rows}×{right.cols} no coinciden"
    mismatches: List[str] = []
    for row_index in range(left.rows):
        for col_index in range(left.cols):
            if left.get(row_index, col_index) != right.get(row_index, col_index):
                mismatches.append(f"({row_index + 1},{col_index + 1})")
    if not mismatches:
        total = left.rows * left.cols
        return f"coinciden las {total} celdas"
    shown = ", ".join(mismatches[:8])
    extra = "" if len(mismatches) <= 8 else f" y {len(mismatches) - 8} más"
    return f"difieren en las celdas {shown}{extra}"


def evaluate_invertible_matrix_theorem(A: Matrix) -> InvertibleMatrixTheoremResult:
    """Evalúa las caracterizaciones del TMI, con énfasis en *c, *e y *h.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    order = _require_square_matrix(A, "evaluar el Teorema de la Matriz Invertible")
    reduced, gauss_tracer = gauss_jordan_elimination(
        A,
        split_col=order,
        initial_description=(
            "Se reduce A por Gauss-Jordan para contar posiciones pivote y ver si A es equivalente a Iₙ."
        ),
        initial_latex=r"\text{Gauss-Jordan sobre } A",
    )
    pivot_columns = _rref_pivot_columns(reduced)
    pivot_count = len(pivot_columns)
    full_rank = pivot_count == order
    row_equivalent_to_identity = reduced == Matrix.identity(order)
    pivot_list = ", ".join(str(index + 1) for index in pivot_columns) or "ninguna"

    determinant = matrix_determinant(A)
    determinant_nonzero = determinant.value != 0

    homogeneous = classify_system(A.augment(Vector.zeros(order)), split_col=order)
    trivial_kernel = homogeneous.system_type == SystemType.CONSISTENT_DETERMINED
    if trivial_kernel:
        kernel_evidence = "A x = 0 solo admite la solución trivial x = 0."
    else:
        free_names = ", ".join(homogeneous.free_variables_names) or "al menos una"
        kernel_evidence = (
            f"A x = 0 tiene variables libres ({free_names}), así que existe una solución no trivial."
        )

    inverse_matrix: Optional[Matrix] = None
    try:
        inverse_result = matrix_inverse(A)
    except SingularMatrixError:
        inverse_exists = False
    else:
        inverse_exists = True
        inverse_matrix = inverse_result.inverse

    identity = Matrix.identity(order)
    if inverse_matrix is not None:
        left_inverse = matrix_multiply(inverse_matrix, A) == identity
        right_inverse = matrix_multiply(A, inverse_matrix) == identity
        inverse_evidence = "Existe A⁻¹ y se comprobó A · A⁻¹ = A⁻¹ · A = Iₙ."
    else:
        left_inverse = False
        right_inverse = False
        inverse_evidence = "No existe A⁻¹: la reducción de [A | Iₙ] no alcanza [Iₙ | A⁻¹]."

    transpose_determinant = matrix_determinant(matrix_transpose(A)).value
    transpose_invertible = transpose_determinant != 0

    shown_det = format_scalar(determinant.value)
    checks = [
        TMICheckItem(
            "a",
            "A es invertible.",
            inverse_exists,
            inverse_evidence,
        ),
        TMICheckItem(
            "b",
            "A es equivalente por filas a Iₙ.",
            row_equivalent_to_identity,
            "La forma reducida de A es Iₙ."
            if row_equivalent_to_identity
            else "La forma reducida de A no es Iₙ.",
        ),
        TMICheckItem(
            "*c",
            f"A tiene exactamente {order} posiciones pivote.",
            full_rank,
            f"Gauss-Jordan encuentra {pivot_count} pivote(s), en las columnas {pivot_list}. "
            f"Se necesitan {order}.",
        ),
        TMICheckItem(
            "d",
            "A x = 0 tiene únicamente la solución trivial.",
            trivial_kernel,
            kernel_evidence,
        ),
        TMICheckItem(
            "*e",
            "Las columnas de A son linealmente independientes.",
            trivial_kernel,
            kernel_evidence
            if trivial_kernel
            else f"{kernel_evidence} Por tanto las columnas son linealmente dependientes.",
        ),
        TMICheckItem(
            "f",
            "La transformación x ↦ A x es inyectiva.",
            trivial_kernel,
            "El núcleo es {0}, así que x ↦ A x es inyectiva."
            if trivial_kernel
            else "Hay un núcleo no trivial, así que x ↦ A x no es inyectiva.",
        ),
        TMICheckItem(
            "g",
            "A x = b tiene al menos una solución para cada b de ℝⁿ.",
            full_rank,
            f"rango(A) = {pivot_count}. "
            + (
                f"Como el rango es {order}, A x = b es consistente para todo b ∈ ℝ{order}."
                if full_rank
                else f"Como el rango es menor que {order}, algún b ∈ ℝ{order} deja el sistema inconsistente."
            ),
        ),
        TMICheckItem(
            "*h",
            f"Las columnas de A generan ℝ{order}.",
            full_rank,
            f"Hay {order} columnas en ℝ{order} y rango(A) = {pivot_count}. "
            + (
                f"Generan todo ℝ{order}."
                if full_rank
                else f"No generan ℝ{order}."
            ),
        ),
        TMICheckItem(
            "i",
            f"La transformación x ↦ A x es sobreyectiva sobre ℝ{order}.",
            full_rank,
            "La imagen es todo el codominio."
            if full_rank
            else "La imagen no es todo el codominio.",
        ),
        TMICheckItem(
            "j",
            "Existe una matriz C tal que C A = Iₙ.",
            left_inverse,
            "C = A⁻¹ cumple C A = Iₙ." if left_inverse else "No existe inversa por la izquierda.",
        ),
        TMICheckItem(
            "k",
            "Existe una matriz D tal que A D = Iₙ.",
            right_inverse,
            "D = A⁻¹ cumple A D = Iₙ." if right_inverse else "No existe inversa por la derecha.",
        ),
        TMICheckItem(
            "l",
            "Aᵀ es invertible.",
            transpose_invertible,
            f"det(Aᵀ) = {format_scalar(transpose_determinant)}"
            + (" ≠ 0." if transpose_invertible else " = 0."),
        ),
        TMICheckItem(
            "det",
            "det(A) ≠ 0.",
            determinant_nonzero,
            f"det(A) = {shown_det}" + (" ≠ 0." if determinant_nonzero else " = 0."),
        ),
    ]
    is_invertible = all(item.holds for item in checks)
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description=(
            f"Teorema de la Matriz Invertible para A de orden {order}. "
            "Las caracterizaciones son equivalentes: se comprueban *c, *e, *h y det(A)."
        ),
        latex_title=r"\text{TMI}",
    )
    for step in gauss_tracer.get_steps():
        if step.step_number == 0:
            continue
        tracer.record_step(
            step.matrix,
            latex_formula=step.latex_formula,
            heuristic_text=step.heuristic_text,
            pivot_pos=step.pivot_pos,
            actor_row=step.actor_row,
            affected_rows=step.affected_rows,
        )
    verdict = "A es invertible." if is_invertible else "A es singular."
    tracer.record_step(
        reduced,
        latex_formula=rf"\det(A) = {format_scalar(determinant.value, mode='latex')}",
        heuristic_text=(
            f"{verdict} Posiciones pivote: {pivot_count} de {order}. "
            f"det(A) = {shown_det}. {kernel_evidence}"
        ),
    )
    return InvertibleMatrixTheoremResult(
        matrix=A.copy(),
        is_invertible=is_invertible,
        checks=checks,
        tracer=tracer,
        determinant=determinant.value,
        pivot_count=pivot_count,
    )


def verify_inverse_algebraic_identities(
    A: Matrix,
    B: Optional[Matrix] = None,
) -> InverseIdentitiesResult:
    """Comprueba (A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹A⁻¹ y (Aᵀ)⁻¹ = (A⁻¹)ᵀ.

    Raises:
        NonSquareMatrixError: Si A no es cuadrada.
    """
    order = _require_square_matrix(A, "comprobar las identidades de la inversa")
    tracer = StepTracer()
    tracer.record_initial(
        A,
        description="Identidades de la inversa: se calculan ambos lados y se comparan celda a celda.",
        latex_title=r"(A^{-1})^{-1} = A",
    )
    checks: List[PropertyCheck] = []

    try:
        inverse_a = matrix_inverse(A).inverse
    except SingularMatrixError as exc:
        singular_detail = str(exc)
        checks.append(PropertyCheck("(A⁻¹)⁻¹ = A", "no_cumple", singular_detail))
        checks.append(
            PropertyCheck(
                "(Aᵀ)⁻¹ = (A⁻¹)ᵀ",
                "no_cumple",
                "A es singular, así que no existen A⁻¹ ni (Aᵀ)⁻¹.",
            )
        )
        tracer.record_step(
            A,
            latex_formula=r"\det(A) = 0",
            heuristic_text=singular_detail,
        )
    else:
        double_inverse = matrix_inverse(inverse_a).inverse
        double_match = double_inverse == A
        checks.append(
            PropertyCheck(
                "(A⁻¹)⁻¹ = A",
                "cumple" if double_match else "no_cumple",
                "Se comparó celda a celda: " + _cell_comparison(double_inverse, A) + ".",
            )
        )
        tracer.record_step(
            double_inverse,
            latex_formula=r"(A^{-1})^{-1}",
            heuristic_text=checks[-1].detail,
        )

        transpose_inverse = matrix_inverse(matrix_transpose(A)).inverse
        inverse_transpose = matrix_transpose(inverse_a)
        transpose_match = transpose_inverse == inverse_transpose
        checks.append(
            PropertyCheck(
                "(Aᵀ)⁻¹ = (A⁻¹)ᵀ",
                "cumple" if transpose_match else "no_cumple",
                "Se comparó celda a celda: " + _cell_comparison(transpose_inverse, inverse_transpose) + ".",
            )
        )
        tracer.record_step(
            inverse_transpose,
            latex_formula=r"(A^{T})^{-1} = (A^{-1})^{T}",
            heuristic_text=checks[-1].detail,
        )

    if B is None:
        product_check = PropertyCheck(
            "(AB)⁻¹ = B⁻¹ A⁻¹",
            "no_aplica",
            "No se entregó una segunda matriz B.",
        )
    elif B.rows != B.cols or B.rows != order:
        product_check = PropertyCheck(
            "(AB)⁻¹ = B⁻¹ A⁻¹",
            "no_aplica",
            f"A es {order}×{order} y B es {B.rows}×{B.cols}. "
            "La identidad pide dos matrices cuadradas del mismo orden.",
        )
    else:
        try:
            inverse_b = matrix_inverse(B).inverse
            product = matrix_multiply(A, B)
            inverse_product = matrix_inverse(product).inverse
        except SingularMatrixError as exc:
            product_check = PropertyCheck("(AB)⁻¹ = B⁻¹ A⁻¹", "no_cumple", str(exc))
        else:
            reversed_product = matrix_multiply(inverse_b, inverse_a)
            product_match = inverse_product == reversed_product
            product_check = PropertyCheck(
                "(AB)⁻¹ = B⁻¹ A⁻¹",
                "cumple" if product_match else "no_cumple",
                "Se comparó celda a celda: " + _cell_comparison(inverse_product, reversed_product) + ".",
            )
            tracer.record_step(
                reversed_product,
                latex_formula=r"(AB)^{-1} = B^{-1} A^{-1}",
                heuristic_text=product_check.detail,
            )
    checks.insert(1, product_check)
    return InverseIdentitiesResult(A=A.copy(), B=None if B is None else B.copy(), checks=checks, tracer=tracer)


def all_theorem_texts() -> List[str]:
    """Compendio completo, en el orden de los módulos de la consola."""
    return [
        text_linear_systems(),
        text_vectors(),
        text_matrices(),
        text_determinants(),
        text_applications(),
        text_factorization(),
    ]
