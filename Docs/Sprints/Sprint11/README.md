# Sprint 11: Movimiento que explica el procedimiento

**Fecha de Inicio:** 2026-11-19  
**Fecha de Fin:** 2026-11-19  
**Estado:** Implementado  
**Rama Git de Trabajo:** `feature/animaciones`  
**Rama Destino:** `main`  
**Asignatura:** Álgebra Lineal (MTM0120) — II Semestre 2026  
**Institución:** Universidad Americana (UAM) — Facultad de Ingeniería y Arquitectura (FIA)

---

## 1. Objetivo del Sprint (Sprint Goal)

Que el movimiento muestre la operación ocurrir: una fila que viaja hasta la fila que modifica, una entrada que cruza la diagonal al transponer, la columna `b` que entra en la columna `i` en Cramer, la solución que sale de la última columna de la RREF hacia el tablero. Cada animación responde qué cambió, de dónde vino o a dónde fue, y ninguna trayectoria contradice la matemática.

El estado de la aplicación es idéntico con y sin animaciones; solo cambia la transición. Las reglas están en [design-rules.md §9](../../design-rules.md).

---

## 2. Requerimientos Específicos de la Iteración

### 2.1. Sistema de movimiento

- [x] **REQ-11.1 — Tokens y ayudantes centrales.** `ui/motion.py`: duraciones (`FAST`, `BASE`, `SLOW`, `EMPHASIS`, `SIGNATURE`, `STAGGER`, `PULSE_CYCLE`), curvas, fundidos con efecto temporal, fundido cruzado por instantánea, desplazamiento suave con el destino de `ensureWidgetVisible`, pulsos, detector de ráfaga, revelado del veredicto y `finish_all()`.
- [x] **REQ-11.2 — Capa de coreografía.** Una capa por ventana pinta todo lo que viaja entre widgets (pixmaps cacheados al empezar), oculta y transparente al ratón; se cancela al redimensionar, desplazar o cambiar de módulo.
- [x] **REQ-11.3 — Reducir animaciones.** Opción en *Apariencia*, guardada en `appearance/reduce_motion`, sin reinicio; `PRETTYCALC_REDUCE_MOTION` y `PRETTYCALC_MOTION_SCALE`; en Windows se toma la preferencia del sistema si el usuario no eligió.

### 2.2. El procedimiento

- [x] **REQ-11.4 — Operación de fila visible.** Suma de un múltiplo (copia con `× k` que viaja y se funde), intercambio en arco, escalado con pulso del pivote, entradas que cambiaron con fundido cruzado, pivote que se desliza, columna reemplazada de Cramer.
- [x] **REQ-11.5 — Tres formas de navegar.** Avanzar reproduce; retroceder y saltar funden; en ráfaga, versión corta.
- [x] **REQ-11.6 — Forma final.** Pivotes en secuencia, cabeceras básicas y libres, fila contradictoria atenuada.
- [x] **REQ-11.7 — Reproducir el procedimiento.** ½×, 1×, 2×, Espacio, tiempo de lectura según el texto; se detiene ante cualquier interacción.
- [x] **REQ-11.8 — Esquemas sincronizados.** Sarrus atenúa con transición y traza la diagonal del paso con su término.

### 2.3. Resultados y orientación

- [x] **REQ-11.9 — Revelado.** Badge que se asienta, secciones escalonadas, pulso si el veredicto no cambió, veredicto viejo que se desvanece al editar.
- [x] **REQ-11.10 — Avisos.** Entrada, salida, reemplazo con fundido cruzado, barra del tiempo para deshacer y pausa con el cursor.
- [x] **REQ-11.11 — Desplazamiento suave** hacia Aplicaciones, la matriz y las pestañas de resultados.
- [x] **REQ-11.12 — La matriz entra al procedimiento** y la columna `b` viaja al tablero en Sistemas.

### 2.4. Momentos por módulo, entrada y navegación

- [x] **REQ-11.13 —** Transpuesta que cruza la diagonal, bloque de A⁻¹, inspector de A·B y de u vᵀ, filas permutadas de LU y `y` antes que `x`, T(v) fila por fila, bases de im(T), nu(T), del conjunto generador y de Ker A, coeficientes de un conjunto dependiente.
- [x] **REQ-11.14 — Cuadrícula.** Corchetes que crecen, celdas nuevas teñidas, destello que decae, celda inválida que pulsa al intentar calcular.
- [x] **REQ-11.15 — Navegación.** Indicador que se desliza, hover con fundido, fundido entre módulos y pestañas, paneles que aparecen, tarjetas de vectores, entrada del logotipo.

## 3. Desglose de Tareas Técnicas

### 3.1. Motor Matemático
- [x] `core/step_diff.py`: reconoce intercambio, escalado y suma de un múltiplo entre dos pasos con aritmética exacta (los metadatos solo orientan), por bloques en `[L | U]`; columna reemplazada; entradas principales, forma escalonada y filas `[0 … 0 | c]`. `CalculationStep` no cambia.

### 3.2. Interfaz / Visualización
- [x] `ui/motion.py`, `ui/choreography.py` (correspondencias puras y vuelos).
- [x] `BookMatrixWidget`: geometría cacheada por estado y tamaño; coreografías pintadas.
- [x] `AlgorithmStepperCarousel`: `stepArrived(int, str)`, `playbackChanged(bool)`, detector de ráfaga, reproducción.
- [x] Toast, tablero, cuadrícula, barra lateral, ventana principal, Sarrus, logotipo (el SVG nombra `frame`, `brackets` y `entries`).

### 3.3. Pruebas y Validación
- [x] `tests/core/test_step_diff.py`: cada paso de Gauss-Jordan, A⁻¹, LU, PLU y Cramer coincide con su operación y la reconstruye.
- [x] `tests/ui/test_motion.py`, `test_carousel_motion.py`, `test_results_motion.py`, `test_module_motion.py`, `test_input_nav_motion.py`, `test_polish_motion.py`: estado final inmediato, reducir animaciones, ráfaga, destrucción a mitad de animación, cancelación de la capa, verdad de cada trayectoria, reproducción.
- [x] `tests/ui/conftest.py`: cada prueba parte con animaciones activas y termina con `finish_all()`.

## 4. Criterios de Aceptación (Definition of Done)

- La suite completa pasa en `QT_QPA_PLATFORM=offscreen`, incluidas la sonda de layout, la cobertura de glifos y la ausencia de desplazamiento horizontal de 1080 a 1920 px.
- Ninguna animación bloquea la entrada, se encola ni muestra valores intermedios.
- Con «Reducir animaciones» no hay nada en vuelo y el estado final queda resaltado.
- Duraciones y curvas salen de `motion.py`.

## 5. Notas y Decisiones Técnicas del Sprint

- **La operación se deduce comparando matrices**, no con campos nuevos en `CalculationStep`: funciona con los pasos anidados (menores, Cramer, A⁻¹) y nunca anima algo que la aritmética no confirme.
- **En LU no viaja el multiplicador:** la fila lleva `−ℓ` y L guarda `ℓ`; la casilla de L se enciende con su valor final.
- **El rótulo «Ir al paso» aparece solo si cabe;** en columnas angostas quedan el deslizador (con su nombre accesible) y la reproducción, sin desplazamiento horizontal. La velocidad lenta se rotula «½×».
- **Los errores en línea de la cuadrícula siguen sin movimiento**, para que escribir se sienta instantáneo.
- **Matrices grandes:** si la cuadrícula o el visor no se ven enteros (por ejemplo 10 × 11 a 1080 px), la matriz no vuela; queda su estado final. Con 8 × 9 vuelan 72 entradas a menos de 1 ms por fotograma.
- **Costo por fotograma** medido con 10 × 11: 1.7 ms el visor durante una operación, 0.5–0.8 ms la capa; 40 pasos con la tecla mantenida tardan unos 200 ms.

## 6. Retrospectiva / Cierre

Pendiente para otra iteración: que Sistemas retire su veredicto al editar la cuadrícula, como ya hacen Ecuaciones y Vectores (la regla de §8 de diseño).
