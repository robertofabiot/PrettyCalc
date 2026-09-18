# Plan de Implementación Paso a Paso - Sprint 2

**Objetivo del Sprint:** Evolucionar PrettyCalc a una Suite Integral de Álgebra Lineal Multi-Módulo, incorporando:
1. Operaciones vectoriales en $\mathbb{R}^n$ y evaluación formal de combinaciones lineales ($\sum c_i v_i = b$).
2. Operaciones matriciales básicas ($A \pm B$, $k \cdot A$, $A_{m \times n} \cdot B_{n \times p}$) con validación estricta de conformabilidad dimensional y desglose de bucles anidados.
3. Formulación y resolución computacional de ecuaciones matriciales ($A \cdot x = b$).
4. Arquitectura de interfaz gráfica multi-módulo con navegación fluida, prevención proactiva de errores y persistencia de estado.
5. Script autónomo de entrega universitaria `Programa 3_Grupo4.py` y casos de prueba para el informe PDF de la Universidad Americana (FIA - MTM0120).

**Documento Base:** [`Tarea 3 (Elaboracion Programa 3_Python).pdf`](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint2/Tarea%203%20(Elaboracion%20Programa%203_Python).pdf)  
**Rama Git:** `feat/sprint-2`  
**Restricción Crítica:** 100% Python estándar (estrictamente prohibido NumPy, SciPy o álgebra de `math`). Aritmética exacta vía `fractions.Fraction`.

---

## 📐 Fase 1: Motor Matemático Puro (`prettycalc.core`)

### Paso 1.1: Tipo Vector y Operaciones Vectoriales en $\mathbb{R}^n$ (`core/vector_ops.py` & `core/types.py`)
* **Objetivo:** Representar vectores columna en $\mathbb{R}^n$ sobre el cuerpo de los racionales (`Fraction`) y dotarlos de operaciones algebraicas fundamentales.
* **Tareas Atómicas:**
  1. Definir la clase `Vector` en `core/types.py` (o como abstracción orientada a matrices columna $n \times 1$ con acceso unidimensional):
     * Inicializador: `Vector(components: Sequence[Any])`.
     * Propiedades: `dimension: int`, `components: List[Fraction]`.
     * Métodos de conveniencia: `to_list()`, `to_latex()`, `zeros(n)`, `copy()`, `__getitem__`, `__eq__`.
  2. Implementar en `core/vector_ops.py`:
     * `vector_add(u: Vector, v: Vector) -> Vector`: Suma elemento a elemento. Valida $\dim(u) == \dim(v)$, lanzando `DimensionMismatchError` en caso contrario.
     * `vector_sub(u: Vector, v: Vector) -> Vector`: Resta elemento a elemento con validación dimensional.
     * `vector_scale(v: Vector, scalar: Any) -> Vector`: Multiplica cada componente por el escalar exacto `parse_scalar(scalar)`.
     * `vector_dot(u: Vector, v: Vector) -> Fraction`: Producto escalar o producto punto euclídeo $\sum_{i=1}^n u_i \cdot v_i$.
* **Commit Sugerido:** `feat(core): tipos y operaciones fundamentales de vectores en Rn`

### Paso 1.2: Operaciones Matriciales y Algoritmo de Multiplicación (`core/matrix_ops.py`)
* **Objetivo:** Implementar las operaciones algebraicas entre matrices asegurando validación estricta y trazabilidad para justificaciones académicas.
* **Tareas Atómicas:**
  1. Definir excepciones de dominio en `core/types.py` o `core/matrix_ops.py`:
     * `DimensionMismatchError(ValueError)`: Con mensaje explícito indicando las dimensiones incompatibles y la regla algebraica violada.
  2. Implementar operaciones en `core/matrix_ops.py`:
     * `matrix_add(A: Matrix, B: Matrix) -> Matrix`:
       - Condición: $A.\text{shape} == B.\text{shape}$.
       - Retorna nueva `Matrix` con $C_{ij} = A_{ij} + B_{ij}$.
     * `matrix_sub(A: Matrix, B: Matrix) -> Matrix`:
       - Condición: $A.\text{shape} == B.\text{shape}$.
       - Retorna nueva `Matrix` con $C_{ij} = A_{ij} - B_{ij}$.
     * `matrix_scale(A: Matrix, scalar: Any) -> Matrix`:
       - Retorna nueva `Matrix` con $C_{ij} = k \cdot A_{ij}$.
     * `matrix_multiply(A: Matrix, B: Matrix) -> Matrix`:
       - Condición estricta de conformabilidad: $A.\text{cols} == B.\text{rows}$.
       - Algoritmo en Python estándar mediante 3 bucles anidados:
         ```python
         # Bucles anidados de multiplicacion matricial pura
         C = Matrix.zeros(m, p)
         for i in range(m):
             for j in range(p):
                 accum = Fraction(0, 1)
                 for k in range(n):
                     accum += A.get(i, k) * B.get(k, j)
                 C.set(i, j, accum)
         ```
     * `matrix_multiply_with_details(A: Matrix, B: Matrix) -> Tuple[Matrix, List[MultiplicationStepDetail]]`:
       - Registra para cada elemento $C_{ij}$ la lista de productos parciales $(A_{ik} \cdot B_{kj})$ y la suma total para su visualización paso a paso en el inspector y el informe técnico.
* **Commit Sugerido:** `feat(core): suma, resta, escala y multiplicacion matricial con bucles anidados`

### Paso 1.3: Evaluador de Combinación Lineal (`core/linear_combination.py`)
* **Objetivo:** Determinar si un vector objetivo $b \in \mathbb{R}^n$ se puede expresar como $\sum_{i=1}^k c_i v_i = b$.
* **Tareas Atómicas:**
  1. Implementar `evaluate_linear_combination(vectors: Sequence[Vector], target: Vector) -> LinearCombinationResult`:
     * Validación: Todos los vectores $v_i$ y el objetivo $target$ deben tener la misma dimensión $n$.
     * Construcción de la matriz aumentada:
       $$M = [v_1 \mid v_2 \mid \dots \mid v_k \mid target]$$
       Donde cada vector $v_j$ conforma la columna $j$ de la matriz de coeficientes ($n \times k$) y $target$ conforma la columna aumentada ($k+1$).
     * Ejecución de eliminación Gauss-Jordan reutilizando `gauss_jordan_elimination(M, split_col=k)`.
     * Clasificación del sistema reutilizando `classify_system(M, split_col=k)`.
  2. Generación del objeto estructurado `LinearCombinationResult`:
     * `is_combination: bool` (`True` para SCD y SCI, `False` para SI).
     * `system_type: SystemType` (SCD, SCI, SI).
     * `weights: Optional[List[Fraction]]`: Valores de los escalares $c_1, \dots, c_k$ (para SCD).
     * `parametric_solution: Optional[str]`: Expresión paramétrica en términos de variables libres (para SCI).
     * `contradiction_info: Optional[str]`: Descripción de la fila contradictoria $[0 \dots 0 \mid c \neq 0]$ (para SI).
     * `verification_checklist: List[Tuple[str, Fraction, Fraction, bool]]`: Comprobación componente a componente de que $\sum c_i v_i = target$.
* **Commit Sugerido:** `feat(core): evaluador y verificador de combinacion lineal en Rn`

### Paso 1.4: Ecuaciones Matriciales $A \cdot x = b$ (`core/matrix_equations.py`)
* **Objetivo:** Abstracción computacional formal de la ecuación matricial $A_{m \times n} \mathbf{x} = \mathbf{b}$.
* **Tareas Atómicas:**
  1. Definir `solve_matrix_equation(A: Matrix, b: Vector) -> MatrixEquationResult`:
     * Valida conformabilidad: $A.\text{rows} == b.\text{dimension}$.
     * Aumenta la matriz $[A \mid b]$.
     * Resuelve mediante Gauss-Jordan, clasifica y verifica la igualdad multiplicando $A \cdot \mathbf{x} \stackrel{?}{=} \mathbf{b}$ con la solución obtenida.
* **Commit Sugerido:** `feat(core): modulo de resolucion y comprobacion de ecuaciones matriciales`

---

## 🧪 Fase 2: Pruebas Unitarias Automatizadas (`tests/`)

### Paso 2.1: Pruebas de Operaciones Vectoriales (`tests/core/test_vector_ops.py`)
* Probar suma y resta de vectores en $\mathbb{R}^2, \mathbb{R}^3, \mathbb{R}^5$.
* Probar multiplicación escalar por enteros, fracciones y cero.
* Probar producto punto euclídeo.
* Validar que dimensiones dispares lancen `DimensionMismatchError`.

### Paso 2.2: Pruebas de Operaciones Matriciales (`tests/core/test_matrix_ops.py`)
* Suma y resta de matrices compatibles ($2 \times 2, 3 \times 3, 2 \times 4$).
* Validar excepción ante suma de matrices de dimensiones incompatibles (ej. $2 \times 3$ con $3 \times 2$).
* Multiplicación escalar $k \cdot A$.
* Multiplicación matricial $A_{m \times n} \cdot B_{n \times p}$ con cálculo exacto fraccionario:
  - $(2 \times 3) \cdot (3 \times 2) \rightarrow (2 \times 2)$.
  - $(3 \times 1) \cdot (1 \times 3) \rightarrow (3 \times 3)$ y $(1 \times 3) \cdot (3 \times 1) \rightarrow (1 \times 1)$.
* Verificación de la no-conmutatividad del producto matricial ($A \cdot B \neq B \cdot A$).
* Validación de error dimensional cuando $A.\text{cols} \neq B.\text{rows}$.

### Paso 2.3: Pruebas del Evaluador de Combinación Lineal (`tests/core/test_linear_combination.py`)
* **Caso 1 (C.L. Única - SCD):** Vectores linealmente independientes con solución única de coeficientes (ej. base estándar o canónica de $\mathbb{R}^3$).
* **Caso 2 (C.L. con Infinitas Soluciones - SCI):** Vectores dependientes donde el objetivo pertenece al subespacio generado.
* **Caso 3 (No es Combinación Lineal - SI):** Vector objetivo fuera del subespacio (ej. vector con componente no nula en z respecto a vectores en el plano xy).
* **Caso 4 (Error Dimensional):** Conjunto de vectores con longitudes inconsistentes.

### Paso 2.4: Pruebas de Ecuaciones Matriciales (`tests/core/test_matrix_equations.py`)
* Resolver $A \mathbf{x} = \mathbf{b}$ con verificación directa $A \cdot \mathbf{x} == \mathbf{b}$.
* Validar comportamiento ante matrices rectangulares ($m > n$ y $m < n$).
* **Commit Sugerido:** `test(core): suite completa de pruebas unitarias para el sprint 2`

---

## 🎨 Fase 3: Arquitectura UI/UX Multi-Módulo (`prettycalc.ui`)

### Paso 3.1: Barra de Navegación Segmentada (`ui/navigation_bar.py`)
* **Objetivo:** Proveer una experiencia de usuario de clase mundial para transicionar entre módulos sin fricción ni pérdida de espacio horizontal.
* **Decisión UI/UX:** Se implementa una **Top Segmented Tab Bar** con botones interactivos dotados de indicadores de estado activo:
  - 🧮 `Sistemas Lineales` (Eliminación por filas / Sprint 1)
  - ⊞ `Álgebra Matricial` ($A \pm B$, $k \cdot A$, $A \cdot B$ / Sprint 2)
  - ↗ `Vectores en ℝⁿ` (Operaciones y Combinación Lineal / Sprint 2)
  - 🔣 `Ecuaciones Matriciales` ($A \cdot x = b$ / Sprint 2)
* **Tokens Visuales Aplicados:**
  - Pestaña Activa: Fondo `#564D65`, texto `#E0FBFC`, borde inferior activo `#98C1D9` (2px).
  - Pestaña Inactiva: Fondo transparente, texto `#98C1D9` atenuado, hover sutil con background `#3A3642`.
* **Manejo en Main Window:** Conectado a un `QStackedWidget` donde cada pestaña conmuta la vista activa al instante sin re-instanciar componentes (preservando el estado de entrada del usuario).
* **Commit Sugerido:** `feat(ui): componente navigation_bar segmentado y shell modular`

### Paso 3.2: Reorganización Modular de Vistas (`ui/modules/`)
* **Objetivo:** Desacoplar el código de `MainWindow` creando módulos independientes y limpios dentro de `prettycalc/ui/modules/`.
* **Estructura de Vistas:**
  ```text
  prettycalc/ui/modules/
  ├── __init__.py
  ├── linear_systems_view.py       # Vista existente de Sprint 1 (encapsulada como QWidget)
  ├── matrix_operations_view.py    # Vista de Álgebra Matricial
  ├── vectors_view.py              # Vista de Vectores en ℝⁿ y Combinación Lineal
  └── matrix_equations_view.py     # Vista de Ecuaciones Matriciales Ax = b
  ```
* **Commit Sugerido:** `refactor(ui): modularizar vista de sistemas lineales en modulo desacoplado`

### Paso 3.3: Vista de Álgebra Matricial (`ui/modules/matrix_operations_view.py`)
* **Layout y Componentes:**
  1. **Disposición Horizontal Ergonómica:**
     `[ Matriz A ]  ──  [ Selector Operación (+, -, ×) ]  ──  [ Matriz B ]  ──  [ = ]  ──  [ Matriz Resultado C ]`
  2. **Controles de Matriz Dinámica:**
     - Ambas matrices $A$ y $B$ utilizan `DynamicMatrixGrid` con Ghosting (`+` en hover) y navegación fluida por teclado.
  3. **Banner / Badge de Validación Dimensional en Tiempo Real (Heurística Nielsen #5):**
     - Al cambiar dimensiones en $A$ o $B$, se actualiza automáticamente el badge de estado:
       - Si es multiplicación y $A.\text{cols} == B.\text{rows}$:
         Badge en verde (`#81B29A`): *"✓ Dimensiones compatibles para producto: (m×n) · (n×p) = (m×p)"*.
       - Si no coinciden:
         Badge en Burnt Peach (`#EE6C4D`): *"✕ Dimensiones incompatibles: Columnas de A ({nA}) ≠ Filas de B ({mB})"*.
       - El botón de cálculo se deshabilita preventivamente si hay incompatibilidad, evitando errores frustrantes.
  4. **Modo Escalar ($k \cdot A$):**
     - Toggle o pestaña secundaria para multiplicar una matriz individual por un escalar fraccionario o decimal.
  5. **Inspector Interactivo de Multiplicación (Bucles Anidados):**
     - Al hacer clic en una celda $(i, j)$ de la matriz resultado $C$, se iluminan la Fila $i$ en $A$ y la Columna $j$ en $B$.
     - Un card inferior muestra la descomposición de la sumatoria:
       $$C_{i,j} = \sum_{k=1}^n A_{i,k} \cdot B_{k,j} = (A_{i,1} \cdot B_{1,j}) + \dots = \text{resultado}$$
* **Commit Sugerido:** `feat(ui): vista de algebra matricial con validacion dimensional e inspector de producto`

### Paso 3.4: Vista de Vectores y Combinación Lineal (`ui/modules/vectors_view.py`)
* **Layout y Componentes:**
  1. **Subsección A: Operaciones Básicas:**
     - Dos vectores $u, v \in \mathbb{R}^n$, selector de dimensión $n$, selector de operación ($+, -, \cdot \text{escalar}$).
     - Visualización del vector resultante con formato de corchetes de libro (`book_matrix`).
  2. **Subsección B: Evaluador de Combinación Lineal ($\sum c_i v_i = b$):**
     - Selector de dimensión $n$ del espacio vectorial $\mathbb{R}^n$ (ej. $n=3$).
     - Lista dinámica de vectores columna $\{v_1, v_2, \dots, v_k\}$ con botones `[ + Añadir Vector ]` y botón de eliminar en cada vector.
     - Tarjeta destacada en `color-interactive-idle` para el vector objetivo $b$.
     - Botón de acción principal: `[ Evaluar Combinación Lineal ]`.
     - **Dashboard de Resultados Especializado:**
       - Badge Semántico grande:
         - 🟢 **SÍ ES COMBINACIÓN LINEAL ÚNICA** (SCD).
         - 🟡 **SÍ ES COMBINACIÓN LINEAL (INFINITAS COMBINACIONES)** (SCI).
         - 🔴 **NO ES COMBINACIÓN LINEAL** (SI).
       - Despliegue de los escalares calculados:
         $$b = c_1 v_1 + c_2 v_2 + \dots + c_k v_k$$
       - Checklist de Comprobación componente a componente con checkmarks verdes (**✓** `#81B29A`).
       - Botón opcional para ver el procedimiento de escalonamiento de la matriz aumentada $[v_1 \dots v_k \mid b]$.
* **Commit Sugerido:** `feat(ui): vista de vectores y evaluador visual de combinacion lineal en Rn`

### Paso 3.5: Vista de Ecuaciones Matriciales (`ui/modules/matrix_equations_view.py`)
* **Layout y Componentes:**
  - Renderizado explícito de la ecuación matricial:
    $$A_{m \times n} \cdot \mathbf{x}_{n \times 1} = \mathbf{b}_{m \times 1}$$
  - Entrada de matriz $A$ y vector $b$.
  - Botón `[ Resolver Ecuación Matricial ]`.
  - Presentación del vector solución $\mathbf{x}$ con su clasificación y comprobación exacta por multiplicación matricial $A \cdot \mathbf{x} = \mathbf{b}$.
* **Commit Sugerido:** `feat(ui): vista de ecuaciones matriciales con visualizacion formal Ax=b`

### Paso 3.6: Integración en Ventana Principal (`ui/main_window.py`)
* Ensamblar la `NavigationBar` en la parte superior y el `QStackedWidget` con las 4 vistas.
* Configuración de accesos directos de teclado para alternar entre módulos (`Ctrl+1`, `Ctrl+2`, `Ctrl+3`, `Ctrl+4`).
* Preservación del estilo global y ajuste responsivo de tamaños.
* **Commit Sugerido:** `feat(ui): integracion final del shell multi-modulo en main_window`

---

## 🚀 Fase 4: Entregables Académicos Universitarios (Tarea 3 - MTM0120)

### Paso 4.1: Script Autónomo `Programa 3_Grupo4.py`
* **Objetivo:** Archivo autocontenido, comentado paso a paso, 100% Python estándar para la entrega oficial en la plataforma Moodle.
* **Características Requeridas:**
  - Cero dependencias externas (`fractions`, `typing`, `sys`).
  - Menú interactivo CLI con 4 opciones principales:
    1. Operaciones con Vectores en $\mathbb{R}^n$ (Suma, resta, multiplicación por escalar).
    2. Evaluación de Combinación Lineal ($\sum c_i v_i = b$).
    3. Operaciones Matriciales ($A \pm B$, $k \cdot A$, $A \cdot B$ con desglose de bucles anidados).
    4. Resolución de Ecuaciones Matriciales ($A \mathbf{x} = \mathbf{b}$).
  - Comentarios exhaustivos explicando el fundamento algebraico equivalente y la lógica algorítmica de los bucles anidados.
* **Commit Sugerido:** `feat(academic): script autonomo interactivo Programa 3_Grupo4.py`

### Paso 4.2: Casos de Prueba Académicos y Material para el Informe PDF
* **Objetivo:** Generar y documentar los casos de prueba exigidos por la rúbrica oficial para el informe:
  1. Multiplicación matricial exitosa con pasos intermedios.
  2. Validación y detección de error ante dimensiones incompatibles.
  3. Cálculo de combinación lineal afirmativa (con pesos exactos) y negativa (inconsistente).
  4. Resolución de ecuación matricial $Ax = b$.
* **Commit Sugerido:** `docs(sprint-2): documentar casos de prueba y reporte para informe pdf`

---

## 📋 Resumen de la Secuencia de Commits Atómicos (Git Flow)

1. `git checkout -b feat/sprint-2`
2. `feat(core): tipos y operaciones fundamentales de vectores en Rn`
3. `feat(core): suma, resta, escala y multiplicacion matricial con bucles anidados`
4. `feat(core): evaluador y verificador de combinacion lineal en Rn`
5. `feat(core): modulo de resolucion y comprobacion de ecuaciones matriciales`
6. `test(core): suite completa de pruebas unitarias para el sprint 2`
7. `feat(ui): componente navigation_bar segmentado y shell modular`
8. `refactor(ui): modularizar vista de sistemas lineales en modulo desacoplado`
9. `feat(ui): vista de algebra matricial con validacion dimensional e inspector de producto`
10. `feat(ui): vista de vectores y evaluador visual de combinacion lineal en Rn`
11. `feat(ui): vista de ecuaciones matriciales con visualizacion formal Ax=b`
12. `feat(ui): integracion final del shell multi-modulo en main_window`
13. `feat(academic): script autonomo interactivo Programa 3_Grupo4.py`
14. `docs(sprint-2): documentar casos de prueba y reporte para informe pdf`
15. `test(ui): pruebas de integracion de navegacion y vistas multi-modulo`
