# Arquitectura del Sistema - PrettyCalc

## 1. Visión General de la Arquitectura
PrettyCalc sigue una arquitectura por capas desacopladas (**Layered Architecture / Clean Architecture**) que garantiza la total independencia del motor matemático respecto a la interfaz gráfica de escritorio.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      Capa de Presentación / GUI                        │
│                           (PySide6 / Qt 6)                             │
│  ┌───────────────────────────────────┐  ┌───────────────────────────┐  │
│  │         DynamicMatrixGrid         │  │  AugmentedMatrixDelegate  │  │
│  │   (Default 2x2 + Ghosting [+]     │  │ (Solid Vertical Line [A|b]│  │
│  │    & Keyboard Tab/Arrows Nav)     │  │  via QStyledItemDelegate) │  │
│  └───────────────────────────────────┘  └───────────────────────────┘  │
│  ┌───────────────────────────────────┐  ┌───────────────────────────┐  │
│  │     AlgorithmStepperCarousel      │  │   ResultsDashboardCard    │  │
│  │  (Pivots, Prev/Next & Heuristics) │  │(Badges, Free Vars & ✓)    │  │
│  └───────────────────────────────────┘  └───────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Dispara acciones / Consume estados
┌───────────────────────────────────▼────────────────────────────────────┐
│                 Capa de Aplicación y Controladores                     │
│  - SessionState: Historial de matrices y navegación de pasos           │
│  - SolutionVerifier: Comprobación de sustitución ($Ax = b$)            │
│  - MathFormatters: Monospace Matrix Formatter, LaTeX & Heuristic text  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Invoca algoritmos puros
┌───────────────────────────────────▼────────────────────────────────────┐
│                Motor Matemático Puro (Core Engine)                     │
│        (100% Python Estándar - Cero dependencias externas)             │
│  - Tipos: Matrix, Vector, Scalar (Fraction / Float)                    │
│  - Algoritmos: Gauss, Gauss-Jordan, Inversa, Determinantes, Cramer, LU │
│  - Aplicaciones: Leontief, balanceo químico, dieta y redes de flujo   │
│  - StepTracer: Registro de pasos (matriz, pivote, operación elemental) │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Componentes Principales

### 2.1. Motor Matemático Puro (`prettycalc.core`)
* **Regla de Oro:** **Cero librerías externas de álgebra lineal** (sin `numpy`, `scipy`, `sympy`).
* **Estructuras Fundamentales:**
  * `Scalar`: Aritmética exacta basada en `fractions.Fraction` estándar.
  * `Matrix`: Estructura bidimensional inmutable para cálculos o manipulada mediante operaciones elementales de fila registradas.
* **Inversión matricial (`matrix_inversion.py`):**
  * `matrix_inverse` reduce $[A \mid I_n]$ con Gauss-Jordan en aritmética exacta y devuelve $A^{-1}$ junto con el `StepTracer`.
  * `solve_via_inverse` resuelve $Ax = b$ mediante $x = A^{-1} b$.
  * `NonSquareMatrixError` y `SingularMatrixError` separan una matriz rectangular de una matriz cuadrada de rango deficiente. El trazador de una matriz singular queda adjunto a la excepción para que la interfaz pueda mostrar dónde apareció la fila de ceros.
* **Forma vectorial paramétrica (`classifier.py`):**
  * En un SCI, `ParametricVectorSolution` descompone la solución en el vector particular $p$ (variables libres en 0) y los vectores de una base del núcleo, uno por cada variable libre: $x = p + \sum t_k v_k$.
* **Sistema de Trazabilidad (`StepTracer`):**
  * Cada algoritmo produce una lista ordenada de `CalculationStep`, conteniendo:
    * Matriz resultante en ese instante.
    * Coordenadas $(fila, col)$ del **Pivote Activo**.
    * Fórmula formal de transformación (LaTeX).
    * Texto heurístico explicativo (*"Se multiplicó la Fila $i$ por $k$ y se sumó a la Fila $j$"*).

### 2.2. Capa de Aplicación y Verificación (`prettycalc.app`)
* **`SolutionVerifier`:** Toma la solución calculada y las ecuaciones originales, realizando la sustitución simbólico-aritmética exacta para generar los datos del checklist de validación (✓).
* **`Formatters`:** Asegura que los números se formateen para fuentes Monospace con alineación vertical simétrica.

### 2.3. Capa de Presentación / GUI (`prettycalc.ui`)
* **`Theme & Design Tokens` (`prettycalc.ui.theme`):** Centralización de tokens cromáticos (`color-bg-base`, `color-surface-elevated`, `color-text-primary`, `color-interactive-idle`, etc.) aplicados mediante hojas de estilo QSS.
* **`DynamicMatrixGrid`:** Cuadrícula interactiva con inicio inmediato en $2 \times 2 (+ b)$, soporte de celdas fantasma (Ghosting) con botón `+` en hover, y navegación completa por teclado (`Tab`, `Shift+Tab`, `Flechas`).
* **`AugmentedMatrixDelegate`:** Delegado personalizado de Qt (`QStyledItemDelegate`) que intercepta `paint()` para renderizar una línea vertical continua en `color-interactive-idle` (`#98C1D9`), delimitando físicamente la columna de términos independientes $[A \mid b]$.
* **`AlgorithmStepperCarousel`:** Visor de navegación paso a paso con botones `[ ◀ Anterior ]` (deshabilitable con `color-interactive-disabled`) y `[ Siguiente ▶ ]`, resaltando la celda del pivote activo.
* **`ResultsDashboardCard`:** Panel montado sobre `color-surface-elevated` con badges semánticos, distinción de variables libres (🔑), checklist de comprobación en `color-feedback-success` (✓) y, en sistemas indeterminados, la forma vectorial paramétrica en vectores columna.
* **Modo $A^{-1}$ en `MatrixOperationsView`:** Quinto modo del álgebra matricial. Muestra $A^{-1}$, el checklist $A \cdot A^{-1} = I_n$ y el carrusel de $[A \mid I_n]$. Deshabilita el cálculo si $A$ no es cuadrada y pinta un badge de error si $A$ es singular.
* **Determinantes (`determinants.py`, `adjugate.py`, `cramer.py`):**
  * `matrix_determinant` evalúa det(A) por fórmula 2×2, Sarrus, triangulación o Laplace, con `StepTracer`.
  * `calculate_adjugate_and_inverse` construye menores, cofactores, adjunta y, si det(A) ≠ 0, \(A^{-1} = \frac{1}{\det A}\operatorname{adj}(A)\).
  * `solve_cramer` resuelve sistemas n×n por cociente de determinantes. Si det(A) = 0 lanza `SingularMatrixError`.
* **Pestaña Determinantes y Cramer en la UI:** `DeterminantsView` es el quinto módulo de la barra (atajo Ctrl+5). El orden n va de 1 a 8. En sistemas lineales, el selector Gauss-Jordan / Regla de Cramer muestra det(A), cada \(A_i(b)\) y las fracciones \(x_i\).
* **Factorización LU (`lu_decomposition.py`):** `lu_decompose` construye \(A = LU\) sin permutar filas. `plu_decompose` construye \(PA = LU\): si el pivote es cero y debajo hay una entrada no nula, intercambia filas en \(U\), en \(P\) y en los multiplicadores ya guardados de \(L\). `solve_via_plu` resuelve \(Ly = Pb\) y después \(Ux = y\). `lu_decompose` sigue lanzando `LUPivotZeroError` en ese caso. Un cero en la diagonal de \(U\) lanza `LUSingularError`.
* **Pestaña Factorización LU:** `LUFactorizationView` es el sexto módulo (atajo Ctrl+6). Muestra \(P\), \(L\) y \(U\). Si \(P = I\), indica que no hubo permutación y comprueba \(L \cdot U = A\). Si hubo intercambio, muestra \(P\) y, al resolver, el vector \(Pb\). Acepta el ejemplo rectangular \(4 \times 5\); el solucionador único queda habilitado solo si \(A\) es cuadrada y \(U\) no tiene pivotes diagonales nulos.
* **Norma, distancia y producto exterior:** `vector_norm_squared` y `vector_norm_exact` calculan \(\|v\|^2\) en fracciones y el radical simplificado. `vector_distance_squared` es la norma de \(u - v\). `vector_outer_product` arma \(u v^T\). En Vectores, la pestaña **Norma y producto exterior** muestra el resultado y el carrusel.
* **Teorema de la Matriz Invertible:** `evaluate_invertible_matrix_theorem` revisa las caracterizaciones de una matriz cuadrada, con énfasis en \*c (n pivotes), \*e (columnas independientes) y \*h (generan \(\mathbb{R}^n\)), además de \(\det(A) \neq 0\). `verify_inverse_algebraic_identities` contrasta \((A^{-1})^{-1} = A\), \((AB)^{-1} = B^{-1}A^{-1}\) y \((A^T)^{-1} = (A^{-1})^T\). En Álgebra Matricial están los modos **TMI** e **Identidades A⁻¹**.
* **Propiedades del determinante:** `verify_determinant_properties` contrasta \(\det(AB) = \det(A)\det(B)\), \(\det(A^T) = \det(A)\), \(\det(A^{-1}) = 1/\det(A)\) y \(\det(kA) = k^n \det(A)\). En Determinantes, el modo **Propiedades** muestra el checklist.
* **Aplicaciones de la sesión 8 (`applied_models.py`):** `balance_chemical_reaction` arma la conservación de átomos y los enteros mínimos. `solve_leontief_exchange` resuelve \((I - C)p = 0\). `solve_nutrition_mix` resuelve la mezcla y rechaza cantidades negativas. `analyze_network_flow` escribe la solución general y, con una variable libre, las cotas \(x_i \ge 0\). En Sistemas Lineales, **V · Aplicaciones** muestra esos formularios y carga la matriz aumentada en la cuadrícula. El compendio de teoremas está en `theorems.py`; la consola de `Calculadora_Algebra_Lineal` solo lo imprime.

## 3. Principios de Diseño Arquitectónico
1. **Desacoplamiento Absoluto:** El motor matemático es 100% independiente de Qt/PySide6, testeable vía CLI y pytest.
2. **Determinismo y Precisión:** Aritmética de fracciones exactas en todo el pipeline de cómputo y comprobación.
3. **Visibilidad Inmediata y Cero Fricción:** Cuadrícula $2 \times 2 (+ b)$ visible desde el milisegundo cero, sin pantallas intermedias invasivas.

## 4. Tecnologías y Stack Técnico
* **Lenguaje:** Python 3.10+
* **Biblioteca Estándar:** `fractions`, `dataclasses`, `typing`, `math`.
* **Framework GUI:** `PySide6` (Qt 6 for Python).
* **Testing:** `pytest`, `pytest-qt`.

## 5. Flujo de Datos y Ejecución
> [!NOTE]
> *Este flujo de datos es conceptual y se refina conforme evolucione el desarrollo.*

1. La aplicación abre instantáneamente con `DynamicMatrixGrid` en formato $2 \times 2$ aumentada con su columna $b$.
2. Conforme el usuario ingresa datos, la cuadrícula sugiere filas/columnas fantasma que crecen con un clic en el `+` o al avanzar con el teclado.
3. El validador en tiempo real bloquea caracteres no numéricos coloreando el borde de la celda en `color-feedback-error`.
4. Al solicitar el cálculo, el motor matemático ejecuta la resolución registrando los pasos en el `StepTracer`.
5. El `SolutionVerifier` calcula la comprobación por sustitución exacta.
6. La interfaz actualiza el `AlgorithmStepperCarousel` con los pasos y despliega el `ResultsDashboardCard` con la clasificación y el checklist de validación (✓).
