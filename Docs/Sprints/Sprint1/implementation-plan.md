# Plan de Implementación Paso a Paso - Sprint 1

**Objetivo del Sprint:** Desarrollar el sistema completo de resolución de sistemas de ecuaciones lineales ($Ax = b$) por eliminación por filas (eliminación gaussiana / escalonamiento), clasificación del sistema (SCD, SCI, SI), verificación automática por sustitución exacta y visualización interactiva en PySide6 con el Design System de PrettyCalc.

**Documento Base:** [`Tarea 1 (Elaboracion Programa 1_Python)(1).docx`](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint1/Tarea%201%20(Elaboracion%20Programa%201_Python)(1).docx)  
**Restricción Crítica:** 100% Python estándar para el motor matemático (sin NumPy, SciPy ni álgebra lineal de `math`).

---

## 📐 Fase 1: Motor Matemático Puro (`prettycalc.core`)

### Paso 1.1: Tipos de Datos y Aritmética Exacta (`core/types.py`)
* **Objetivo:** Definir el manejo de escalares con `fractions.Fraction` y la estructura inmutable/mutable de matrices y vectores.
* **Tareas Atómicas:**
  1. Implementar función `parse_scalar(value: str | int | float | Fraction) -> Fraction` (soporta enteros, fracciones `"3/4"` y decimales `"0.75"`).
  2. Implementar clase `Matrix` basada en listas anidadas de `Fraction`.
  3. Implementar métodos de conveniencia: `from_list()`, `to_augmented()`, `copy()`, `dimensions()`, `get_row()`, `get_col()`, `to_latex()`, `to_string()`.

### Paso 1.2: Operaciones Elementales de Fila (`core/operations.py`)
* **Objetivo:** Métodos puros para transformar filas con registro matemático.
* **Tareas Atómicas:**
  1. `swap_rows(matrix, r1, r2)`: Intercambia fila $r_1$ con $r_2$ ($f_{r1} \leftrightarrow f_{r2}$).
  2. `scale_row(matrix, r, scalar)`: Multiplica la fila $r$ por $k$ ($f_r \underset{\sim}\rightarrow k \cdot f_r$).
  3. `add_row_multiple(matrix, target_r, source_r, scalar)`: Suma a la fila destino un múltiplo de la fila origen ($f_{target} \underset{\sim}\rightarrow k \cdot f_{source} + f_{target}$).

### Paso 1.3: Sistema de Trazabilidad de Pasos (`core/tracer.py`)
* **Objetivo:** Capturar cada mutación intermedia del algoritmo para la UI.
* **Tareas Atómicas:**
  1. Definir `CalculationStep(step_number, matrix_snapshot, pivot_pos, latex_formula, heuristic_text)`.
  2. Implementar `StepTracer` con métodos `record_step(...)` y `get_steps() -> list[CalculationStep]`.

### Paso 1.4: Algoritmo de Eliminación y Escalonamiento (`core/elimination.py`)
* **Objetivo:** Escalonar la matriz aumentada $[A \mid b]$ registrando cada paso.
* **Tareas Atómicas:**
  1. Identificación y pivoteo parcial (búsqueda del pivote no nulo e intercambio de filas si $A_{i,i} = 0$).
  2. Eliminación hacia adelante (generación de ceros debajo de cada pivote).
  3. Sustitución hacia atrás (back-substitution) para despeje de variables.

### Paso 1.5: Clasificador de Sistemas y Verificador (`core/classifier.py` & `core/verifier.py`)
* **Objetivo:** Clasificar el sistema según Rouché-Frobenius y verificar la solución.
* **Tareas Atómicas:**
  1. **Clasificación:**
     * **SCD (Consistente Determinado):** Rango igual a número de incógnitas $\rightarrow$ Solución única.
     * **SCI (Consistente Indeterminado):** Rango menor a número de incógnitas $\rightarrow$ Identificar variables libres y solución paramétrica.
     * **SI (Inconsistente):** Fila de la forma $[0 \dots 0 \mid c]$ con $c \neq 0 \rightarrow$ Sin solución.
  2. **Verificación por Sustitución (`SolutionVerifier`):**
     * Sustituir el vector $x$ en cada ecuación original $\sum A_{ij} x_j \stackrel{?}{=} b_i$.
     * Generar lista de resultados booleanos exactos para el checklist visual (**✓**).

---

## 🧪 Fase 2: Pruebas Unitarias Automatizadas (`tests/`)

### Paso 2.1: Pruebas de Operaciones Elementales y Parser (`tests/test_operations.py`)
* Validar parsing de enteros, fracciones negativas y decimales.
* Probar que las tres operaciones elementales no corrompan dimensiones ni valores.

### Paso 2.2: Pruebas de los 3 Casos Canónicos Obligatorios (`tests/test_elimination.py`)
* **Caso 1 (SCD - Solución Única):** Sistema $3 \times 3$ determinado y verificación de los valores de $x$.
* **Caso 2 (SCI - Infinitas Soluciones):** Sistema con variable libre y comprobación de identificación.
* **Caso 3 (SI - Sin Solución):** Sistema inconsistente con detección de la fila contradictoria.

### Paso 2.3: Pruebas del Verificador de Sustitución (`tests/test_verifier.py`)
* Comprobar que el residuo $A x - b = 0$ sea evaluado exactamente como `True` con `Fraction`.

---

## 🎨 Fase 3: Capa de Presentación PySide6 (`prettycalc.ui`)

### Paso 3.1: Configuración de Tema y Tokens QSS (`ui/theme.py`)
* Definir paleta de tokens HEX: `#1A181B` (Fondo), `#564D65` (Superficies), `#E0FBFC` (Texto primario), `#98C1D9` (Bordes/Fórmulas), `#81B29A` (Éxito), `#EE6C4D` (Error/Inconsistencia), `#3A3642` (Deshabilitado).
* Crear hoja de estilos QSS global con tipografía Sans-serif para la app y Monospace para matrices.

### Paso 3.2: Delegado de Matriz Aumentada (`ui/augmented_delegate.py`)
* Implementar `QStyledItemDelegate` sobrecargando `paint()` para dibujar la línea vertical continua en `#98C1D9` antes de la columna $b$.

### Paso 3.3: Cuadrícula Dinámica y Ghosting (`ui/matrix_grid.py`)
* Inicializar en formato $2 \times 2 (+ b)$.
* Implementar filas/columnas fantasma (Ghosting) con opacidad reducida.
* Mostrar icono `+` al pasar el cursor (Hover) sobre las celdas fantasma para expandir la matriz al hacer clic.
* Manejo de teclado fluido (`Tab`, `Shift+Tab`, `Flechas`) y validador en tiempo real (borde rojo `#EE6C4D` ante caracteres no numéricos).

### Paso 3.4: Visor de Pasos en Carrusel / Stepper (`ui/stepper_carousel.py`)
* Componente con botones `[ ◀ Paso Anterior ]` y `[ Siguiente Paso ▶ ]`.
* Resaltado visual de la celda pivote activa y la fila mutada.
* Subtítulo con fórmula LaTeX y texto explicativo en cursiva (*"Se multiplicó la Fila 1 por -3..."*).

### Paso 3.5: Dashboard de Resultados (`ui/results_dashboard.py`)
* Card lateral sobre `#564D65`.
* Badge semántico (🟢 Consistente Determinado, 🟡 Consistente Indeterminado, 🔴 Inconsistente).
* Panel de variables con ícono (🔑) para variables libres.
* Checklist animado de comprobación de ecuaciones originales con checkmarks verdes (**✓** `#81B29A`).

---

## 🚀 Fase 4: Integración, Exportación y Entregables de la Tarea 1

### Paso 4.1: Ventana Principal (`ui/main_window.py`)
* Ensamblar `MatrixGrid`, `StepperCarousel` y `ResultsDashboard`.
* Conectar eventos de cálculo y reset de matriz.

### Paso 4.2: Script Autónomo para Entrega Universitaria (`standalone_task1.py` / `Programa 1_Grupox.py`)
* Generar el archivo autocontenido comentado paso a paso requerido por la rúbrica de la Tarea 1.

### Paso 4.3: Reporte de Casos de Prueba
* Ejecutar y documentar los 3 casos de prueba con capturas para el informe PDF de la tarea.
