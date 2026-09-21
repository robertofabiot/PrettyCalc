# Sprint 1: Solución de Sistemas Lineales por Eliminación por Filas

**Carpeta:** [`Docs/Sprints/Sprint1/`](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint1/)  
**Estado:** Planificado / Listo para Implementación  
**Entregable Académico Asociado:** *Programa 1 - Álgebra Lineal (MTM0120)*

---

## 1. Documentos del Sprint

* [**`implementation-plan.md`**](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint1/implementation-plan.md): **Plan de implementación paso a paso (atómico)** para el motor y la UI.
* [`Tarea 1 (Elaboracion Programa 1_Python)(1).docx`](file:///home/ro/Projects/PrettyCalc/Docs/Sprints/Sprint1/Tarea%201%20(Elaboracion%20Programa%201_Python)(1).docx): Especificación formal de la actividad universitaria.

---

## 2. Requerimientos Funcionales del Sprint

1. **Entrada de Datos:**
   * Matriz aumentada $[A \mid b]$ con inicio $2 \times 2 (+ b)$ y crecimiento dinámico con celdas fantasma (`+` en hover).
   * Línea vertical divisoria en la columna $b$ vía `AugmentedMatrixDelegate`.
   * Navegación 100% por teclado (`Tab`/flechas) y validación en tiempo real.
2. **Procesamiento y Algoritmo de Eliminación:**
   * Proceso ordenado de escalonamiento por operaciones elementales de fila ($100\%$ Python estándar).
   * Registro de cada paso en `StepTracer` con fórmula LaTeX y texto explicativo en cursiva.
3. **Clasificación del Sistema:**
   * Evaluación y categorización en **SCD** (Solución Única), **SCI** (Infinitas Soluciones con variables libres 🔑) o **SI** (Inconsistente).
4. **Verificación y Salida:**
   * Despliegue de variables en el Dashboard de Resultados.
   * Comprobación automática por sustitución exacta en las ecuaciones originales con checklist (**✓**).
