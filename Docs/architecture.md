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
│  - Algoritmos: Gauss, Gauss-Jordan, Inversa, RREF                      │
│  - StepTracer: Registro de pasos (matriz, pivote, operación elemental) │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Componentes Principales

### 2.1. Motor Matemático Puro (`prettycalc.core`)
* **Regla de Oro:** **Cero librerías externas de álgebra lineal** (sin `numpy`, `scipy`, `sympy`).
* **Estructuras Fundamentales:**
  * `Scalar`: Aritmética exacta basada en `fractions.Fraction` estándar.
  * `Matrix`: Estructura bidimensional inmutable para cálculos o manipulada mediante operaciones elementales de fila registradas.
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
* **`ResultsDashboardCard`:** Panel montado sobre `color-surface-elevated` con badges semánticos, distinción de variables libres (🔑) y checklist de comprobación en `color-feedback-success` (✓).

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
