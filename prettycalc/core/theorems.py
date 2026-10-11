"""Compendio de teoremas de Álgebra Lineal MTM0120.

El texto vive en el motor para que la consola y cualquier otra capa lo impriman
sin copiarlo. No hay entrada interactiva aquí: quien muestra el texto decide
cómo pausar.
"""

from __future__ import annotations

from typing import List


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
   eliminacion debajo. U es la forma escalonada de A. No se intercambian filas.
   Si un pivote es cero y debajo hay una entrada distinta de cero, hace falta una
   permutacion PLU, que esta factorizacion no construye.

2. RESOLUCION EN DOS ETAPAS:
   Para A x = b, con A = LU y la diagonal de U distinta de cero:
   a) Sustitucion hacia adelante: L y = b.
   b) Sustitucion hacia atras: U x = y.
   Los factores se reutilizan con varios vectores de carga b.
""",
    )


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
