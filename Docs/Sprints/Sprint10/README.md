# Sprint 10: Excelencia UI/UX (auditoría 10/10) y paridad Windows/Linux

**Fecha de Inicio:** 2026-10-11  
**Fecha de Fin:** 2026-10-12  
**Estado:** Implementado  
**Rama Git de Trabajo:** `feature/sprint-10-excelencia-ui-ux`  
**Rama Destino:** `main`  
**Asignatura:** Álgebra Lineal (MTM0120) — II Semestre 2026  
**Institución:** Universidad Americana (UAM) — Facultad de Ingeniería y Arquitectura (FIA)

---

## 1. Objetivo del Sprint (Sprint Goal)

Cerrar cada brecha heurística, caso límite y limitación ergonómica que la auditoría maestra (`auditoria_ui_ux/AUDITORIA_SISTEMAS_UI_UX.md`, Módulos 1 a 7) documentó, hasta que cada flujo merezca 10/10, y lograr que la aplicación **se vea igual en Windows y en Linux**.

El motor matemático conserva su contrato (LaTeX puro, `Fraction` exacta, sin dependencias externas). Las ampliaciones del núcleo son aditivas: diagnóstico de entradas, filas de alerta y celdas resaltadas en el trazador, desglose componente a componente de u ± v y k·v, diagonales de Sarrus, línea sugerida de Laplace y el desglose kⁿ.

---

## 2. Requerimientos Específicos de la Iteración

### 2.1. Transversal (Módulo 7 y design system)

- [x] **REQ-10.1 — Paridad de plataformas.** Fuentes empaquetadas (Inter, Fira Code, DejaVu Sans) registradas al arrancar, tamaños en píxeles sin *hinting*, estilo Fusion, iconos de diálogos dibujados por la app, diálogo de archivos no nativo, rutas QSS con `/`, sin emojis. Se verificó que la geometría de 113 widgets es idéntica con 96 y 144 ppp y sin ninguna fuente del sistema.
- [x] **REQ-10.2 — Tokens WCAG AA.** `text_muted` `#C9C3D6` y `surface_elevated` `#4A4257` (≥ 4.5:1); temas oscuro, alto contraste y claro; escala de interfaz; texto de badge elegido por contraste.
- [x] **REQ-10.3 — Cuadrícula.** Deshacer/rehacer de cambios masivos, explicación en línea de la celda inválida (coma decimal, letra O, división entre cero…), celda vacía → 0 al salir, Ctrl+Intro, Ctrl+Supr / Ctrl+Mayús+Supr, aviso de pegado con «Deshacer», resaltado visible (la hoja de estilo de la cuadrícula ya no tapaba el fondo de las celdas).
- [x] **REQ-10.4 — Componentes comunes.** Avisos no modales con acción, estado «Calculando…», campo escalar con pista decimal y chips, control directo de tamaño `m × n`, filas adaptables, pila de páginas que mide la página visible, editor de conjuntos de vectores con salto de línea.
- [x] **REQ-10.5 — Carrusel.** Deslizador «Ir al paso», teclado, exportar (PDF, HTML, LaTeX, texto), salto a la fila crítica (singular / contradicción), señal `stepChanged` y cabeceras x₁…xₙ solo donde hay un sistema.
- [x] **REQ-10.6 — Ayuda.** Hoja de atajos (F1) y diálogo de apariencia (Ctrl+,).

### 2.2. Módulo 1 — Sistemas lineales

- [x] Control directo ecuaciones × incógnitas; reinicio deshacible; marca del caso de prueba activo.
- [x] Cramer en sistemas no cuadrados o singulares: guía con «Igualar a n×n» y «Usar Gauss-Jordan».
- [x] Contradicción con su valor (`0 = 1`), paso final explícito de det(A) y llamada a la acción en sistemas singulares.
- [x] Aplicaciones: sumas de Leontief, dieta y red de flujo personalizables.

### 2.3. Módulo 2 — Álgebra matricial

- [x] Un solo «Calcular», «Ajustar B», ejemplos por página, inspector celda a celda con insignia.
- [x] Escalar k con chips; transpuesta con B opcional; propiedades ternarias con intermedios.
- [x] Inversa singular: salto al paso crítico; «Usar A⁻¹ como entrada»; recibir A⁻¹ desde Determinantes.
- [x] TMI con tarjeta clave y filtros; identidades con la comparación AB vs. BA.

### 2.4. Módulo 3 — Vectores en ℝⁿ

- [x] u ± v y k·v con operador visible, «⇄ Intercambiar u y v» (deshacible) y carrusel componente a componente.
- [x] Métricas con selector segmentado y un único «Calcular»; inspector de u vᵀ que resalta uᵢ y vⱼ.
- [x] Conjuntos en varias filas, «Pegar matriz» (columnas o `[v₁ … vₖ | b]`), quitar vector con «Deshacer», aviso k > n antes de evaluar.
- [x] Validación en línea, fila y valor de la contradicción en el SI, ejemplo SCI, veredictos marcados como desactualizados, teoremas del Módulo 3.

### 2.5. Módulo 4 — Ecuaciones matriciales

- [x] Un único «Resolver», tamaño `m × n` con «Hacer cuadrada», «Ajustar b», reinicio deshacible.
- [x] Insignia «Solución particular (variables libres = 0)» con las componentes libres resaltadas; fila contradictoria concreta en el SI.
- [x] Propiedades de A·x: «Vincular u y v a las columnas de A», LHS y RHS en una fila (apilables), escalar c común con pista `≈ 1.5`, nota pedagógica para c = 0.

### 2.6. Módulo 5 — Determinantes

- [x] Orden con spinbox directo; errores en línea sin diálogos.
- [x] Sarrus: «Ajustar a 3×3» (badge y aviso), un paso por diagonal y esquema gráfico de diagonales que sigue al carrusel.
- [x] Laplace: fila o columna de expansión resaltada en A y sugerencia de la línea con más ceros.
- [x] Menores, cofactores, adjunta e inversa en pestañas; «Usar A⁻¹ como A» y «Enviar A⁻¹ a Matrices».
- [x] Propiedades con B al lado de A y desglose `kⁿ = 2² = 4 ⇒ 4 · 9 = 36`.

### 2.7. Módulo 6 — Factorización LU

- [x] Tamaño `m × n` con spinboxes; el panel de A se ensancha con matrices anchas.
- [x] Filas permutadas por P marcadas en ocre sobre A, con leyenda.
- [x] Etapa 1, etapa 2 y clasificación en pestañas; con pivote nulo en U o A rectangular, «Clasificar A x = b» muestra el tablero de resultados (SCI/SI con variables libres).

---

## 3. Desglose de Tareas Técnicas

### 3.1. Motor Matemático (`prettycalc/core`)

- [x] `input_diagnostics.py`: `diagnose_scalar_text()` y `decimal_hint()`.
- [x] `tracer.py`: `alert_rows` y `highlight_cells` por paso.
- [x] `determinants.py`: paso final con el producto de la diagonal, diagonales de Sarrus, línea de Laplace resaltada, `best_expansion_line()` y `scaling_breakdown()`.
- [x] `classifier.py`: `inconsistent_value` en `SystemAnalysis`.
- [x] `vector_ops.py`: `trace_vector_sum()` y `trace_vector_scale()`.

### 3.2. Interfaz

- [x] Nuevos: `platform_setup.py`, `feedback.py`, `scalar_field.py`, `size_control.py`, `responsive.py`, `export.py`, `preferences_dialog.py`, `vector_set_editor.py`, `sarrus_diagram.py`, `assets/fonts/`.
- [x] Reescritos o ampliados: `theme.py`, `matrix_grid.py`, `stepper_carousel.py`, `book_matrix.py`, `results_dashboard.py`, `navigation_bar.py`, `main_window.py` y las vistas de los seis módulos.

### 3.3. Pruebas y Validación

- [x] `tests/core/test_input_diagnostics.py`.
- [x] `tests/ui/test_cross_platform.py` (fuentes, píxeles, Fusion, sin emojis, geometría estable).
- [x] `tests/ui/test_sprint10_ui.py`, `test_sprint10_vectors.py`, `test_sprint10_equations.py`, `test_sprint10_det_lu.py`.
- [x] CI: `.github/workflows/tests.yml` en Ubuntu y Windows con Python 3.10 y 3.13.
- [x] `QT_QPA_PLATFORM=offscreen pytest`: **448 pruebas en verde**, incluidas todas las anteriores sin modificar su intención.
- [x] Barrido de desbordamiento: ninguna vista tiene desplazamiento horizontal a 1366×768 con los ejemplos cargados.

---

## 4. Criterios de Aceptación (Definition of Done)

- [x] Cada brecha de la auditoría tiene su cambio y, cuando es observable, su prueba.
- [x] Ningún flujo usa un diálogo modal para validar entradas.
- [x] Toda acción masiva se puede deshacer.
- [x] La app no depende de fuentes, estilo nativo ni emojis del sistema.
- [x] La suite completa pasa.

---

## 5. Notas y Decisiones Técnicas del Sprint

1. **Fusion sin `QProxyStyle`.** Un estilo proxy en Python se consultaba unas 28 000 veces al iniciar (2 s). Fusion con QSS da el mismo resultado sin ese costo.
2. **Familias renombradas en las fuentes.** Inter Medium/SemiBold y Fira Code SemiBold se registraban como familias distintas; se ajustó la tabla `name` (detalle en `assets/fonts/README.md`).
3. **`\text{}` usa `FONT_FAMILY_SANS`.** `sans-serif` genérico tomaba la fuente del sistema y movía el layout 2 px.
4. **`CurrentPageStack` en lugar de `QStackedWidget`.** El stack medía lo que la página más alta y empujaba el contenido fuera de la vista.
5. **Sarrus en orden ≠ 3 ofrece ajustar, no ajusta solo.** Cambiar el tamaño en silencio sorprendería; el badge mantiene el bloqueo y el aviso propone «Ajustar a 3×3» con «Deshacer».
6. **Comprobaciones a 22 px.** Una prueba existente exige ese mínimo; para que entren a 1366 px se reparte el ancho (1:1) en vez de bajar la letra.
7. **`1e5` es válido.** El parser lo acepta, así que el diagnóstico también; una celda no puede marcarse inválida y calcularse a la vez.
8. **Temporizadores ligados al widget.** `QTimer.singleShot(0, self, …)` evita `RuntimeError` cuando una vista se destruye con un ajuste pendiente.
9. **Lo único distinto entre Windows y Linux** es la barra de título, que dibuja el sistema operativo.

---

## 6. Guía de Commits Atómicos

1. `feat(ui): apariencia identica en Windows y Linux, tokens WCAG AA y temas`
2. `feat(core): diagnostico de entradas, alertas de fila y paso final explicito de det(A)`
3. `feat(ui): componentes transversales del sprint 10`
4. `feat(sel): modulo 1 al estandar 10/10`
5. `feat(matrices): modulo 2 al estandar 10/10`
6. `feat(vectores, ecuaciones): modulos 3 y 4 al estandar 10/10`
7. `feat(determinantes, lu): modulos 5 y 6 al estandar 10/10`
8. `docs(sprint10): registro del sprint, reglas de diseño y atajos`
