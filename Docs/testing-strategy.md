# Estrategia de Pruebas (Testing) - PrettyCalc

## 1. Marco de Trabajo y Herramientas
* **Framework Principal:** `pytest`.
* **Módulos Auxiliares:** `pytest-qt` (para pruebas de interfaz gráfica, simulación de mouse/hover y eventos de teclado), `pytest-mock` y `pytest-cov`.

---

## 2. Niveles de Pruebas

### 2.1. Pruebas Unitarias del Motor Matemático (`tests/core/`)
* **Aritmética Exacta con Fracciones:**
  * Operaciones con `Fraction` (simplificación automática, signos negativos, división por cero).
  * Parsing de entradas numéricas mixtas (`"-3/4"`, `"2"`, `"0.5"` -> `Fraction(1, 2)`).
* **Operaciones Elementales y Trazabilidad:**
  * Ejecución correcta de $f_i \leftrightarrow f_j$, $f_i \rightarrow k f_i$, $f_i \rightarrow k f_j + f_i$.
  * Comprobación de que cada paso registre correctamente el `pivot_position`, la fórmula LaTeX y el texto heurístico descriptivo.
* **Algoritmo de Verificación por Sustitución (`SolutionVerifier`):**
  * Validación exacta de $\sum A_{ij} x_j = b_i$ para comprobar el checklist de confirmación (✓).
  * Comprobación de sistemas inconsistentes y detección de ecuaciones contradictorias.

### 2.2. Pruebas de Interfaz de Usuario y UX (`tests/ui/`)
* **Estado Inicial y Crecimiento Dinámico (`DynamicMatrixGrid`):**
  * Comprobación de que la interfaz inicialice en formato $2 \times 2$ con la columna $b$ visible.
  * Simulación de hover y clic sobre la fila/columna fantasma (Ghosting) para verificar la adición dinámica de filas y columnas.
* **Delegado de Matriz Aumentada (`AugmentedMatrixDelegate`):**
  * Verificación de la renderización de la línea divisoria vertical en el borde izquierdo de la columna de términos independientes.
* **Navegabilidad por Teclado:**
  * Simulación con `pytest-qt` del foco de celda al presionar `Tab`, `Shift+Tab` y teclas de flecha.
* **Validador en Tiempo Real (Prevención de Errores):**
  * Rechazo inmediato de caracteres no numéricos y activación del borde con `color-feedback-error`.
* **Visor Stepper/Carrusel y Dashboard:**
  * Verificación de avance y retroceso (`[ ◀ Anterior ]`, `[ Siguiente ▶ ]`) y estado deshabilitado inicial en el Paso 1.
  * Comprobación de que el Badge de estado refleje el color correcto (Verde, Amarillo, Rojo).

---

## 3. Criterios de Aceptación y Calidad (Definition of Done)
1. Cobertura de código superior al **90%** en el módulo matemático `core/` y en `SolutionVerifier`.
2. Toda nueva funcionalidad de UI debe contar con tests de integración de teclado y eventos con `pytest-qt`.
