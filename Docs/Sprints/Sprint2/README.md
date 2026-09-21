# Sprint 2: Operaciones Algebraicas en ℝⁿ, Combinación Lineal y Ecuaciones Matriciales

**Carpeta:** [`Docs/Sprints/Sprint2/`](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint2/)  
**Rama Git Asociada:** `feat/sprint-2`  
**Estado:** Planificado / Listo para Implementación  
**Entregable Académico Asociado:** *Programa 3 - Álgebra Lineal (MTM0120) - FIA Universidad Americana (Primer Corte Evaluativo)*

---

## 1. Documentos del Sprint

* [**`implementation-plan.md`**](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint2/implementation-plan.md): **Plan de implementación atómico y paso a paso** para el motor matemático (`core`), la arquitectura multi-módulo (`ui`) y los entregables académicos.
* [**`Tarea 3 (Elaboracion Programa 3_Python).pdf`**](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint2/Tarea%203%20(Elaboracion%20Programa%203_Python).pdf): Guía oficial y rúbrica académica de la cátedra de Álgebra Lineal.

---

## 2. Visión y Alcance del Sprint 2

El **Sprint 1** dotó a PrettyCalc de una base sólida: aritmética exacta con `fractions.Fraction`, manipulación bidimensional de matrices (`Matrix`), eliminación por filas (Gauss-Jordan), clasificación rigurosa (SCD, SCI, SI), verificación por sustitución y una interfaz visual de alta gama con el Design System oscuro de PrettyCalc.

El **Sprint 2** evoluciona PrettyCalc de una herramienta mono-propósito de escalonamiento a una **Suite Integral de Álgebra Lineal Multi-Módulo**, cubriendo tres áreas fundamentales del Contrato Didáctico:
1. **Álgebra Vectorial en $\mathbb{R}^n$ y Combinación Lineal.**
2. **Álgebra Matricial Básica ($A \pm B$, $k \cdot A$, $A \cdot B$).**
3. **Ecuaciones Matriciales ($A \cdot x = b$).**

---

## 3. Requerimientos Funcionales del Sprint

### 3.1. Módulo de Vectores ($\mathbb{R}^n$)
1. **Operaciones Básicas:**
   * Suma y resta de vectores en $\mathbb{R}^n$ validando compatibilidad de dimensión ($n$).
   * Multiplicación de un vector por un escalar exacto ($k \in \mathbb{Q}$).
2. **Evaluación de Combinación Lineal:**
   * Evaluar si un vector objetivo $b \in \mathbb{R}^n$ es combinación lineal de un conjunto de vectores dados $\{v_1, v_2, \dots, v_k\}$:
     $$c_1 v_1 + c_2 v_2 + \dots + c_k v_k = b$$
   * Reducción al sistema de ecuaciones lineales $A c = b$, donde las columnas de $A$ son los vectores $v_j$.
   * Reutilización directa y elegante del motor de escalonamiento y clasificación del Sprint 1.
   * Diagnóstico categórico:
     * **SCD:** El vector **SÍ** es combinación lineal única (presentando los coeficientes/pesos $c_1, \dots, c_k$).
     * **SCI:** El vector **SÍ** es combinación lineal con infinitas soluciones de pesos (solución general paramétrica).
     * **SI:** El vector **NO** es combinación lineal (indicando la contradicción algebraica).
   * Verificación automática por sustitución exacta ($\sum c_i v_i \stackrel{?}{=} b$) con checklist visual (**✓**).

### 3.2. Módulo de Operaciones Matriciales Básicas
1. **Suma y Resta de Matrices ($A_{m \times n} \pm B_{m \times n}$):**
   * Validación estricta en tiempo real de dimensiones idénticas ($m_A = m_B$ y $n_A = n_B$).
   * Excepción pedagógica de dominio `DimensionMismatchError` si son incompatibles (sin caídas de la app).
2. **Multiplicación de Matriz por Escalar ($k \cdot A_{m \times n}$):**
   * Producto distributivo de cada celda $A_{ij}$ por el escalar exacto $k$.
3. **Multiplicación de Matrices ($A_{m \times n} \cdot B_{n \times p}$):**
   * Validación estricta de conformabilidad: columnas de $A$ deben ser iguales a las filas de $B$ ($n_A = m_B$).
   * Implementación de tres bucles anidados en Python puro con cálculo exacto por producto punto:
     $$C_{i,j} = \sum_{k=1}^n A_{i,k} \cdot B_{k,j}$$
   * Trazador/inspector interactivo de pasos para documentar la deducción de cada celda $C_{ij}$ (crucial para el informe universitario).

### 3.3. Módulo de Ecuaciones Matriciales ($A \cdot x = b$)
1. **Representación Matricial Explícita:**
   * Despliegue visual de la igualdad $A_{m \times n} \cdot \mathbf{x}_{n \times 1} = \mathbf{b}_{m \times 1}$.
   * Entrada de la matriz $A$ y el vector de términos independientes $b$.
   * Conexión con el resolvedor para despejar el vector de incógnitas $\mathbf{x}$.
   * Checklist de verificación del producto $A \cdot \mathbf{x} = \mathbf{b}$.

---

## 4. Solución UI/UX para Manejo de Múltiples Módulos

Como evolución a una suite multi-módulo, PrettyCalc adopta una arquitectura de interfaz centrada en la **Carga Progresiva**, **Prevención Proactiva de Errores (Nielsen)** y **Conservación de Espacio Horizontal**:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  PrettyCalc   [ 🧮 Sistemas Lineales ] [ ⊞ Álgebra Matricial ] [ ↗ Vectores ℝⁿ ] [ 🔣 Ecuaciones ] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ QStackedWidget ] -> Renderiza la vista del módulo activo preservando su estado      │
│                                                                                        │
│  - Álgebra Matricial:                                                                  │
│    [ Matriz A ]    [ + | - | × ]    [ Matriz B ]    =    [ Matriz Resultado C ]        │
│    Badge: "✓ Compatible para producto (2x3 · 3x2 = 2x2)"                               │
│    Badge error: "✕ Incompatible: Columnas de A (3) ≠ Filas de B (2)"                   │
│                                                                                        │
│  - Vectores ℝⁿ & Combinación:                                                          │
│    Dimensión: [ n = 3 ]                                                                │
│    Conjunto {v₁, v₂, ...} + Botón [+ Añadir]   |   Vector b   |   [ Evaluar ]          │
│    Resultados: Badge (🟢 / 🟡 / 🔴) + Pesos cᵢ + Verificación celda a celda (✓)        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Principios UI/UX Clave
1. **Top Segmented Navigation Bar:**
   * Navegación por pestañas segmentadas en el encabezado principal, integradas con los tokens cromáticos del Design System (`#564D65`, `#E0FBFC`, `#98C1D9`).
   * No penaliza el ancho de pantalla (a diferencia de un sidebar invasivo), permitiendo que operaciones como $A \cdot B = C$ tengan suficiente holgura horizontal.
2. **Prevención de Errores en Tiempo Real (Pre-flight Feedback):**
   * Badges dinámicos de compatibilidad dimensional calculados al vuelo mientras el usuario redimensiona o edita matrices.
   * Si las dimensiones no coinciden con la operación seleccionada, el botón de cálculo se bloquea preventivamente y se muestra un banner explicativo con el fundamento algebraico en `Burnt Peach` (`#EE6C4D`).
3. **Inspector Interactivo de Producto Matricial:**
   * Al hacer clic sobre cualquier celda $C_{ij}$ del resultado, se iluminan la fila $i$ de $A$ y la columna $j$ de $B$, mostrando la fórmula de producto punto desgMenuItemosada.
4. **Persistencia de Sesión por Módulo:**
   * El usuario puede cambiar de módulo sin perder los datos ingresados en los otros, gracias a `QStackedWidget` desacoplado.

---

## 5. Entregables y Criterios de Aceptación (DoD)

- [ ] **Motor Matemático (`prettycalc.core`):**
  - [ ] Implementar `core/vector_ops.py` (operaciones vectoriales y combinación lineal).
  - [ ] Implementar `core/matrix_ops.py` (suma, resta, multiplicación escalar y multiplicación $A \cdot B$).
  - [ ] Cero dependencias externas (100% Python estándar: `fractions`, `typing`, `math`).
- [ ] **Capa de Presentación (`prettycalc.ui`):**
  - [ ] Barra de navegación segmentada (`ui/navigation_bar.py`) y shell modular con `QStackedWidget`.
  - [ ] Extracción limpia del módulo 1 a `ui/modules/linear_systems_view.py`.
  - [ ] Implementación de `ui/modules/matrix_operations_view.py` con pre-flight validation.
  - [ ] Implementación de `ui/modules/vectors_view.py` con evaluador de combinación lineal.
  - [ ] Implementación de `ui/modules/matrix_equations_view.py`.
- [ ] **Pruebas Automatizadas:**
  - [ ] 100% de tests existentes y nuevos pasando con `pytest`.
  - [ ] Cobertura de casos canónicos y validación de errores dimensionales.
- [ ] **Entregable Académico Universitario:**
  - [ ] `Programa 3_Grupo4.py` en la raíz del proyecto (script interactivo CLI comentado de forma didáctica).
  - [ ] Casos de prueba académicos documentados para el informe en PDF.
