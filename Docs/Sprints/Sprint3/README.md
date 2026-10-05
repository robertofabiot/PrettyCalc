# Sprint 3: Transpuesta, propiedades matriciales y paridad consola/interfaz

**Rama Git:** `feat/sprint-3`  
**Asignatura:** Álgebra Lineal MTM0120, Universidad Americana (UAM). Grupo 4.

## Alcance

- Transpuesta pura `matrix_transpose` en `prettycalc/core/matrix_ops.py`.
- Inspector `analyze_matrix` en `prettycalc/core/matrix_properties.py`.
- Opción de consola en `Programa 3_Grupo4.py` (submenú de matrices: Aᵀ y propiedades).
- Operación unaria Aᵀ en la vista de álgebra matricial, con tarjetas de propiedades.

## Decisiones de arquitectura

`operations.py` se queda con las operaciones elementales de fila. `matrix_ops.py` concentra suma, resta, escala, producto y transpuesta. No había dos implementaciones de la misma operación dentro del paquete; el riesgo era añadir la transpuesta en ambos. El inspector vive aparte para que cada función siga teniendo una sola responsabilidad.

La consola académica conserva sus bucles de suma, producto y Gauss-Jordan, porque ese archivo es el entregable autónomo del programa. La transpuesta y el análisis de propiedades sí llaman al motor de `prettycalc.core`, el mismo que usa la interfaz, para que esas comprobaciones no se desvíen.

## Paridad

| Tema | Consola | Interfaz | Motor |
| --- | --- | --- | --- |
| Sistemas y Gauss-Jordan | `Programa 1_Grupo4.py` | Sistemas lineales | `core` en la interfaz; el programa 1 es autónomo |
| Vectores y combinación lineal (pesos) | Programa 3, opciones 1 y 2 | Vectores | Equivalente; la interfaz usa `core` |
| A ± B, k·A, A·B con desglose | Programa 3, opción 3 | Álgebra matricial | Equivalente |
| A x = b y comprobación | Programa 3, opción 4 | Ecuaciones | Equivalente |
| Aᵀ y propiedades | Programa 3, opciones 5 y 6 | Modo Aᵀ | Mismo `core` |
