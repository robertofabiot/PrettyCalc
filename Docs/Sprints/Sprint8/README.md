# Sprint 8: Consolidación Final, Propiedades Avanzadas y Factorización PLU (Sesiones 1 a 12)

**Fecha de Inicio:** 2026-10-11  
**Fecha de Fin:** 2026-10-18  
**Estado:** Implementado  
**Rama Git de Trabajo:** `feature/sprint-8-consolidacion-propiedades-plu`  
**Rama Destino:** `main`  
**Asignatura:** Álgebra Lineal (MTM0120) — II Semestre 2026  
**Institución:** Universidad Americana (UAM) — Facultad de Ingeniería y Arquitectura (FIA)  

---

## 1. Objetivo del Sprint (Sprint Goal)

El objetivo de este sprint es alcanzar el **100% de cobertura y cálculo directo y nativo** de todos los requerimientos, teoremas destacados y ejercicios procedimentales impartidos en las **Sesiones 1 a 12** de Álgebra Lineal, resolviendo las brechas menores y casos de generalización pendientes identificados tras la auditoría integral de `main`.

Con este ciclo, PrettyCalc:
1. Dotará al módulo de vectores de métricas métricas euclidianas (norma $\|v\|$ y distancia $\|u - v\|$) y el producto diádico o exterior $u v^T$ pedido explícitamente en clase.
2. Implementará un evaluador programático del **Teorema de la Matriz Invertible (TMI)** enfocado en las condiciones destacadas con asterisco por la cátedra (\*c pivotes, \*e independencia lineal de columnas, \*h generación de $\mathbb{R}^n$), junto con la verificación formal de las identidades algebraicas de la inversa ($(A^{-1})^{-1}$, $(AB)^{-1}$, $(A^T)^{-1}$).
3. Añadirá un comprobador sistemático de las **propiedades multiplicativas del determinante** ($\det(AB) = \det(A)\det(B)$, $\det(A^T) = \det(A)$, $\det(A^{-1}) = 1/\det(A)$, $\det(kA) = k^n \det(A)$).
4. Generalizará la descomposición triangular a **Factorización PLU ($PA = LU$)** con permutaciones de filas cuando un pivote sea nulo, permitiendo resolver $Ax = b$ mediante $Ly = Pb$ y $Ux = y$ para cualquier matriz cuadrada invertible sin restricciones de pivote cero.

---

## 2. Requerimientos Específicos de la Iteración

### 2.1. Métricas Vectoriales y Producto Exterior (Sesiones 5 y 9)
- [x] **REQ-8.1 (Norma Euclidiana y Distancia):**
  - Implementar en `prettycalc.core.vector_ops` el cálculo exacto de la norma al cuadrado $\|v\|^2 = \sum v_i^2 = v \cdot v \in \mathbb{Q}$, la simplificación radical simbólica exacta $\sqrt{p/q}$ o representación irreductible $a\sqrt{b}/c$, y la distancia euclidiana entre dos vectores $d(u, v) = \|u - v\|$.
  - Incorporar en `prettycalc.ui.modules.vectors_view` controles para calcular directamente la norma de cualquier vector y la distancia entre pares de vectores con trazabilidad paso a paso.
- [x] **REQ-8.2 (Producto Exterior de Vectores $u v^T$):**
  - Implementar en `prettycalc.core.vector_ops` la función `vector_outer_product(u: Vector, v: Vector) -> Matrix`, generando la matriz de rango 1 de dimensiones $m \times n$ donde $M_{ij} = u_i \cdot v_j$, cubriendo el ejercicio de la Sesión 9 (Slide 15: cálculo de $x x^T$).
  - Integrar la opción de producto exterior en la interfaz gráfica (`VectorsView`).

### 2.2. Evaluador del Teorema de la Matriz Invertible y Propiedades de la Inversa (Sesión 10)
- [x] **REQ-8.3 (Evaluador Programático del TMI - Condiciones con Asterisco):**
  - Implementar en `prettycalc.core.theorems` / `matrix_properties.py` la función `evaluate_invertible_matrix_theorem(A: Matrix) -> InvertibleMatrixTheoremResult` que analice una matriz cuadrada $n \times n$ y verifique con evidencia formal:
    - **Condición \*c:** $A$ tiene exactamente $n$ posiciones pivote ($\text{rango}(A) = n$).
    - **Condición \*e:** Las columnas de $A$ son linealmente independientes ($Ax = 0$ solo tiene solución trivial).
    - **Condición \*h:** Las columnas de $A$ generan a $\mathbb{R}^n$ ($\text{Span}(\text{col}(A)) = \mathbb{R}^n$).
    - **Condiciones complementarias:** $\det(A) \neq 0$, $A \sim I_n$, existencia efectiva de $A^{-1}$.
  - Diseñar en `prettycalc.ui` una tarjeta/panel interactivo de inspección del TMI dentro del módulo de Álgebra Matricial / Inversa.
- [x] **REQ-8.4 (Comprobador de Identidades Algebraicas de la Inversa):**
  - Implementar la verificación y desglose paso a paso de:
    - Identidad 1: $(A^{-1})^{-1} = A$.
    - Identidad 2: $(AB)^{-1} = B^{-1} A^{-1}$ (con matrices cuadradas invertibles conformables).
    - Identidad 3: $(A^T)^{-1} = (A^{-1})^T$.
  - Desplegar checklist celda a celda de verificación de estas identidades.

### 2.3. Propiedades Multiplicativas de Determinantes (Sesión 11)
- [x] **REQ-8.5 (Verificador de Propiedades de Determinantes):**
  - Implementar en `prettycalc.core.determinants` / `matrix_properties.py` el verificador `verify_determinant_properties(A: Matrix, B: Optional[Matrix] = None, k: Optional[Fraction] = None)` que contraste formalmente:
    - Multiplicatividad: $\det(AB) \stackrel{?}{=} \det(A) \cdot \det(B)$ (Sesión 11, Slide 24).
    - Transpuesta: $\det(A^T) \stackrel{?}{=} \det(A)$.
    - Inversa: $\det(A^{-1}) \stackrel{?}{=} 1 / \det(A)$ (para matrices no singulares).
    - Escalamiento: $\det(kA) \stackrel{?}{=} k^n \det(A)$ para matriz $n \times n$.
  - Agregar en `DeterminantsView` una sub-pestaña o tarjeta de "Propiedades de Determinantes" para comprobar estas leyes con matrices arbitrarias o ejemplos de clase.

### 2.4. Descomposición PLU ($PA = LU$) y Solucionador Generalizado (Sesión 12)
- [x] **REQ-8.6 (Factorización PLU con Permutación de Filas):**
  - Extender `prettycalc.core.lu_decomposition` para admitir matrices donde un pivote natural es cero mediante permutación parcial de filas:
    $$P \cdot A = L \cdot U$$
    donde $P$ es una matriz de permutación cuadrada $m \times m$, $L$ es triangular inferior unitaria con unos en la diagonal, y $U$ es escalonada superior.
  - Registrar formalmente en `StepTracer` cada permutación de fila $f_i \leftrightarrow f_j$ y su impacto en la matriz de permutación acumulada $P$.
- [x] **REQ-8.7 (Solución Encadenada PLU en 2 Etapas):**
  - Implementar `solve_via_plu(A: Matrix, b: Vector)` resolviendo:
    1. Etapa 1: $L y = P b$ (sustitución hacia adelante con vector de carga permutado).
    2. Etapa 2: $U x = y$ (sustitución hacia atrás).
  - Actualizar `prettycalc.ui.modules.lu_factorization_view` para visualizar la matriz de permutación $P$, el vector permutado $Pb$ y permitir factorizar matrices que antes arrojaban `LUPivotZeroError`.

---

## 3. Desglose de Tareas Técnicas

### 3.1. Motor Matemático (`prettycalc.core`)

#### Módulo `vector_ops.py`
- [x] `vector_norm_squared(v: Vector) -> Fraction`: Retorna el valor exacto racional de $\sum v_i^2$.
- [x] `vector_norm_exact(v: Vector) -> Tuple[Fraction, int, int]`: Retorna la descomposición radical exacta $(coef, radical\_num, radical\_den)$ tal que $\|v\| = coef \sqrt{rad}$.
- [x] `vector_distance_squared(u: Vector, v: Vector) -> Fraction`: Retorna $\|u - v\|^2$.
- [x] `vector_outer_product(u: Vector, v: Vector) -> Matrix`: Construye la matriz de rango 1 de dimensiones $u.dim \times v.dim$.

#### Módulo `theorems.py` y `matrix_properties.py`
- [x] Definir dataclass `TMICheckItem(code: str, statement: str, holds: bool, evidence: str)`.
- [x] Definir dataclass `InvertibleMatrixTheoremResult(matrix: Matrix, is_invertible: bool, checks: List[TMICheckItem], tracer: StepTracer)`.
- [x] Implementar `evaluate_invertible_matrix_theorem(A: Matrix) -> InvertibleMatrixTheoremResult`:
  - Evalúa y reporta pivotes (\*c), independencia de columnas (\*e), generación de $\mathbb{R}^n$ (\*h), y valor de $\det(A)$.
- [x] Implementar `verify_inverse_algebraic_identities(A: Matrix, B: Optional[Matrix] = None) -> List[PropertyCheck]`.

#### Módulo `determinants.py`
- [x] Definir dataclass `DeterminantPropertiesResult(det_A: Fraction, det_B: Optional[Fraction], ... checklist)`.
- [x] Implementar `verify_determinant_multiplicative(A: Matrix, B: Matrix) -> Tuple[Fraction, Fraction, Fraction, bool, StepTracer]`.
- [x] Implementar `verify_determinant_transpose(A: Matrix) -> Tuple[Fraction, Fraction, bool]`.
- [x] Implementar `verify_determinant_inverse(A: Matrix) -> Tuple[Fraction, Fraction, bool]`.
- [x] Implementar `verify_determinant_scalar_scaling(A: Matrix, k: Fraction) -> Tuple[Fraction, Fraction, bool]`.

#### Módulo `lu_decomposition.py`
- [x] Definir dataclass `PLUFactorizationResult(P: Matrix, L: Matrix, U: Matrix, original: Matrix, is_valid: bool, permutation_count: int, tracer: StepTracer)`.
- [x] Implementar `plu_decompose(A: Matrix) -> PLUFactorizationResult`:
  - Algoritmo con pivoteo parcial: si $A_{pivot, pivot} == 0$, buscar fila $k > pivot$ con mayor magnitud o primera entrada no nula, aplicar intercambio a $A$, actualizar $P$, e intercambiar los multiplicadores ya acumulados en las columnas previas de $L$.
- [x] Implementar `solve_from_plu_factorization(plu: PLUFactorizationResult, b: Vector) -> LUSystemSolutionResult`:
  - Permutar vector de carga $b_{perm} = P \cdot b$.
  - Resolver $Ly = b_{perm}$ y $Ux = y$.
- [x] Mantener `lu_decompose(A)` como caso particular / atajo que no permuta, o redirigir de forma transparente preservando retrocompatibilidad.

---

### 3.2. Interfaz / Visualización (`prettycalc.ui`)

#### Vista de Vectores (`prettycalc/ui/modules/vectors_view.py`)
- [x] Añadir panel/botones en `VectorsView` para:
  - "Calcular Norma $\|v\|$" para cualquier vector del conjunto.
  - "Calcular Distancia $d(u, v)$" entre dos vectores seleccionados.
  - "Producto Exterior $u \cdot v^T$" con visualización de la matriz resultante en el grid estándar.

#### Vista de Operaciones Matriciales (`prettycalc/ui/modules/matrix_operations_view.py`)
- [x] Añadir sub-pestaña "Teorema de la Matriz Invertible (TMI)":
  - Selector de matriz cuadrada $A$.
  - Botón "Evaluar TMI (Caracterizaciones de Invertibilidad)".
  - Despliegue en tarjetas estilo checklist con badges verdes/rojos para las propiedades \*c, \*e, \*h y $\det(A) \neq 0$.
- [x] Sub-pestaña o tarjeta de "Identidades de la Inversa" ($(AB)^{-1} = B^{-1} A^{-1}$ y $(A^T)^{-1} = (A^{-1})^T$).

#### Vista de Determinantes (`prettycalc/ui/modules/determinants_view.py`)
- [x] Añadir sección "Comprobación de Propiedades de Determinantes":
  - Entradas para matrices $A$ y $B$, y escalar $k$.
  - Verificación visual de $\det(AB) = \det(A)\det(B)$, $\det(A^T) = \det(A)$ y $\det(kA) = k^n \det(A)$.

#### Vista de Factorización LU (`prettycalc/ui/modules/lu_factorization_view.py`)
- [x] Incorporar visualización de la matriz de permutación $P$ en el layout de resultados ($P \cdot A = L \cdot U$).
- [x] Actualizar el banner y el visor de pasos para matrices que requieran permutación de filas, mostrando $Pb$ y explicando el paso de pivoteo.

---

### 3.3. Pruebas y Validación (`tests/`)

- [x] **Tests de Vectores:**
  - `tests/core/test_vector_metric_ops.py`:
    - Norma de vectores canónicos y ejemplos de clase (ej. $v = [3, 4]^T \implies \|v\| = 5$).
    - Distancia entre puntos/vectores en $\mathbb{R}^2$ y $\mathbb{R}^3$.
    - Producto exterior $x x^T$ con el ejemplo de la Sesión 9 (Slide 15).
- [x] **Tests del TMI e Inversa:**
  - `tests/core/test_invertible_matrix_theorem.py`:
    - Matriz invertible de la Sesión 10 Diapositiva 19:
      $$A = \begin{bmatrix} 1 & 0 & -2 \\ 3 & 1 & -2 \\ -5 & -1 & 9 \end{bmatrix}$$
      Verificar que cumple \*c (3 pivotes), \*e (columnas L.I.), \*h (generan $\mathbb{R}^3$) y $\det(A) \neq 0$.
    - Matriz singular de la Sesión 10 Diapositiva 20:
      $$A = \begin{bmatrix} 2 & 3 & 4 \\ 2 & 3 & 4 \\ 2 & 3 & 4 \end{bmatrix}$$
      Verificar que no cumple ninguna de las caracterizaciones del TMI.
    - Identidades $(AB)^{-1} = B^{-1} A^{-1}$ con matrices invertibles de la sesión.
- [x] **Tests de Propiedades de Determinantes:**
  - `tests/core/test_determinant_properties.py`:
    - Ejemplo exacto de la Sesión 11 Diapositiva 24:
      $$A = \begin{bmatrix} 6 & 1 \\ 3 & 2 \end{bmatrix}, \quad B = \begin{bmatrix} 4 & 3 \\ 1 & 2 \end{bmatrix}$$
      Comprobar que $\det(A) = 9$, $\det(B) = 5$, $\det(AB) = 45 = 9 \cdot 5$.
    - Comprobación de $\det(A^T) = \det(A)$ y $\det(kA) = k^n \det(A)$.
- [x] **Tests de Factorización PLU:**
  - `tests/core/test_plu_decomposition.py`:
    - Matriz con pivote cero inicial que requiere permutación:
      $$A = \begin{bmatrix} 0 & 1 & 2 \\ 1 & 0 & 3 \\ 4 & -3 & 8 \end{bmatrix}$$
      Verificar que `plu_decompose(A)` encuentra $P, L, U$ tales que $PA = LU$ sin fallar con `LUPivotZeroError`.
    - Resolver el sistema $Ax = b$ usando la factorización PLU y verificar que la solución coincide exactamente con la solución de Gauss-Jordan y de la matriz inversa.
- [x] **Tests de Interfaz Gráfica (`tests/ui/`):**
  - Pruebas con `pytest-qt` para la renderización del panel TMI, propiedades de determinantes y visualización de PLU.

---

## 4. Criterios de Aceptación (Definition of Done)

1. **Aritmética Exacta:** Todo cálculo se realiza 100% con `fractions.Fraction` sin dependencias de librerías simbólicas externas o flotantes.
2. **Trazabilidad Pedagógica:** Toda nueva función generará pasos detallados con fórmulas LaTeX a través de `StepTracer`.
3. **Paridad Core-UI:** Cada nueva capacidad del motor tiene controles y representación visual dedicada en la interfaz PySide6.
4. **Cero Regresiones:** El 100% de los 304 tests existentes continúan pasando exitosamente (`pytest`).
5. **Cobertura de Casos de Clase:** Los ejercicios numéricos específicos de las diapositivas (S5 slide 7, S9 slide 15, S10 slides 16-20, S11 slide 24, S12 PLU) están incluidos como casos de prueba automatizados.
6. **Código Limpio y Tipado:** Cobertura estricta de `type hints` y cumplimiento de los principios de diseño de PrettyCalc.

---

## 5. Notas y Decisiones Técnicas del Sprint

1. **Representación de la Norma Euclidiana en Aritmética Racional:**
   Dado que PrettyCalc prohíbe el uso de punto flotante y no utiliza librerías CAS simbólicas (`sympy`), la norma se expondrá en dos niveles complementarios:
   - Valor exacto al cuadrado $\|v\|^2 = \sum v_i^2 \in \mathbb{Q}$ (completamente exacto en fracciones).
   - Formato radical simplificado pedagógico en cadena de texto/LaTeX (por ejemplo $\sqrt{29}$ o $\frac{5}{2}\sqrt{3}$) obtenido mediante factorización prima de enteros en Python puro, preservando la exactitud analítica requerida en la cátedra.
2. **Permutaciones en Factorización PLU:**
   En la descomposición $PA = LU$, la matriz $P$ se inicia como la identidad $I_m$. Al intercambiar las filas $i$ y $k$, no solo se permutan las filas de la matriz de trabajo $U$, sino también las filas de $P$ y las entradas ya calculadas de $L$ por debajo de la diagonal en las columnas anteriores ($1 \dots pivot-1$), garantizando que $PA = LU$ sea matemáticamente idéntica.
3. **Evaluador del TMI como Herramienta Diagnóstica:**
   El evaluador no solo devuelve un booleano `True/False`, sino una lista estructurada de enunciados con su correspondiente justificación matemática, permitiendo al estudiante verificar exactamente qué enunciado falló o se cumplió para la matriz estudiada.

---

## 6. Guía de Commits Atómicos Mínimos

*Nota: Esta lista sirve como guía referencial; durante el desarrollo pueden realizarse commits atómicos adicionales según sea necesario.*

1. `feat(core): agregar calculo de norma euclidiana, distancia y producto exterior`
2. `feat(ui): integrar norma, distancia y producto exterior en VectorsView`
3. `test(core): verificar metricas vectoriales con ejercicios de la sesion 5 y 9`
4. `feat(core): implementar evaluador del Teorema de la Matriz Invertible y propiedades de la inversa`
5. `feat(ui): incorporar panel interactivo del TMI en MatrixOperationsView`
6. `test(core): verificar casos del TMI con ejercicios de la sesion 10`
7. `feat(core): implementar verificador de propiedades multiplicativas y de escala de determinantes`
8. `feat(ui): agregar seccion de comprobacion de propiedades en DeterminantsView`
9. `test(core): validar propiedades de determinantes con ejemplos de la sesion 11`
10. `feat(core): implementar factorizacion PLU con permutacion de filas y solucionador en 2 etapas`
11. `feat(ui): actualizar LUFactorizationView con soporte para matriz de permutacion P`
12. `test(core): verificar PLU con matrices que contienen pivotes nulos`
13. `test(ui): agregar pruebas de integracion para TMI, propiedades y PLU en PySide6`
14. `docs: actualizar documentacion de sprints y README principal`

---

## 7. Retrospectiva / Cierre

El sprint quedó en `feature/sprint-8-consolidacion-propiedades-plu`, partido desde `main` (`350640d`).

* La norma no usa flotantes: \(\|v\|^2\) es un `Fraction` y el radical sale de factorizar enteros.
* `lu_decompose` sigue sin permutar filas. La interfaz usa `plu_decompose`, así que un pivote cero ya no corta el cálculo: muestra \(P\) y resuelve \(Ly = Pb\).
* El evaluador del TMI escribe las caracterizaciones de Lay (a–l) más \(\det(A) \neq 0\), y destaca \*c, \*e y \*h.
* La suite completa pasa: 326 pruebas.
