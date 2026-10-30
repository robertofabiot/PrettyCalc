# AUDITORÍA DE SISTEMAS UI/UX — PRETTYCALC
**Documento Técnico de Arquitectura de Interfaz, Ergonomía Cognitiva y Flujos de Usuario**
**Analista / Autor:** Technical UI/UX Systems Architect
**Destinatario:** Consultoría UI/UX y Equipo de Ingeniería Frontend

---

Procede con la auditoría profunda y detallada del módulo: Módulo 1: Sistemas de Ecuaciones Lineales y Modelos Aplicados

---

## [SEL_FLUJO_01] - Resolución por Eliminación de Gauss-Jordan

### 1. Metadatos Técnicos
- **Objetivo:** Resolver un sistema de ecuaciones lineales $m \times n$ ingresado como matriz aumentada $[A \mid b]$ mediante el algoritmo de Gauss-Jordan exacto en fracciones, obteniendo la clasificación del sistema, la solución analítica/paramétrica, la comprobación por sustitución y la navegación paso a paso de las operaciones elementales de fila.
- **Punto de inicio:** Ruta: Stack Index 0 (`Ctrl+1`), componente principal: [`LinearSystemsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L43).
- **Condiciones previas:** Aplicación inicializada. Estado local con cuadrícula mínima de $2 \times 3$ ($2 \times 2$ coeficientes $+ 1$ columna de términos independientes $b$). Todas las celdas con valores escalares válidos (enteros, fracciones `a/b` o decimales). Selector de método en `Gauss-Jordan` (estado por defecto).

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Exploración e ingreso de coeficientes**
  - **Interacción:** El usuario hace clic en una celda de la matriz aumentada o navega hacia ella mediante las teclas `Tab` / `Shift+Tab` o las `Flechas del Teclado` ($\leftarrow, \rightarrow, \uparrow, \downarrow$), e introduce coeficientes numéricos (ej. `2`, `-1/3`, `4.5`).
  - **Componente:** [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) dentro de [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor [`QFrame`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L69) con clase `elevated-card` mantiene su elevación visual (`color-surface-elevated` `#564D65`).
    - *Colores y Tokens:* Al recibir el foco, el texto completo de la celda se autoselecciona (`selectAll()`). El fondo de la celda es `color-surface-inner` (`#242028`), texto en `color-text-primary` (`#E0FBFC`). La celda aplica la clase CSS `matrix-cell`. La línea vertical divisoria entre coeficientes y términos independientes se renderiza en `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* Valor por defecto `"0"`. Tipografía de entrada: Monospace (`Fira Code`, 12pt).
    - *Feedback de Carga:* Inmediato; validación sintáctica en el evento `textChanged`.

- **Paso 02: Expansión de dimensiones del sistema (Ghosting Pattern)**
  - **Interacción:** El usuario sitúa el cursor sobre el margen inferior o derecho de la cuadrícula o pulsa los botones con el símbolo `+`. Alternativamente, presiona `Tab` en la última celda de una fila o `Flecha Abajo` en la última fila.
  - **Componente:** `QPushButton` de celda fantasma ([`_make_ghost_button`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L53)) con clase `ghost-cell` en [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La cuadrícula recalcula su tamaño sin saltos bruscos (`setFixedSize`), desplazando los controles adyacentes de forma natural.
    - *Colores y Tokens:* Los botones fantasma cambian de opacidad tenue a cursor de mano (`Qt.PointingHandCursor`) con borde sutil en `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* Tooltip: `"Agregar fila (o pulsa Abajo en la última fila)"` o `"Agregar columna (o pulsa Tab en la última columna)"`. Las nuevas celdas se inicializan con `"0"`.

- **Paso 03: Ejecución de la resolución**
  - **Interacción:** El usuario hace clic en el botón principal `"Resolver sistema"`.
  - **Componente:** `self.solve_btn` (`QPushButton` con ID `primaryAction`) en [`LinearSystemsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L117).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El panel central ([`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32)) y el panel lateral derecho ([`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80)) se actualizan instantáneamente de forma síncrona.
    - *Colores y Tokens:* El botón presenta estado activo en `color-interactive-idle` (`#98C1D9`) con texto `color-bg-base` (`#1A181B`). Al resolver, el badge de estado en el Dashboard adopta `color-feedback-success` (`#81B29A`) si es compatible determinado, `color-accent-warning` (`#E9C46A`) si es indeterminado, o `color-feedback-error` (`#EE6C4D`) si es inconsistente.
    - *Textos y Microcopia:* Botón: `"Resolver sistema"`. Título del carrusel: `"Procedimiento"`. Título del dashboard: `"Resultados"`.

- **Paso 04: Inspección de resultados y comprobación analítica**
  - **Interacción:** El usuario lee la clasificación en el panel derecho y examina las variables y ecuaciones de comprobación.
  - **Componente:** [`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80) y sus widgets de vectores columna (`_ColumnVectorWidget`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Aparecen bloques modulares: badge de tipo de sistema, tarjeta de variables básicas / libres (con distintivo 🔑), solución única o forma vectorial paramétrica $x = p + \sum t_k v_k$, y el checklist de verificación.
    - *Colores y Tokens:* Cada ecuación verificada muestra un icono `✓` en `color-feedback-success` (`#81B29A`). Los vectores columna se dibujan con corchetes vectoriales estilizados sobre fondo `color-surface-inner` (`#242028`).
    - *Textos y Microcopia:* 
      - Badges: `"SISTEMA COMPATIBLE DETERMINADO  (SCD)"`, `"SISTEMA COMPATIBLE INDETERMINADO  (SCI)"` o `"SISTEMA INCONSISTENTE  (SI)"`.
      - Ecuaciones de validación: `"✓  Ec. 1:  2·(1) + 3·(2) = 8  (8 = 8)"`.

- **Paso 05: Navegación por el carrusel de pasos algorítmicos**
  - **Interacción:** El usuario hace clic en `"Siguiente"` o `"Anterior"`, o conmuta el botón `"Fracciones"`.
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`self.prev_btn`, `self.next_btn`, `self.mode_btn`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La matriz intermedia se actualiza en [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1).
    - *Colores y Tokens:* La celda correspondiente al pivote activo de la iteración se resalta en verde tenue `color-feedback-success` (`#81B29A`). El botón `"Anterior"` se deshabilita (`color-interactive-disabled` `#3A3642`) en el Paso 0.
    - *Textos y Microcopia:* Label superior: `"Paso i de N"`. Label explicativo: transforma la fórmula formal a RichText de libro (ej. $F_2 \rightarrow F_2 - 2F_1$) y añade la heurística explicativa en cursiva (*"Se multiplicó la Fila 1 por -2 y se sumó a la Fila 2"*).

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Entrada no numérica (letras, símbolos no reconocidos, ej. `abc`, `3..2`) | [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) | Borde de la celda cambia inmediatamente a `color-feedback-error` (`#EE6C4D`, 2px sólido). La bandera interna `_is_valid` pasa a `False`. | Ninguna microcopia dentro de la celda; feedback netamente cromático. | El usuario borra o corrige los caracteres. Al detectar número válido, el borde regresa al estado neutro. |
| Intento de resolver con celdas inválidas en la cuadrícula | Diálogo emergente modal [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L214) | Modal nativo temático con icono `QMessageBox.Warning`. Fondo `color-surface-elevated`, botón con borde `color-interactive-idle`. | **Título:** `"Entrada inválida"`<br>**Cuerpo:** `"Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales."` | Botón `"OK"` que cierra el modal y devuelve el foco a la ventana principal. |
| Matriz vacía o con entradas en blanco | [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L107) | Si se vacía el texto, la celda asume temporalmente estado neutral sin error, pero `parse_scalar` fallará si queda vacía al calcular. | Al calcular vacía, dispara el modal de `"Entrada inválida"`. | Rellenar las celdas con valores válidos o `"0"`. |
| Sistema inconsistente con fila de ceros y término independiente no nulo ($[0\dots 0 \mid c]$) | [`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80) | Badge rojo en `color-feedback-error` (`#EE6C4D`). La sección de checklist se oculta y se sustituye por la alerta de contradicción. | **Badge:** `"SISTEMA INCONSISTENTE  (SI)"`<br>**Detalle:** `"Contradicción: Fila [k] produce 0 = c (con c ≠ 0). El sistema no tiene solución."` | Explorar el carrusel de pasos para ubicar la fila inconsistente o modificar coeficientes en la cuadrícula. |
| Error matemático o excepción de desbordamiento | Diálogo modal [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L271) | Modal crítico nativo estilizado (`QMessageBox.Critical`). | **Título:** `"Error matemático"`<br>**Cuerpo:** `"No se pudo resolver el sistema:\n{detalle_excepcion}"` | Botón `"OK"`. Permite corregir entradas. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Cuadrícula Dinámica ([`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1))
- **Empty State:** No existe estado en blanco; la vista arranca siempre con la cuadrícula base de $2 \times 3$ rellenada con `"0"`.
- **Hover / Focus:** Celdas adquieren borde `color-interactive-idle` (`#98C1D9`). Botones fantasma `+` cambian de opacidad reducida a 100% de visibilidad con fondo interactivo. Al hacer foco, se resalta la celda con selección de texto total.
- **Disabled:** Cuando se deshabilitan las celdas fantasma (ej. en editores fijos), se ocultan completamente sin ocupar espacio en el layout.

#### B. Botón Resolver Sistema (`solve_btn`)
- **Empty State:** Habilitado por defecto con el sistema $2 \times 3$ en ceros.
- **Hover / Focus:** Fondo transiciona a `#BEE1F5` con cursor de mano (`PointingHandCursor`). En foco por teclado, resalta el contorno.
- **Disabled:** Mantiene visualización activa, pero intercepta el clic mostrando el modal de validación si alguna celda no es válida.

#### C. Carrusel de Pasos ([`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32))
- **Empty State:** Antes de resolver, la etiqueta muestra `"Paso 0 de 0"`, la caja de fórmulas está vacía y la cuadrícula interior no tiene celdas renderizadas. Los botones `"Anterior"` y `"Siguiente"` están deshabilitados en `color-interactive-disabled` (`#3A3642`).
- **Hover / Focus:** En estado activo, los botones navegan fluidamente. El botón `"Fracciones"` conmuta su estado visual de checked.
- **Disabled:** Botón `"Anterior"` inactivo en el Paso 0; botón `"Siguiente"` inactivo en el paso final ($N-1$). Cursor de bloqueo visual.

#### D. Dashboard de Clasificación y Resultados ([`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80))
- **Empty State:** Muestra la tarjeta vacía con título `"Resultados"` y espacio en reposo. Al pulsar `"Reiniciar"`, se invoca `clear()` y se remueven todos los badges, vectores y checklists.
- **Hover / Focus:** Los textos de resultados tienen banderas `TextSelectableByMouse` para permitir copiar la solución al portapapeles.
- **Disabled:** No aplica estado deshabilitado.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado del sistema]:** La resolución de Gauss-Jordan se ejecuta en el hilo principal de la interfaz (`solve_system()`). En matrices grandes (ej. $6 \times 7$) con coeficientes fraccionarios densos, la interfaz sufre un congelamiento momentáneo (jank/lag) sin presentar un spinner local ni deshabilitar temporalmente el botón de acción con feedback visual de carga.
2. **[Nielsen #3 - Control y libertad del usuario]:** El botón `"Reiniciar"` restablece la cuadrícula a $2 \times 3$ y borra todos los datos de forma inmediata y destructiva, sin solicitar confirmación previa (`QMessageBox.question`) ni ofrecer un mecanismo de deshacer (`Ctrl+Z`). Si el usuario introdujo manualmente un sistema de $5 \times 6$, un clic accidental destruye todo su trabajo.
3. **[Nielsen #5 - Prevención de errores]:** Cuando una celda se marca en rojo por entrada no numérica, no existe un tooltip accesible o mensaje contextual bajo la celda que explique qué carácter causó el error (ej. confundir la letra `O` con el número `0` o ingresar coma en lugar de punto).
4. **[Nielsen #7 - Flexibilidad y eficiencia de uso]:** No existe un control de entrada rápida de dimensiones (spinboxes $m \times n$) en este módulo; para crear un sistema $5 \times 5$, el usuario se ve forzado a hacer múltiples clics sucesivos en los botones `+` de filas y columnas fantasma.
5. **[Nielsen #8 - Estética y diseño minimalista]:** La columna izquierda contiene apiladas la tarjeta de la matriz, la tarjeta de casos de prueba y el panel colapsable de aplicaciones. En pantallas con resolución vertical inferior a 800px, el scroll vertical lateral se satura visualmente compitiendo con el scroll horizontal de la matriz.

---

## [SEL_FLUJO_02] - Resolución por Regla de Cramer $n \times n$

### 1. Metadatos Técnicos
- **Objetivo:** Resolver un sistema cuadrado de $n$ ecuaciones con $n$ incógnitas evaluando el determinante de la matriz de coeficientes $\det(A)$ y los determinantes de las matrices sustituidas $\det(A_i(b))$, presentando los cocientes analíticos de Cramer y la solución única resultante.
- **Punto de inicio:** Ruta: Stack Index 0 (`Ctrl+1`), Selector de método: Botón `"Regla de Cramer"`.
- **Condiciones previas:** El sistema ingresado en la cuadrícula debe ser estrictamente cuadrado en sus coeficientes (filas $m = n$ incógnitas, es decir, dimensiones $n \times (n+1)$ con la columna aumentada). Determinante $\det(A) \ne 0$.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección del método de resolución**
  - **Interacción:** El usuario hace clic en el botón `"Regla de Cramer"` en la barra de métodos.
  - **Componente:** `self.cramer_method_btn` (`QPushButton` con ID `modeToggle`) en [`LinearSystemsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L97).
  - **Comportamiento visual:**
    - *Colores y Tokens:* `cramer_method_btn` pasa a estado checked (fondo elevado, texto resaltado). `gauss_method_btn` se desmarca automáticamente por exclusión en `QButtonGroup`.
    - *Textos y Microcopia:* Botón: `"Regla de Cramer"`.

- **Paso 02: Ingreso o verificación de la matriz cuadrada $n \times n$**
  - **Interacción:** El usuario edita la matriz asegurando que el número de filas equivalga al número de columnas de coeficientes (ej. $3 \times 4$ aumentada: 3 ecuaciones, 3 incógnitas y columna $b$).
  - **Componente:** [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1).
  - **Comportamiento visual:**
    - La cuadrícula conserva los valores introducidos sin recargar.

- **Paso 03: Ejecución de Cramer**
  - **Interacción:** El usuario hace clic en `"Resolver sistema"`.
  - **Componente:** `self.solve_btn` disparando el método interno `_solve_with_cramer(augmented)`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El carrusel de pasos se llena con el cálculo de determinantes. El Dashboard lateral se formatea para el despliegue específico de la Regla de Cramer.
    - *Colores y Tokens:* El dashboard adopta `color-feedback-success` (`#81B29A`) indicando solución única.
    - *Textos y Microcopia:* 
      - Dashboard: despliega la tarjeta con $\det(A)$, cada matriz $A_i(b)$ con su respectivo determinante $\det(A_i(b))$ y las fracciones finales simplificadas:
        $$x_i = \frac{\det(A_i(b))}{\det(A)}$$
      - Checklist: comprobación por sustitución exacta en las ecuaciones originales.

- **Paso 04: Trazabilidad en el carrusel de Cramer**
  - **Interacción:** El usuario avanza con `"Siguiente"` en el carrusel.
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32).
  - **Comportamiento visual:**
    - *Paso 0:* Muestra la matriz de coeficientes $A$ y el valor de $\det(A)$ en notación de libro.
    - *Pasos subsiguientes ($1$ a $n$):* Muestra cada matriz $A_i(b)$ en la que la columna $i$-ésima fue reemplazada por el vector $b$, destacando el valor del determinante de columna obtenido.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Matriz de coeficientes rectangular ($m \ne n$, ej. $2 \times 3$ coeficientes) | [`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80) vía `display_notice` | El carrusel de pasos se vacía (`set_steps([])`). El dashboard muestra un panel de aviso con fondo informativo tenue. | **Título:** `"Regla de Cramer"`<br>**Cuerpo:** `"La Regla de Cramer exige un sistema n×n: la matriz de coeficientes A es m×k. Hace falta el mismo número de ecuaciones y de incógnitas."` | Conmutar al método `"Gauss-Jordan"` o ajustar las dimensiones de la matriz agregando/eliminando filas/columnas. |
| Matriz singular ($\det(A) = 0$) | [`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80) vía `display_notice` | Carrusel se vacía. El dashboard reemplaza la solución por el aviso de singularidad. | **Título:** `"Regla de Cramer"`<br>**Cuerpo:** Explicación detallada: `"det(A) = 0. La matriz es singular; el sistema no tiene solución única y Cramer no es aplicable."` | Utilizar Gauss-Jordan para determinar si el sistema es incompatible (SI) o indeterminado (SCI). |
| Discrepancia dimensional en vector $b$ | [`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80) | Panel de aviso de incompatibilidad dimensional. | Mensaje de excepción formateado capturado de `DimensionMismatchError`. | Revisar la columna de términos independientes. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Selector de Método (`solver_group`)
- **Estado Normal / Inactivo:** Botón no presionado, fondo sutil `color-surface-inner` (`#242028`), texto `color-text-primary`.
- **Estado Checked (Activo):** Borde y fondo realzados con `color-interactive-idle` (`#98C1D9`), tipografía en negrita.
- **Hover:** Transición cromática suave con cursor de mano.

#### B. Tarjeta de Desglose de Cramer en el Dashboard
- **Empty State:** Oculta hasta que se ejecuta la resolución con éxito.
- **Active State:** Muestra en formato vertical de alta legibilidad cada variable $x_1, x_2, \dots, x_n$ con su cociente fraccionario expandido.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #5 - Prevención de errores]:** Si la matriz actual en la cuadrícula es rectangular (ej. $2 \times 4$), el botón `"Regla de Cramer"` permanece completamente interactivo y permite hacer clic en `"Resolver sistema"`. Sería cognitivamente superior deshabilitar visualmente el botón `"Regla de Cramer"` con un tooltip preventivo (*"Requiere matriz cuadrada $n \times n$"*) cuando las dimensiones no coincidan.
2. **[Nielsen #2 - Correspondencia entre el sistema y el mundo real]:** Cuando $\det(A) = 0$, el aviso simplemente indica que Cramer no aplica, pero no ofrece un botón directo de acción rápida (CTA) que diga: *"[ Cambiar a Gauss-Jordan para clasificar ]"*.

---

## [SEL_FLUJO_03] - Carga y Verificación de Casos Académicos Preset

### 1. Metadatos Técnicos
- **Objetivo:** Cargar en un solo clic matrices preconfiguradas que ejemplifican los diferentes teoremas y clasificaciones del álgebra lineal (Solución única, Infinitas soluciones, Sin solución y Cramer 3×3), ejecutando la resolución inmediata para demostración pedagógica.
- **Punto de inicio:** Ruta: Stack Index 0 (`Ctrl+1`), panel lateral `"Casos de prueba"`.
- **Condiciones previas:** Vista de Sistemas Lineales cargada.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección del caso de prueba**
  - **Interacción:** El usuario hace clic en cualquiera de los botones de preajuste:
    - `"I · Solución única"` ([`load_sample_case1`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L336))
    - `"II · Infinitas soluciones"` ([`load_sample_case2`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L346))
    - `"III · Sin solución"` ([`load_sample_case3`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L356))
    - `"IV · Cramer 3×3"` ([`load_cramer_sample`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L365))
  - **Componente:** Botones `btn_case1`, `btn_case2`, `btn_case3`, `btn_cramer` con clase `secondaryAction`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La cuadrícula [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) se redimensiona automáticamente y se puebla con la matriz del caso.
    - *Ejecución reactiva:* El sistema invoca automáticamente `solve_system()`, actualizando simultáneamente el carrusel de pasos y el Dashboard de resultados sin requerir un segundo clic.
    - *Textos y Microcopia:* 
      - Caso I: Carga matriz $3 \times 4$. Solución única $x=(1, 1, 2)$ (o valores correspondientes). Badge verde SCD.
      - Caso II: Carga matriz $3 \times 4$ con filas linealmente dependientes. Badge ámbar SCI con desglose paramétrico.
      - Caso III: Carga matriz $2 \times 3$ inconsistente. Badge rojo SI con fila contradictoria.
      - Caso IV: Conmuta el selector de método a `"Regla de Cramer"`, carga matriz $3 \times 4$ y muestra la solución por determinantes $x=(4, -2, 3)$.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Sobrescritura no deseada de una matriz personalizada | [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) | Los datos previos se reemplazan inmediatamente sin diálogo de advertencia. | Ninguna microcopia de advertencia previa. | No existe botón de deshacer; el usuario debe reingresar manualmente sus datos. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Botones de Casos Preset (`btn_case1` a `btn_case4`)
- **Normal:** Fondo transparente o semielevado con borde `color-interactive-idle` (`#98C1D9`).
- **Hover:** Fondo con realce interactivo, cursor de mano.
- **Focus:** Contorno activo accesible.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #3 - Control y libertad del usuario]:** La carga de un preset sobrescribe inmediatamente cualquier dato que el usuario haya escrito en la cuadrícula sin preguntar: *"¿Deseas reemplazar la matriz actual?"*.
2. **[Nielsen #1 - Visibilidad del estado]:** Los botones preset no indican cuál es el caso actualmente cargado (no son botones tipo toggle ni marcan un indicador visual persistente de selección activa).

---

## [SEL_FLUJO_04] - Asistente de Modelos Aplicados (Química, Leontief, Dieta Cambridge, Redes de Flujo)

### 1. Metadatos Técnicos
- **Objetivo:** Modelar problemas del mundo real basados en sistemas lineales (balanceo de reacciones químicas, equilibrio económico de Leontief, optimización nutricional y flujo vehicular en redes de un solo sentido) mediante formularios especializados que construyen y resuelven automáticamente la matriz aumentada sin requerir planteamiento manual.
- **Punto de inicio:** Ruta: Stack Index 0 (`Ctrl+1`), botón `"V · Aplicaciones"` que despliega [`AppliedModelsPanel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/applied_models_panel.py#L93).
- **Condiciones previas:** Módulo de sistemas lineales visible.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Apertura del panel de aplicaciones**
  - **Interacción:** El usuario hace clic en el botón `"V · Aplicaciones"`.
  - **Componente:** `self.applications_toggle` en [`LinearSystemsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/linear_systems_view.py#L157).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor [`AppliedModelsPanel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/applied_models_panel.py#L93) conmuta su visibilidad de `hidden` a `visible` desplegándose bajo la caja de muestras.
    - *Textos y Microcopia:* Título del panel: `"Aplicaciones de SEL"`. Cuatro botones de modo: `"Química"`, `"Leontief"`, `"Dieta"`, `"Tráfico"`. Etiqueta inferior informativa: `"Elige una aplicación y calcula. La matriz aumentada se carga sola."`.

- **Paso 02: Selección de modo y llenado de formulario**
  - **Subflujo A: Balanceo Químico**
    - Usuario selecciona `"Química"`.
    - Formulario muestra campos: `chemicalReactants` (placeholder/default: `"C3H8 + O2"`) y `chemicalProducts` (default: `"CO2 + H2O"`).
    - Clic en `"Balancear reacción"`.
    - La matriz aumentada de balance atómico se genera sola, se carga en `DynamicMatrixGrid`, se resuelve con Gauss-Jordan y la etiqueta de resultado muestra la ecuación balanceada con los coeficientes estequiométricos resaltados en color dorado/ámbar (`color-accent-warning` `#E9C46A`):
      $$\mathbf{1} \text{ C}_3\text{H}_8 + \mathbf{5} \text{ O}_2 \rightarrow \mathbf{3} \text{ CO}_2 + \mathbf{4} \text{ H}_2\text{O}$$
  - **Subflujo B: Modelo de Leontief**
    - Usuario selecciona `"Leontief"`.
    - Formulario muestra campo `leontiefConsumption` (default: `"0, 0.4, 0.6; 0.6, 0.1, 0.2; 0.4, 0.5, 0.2"`).
    - Botón secundario `"Carbón, electricidad y acero"` para cargar el caso de estudio.
    - Clic en `"Precios de equilibrio"`.
    - Se resuelve $(I - C)p = 0$, cargando la matriz aumentada en la cuadrícula y mostrando en el label los precios exactos en fracciones y su aproximación decimal a dos dígitos.
  - **Subflujo C: Dieta Cambridge**
    - Usuario selecciona `"Dieta"`.
    - Lectura de requerimientos nutricionales fijos (proteínas, carbohidratos, grasa) y alimentos (leche descremada, harina de soya, suero).
    - Clic en `"Resolver dieta Cambridge"`.
    - Se resuelve la mezcla exacta y se muestra el desglose de unidades y gramos por ingrediente.
  - **Subflujo D: Red de Tráfico de Baltimore**
    - Usuario selecciona `"Tráfico"`.
    - Red de calles de un solo sentido con conservación de flujo en nodos.
    - Clic en `"Analizar red de Baltimore"`.
    - Carga la matriz de balance de nodos y calcula los rangos válidos con restricciones de no-negatividad ($x_i \ge 0$).

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Sintaxis química inválida (fórmulas mal escritas, elementos inexistentes, paréntesis desbalanceados) | `self.result_label` en [`AppliedModelsPanel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/applied_models_panel.py#L332) | El texto de resultado cambia inmediatamente a color `color-feedback-error` (`#EE6C4D`). No se actualiza la cuadrícula. | Mensaje de excepción exacto capturado de `ChemicalFormulaError` (ej. `"Elemento desconocido: Xz"`, `"Sintaxis inválida en reactivos"`). | Corregir la cadena en el campo de texto y volver a pulsar `"Balancear reacción"`. |
| Matriz de consumo de Leontief con formato incorrecto o columnas que no suman 1 | `self.result_label` en [`AppliedModelsPanel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/applied_models_panel.py#L332) | Texto en color `color-feedback-error` (`#EE6C4D`). | `"Escribe la matriz de consumo, con una fila entre cada punto y coma."` o aviso de columnas no estocásticas. | Revisar y corregir los coeficientes en el campo de texto. |
| Reacción química imposible o linealmente inconsistente | `self.result_label` en [`AppliedModelsPanel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/applied_models_panel.py#L332) | Texto en color rojo de error. | Mensaje de resumen de inconsistencia: no existen coeficientes enteros positivos que balanceen la ecuación. | Verificar los reactivos y productos químicos introducidos. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Botón Desplegable `"V · Aplicaciones"`
- **Estado Normal:** Botón secundario con texto `"V · Aplicaciones"`.
- **Estado Toggle:** Alterna la propiedad de visibilidad del panel (`setVisible(not isVisible())`).

#### B. Formularios de Aplicaciones (`QStackedWidget`)
- **Navegación:** Controlada por botones de modo tipo segmentado (`chemicalMode`, `leontiefMode`, `dietMode`, `trafficMode`).
- **Campos de Texto (`QLineEdit` con `_FIELD_STYLE`):**
  - Fondo: `color-surface-inner` (`#242028`).
  - Borde: `1px solid #98C1D9` (`color-interactive-idle`).
  - Tipografía: Monospace (`Fira Code`, 14pt).
  - Selección: Fondo `#98C1D9`, texto `#242028`.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado del sistema]:** El panel de aplicaciones se abre en el panel izquierdo desplazando verticalmente el layout. Dado que la matriz resultante se carga en la cuadrícula superior, el usuario debe desplazarse con scroll hacia arriba para ver la matriz aumentada cargada.
2. **[Nielsen #8 - Estética y claridad]:** En el modelo de Leontief, ingresar una matriz de $3 \times 3$ en un solo campo de texto plano de una sola línea (`QLineEdit`) mediante punto y coma (`"0, 0.4, 0.6; 0.6, 0.1, 0.2; ..."`) es extremadamente propenso a errores tipográficos y tiene muy baja legibilidad. Debería reemplazarse por una pequeña tabla interactiva o cuadrícula visual editable.
3. **[Nielsen #6 - Reconocimiento antes que recuerdo]:** En los modelos de Dieta y Tráfico, no hay campos editables; únicamente botones para resolver ejemplos fijos de la clase. El usuario no tiene affordance para ingresar su propia red de tráfico o sus propios alimentos personalizados.

---

## Resumen Ejecutivo de la Auditoría del Módulo 1

| Componente Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **Cuadrícula Aumentada $[A \mid b]$** | **9 / 10** | Navegación por teclado impecable, Ghosting fluido, barra divisoria de libro. | Falta de selector directo de dimensiones ($m \times n$). |
| **Carrusel de Pasos** | **9.5 / 10** | Notación matemática de libro en RichText, pivote resaltado en verde, heurística explicativa. | No permite saltar directamente a un paso intermedio arbitrario. |
| **Dashboard de Clasificación** | **9 / 10** | Distinción clara de variables libres (🔑), checklist de verificación con checkmarks verdes. | Falta exportación directa de resultados en un clic (PDF/LaTeX). |
| **Regla de Cramer** | **8.5 / 10** | Excelente desglose de determinantes columna y cocientes. | Debería bloquearse proactivamente si la matriz no es cuadrada. |
| **Asistente de Aplicaciones** | **7.5 / 10** | Balanceo químico y Leontief automáticos con gran valor pedagógico. | Entrada de matriz por texto en una sola línea; falta de interactividad en redes de flujo. |

---

*Fin del reporte técnico del Módulo 1.*


---

# Procede con la auditoría profunda y detallada del módulo: Módulo 2: Álgebra Matricial y Propiedades de Inversión (Parte 1: Flujos 01 a 04)

---

## [MAT_FLUJO_01] - Operaciones Binarias A ∘ B e Inspector de Producto Celda a Celda

### 1. Metadatos Técnicos
- **Objetivo:** Ejecutar operaciones binarias de álgebra matricial clásica ($A + B$, $A - B$, $A \cdot B$) con verificación dimensional automática en tiempo real, renderizado exacto de la matriz resultante $C$ en fracciones, y exploración interactiva celda a celda para auditar la sumatoria de productos parciales fila por columna ($C_{ij} = \sum_k A_{ik} B_{kj}$) con retroalimentación visual de resaltado simultáneo en los operandos de entrada.
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"A ∘ B"` (`binary_mode_btn`), componente de vista principal: [`MatrixOperationsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L110).
- **Condiciones previas:** Aplicación inicializada en la pestaña de Álgebra Matricial. Estado local con dos cuadrículas no aumentadas: Matriz $A$ ($2 \times 3$) y Matriz $B$ ($3 \times 2$). Operador seleccionado por defecto: Multiplicación (`×`). Ambas matrices con valores válidos (inicializados en `"0"` o predefinidos).

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección del operador binario (+, −, ×)**
  - **Interacción:** El usuario hace clic en uno de los tres botones selectores de operador ubicados verticalmente entre ambas matrices: `add_btn` (`+`), `sub_btn` (`−`) o `mul_btn` (`×`).
  - **Componente:** `QPushButton#opSelect` agrupados en `QButtonGroup` exclusivo (`self.op_group`) en [`MatrixOperationsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L250-L261).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La disposición espacial de tres columnas (`[Matriz A] [Operador] [Matriz B] = [Matriz C]`) se mantiene estable sin reflow.
    - *Colores y Tokens:* El botón seleccionado adopta fondo `color-interactive-idle` (`#98C1D9`) y texto `color-bg-base` (`#1A181B`). Los botones no seleccionados permanecen con fondo `color-surface-elevated` (`#564D65`) y borde tenue.
    - *Textos y Microcopia:* Glifos de gran tamaño: `+`, `−`, `×` (22pt, negrita).
    - *Feedback Reactivo:* Se invoca inmediatamente `_refresh_compatibility()`. Si la matriz actual es compatible para la operación seleccionada, el badge superior se tiñe de `color-feedback-success` (`#81B29A`); de lo contrario, pasa a `color-feedback-error` (`#EE6C4D`) y desactiva el botón de cálculo.

- **Paso 02: Edición matricial y ajuste dimensional**
  - **Interacción:** El usuario escribe coeficientes en las celdas de $A$ o $B$, o expande filas/columnas mediante los botones fantasma `+` (`ghost-cell`), o elimina filas/columnas mediante el menú contextual (clic derecho).
  - **Componente:** [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) (`self.grid_a` y `self.grid_b`) con celdas [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63).
  - **Comportamiento visual:**
    - *Colores y Tokens:* Al editar, cualquier entrada numérica válida mantiene el borde inferior tenue `color-interactive-disabled` (`#3A3642`), pasando a `color-text-primary` (`#E0FBFC`) durante el foco.
    - *Microcopia del Badge de Compatibilidad:* Se recalcula en cada cambio de texto (`matrixChanged`).
      - Para suma/resta compatible: `"✓ Dimensiones compatibles para suma/resta: (r×c) = (r×c)"`.
      - Para producto compatible: `"✓ Dimensiones compatibles para producto: (m×n) · (n×p) = (m×p)"`.
      - Para dimensiones incompatibles: `"✕ Dimensiones incompatibles: Columnas de A (ca) ≠ Filas de B (rb). El producto A (m×n) · B (n×p) exige que las columnas de A igualen las filas de B."`.

- **Paso 03: Disparo del cálculo matricial**
  - **Interacción:** El usuario pulsa el botón `"▶ Calcular"` en la barra de herramientas superior (`header_compute_btn`) o en la barra de acciones inferior (`compute_btn`).
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La tarjeta de `Matriz C` ([`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1)) dibuja instantáneamente la matriz producto o suma/resta.
    - *Colores y Tokens:* La matriz resultante se dibuja con tipografía Monospace (`Fira Code`, 12pt negrita), corchetes vectoriales cerrados en `color-text-primary` (`#E0FBFC`) y fracciones apiladas en renderizado de libro.
    - *Textos y Microcopia:* 
      - En producto: Las celdas de $C$ se vuelven clickeables con cursor `PointingHandCursor`. La tarjeta inferior del inspector muestra: `"Producto calculado con tres bucles anidados. Pulsa una celda de C para inspeccionar Cᵢⱼ = Σₖ Aᵢₖ · Bₖⱼ."`.
      - En suma/resta: El inspector muestra `"Suma elemento a elemento: Cᵢⱼ = Aᵢⱼ + Bᵢⱼ."` o `"Resta elemento a elemento: Cᵢⱼ = Aᵢⱼ − Bᵢⱼ."`.
      - La tarjeta inferior `"Propiedades de la matriz y de la transpuesta"` despliega el análisis estructural de $A$ y de su relación con $B$ mediante badges estilizados de 22px (simétrica, antisimétrica, diagonal, ortogonal, identidades de la transpuesta).

- **Paso 04: Inspección analítica celda a celda (Inspector de Producto)**
  - **Interacción:** El usuario hace clic sobre una celda específica de la matriz resultado $C$ (ej. fila 1, columna 2: $C_{1,2}$).
  - **Componente:** [`BookMatrixWidget.cellClicked`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1) conectado al manejador `_on_result_cell_clicked` en [`MatrixOperationsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L1093).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Las cuadrículas de entrada se iluminan coordinadamente:
      - En `Matriz A`: Toda la fila seleccionada (fila $i$) se resalta en verde tenue (`QLineEdit[highlighted="true"]`, fondo `rgba(129, 178, 154, 0.32)` con borde inferior `#81B29A`).
      - En `Matriz B`: Toda la columna seleccionada (columna $j$) se resalta exactamente con el mismo tono.
      - En `Matriz C`: La celda $(i, j)$ dibuja un recuadro de selección activo.
    - *Textos y Microcopia:* La tarjeta del Inspector se actualiza mostrando la fórmula formal y el desglose de productos parciales:
      ```text
      C_1,2 = A_1,1·B_1,2 + A_1,2·B_2,2 + A_1,3·B_3,2 = (1)·(8) + (2)·(10) + (3)·(12) = 64
      A_11·B_12 = (1)·(8) = 8
      A_12·B_22 = (2)·(10) = 20
      A_13·B_32 = (3)·(12) = 36
      ```

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Entrada no numérica en alguna celda de $A$ o $B$ (ej. `x`, `2..1`, espacios) | Celda [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) y Badge Superior | La celda activa aplica clase CSS `matrix-cell-error` (fondo rojizo `rgba(238, 108, 77, 0.12)` y borde inferior rojo `2px solid #EE6C4D`). El badge superior adopta fondo rojo `color-feedback-error`. El botón `"▶ Calcular"` se deshabilita (`disabled=True`). | **Badge:** `"✕ Hay celdas no numéricas. Corrige las entradas marcadas."`<br>**Tooltip del botón:** `"✕ Hay celdas no numéricas. Corrige las entradas marcadas."` | El usuario borra o corrige los caracteres en la celda marcada. La validación se restablece automáticamente en `textChanged`. |
| Dimensiones incompatibles para producto ($c_A \ne r_B$) | Badge Superior y Botón de Acción | El badge adopta `color-feedback-error` (`#EE6C4D`). Los botones `"▶ Calcular"` se deshabilitan. Si ya había un resultado previo, se limpia la matriz $C$. | **Badge:** `"✕ Dimensiones incompatibles: Columnas de A (ca) ≠ Filas de B (rb). El producto A (m×n) · B (n×p) exige que las columnas de A igualen las filas de B."` | Modificar las dimensiones agregando/eliminando filas en $B$ o columnas en $A$ hasta satisfacer $c_A = r_B$, o cargar el preset `"Ejemplo 2×3 · 3×2"`. |
| Dimensiones incompatibles para suma o resta ($(r_A, c_A) \ne (r_B, c_B)$) | Badge Superior y Botón de Acción | Badge en rojo `#EE6C4D`. Botón `"▶ Calcular"` deshabilitado. | **Badge:** `"✕ Dimensiones incompatibles: A es ra×ca y B es rb×cb. La suma/resta exige matrices de idénticas dimensiones m×n."` | Igualar las dimensiones de ambas matrices usando los botones `+` o borrando filas/columnas. |
| Excepción matemática inesperada o desbordamiento fraccionario | Modal de Error [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L843) | Cuadro de diálogo modal temático con icono crítico (`QMessageBox.Critical`), fondo `#564D65` y botón con borde Powder Blue. | **Título:** `"Error matemático"`<br>**Cuerpo:** Detalle textual de la excepción generada por el motor. | Botón `"OK"` que cierra el diálogo y preserva el estado de las cuadrículas para corrección. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Selector de Operaciones (`add_btn`, `sub_btn`, `mul_btn`)
- **Normal / Inactivo:** Fondo `color-surface-elevated` (`#564D65`), texto `color-text-primary` (`#E0FBFC`), borde `color-interactive-idle` (`#98C1D9`). Dimensiones mínimas: $52 \times 44\text{ px}$.
- **Hover:** Fondo `color-interactive-idle` (`#98C1D9`), texto `color-bg-base` (`#1A181B`).
- **Checked (Activo):** Fondo `#98C1D9`, texto `#1A181B`, borde firme.
- **Focus:** Contorno accesible de navegación por teclado.

#### B. Botones de Acción de Cálculo (`compute_btn` y `header_compute_btn`)
- **Habilitado (Ready):** Fondo `color-feedback-success` (`#81B29A`), texto `color-bg-base` (`#1A181B`), cursor `PointingHandCursor`.
- **Hover:** Fondo iluminado `#93C4AE`, realce de elevación.
- **Disabled:** Fondo `color-interactive-disabled` (`#3A3642`), texto atenuado `#A8A3B2`, borde inactivo. Cursor de bloqueo, clics interceptados. Tooltip descriptivo de la causa de bloqueo.

#### C. Matriz Resultado C ([`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1))
- **Empty State:** Cuadro en reposo sin corchetes ni números; al inicializarse o pulsar `"Limpiar"`, no renderiza elementos gráficos.
- **Active State (Modo Multiplicación):** Renderizado de libro completo, cursor de mano al posarse sobre celdas individuales, respuesta inmediata a clics para inspección.
- **Active State (Modo Suma / Resta):** Celdas no clickeables (`clickable=False`), cursor estándar de flecha.

#### D. Tarjeta del Inspector de Producto
- **Empty State:** Label en reposo con tipografía Monospace (22px): `"Calcula un producto A · B y pulsa una celda de C para ver la fila de A, la columna de B y la sumatoria de productos parciales."`.
- **Active State:** Texto estructurado con la fórmula formal del elemento seleccionado y la lista vertical de sumandos en aritmética exacta.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado]:** En matrices de gran orden (ej. $5 \times 5$), al hacer clic en una celda de $C$ para inspeccionarla, no hay un indicador textual prominente en la cabecera de la matriz resultante que resalte las coordenadas activas (ej. un badge tipo `"Inspeccionando C[2, 3]"`). El usuario depende exclusivamente de leer el texto inferior del inspector.
2. **[Nielsen #7 - Flexibilidad y eficiencia de uso]:** Si el usuario se encuentra en modo multiplicación ($2 \times 3 \cdot 3 \times 2$) y conmuta a suma (`+`), la interfaz se bloquea inmediatamente en rojo porque las dimensiones son diferentes. No existe un botón de ayuda contextual rápida o atajo (ej. *"[ Ajustar B a dimensiones de A ]"*), obligando a modificar manualmente las filas y columnas.
3. **[Nielsen #4 - Consistencia y estándares]:** En la cabecera coexisten dos botones idénticos `"▶ Calcular"`: uno en la barra de herramientas superior y otro debajo de las matrices. Aunque favorece la accesibilidad en pantallas con scroll, puede generar redundancia cognitiva si no se especifica su sincronización.

---

## [MAT_FLUJO_02] - Multiplicación por Escalar (k · A)

### 1. Metadatos Técnicos
- **Objetivo:** Escalar homogéneamente todas las entradas de una matriz $A$ de dimensiones arbitrarias $m \times n$ mediante un factor escalar $k \in \mathbb{R}$ (admitiendo enteros, fracciones irreducibles o decimales), visualizando el producto exacto $k \cdot A$ y contrastando la propiedad de conmutación de la transpuesta escalar $(k \cdot A)^T = k \cdot A^T$.
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"k · A"` (`scalar_mode_btn`), página índice 1 de `self.pages`.
- **Condiciones previas:** Matriz $A$ inicializada en la cuadrícula de escalamiento (`grid_scalar`) con dimensiones base $2 \times 2$. Campo de entrada de escalar $k$ (`scalar_edit`) poblado por defecto con `"2"`.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Conmutar al modo Escalar**
  - **Interacción:** El usuario pulsa el botón `"k · A"` en la barra de herramientas de modos.
  - **Componente:** `QPushButton#modeToggle` ([`scalar_mode_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L137)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* `self.pages` (`QStackedWidget`) conmuta a la página 1 (`_build_scalar_page`). Se despliega una tarjeta dedicada para el escalar $k$, un símbolo de producto central `·` en fuente grande (32px), la tarjeta de `Matriz A` y la tarjeta de `k · A`.
    - *Colores y Tokens:* `scalar_mode_btn` se activa con fondo `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* Título del card: `"Escalar k"`. Subtexto de ayuda: `"Entero, fracción o decimal"`. Título del resultado: `"k · A"`.

- **Paso 02: Ingreso y validación del escalar k**
  - **Interacción:** El usuario hace foco en el campo de texto `scalar_edit` e introduce un valor escalar (ej. `-3/4`, `0.5`, `7`).
  - **Componente:** `QLineEdit#scalarField` ([`scalar_edit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L294)) con fuente `Fira Code` (14pt, centrado).
  - **Comportamiento visual:**
    - *Colores y Tokens:* Al recibir foco, resalta su borde. La validación en `textChanged` verifica la conformabilidad mediante `parse_scalar()`.
    - *Microcopia del Badge:* Si el escalar es válido y las celdas de $A$ son correctas, el badge superior adopta verde: `"✓ Multiplicación escalar definida: k · A (m×n)"`.

- **Paso 03: Ajuste de coeficientes y dimensiones de la matriz A**
  - **Interacción:** El usuario edita celdas o agrega filas/columnas en `grid_scalar`.
  - **Componente:** [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) (`self.grid_scalar`).
  - **Comportamiento visual:** Las dimensiones se actualizan en el badge reactivamente sin restricciones de cuadratura (el escalamiento está definido para cualquier matriz $m \times n$).

- **Paso 04: Ejecución del escalamiento**
  - **Interacción:** El usuario pulsa `"▶ Calcular"`.
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)), invocando `_compute_scalar()`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1) (`scalar_result_view`) dibuja la matriz resultante de forma instantánea.
    - *Colores y Tokens:* Si $k = 0$, la matriz resultante muestra la matriz nula $O_{m \times n}$. Si $k$ es fraccionario, cada entrada se simplifica a su mínima expresión fraccionaria.
    - *Textos y Microcopia:* 
      - Inspector de producto: `"Cada celda se escala: Cᵢⱼ = (k) · Aᵢⱼ."`.
      - Tarjeta de propiedades: Despliega la verificación algebraica formal de $(k \cdot A)^T = k \cdot A^T$ junto con el análisis de simetría de la matriz escalada.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Escalar $k$ sintácticamente inválido (letras, división entre cero como `5/0`, símbolos) | Campo de texto `scalar_edit` y Badge Superior | El badge adopta inmediatamente `color-feedback-error` (`#EE6C4D`). El botón `"▶ Calcular"` se desactiva (`setEnabled(False)`). | **Badge:** `"✕ El escalar k no es un número válido (usa enteros, a/b o decimales)."` | Corregir la cadena en el campo de texto; la reactividad restaura el estado verde en cuanto se ingresa un valor analizable. |
| Campo escalar $k$ dejado en blanco | Badge Superior | El badge pasa a estado de error rojo y bloquea el botón de cálculo. | **Badge:** `"✕ El escalar k no es un número válido (usa enteros, a/b o decimales)."` | Escribir un número en el campo $k$. |
| Celdas con caracteres no numéricos en la matriz $A$ | Cuadrícula `grid_scalar` y Badge Superior | Las celdas erróneas aplican borde rojo `#EE6C4D`. El badge superior alerta del fallo en $A$. | **Badge:** `"✕ Hay celdas no numéricas en A."` | Corregir los coeficientes en la cuadrícula. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Campo de Escalar (`scalar_edit`)
- **Normal:** Fondo `color-surface-inner` (`#242028`), texto `color-text-primary` (`#E0FBFC`), borde `1px solid #98C1D9`. Ancho adaptado y texto centrado.
- **Focus:** Borde realzado, selección completa del texto existente.
- **Error:** Si el valor no parsea, el campo retiene el texto pero el badge global informa el bloqueo.

#### B. Matriz de Resultado Escalar (`scalar_result_view`)
- **Empty State:** Vacía antes del primer cálculo o tras pulsar limpiar.
- **Active State:** Despliegue estático de la matriz escalada (no clickeable).

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #5 - Prevención de errores]:** Si bien el campo escalar bloquea el botón global de cálculo cuando el texto es inválido (ej. `"abc"`), el propio `QLineEdit` de $k$ no cambia su borde a rojo como sí lo hacen las celdas de la cuadrícula matricial, provocando una inconsistencia visual dentro de la misma pantalla.
2. **[Nielsen #7 - Atajos y presets]:** No existen botones de acceso rápido para escalares canónicos frecuentes en ejercicios académicos, tales como $k = -1$ (matriz opuesta $-A$), $k = 0$ (anulación) o $k = 1/2$ (escalamiento unitario).

---

## [MAT_FLUJO_03] - Transposición e Identidades de la Transpuesta (Aᵀ, (Aᵀ)ᵀ = A, (kA)ᵀ, (A+B)ᵀ, (AB)ᵀ)

### 1. Metadatos Técnicos
- **Objetivo:** Calcular la matriz transpuesta $A^T$ intercambiando filas por columnas (mutando dimensiones de $m \times n$ a $n \times m$), demostrar visualmente el teorema de la doble transpuesta $(A^T)^T = A$, y validar celda a celda las propiedades algebraicas estructurales: simetría ($A^T = A$), antisimetría ($A^T = -A$), transpuesta del múltiplo escalar $(k \cdot A)^T = k \cdot A^T$, y transpuesta de operaciones binarias con una matriz asociada $B$ ($(A+B)^T = A^T + B^T$ y $(A \cdot B)^T = B^T A^T$).
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"Aᵀ"` (`transpose_mode_btn`), página índice 2 de `self.pages`.
- **Condiciones previas:** Cuadrícula de transposición (`grid_transpose`) inicializada en $2 \times 3$ con valores numéricos válidos. Campo auxiliar de escalar $k$ (`identity_scalar_edit`) inicializado en `"1"`. Botón toggle de inclusión de $B$ (`include_b_btn`) en estado no presionado.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Conmutar al modo Transposición**
  - **Interacción:** El usuario pulsa `"Aᵀ"` en la barra de herramientas.
  - **Componente:** `QPushButton#modeToggle` ([`transpose_mode_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L140)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La página despliega una secuencia horizontal unaria de tres tarjetas matriciales conectadas por flechas directas:
      `[Matriz A (m×n)]` $\rightarrow$ `[Aᵀ (n×m)]` $\rightarrow$ `[(Aᵀ)ᵀ = A (m×n)]`.
      Bajo la secuencia se despliega la barra de identidades auxiliares con el campo $k$ y el botón `"Incluir B en (A+B)ᵀ y (A·B)ᵀ"`.
    - *Colores y Tokens:* Las flechas de transición `→` se renderizan en color `color-interactive-idle` (`#98C1D9`, 28pt negrita).
    - *Textos y Microcopia:* Badge superior: `"✓ Transpuesta definida: A es 2×3  ⇒  Aᵀ es 3×2"`.

- **Paso 02: Configuración de parámetros de identidades (Escalar y Matriz B)**
  - **Interacción:** El usuario puede modificar el escalar $k$ en `identity_scalar_edit` y pulsar el botón toggle `"Incluir B en (A+B)ᵀ y (A·B)ᵀ"`.
  - **Componente:** `QLineEdit#scalarField` (`identity_scalar_edit`) y `QPushButton#modeToggle` (`include_b_btn`).
  - **Comportamiento visual:**
    - *Colores y Tokens:* Al pulsar `include_b_btn`, adopta estado checked en color `color-interactive-idle` (`#98C1D9`).
    - *Microcopia del Tooltip:* `"Usa la matriz B de la vista A ∘ B"`.

- **Paso 03: Ejecución de la transposición**
  - **Interacción:** El usuario pulsa `"▶ Calcular"`.
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)), ejecutando `_compute_transpose()`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* 
      - `transpose_result_view` dibuja $A^T$ invirtiendo filas y columnas (de $2 \times 3$ a $3 \times 2$).
      - `double_transpose_result_view` dibuja $(A^T)^T$ recuperando las dimensiones originales ($2 \times 3$) con valores exactamente idénticos a $A$.
    - *Textos y Microcopia:* 
      - Inspector de producto: Texto RichText que explica el teorema fundamental:
        `Transpuesta doble: (Aᵀ)ᵀ = A. A es m×n, Aᵀ es n×m, y (Aᵀ)ᵀ vuelve a ser m×n exactamente igual a A.`
      - Tarjeta de propiedades: Muestra la lista de comprobación completa en tarjetas de 22px:
        - `Simetría (Aᵀ = A)`: ✓ si cumple, ✗ si no cumple, o — si no aplica (cuando $A$ es rectangular).
        - `Antisimetría (Aᵀ = -A)`: Verificación del signo opuesto.
        - `(k·A)ᵀ = k·Aᵀ`: ✓ Cumple (siempre válida en $\mathbb{R}$).
        - Si $B$ está incluida: `(A+B)ᵀ = Aᵀ + Bᵀ` y `(A·B)ᵀ = Bᵀ·Aᵀ` comprobadas celda a celda.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Escalar auxiliar $k$ no numérico en la barra de identidades | Campo `identity_scalar_edit` y Badge Superior | El badge superior adopta fondo rojo `color-feedback-error`. El botón de cálculo se bloquea. | **Badge:** `"✕ El escalar k de la comprobación no es válido."` | Corregir o vaciar el campo $k$. |
| Entradas no válidas en la cuadrícula de $A$ | Cuadrícula `grid_transpose` y Badge Superior | Celdas afectadas se marcan con borde rojo. Badge en rojo. | **Badge:** `"✕ Hay celdas no numéricas en A."` | Corregir los coeficientes numéricos en $A$. |
| Matriz $B$ incompatible en dimensiones cuando se activa la comprobación $(A+B)^T$ o $(AB)^T$ | Tarjetas de Propiedades inferiores | Las tarjetas de identidades binarias marcan el estado en gris (`no_aplica`) o coral (`no_cumple`) explicando el desacople. | Detalle en tarjeta: `"No aplica: A (2×3) y B (2×2) tienen dimensiones incompatibles para la suma."` | Ir a la vista `A ∘ B` y ajustar las dimensiones de $B$ para que sean conformables con $A$. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Botón de Inclusión de B (`include_b_btn`)
- **Estado Unchecked:** Fondo transparente, borde `color-interactive-idle` (`#98C1D9`), texto `color-interactive-idle`.
- **Estado Checked:** Fondo `#98C1D9`, texto `#1A181B`, tipografía en negrita.
- **Hover:** Fondo con brillo translúcido `rgba(152, 193, 217, 0.28)`.

#### B. Visores de Transpuesta y Doble Transpuesta
- **Empty State:** Ocultos o vacíos antes de calcular.
- **Active State:** Presentación clara con alineación vertical perfecta en tipografía monospace, demostrando visualmente la equivalencia $A \equiv (A^T)^T$.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #2 - Correspondencia con el mundo real]:** Cuando el usuario marca `"Incluir B en (A+B)ᵀ y (A·B)ᵀ"`, la matriz $B$ no se visualiza en esta pantalla; el sistema toma de forma "invisible" la matriz que haya quedado configurada en la pestaña `A ∘ B`. Esto viola la heurística de visibilidad, ya que el usuario debe confiar ciegamente en qué valores tiene $B$ sin poder verla ni editarla aquí.
2. **[Nielsen #8 - Claridad y ergonomía]:** La secuencia horizontal de tres tarjetas matriciales (`A → Aᵀ → (Aᵀ)ᵀ`) requiere un ancho mínimo de pantalla considerable ($\ge 1200\text{ px}$). En pantallas de resolución modesta, las celdas se comprimen o generan scroll horizontal dentro de la tarjeta.

---

## [MAT_FLUJO_04] - Propiedades Distributiva y Asociativa Ternaria (A(B+C), (A+B)C, A(BC))

### 1. Metadatos Técnicos
- **Objetivo:** Auditar y comprobar de forma exhaustiva las leyes algebraicas ternarias del álgebra lineal sobre tres matrices arbitrarias $A$, $B$ y $C$: distributividad por la izquierda ($A \cdot (B + C) = A \cdot B + A \cdot C$), distributividad por la derecha ($(A + B) \cdot C = A \cdot C + B \cdot C$) y asociatividad del producto matricial ($A \cdot (B \cdot C) = (A \cdot B) \cdot C$), verificando la identidad elemento a elemento entre el Miembro Izquierdo (LHS) y el Miembro Derecho (RHS).
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"A · (B + C)"` (`distrib_mode_btn`), página índice 3 de `self.pages`.
- **Condiciones previas:** Tres cuadrículas dinámicas independientes disponibles en la vista: `grid_dist_a`, `grid_dist_b` y `grid_dist_c`. Selector de propiedad activo en `"A · (B + C) = A·B + A·C"` por defecto. Valores numéricos válidos en las tres matrices.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Conmutar al modo de Propiedades Ternarias**
  - **Interacción:** El usuario hace clic en el botón `"A · (B + C)"` en la barra de herramientas superior.
  - **Componente:** `QPushButton#modeToggle` ([`distrib_mode_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L143)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La página 3 despliega tres niveles de información:
      1. Barra superior de selección de propiedad algebraica.
      2. Fila horizontal con 3 cuadrículas editables (`Matriz A`, `Matriz B`, `Matriz C`).
      3. Fila de resultados comparativos: Tarjeta LHS = Tarjeta RHS.
      4. Tarjeta destacada de comprobación de equivalencia con texto de gran escala ($\ge 22\text{ px}$).
    - *Colores y Tokens:* El botón de la toolbar se activa con realce visual.

- **Paso 02: Selección de la propiedad a comprobar**
  - **Interacción:** El usuario pulsa una de las tres opciones en la barra de propiedades:
    - `"A · (B + C) = A·B + A·C"` (`dist_left_btn`, id 0)
    - `"(A + B) · C = A·C + B·C"` (`dist_right_btn`, id 1)
    - `"A · (B · C) = (A · B) · C"` (`dist_assoc_btn`, id 2)
  - **Componente:** `QButtonGroup` exclusivo (`self.dist_prop_group`) conectado al evento `_on_dist_prop_changed`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Los títulos de las tarjetas de resultado se renombran automáticamente:
      - Para id 0: `"LHS: A · (B + C)"` y `"RHS: A·B + A·C"`.
      - Para id 1: `"LHS: (A + B) · C"` y `"RHS: A·C + B·C"`.
      - Para id 2: `"LHS: A · (B · C)"` y `"RHS: (A · B) · C"`.
    - *Microcopia del Badge de Validación:* Se dispara `_distributive_compatibility()` validando la compatibilidad cruzada entre las dimensiones $(r_a, c_a)$, $(r_b, c_b)$ y $(r_c, c_c)$.
      - Si son compatibles: `"✓ Compatible para distributiva izquierda: A (ra×ca) · [B+C (rb×cb)] = A·B + A·C ⇒ (ra×cb)"`.
      - Si hay error: Explica con exactitud matemática qué condición de suma o producto se viola.

- **Paso 03: Carga rápida de preset o edición libre**
  - **Interacción:** El usuario puede pulsar el botón de preajuste `"Ejemplo A(B+C)"` (`sample_dist`), que carga automáticamente matrices $2 \times 2$ representativas y ejecuta el cálculo de inmediato.
  - **Componente:** `QPushButton#secondaryAction` ([`load_distributive_matrix_sample`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L1317)).
  - **Comportamiento visual:** Las tres cuadrículas se pueblan con matrices enteras válidas y el sistema calcula la comprobación sin requerir más acciones.

- **Paso 04: Ejecución del cálculo y verificación de la igualdad**
  - **Interacción:** El usuario pulsa `"▶ Calcular"`.
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)), invocando `_compute_distributive()`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* 
      - `dist_lhs_view` dibuja la matriz calculada para el miembro izquierdo.
      - `dist_rhs_view` dibuja la matriz calculada para el miembro derecho.
      - Ambas matrices quedan separadas por un gran signo `=` (`QLabel` de 32pt).
    - *Colores y Tokens:* 
      - Si las matrices son idénticas en todas sus celdas, la tarjeta destacada `dist_comparison_label` se tiñe con fondo verde translúcido (`rgba(129, 178, 154, 0.08)`), borde verde (`1px solid rgba(129, 178, 154, 0.35)`) y texto en `color-feedback-success` (`#81B29A`):
        ```text
        ✓   Distributiva izquierda:   A · (B + C)   =   A·B + A·C   (Coinciden exactamente)
        ```
    - *Textos y Microcopia:* 
      - Inspector de producto: Resume las dimensiones resultantes y la conclusión formal:
        ```text
        Comprobación distributiva por la izquierda:
        LHS = A · (B + C): Matriz 2×2
        RHS = (A · B) + (A · C): Matriz 2×2
        ¿Ambas matrices son idénticas elemento a elemento? ✓ SÍ, coinciden exactamente
        ```
      - Tarjeta de propiedades: Muestra el informe estructural derivado de `analyze_matrix(A, B, C=C)`.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Incompatibilidad de suma interna en distributiva izquierda: $(r_B, c_B) \ne (r_C, c_C)$ | Badge Superior y Botón de Acción | Badge en rojo `color-feedback-error`. Botón `"▶ Calcular"` deshabilitado. | **Badge:** `"✕ Dimensiones incompatibles para B + C: B es rb×cb y C es rc×cc. Para sumarse, B y C deben tener idénticas dimensiones."` | Ajustar filas y columnas de $B$ o $C$ hasta que coincidan exactamente en tamaño. |
| Incompatibilidad de producto exterior en distributiva izquierda: $c_A \ne r_B$ | Badge Superior y Botón de Acción | Badge en rojo. Botón de cálculo deshabilitado. | **Badge:** `"✕ Dimensiones incompatibles para A · (B + C): Columnas de A (ca) ≠ Filas de (B+C) (rb). El producto exige que las columnas de A igualen las filas de B."` | Igualar las columnas de $A$ con las filas de $B$. |
| Incompatibilidad en propiedad asociativa: $c_A \ne r_B$ o $c_B \ne r_C$ | Badge Superior y Botón de Acción | Badge en rojo. Botón de cálculo deshabilitado. | **Badge:** `"✕ Incompatible para A · B: Columnas de A (ca) ≠ Filas de B (rb)."` o `"✕ Incompatible para B · C: Columnas de B (cb) ≠ Filas de C (rc)."` | Rectificar la cadena de dimensiones conformables ($m \times n$, $n \times p$, $p \times q$). |
| Entradas no numéricas en cualquiera de las tres matrices ($A$, $B$ o $C$) | Celdas afectadas y Badge Superior | Celdas con borde inferior rojo `#EE6C4D`. Badge en rojo. | **Badge:** `"✕ Hay celdas no numéricas en A, B o C. Corrige las entradas marcadas."` | Corregir las celdas marcadas con error. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Selector de Propiedad Ternaria (`dist_prop_group`)
- **Normal:** Botón tipo toggle con borde `color-interactive-idle` (`#98C1D9`), tipografía sans-serif (14pt).
- **Checked (Activo):** Fondo `#98C1D9`, texto `#1A181B`.
- **Hover:** Brillo tenue con cursor de mano.

#### B. Tarjeta Comparativa Destacada (`dist_comparison_label`)
- **Empty State:** Vacía antes del cálculo.
- **Success State:** Caja destacada en tipografía grande (22px), fondo sage translúcido, borde sutil y marca `✓`.
- **Fail State:** Caja con fondo coral translúcido, borde de error y marca `✗`.

#### C. Cuadrículas de Entrada ($A$, $B$, $C$)
- Disposición en tres columnas en paralelo dentro de la misma vista, con títulos claros: `"Matriz A"`, `"Matriz B"`, `"Matriz C"`.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #8 - Estética y sobrecarga cognitiva]:** Alojar tres cuadrículas matriciales completas ($A, B, C$) más dos cuadrículas de resultados (LHS, RHS) en una única pantalla produce una densidad informativa muy alta. En resoluciones de $1366 \times 768$ (laptop estándar), se genera una cantidad excesiva de scroll vertical para contrastar la entrada con el resultado.
2. **[Nielsen #7 - Flexibilidad y presets]:** Solo existe el botón `"Ejemplo A(B+C)"` configurado para distributiva izquierda. No existen botones de ejemplo rápido dedicados para distributiva derecha ni para la propiedad asociativa, obligando al usuario a configurar manualmente matrices compatibles para la asociatividad en cadena.
3. **[Nielsen #1 - Visibilidad de pasos intermedios]:** A diferencia del módulo de sistemas lineales o de inversión, la comprobación distributiva no incluye un carrusel de pasos algorítmicos intermedios (ej. no muestra la matriz intermedia $B+C$ ni las matrices parciales $AB$ y $AC$ antes de sumarlas; salta directamente al resultado final de ambos lados).

---

## Resumen Ejecutivo de la Auditoría del Módulo 2 (Parte 1: Flujos 01 a 04)

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[MAT_FLUJO_01] Operaciones Binarias y Clicks en C** | **9.5 / 10** | La interacción de hacer clic en una celda de $C$ para iluminar en verde la fila de $A$ y la columna de $B$ es sobresaliente a nivel pedagógico y cognitivo. | Falta un indicador visual destacado en la cabecera que recuerde la celda actualmente inspeccionada. |
| **[MAT_FLUJO_02] Multiplicación Escalar ($k \cdot A$)** | **9 / 10** | Simplicidad de uso impecable, validación de fracciones exactas y comprobación de $(kA)^T$. | El campo de entrada de $k$ no aplica el borde rojo de error cuando tiene sintaxis errónea. |
| **[MAT_FLUJO_03] Transposición e Identidades ($A^T$)** | **8.5 / 10** | Demostración visual directa de $(A^T)^T = A$ en cadena de tres matrices conectadas por flechas. | La inclusión de la matriz $B$ es opaca: se toma de otra pestaña sin visualización ni edición in situ. |
| **[MAT_FLUJO_04] Propiedades Distributiva y Asociativa** | **8.5 / 10** | Comparación LHS vs RHS con tipografía destacada de 22px y validación estricta de conformabilidad. | Alta saturación visual con 5 matrices en la misma vista; carece de vista de matrices intermedias ($B+C, AB, AC$). |

---

*Fin del reporte técnico de los Flujos 01 a 04 del Módulo 2.*


---

# Procede con la auditoría profunda y detallada del módulo: Módulo 2: Álgebra Matricial y Propiedades de Inversión (Parte 2: Flujos 05 a 07)

---

## [MAT_FLUJO_05] - Inversión de Matrices por Reducción de [A | Iₙ]

### 1. Metadatos Técnicos
- **Objetivo:** Calcular la matriz inversa $A^{-1}$ para una matriz cuadrada $A \in \mathbb{R}^{n \times n}$ mediante el algoritmo de eliminación de Gauss-Jordan aplicado sobre la matriz aumentada $[A \mid I_n]$ en aritmética exacta de fracciones, desplegar el carrusel de transformaciones elementales resaltando pivotes, contrastar el checklist bilateral $A \cdot A^{-1} = I_n$ y $A^{-1} \cdot A = I_n$, o diagnosticar y justificar la singularidad cuando $\det(A) = 0$.
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"A⁻¹ (Inversa)"` (`inverse_mode_btn`), página índice 4 de `self.pages`.
- **Condiciones previas:** Matriz $A$ cuadrada ($n \times n$). Por defecto inicializada en $2 \times 2$ no aumentada en `grid_inverse`.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Conmutar al modo de Inversión Matricial**
  - **Interacción:** El usuario hace clic en el botón `"A⁻¹ (Inversa)"` en la barra de herramientas de modos.
  - **Componente:** `QPushButton#modeToggle` ([`inverse_mode_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L147)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* `self.pages` conmuta a la página 4 (`_build_inverse_page`). Se visualiza la disposición unaria: `[Matriz A]` $\rightarrow$ `[A⁻¹]`, la etiqueta de verificación de identidad `inverse_check_label` y el carrusel de pasos algorítmicos [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`inverse_stepper`).
    - *Colores y Tokens:* `inverse_mode_btn` se resalta en `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* 
      - Título de entrada: `"Matriz A"`. Título del visor resultado: `"A⁻¹"`.
      - Label de checklist inicial: `"Calcula para comprobar A · A⁻¹ = Iₙ y ver la reducción de [A | Iₙ]."`.
      - Badge superior: `"✓ Inversa definida para A de orden 2×2. Se reducirá [A | Iₙ] hasta [Iₙ | A⁻¹]."`.

- **Paso 02: Ingreso de coeficientes o carga de muestra**
  - **Interacción:** El usuario escribe valores en `grid_inverse` o pulsa el botón de preset `"Ejemplo A⁻¹"` (`sample_inverse`).
  - **Componente:** [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) o botón `sample_inverse` ([`load_inverse_sample`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L1306)).
  - **Comportamiento visual:** Al pulsar `"Ejemplo A⁻¹"`, se carga la matriz $3 \times 3$ de la Sesión 10:
    $$\begin{pmatrix} 0 & 1 & 2 \\ 1 & 0 & 3 \\ 4 & -3 & 8 \end{pmatrix}$$
    y se ejecuta automáticamente el cálculo.

- **Paso 03: Ejecución de la inversión**
  - **Interacción:** El usuario pulsa `"▶ Calcular"`.
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)), invocando `_compute_inverse()`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* 
      - [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1) (`inverse_result_view`) dibuja la matriz inversa $A^{-1}$ con fracciones simplificadas.
      - `inverse_stepper` se carga con la traza completa de pasos de $[A \mid I_n] \sim [I_n \mid A^{-1}]$.
    - *Colores y Tokens:* 
      - Badge superior en verde `color-feedback-success` (`#81B29A`): `"✓ Matriz invertible n×n. A · A⁻¹ = I_n."`.
      - La etiqueta `inverse_check_label` despliega en tipografía grande (22px) dos renglones verdes con checkmarks:
        ```text
        ✓  A · A⁻¹ = I_3
        ✓  A⁻¹ · A = I_3
        ```
    - *Textos y Microcopia:* 
      - Inspector de producto: `"Inversión por Gauss-Jordan sobre [A | Iₙ]. El bloque derecho de la forma reducida es A⁻¹. Recorre el carrusel para ver cada operación elemental."`.
      - Tarjeta de propiedades: Muestra que $A$ es no singular y verifica identidades estructurales.

- **Paso 04: Exploración del procedimiento en el carrusel de inversión**
  - **Interacción:** El usuario pulsa `"Siguiente"` y `"Anterior"` en `inverse_stepper`.
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`self.inverse_stepper`).
  - **Comportamiento visual:**
    - Muestra cada matriz aumentada intermedia $[A_k \mid B_k]$.
    - La celda del pivote activo se resalta en verde tenue `color-feedback-success` (`#81B29A`).
    - Las operaciones elementales se describen en notación de libro (ej. $F_1 \leftrightarrow F_2$, $F_3 \rightarrow F_3 - 4F_1$).

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Matriz $A$ no cuadrada ($m \ne n$, ej. $2 \times 3$) | Badge Superior y Botón de Acción | El badge adopta `color-feedback-error` (`#EE6C4D`). El botón `"▶ Calcular"` se desactiva (`setEnabled(False)`). La matriz $A^{-1}$ se limpia. | **Badge:** `"✕ La inversa solo está definida para matrices cuadradas (n×n). A es m×n."`<br>**Tooltip del botón:** `"✕ La inversa solo está definida para matrices cuadradas (n×n). A es m×n."` | Ajustar filas o columnas en `grid_inverse` hasta que $m = n$ (usando los botones `+` o borrando filas/columnas con clic derecho). |
| Matriz singular ($\det(A) = 0$, rango deficiente) | Badge Superior, `inverse_check_label` y `inverse_stepper` | El badge superior pasa a rojo `#EE6C4D`. `inverse_result_view` se limpia. `inverse_check_label` muestra mensaje de fallo en 22px rojo. `inverse_stepper` retiene los pasos hasta la fila nula. | **Badge:** `"✕ No se pudo invertir la matriz: la matriz es singular (det(A) = 0)."`<br>**Checklist:** `"✗ No se pudo invertir la matriz: la matriz es singular (det(A) = 0)."`<br>**Inspector:** `"La reducción de [A | Iₙ] no alcanzó [Iₙ | A⁻¹]. Recorre el carrusel: una fila de ceros en el bloque izquierdo prueba que A es singular."` | Explorar el carrusel para ubicar en qué paso surgió la fila de ceros o modificar coeficientes en $A$. |
| Celdas con valores no numéricos en $A$ | Cuadrícula y Badge Superior | Celdas afectadas muestran borde inferior rojo `#EE6C4D`. Badge en rojo. Botón de cálculo bloqueado. | **Badge:** `"✕ Hay celdas no numéricas en A."` | Corregir los coeficientes en la cuadrícula. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Cuadrícula de Entrada (`grid_inverse`)
- **Estado Normal:** Cuadrícula $n \times n$ no aumentada con celdas de edición rápida.
- **Validación Cuadrada:** Controlada por `_inverse_compatibility()`. Si el usuario agrega una columna sin fila (haciéndola $2 \times 3$), el estado se invalida proactivamente.

#### B. Tarjeta de Verificación Bilateral (`inverse_check_label`)
- **Empty State:** Texto informativo en gris: `"Calcula para comprobar A · A⁻¹ = Iₙ y ver la reducción de [A | Iₙ]."`.
- **Success State:** Dos bloques de 22px en verde con marcas `✓` para $A \cdot A^{-1} = I_n$ y $A^{-1} \cdot A = I_n$.
- **Error State:** Bloque de 22px en coral con marca `✗` explicando la singularidad.

#### C. Carrusel de Inversión (`inverse_stepper`)
- **Empty State:** Pasos vacíos (`0 de 0`), botones inactivos.
- **Active State:** Recorrido interactivo de la reducción de $[A \mid I_n]$ a $[I_n \mid A^{-1}]$ con pivotes resaltados.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado]:** En matrices singulares, la excepción adjunta la traza de pasos (`exc.tracer`) y el carrusel permite navegarla, lo cual es excelente; sin embargo, no hay un resaltado visual explícito sobre la fila de ceros en el carrusel para alertar al usuario del momento exacto del colapso del rango.
2. **[Nielsen #7 - Eficiencia de uso]:** La cuadrícula no incluye un botón de un clic para invertir la relación (cargar $A^{-1}$ en la posición de $A$ para comprobar $(A^{-1})^{-1} = A$ directamente en esta vista).

---

## [MAT_FLUJO_06] - Evaluación del Teorema de la Matriz Invertible (TMI)

### 1. Metadatos Técnicos
- **Objetivo:** Auditar una matriz cuadrada $A \in \mathbb{R}^{n \times n}$ evaluando simultáneamente las caracterizaciones lógicas equivalentes del Teorema de la Matriz Invertible (TMI), con énfasis pedagógico en las caracterizaciones de la cátedra: **\*c** ($n$ posiciones pivote / rango completo), **\*e** (columnas linealmente independientes en $\mathbb{R}^n$), **\*h** (columnas generan $\mathbb{R}^n$) y el criterio del determinante $\det(A) \ne 0$.
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"TMI"` (`tmi_mode_btn`), página índice 5 de `self.pages`.
- **Condiciones previas:** Matriz $A$ cuadrada ($n \times n$). Por defecto inicializada en $3 \times 3$ no aumentada en `grid_tmi`.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Conmutar al modo TMI**
  - **Interacción:** El usuario hace clic en el botón `"TMI"` en la barra de herramientas de modos.
  - **Componente:** `QPushButton#modeToggle` ([`tmi_mode_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L149)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* `self.pages` conmuta a la página 5 (`_build_tmi_page`). Se despliega una barra con dos presets académicos (`"Ejemplo invertible (S10)"` y `"Ejemplo singular (S10)"`), la cuadrícula de `Matriz A` ($3 \times 3$), el checklist del TMI (`tmi_checklist`) y el carrusel algorítmico `tmi_stepper`.
    - *Colores y Tokens:* `tmi_mode_btn` se activa en `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* 
      - Checklist inicial: `"Calcula para ver *c, *e, *h y det(A) ≠ 0."`.
      - Badge superior: `"✓ A es 3×3. Se puede evaluar el Teorema de la Matriz Invertible."`.

- **Paso 02: Selección de caso de prueba o edición de coeficientes**
  - **Interacción:** El usuario puede ingresar una matriz personalizada o pulsar uno de los botones predefinidos de la Sesión 10:
    - Clic en `"Ejemplo invertible (S10)"` ([`load_tmi_invertible_sample`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L1246)): Carga la matriz invertible de la diapositiva 19:
      $$\begin{pmatrix} 1 & 0 & -2 \\ 3 & 1 & -2 \\ -5 & -1 & 9 \end{pmatrix}$$
    - Clic en `"Ejemplo singular (S10)"` ([`load_tmi_singular_sample`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L1258)): Carga la matriz con filas idénticas de la diapositiva 20:
      $$\begin{pmatrix} 2 & 3 & 4 \\ 2 & 3 & 4 \\ 2 & 3 & 4 \end{pmatrix}$$
  - **Componente:** `QPushButton#secondaryAction` (`invertible_sample` o `singular_sample`).
  - **Comportamiento visual:** La cuadrícula `grid_tmi` se puebla y el cálculo se ejecuta de forma síncrona.

- **Paso 03: Ejecución de la evaluación del TMI**
  - **Interacción:** El usuario pulsa `"▶ Calcular"` (si ingresó matriz manual).
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)), invocando `_compute_tmi()`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* 
      - El checklist `tmi_checklist` se actualiza con una lista exhaustiva de afirmaciones evaluadas de la letra `a` a la `l` más `det`.
      - `tmi_stepper` muestra el proceso de escalonamiento de Gauss-Jordan que determina los pivotes y el determinante.
    - *Colores y Tokens:*
      - **Caso Invertible:** Badge verde `color-feedback-success` (`#81B29A`): `"✓ A es invertible. det(A) = k. Cumple *c, *e y *h (3 pivotes)."`. Cada renglón del checklist se renderiza en verde sage con la marca `"Cumple"`.
      - **Caso Singular:** Badge rojo `color-feedback-error` (`#EE6C4D`): `"✕ A es singular. det(A) = 0. Alguna caracterización del TMI no se cumple."`. Los renglones que fallan se renderizan en rojo con la marca `"No cumple"`.
    - *Textos y Microcopia del Checklist:* Desglose formal de equivalencias:
      ```text
      Cumple   a   A es invertible. Existe A⁻¹ y se comprobó A · A⁻¹ = A⁻¹ · A = Iₙ.
      Cumple   b   A es equivalente por filas a Iₙ. La forma reducida de A es Iₙ.
      Cumple  *c   A tiene exactamente 3 posiciones pivote. Gauss-Jordan encuentra 3 pivote(s), en las columnas 1, 2, 3. Se necesitan 3.
      Cumple   d   A x = 0 tiene únicamente la solución trivial. A x = 0 solo admite la solución trivial x = 0.
      Cumple  *e   Las columnas de A son linealmente independientes. A x = 0 solo admite la solución trivial x = 0.
      Cumple   f   La transformación x ↦ A x es inyectiva. El núcleo es {0}, así que x ↦ A x es inyectiva.
      Cumple   g   A x = b tiene al menos una solución para cada b de ℝⁿ. rango(A) = 3.
      Cumple  *h   Las columnas de A generan ℝ³. Hay 3 columnas en ℝ³ y rango(A) = 3. Generan todo ℝ³.
      Cumple   i   La transformación x ↦ A x es sobreyectiva sobre ℝ³. La imagen es todo el codominio.
      Cumple   j   Existe una matriz C tal que C A = Iₙ. C = A⁻¹ cumple C A = Iₙ.
      Cumple   k   Existe una matriz D tal que A D = Iₙ. D = A⁻¹ cumple A D = Iₙ.
      Cumple   l   Aᵀ es invertible. det(Aᵀ) = k ≠ 0.
      Cumple det   det(A) ≠ 0. det(A) = k ≠ 0.
      ```

- **Paso 04: Navegación del carrusel de reducción**
  - **Interacción:** El usuario avanza en `tmi_stepper` para verificar el escalonamiento de filas que sustenta el conteo de posiciones pivote.
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`tmi_stepper`).

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Matriz $A$ no cuadrada ($m \ne n$) | Badge Superior y Botón de Acción | Badge en rojo `color-feedback-error`. Botón `"▶ Calcular"` deshabilitado. | **Badge:** `"✕ El Teorema de la Matriz Invertible exige una matriz cuadrada (n×n). A es m×n."` | Agregar o eliminar filas/columnas para que $A$ sea de orden $n \times n$. |
| Celdas no numéricas en $A$ | Cuadrícula y Badge Superior | Celdas con borde inferior rojo. Badge en rojo. Botón deshabilitado. | **Badge:** `"✕ Hay celdas no numéricas en A."` | Corregir las celdas marcadas. |
| Matriz singular ($\det(A) = 0$, rango $< n$) | Badge Superior y Checklist | Badge en rojo. Los ítems `*c`, `*e`, `*h` y `det` cambian a color rojo con marca `"No cumple"`, exponiendo la evidencia exacta de variables libres y rango deficiente. | **Badge:** `"✕ A es singular. det(A) = 0. Alguna caracterización del TMI no se cumple."`<br>**Evidencia \*c:** `"Gauss-Jordan encuentra r pivote(s)... Se necesitan n."` | Comportamiento esperado: permite al estudiante verificar por qué la matriz no es invertible. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Botones Presets Académicos (`invertible_sample` y `singular_sample`)
- **Normal:** Botones secundarios con texto `"Ejemplo invertible (S10)"` y `"Ejemplo singular (S10)"`, borde `color-interactive-idle` (`#98C1D9`).
- **Hover:** Fondo con realce Powder Blue, texto oscuro.
- **Focus:** Contorno accesible.

#### B. Checklist del TMI (`tmi_checklist`)
- **Empty State:** Texto atenuado: `"Calcula para ver *c, *e, *h y det(A) ≠ 0."`.
- **Active State:** Lista estructurada en RichText de 18px con colores semánticos (`#81B29A` o `#EE6C4D`) y texto seleccionable con el ratón (`TextSelectableByMouse`).

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #8 - Jerarquía visual y escaneabilidad]:** El checklist lista las 13 caracterizaciones en un bloque de texto plano apilado verticalmente. Aunque las marcadas por la cátedra tienen un asterisco (`*c`, `*e`, `*h`), no cuentan con un badge o contenedor visual diferenciado (ej. una tarjeta destacada *"Caracterizaciones Clave de la Sesión"*) que las separe del resto de propiedades secundarias.
2. **[Nielsen #7 - Flexibilidad y filtros]:** No existe un filtro de visualización (ej. radio buttons *"[ Ver todas ]"*, *"[ Ver solo reprobadas ]"*, *"[ Ver solo clave (\*c, \*e, \*h) ]"*), lo que obliga a hacer scroll en pantallas pequeñas para revisar el listado completo.

---

## [MAT_FLUJO_07] - Comprobación de Identidades Algebraicas de la Inversa ((A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹A⁻¹, (Aᵀ)⁻¹ = (A⁻¹)ᵀ)

### 1. Metadatos Técnicos
- **Objetivo:** Contrastar celda a celda las tres identidades algebraicas canónicas de la matriz inversa entre dos matrices cuadradas del mismo orden $A, B \in \mathbb{R}^{n \times n}$:
  1. Involución de la inversa: $(A^{-1})^{-1} = A$
  2. Inversa del producto (reversión del orden): $(AB)^{-1} = B^{-1} A^{-1}$
  3. Conmutación con la transpuesta: $(A^T)^{-1} = (A^{-1})^T$
  presentando un informe comparativo que certifica si coinciden todas las celdas o detalla las coordenadas exactas de discrepancia en caso de fallo o singularidad.
- **Punto de inicio:** Ruta: Stack Index 1 (`Ctrl+2`), botón toolbar `"Identidades A⁻¹"` (`identities_mode_btn`), página índice 6 de `self.pages`.
- **Condiciones previas:** Dos cuadrículas de entrada cuadradas del mismo orden: `grid_id_a` ($3 \times 3$) y `grid_id_b` ($3 \times 3$). Matrices invertibles ($\det(A) \ne 0$ y $\det(B) \ne 0$).

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Conmutar al modo de Identidades de la Inversa**
  - **Interacción:** El usuario hace clic en el botón `"Identidades A⁻¹"` en la barra de herramientas.
  - **Componente:** `QPushButton#modeToggle` ([`identities_mode_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L153)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* `self.pages` conmuta a la página 6 (`_build_inverse_identities_page`). Se visualiza el botón de ejemplo `"Ejemplo (AB)⁻¹"`, dos cuadrículas de entrada (`Matriz A` y `Matriz B`), el checklist de identidades (`identity_checklist`) y el carrusel de pasos `identity_stepper`.
    - *Colores y Tokens:* `identities_mode_btn` se resalta en `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* 
      - Checklist inicial: `"Calcula para contrastar las tres identidades celda a celda."`.
      - Badge superior: `"✓ A y B son 3×3. Se contrastarán las tres identidades."`.

- **Paso 02: Carga de muestra académica o edición libre**
  - **Interacción:** El usuario pulsa el botón `"Ejemplo (AB)⁻¹"` (`sample`).
  - **Componente:** `QPushButton#secondaryAction` ([`load_inverse_identities_sample`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L1270)).
  - **Comportamiento visual:**
    - Se carga en $A$ la matriz invertible de la Sesión 10 y en $B$ una matriz triangular superior unitaria:
      $$A = \begin{pmatrix} 1 & 0 & -2 \\ 3 & 1 & -2 \\ -5 & -1 & 9 \end{pmatrix}, \quad B = \begin{pmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \\ 0 & 0 & 1 \end{pmatrix}$$
    - El cálculo se ejecuta automáticamente.

- **Paso 03: Ejecución de la comprobación algebraica**
  - **Interacción:** El usuario pulsa `"▶ Calcular"`.
  - **Componente:** `QPushButton#primaryAction` ([`compute_btn`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_operations_view.py#L212)), ejecutando `_compute_identities()`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* 
      - `identity_checklist` despliega tres tarjetas de comprobación con tipografía de 22px en verde sage (`color-feedback-success` `#81B29A`):
        ```text
        ✓  (A⁻¹)⁻¹ = A: Se comparó celda a celda: coinciden las 9 celdas.
        ✓  (Aᵀ)⁻¹ = (A⁻¹)ᵀ: Se comparó celda a celda: coinciden las 9 celdas.
        ✓  (AB)⁻¹ = B⁻¹ A⁻¹: Se comparó celda a celda: coinciden las 9 celdas.
        ```
      - `identity_stepper` registra la traza de cálculo de $A^{-1}$, $B^{-1}$, $AB$ y $(AB)^{-1}$.
    - *Colores y Tokens:* Badge superior en verde: `"✓ Las tres identidades de la inversa se cumplen celda a celda."`.
    - *Textos y Microcopia:* Inspector de producto: `"(A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹ A⁻¹ y (Aᵀ)⁻¹ = (A⁻¹)ᵀ. El checklist compara ambos lados celda a celda."`.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Matrices no cuadradas o de órdenes desiguales ($A$ es $2 \times 2$ y $B$ es $3 \times 3$) | Badge Superior y Botón de Acción | Badge en rojo `color-feedback-error`. Botón `"▶ Calcular"` deshabilitado. | **Badge:** `"✕ Las identidades piden dos matrices cuadradas del mismo orden. A es ra×ca y B es rb×cb."` | Ajustar las dimensiones de $A$ y $B$ para que ambas sean $n \times n$ con idéntico valor de $n$. |
| Matriz $A$ o $B$ singular ($\det(A) = 0$ o $\det(B) = 0$) | Checklist de Identidades y Badge Superior | Badge en rojo. Las identidades dependientes de la matriz singular se marcan en coral con marca `✗`. | **Checklist:** `"(AB)⁻¹ = B⁻¹ A⁻¹: A es singular, así que no existe (AB)⁻¹."`<br>**Badge:** `"✕ Alguna identidad de la inversa no se cumple o no aplica."` | Modificar los coeficientes de la matriz singular o pulsar `"Ejemplo (AB)⁻¹"` para cargar matrices invertibles válidas. |
| Celdas con caracteres no numéricos en $A$ o $B$ | Cuadrículas y Badge Superior | Celdas erróneas con borde rojo. Badge en rojo. Botón bloqueado. | **Badge:** `"✕ Hay celdas no numéricas en A o en B."` | Corregir los coeficientes en la cuadrícula correspondiente. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Cuadrículas Gemelas (`grid_id_a` y `grid_id_b`)
- Disposición simétrica en dos columnas paralelas dentro del mismo card con encabezados `"Matriz A"` y `"Matriz B"`.

#### B. Checklist de Identidades (`identity_checklist`)
- **Empty State:** Texto informativo tenue en 16px.
- **Success State:** Tres tarjetas de 22px con fondo verde translúcido (`rgba(129, 178, 154, 0.08)`), borde verde sage y texto explicativo del conteo de celdas idénticas.
- **Fail State:** Tarjetas en fondo coral con marca `✗` y detalle de las coordenadas exactas de divergencia.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado]:** Aunque la verificación celda a celda es matemáticamente impecable, la interfaz no muestra físicamente las matrices intermedias $(AB)^{-1}$ ni $B^{-1} A^{-1}$ lado a lado en pantalla. El usuario debe confiar en el texto de la tarjeta (`"coinciden las 9 celdas"`) o avanzar en el carrusel para verlas.
2. **[Nielsen #6 - Reconocimiento antes que recuerdo]:** En el producto $(AB)^{-1} = B^{-1} A^{-1}$, la inversión en el orden de los factores ($B^{-1}$ va primero) es la fuente número uno de errores conceptuales en estudiantes. Sería de alto valor pedagógico añadir una nota o alerta informativa visual que contraste explícitamente: *"Nota: $(AB)^{-1} \ne A^{-1} B^{-1}$ en general debido a la no-conmutatividad del producto"*.

---

## Resumen Ejecutivo de la Auditoría del Módulo 2 (Parte 2: Flujos 05 a 07)

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[MAT_FLUJO_05] Inversión $[A \mid I_n]$** | **9.5 / 10** | Traza de pasos completa de Gauss-Jordan sobre $[A \mid I_n]$, checklist bilateral $A \cdot A^{-1} = I_n$ y diagnóstico certero de singularidad. | Falta resaltar visualmente la fila de ceros en el carrusel cuando la matriz es singular. |
| **[MAT_FLUJO_06] Teorema de la Matriz Invertible (TMI)** | **9.0 / 10** | Cobertura pedagógica exhaustiva de 13 caracterizaciones equivalentes con presets de la Sesión 10 y conteo de pivotes. | Sobrecarga de texto plano en el checklist; falta separar visualmente las caracterizaciones clave (\*c, \*e, \*h). |
| **[MAT_FLUJO_07] Identidades de la Inversa** | **9.0 / 10** | Comparación celda a celda de alta precisión ($\ge 22\text{ px}$) para $(A^{-1})^{-1}$, $(AB)^{-1}$ y $(A^T)^{-1}$. | No despliega las matrices $B^{-1}A^{-1}$ y $(AB)^{-1}$ físicamente en paralelo para inspección visual directa. |

---

*Fin del reporte técnico de los Flujos 05 a 07 del Módulo 2.*


---

# Procede con la auditoría profunda y detallada del módulo: Módulo 3: Vectores en ℝⁿ e Independencia Lineal

---

## [VEC_FLUJO_01] - Operaciones Básicas Vectoriales en ℝⁿ (u ± v, k · v)

### 1. Metadatos Técnicos
- **Objetivo:** Ejecutar operaciones de adición ($u + v$), sustracción ($u - v$) o escalamiento ($k \cdot v$) en el espacio vectorial $\mathbb{R}^n$ con sincronización dimensional automática ($n \in [2, 10]$), validación en tiempo real de componentes y escalares, y renderizado del vector resultante en fracciones exactas con notación de libro.
- **Punto de inicio:** Ruta: Stack Index 2 (`Ctrl+3`), Pestaña `QTabWidget` index 0 (`"Operaciones básicas"`), componente de vista principal: [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L155).
- **Condiciones previas:** Aplicación inicializada en el módulo de Vectores. Estado local con dimensión inicial $n = 3$, operación por defecto $u + v$, vectores $u$ y $v$ preinicializados en ceros y escalar $k$ preinicializado en `"2"`.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección de dimensión del espacio euclidiano**
  - **Interacción:** El usuario modifica el control `basic_dim` (`QSpinBox`) mediante clics en las flechas de incremento/decremento o escribiendo un valor numérico entre 2 y 10.
  - **Componente:** `self.basic_dim` (`QSpinBox`) en [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L196-L201).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Los editores [`VectorColumnEditor`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L71) (`vec_u` y `vec_v`) recalculan dinámicamente la cantidad de filas de sus cuadrículas internas sin parpadeos.
    - *Colores y Tokens:* Fondo del spinbox en `color-surface-inner` (`#242028`), texto en `color-text-primary` (`#E0FBFC`). El badge de estado `basic_badge` actualiza inmediatamente el superíndice de $\mathbb{R}^n$ en verde sage (`#81B29A`).
    - *Textos y Microcopia:* Label: `"Dimensión n"`. El resultado previo se limpia automáticamente (`basic_result.clear()`).
    - *Feedback de Carga:* Síncrono e instantáneo.

- **Paso 02: Selección del operador aritmético**
  - **Interacción:** El usuario hace clic sobre uno de los botones del grupo exclusivo de modos: `"u + v"`, `"u − v"` o `"k · v"`.
  - **Componente:** `self.basic_op_group` (`QButtonGroup`) conteniendo `self.basic_add_btn`, `self.basic_sub_btn`, `self.basic_scale_btn` ([`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L203-L215)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Si se selecciona `"k · v"`, el contenedor central `self.basic_mid` (`QStackedWidget`) conmuta de la página 0 (`VectorColumnEditor` de $v$) a la página 1 (`scale_card` con campo `basic_k`). Si se selecciona suma o resta, vuelve a la página 0.
    - *Colores y Tokens:* El botón activo adopta clase `modeToggle` con fondo activo `color-interactive-idle` (`#98C1D9`) y texto `color-bg-base` (`#1A181B`). Los inactivos permanecen con fondo transparente y borde tenue.
    - *Textos y Microcopia:* Botones: `"u + v"`, `"u − v"`, `"k · v"`. En modo escalar, aparece la tarjeta con label `"Escalar k"` y el campo centrado.
    - *Feedback de Carga:* Conmutación visual inmediata.

- **Paso 03: Edición de componentes y valores escalares**
  - **Interacción:** El usuario ingresa enteros, fracciones o decimales en las celdas de $u$, $v$ o en el campo de texto del escalar $k$.
  - **Componente:** Celdas [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) dentro de [`VectorColumnEditor`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L71) y `self.basic_k` (`QLineEdit`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Cada columna vectorial se aloja en un card con clase `elevated-card` (`#564D65`).
    - *Colores y Tokens:* Cada celda válida aplica `matrix-cell`. Al cambiar texto, se valida sintácticamente con `parse_scalar()`; si es válido, el badge superior se mantiene en verde sage `color-feedback-success` (`#81B29A`).
    - *Textos y Microcopia:* Badge: `"✓ u, v ∈ ℝⁿ con la misma dimensión. La suma y la resta están definidas."` o `"✓ Escalado definido en ℝⁿ: (k · v) ∈ ℝⁿ"`.
    - *Feedback de Carga:* Validación en tiempo real conectada a la señal `changed`.

- **Paso 04: Ejecución del cálculo vectorial**
  - **Interacción:** El usuario hace clic en el botón `"▶ Calcular"`.
  - **Componente:** `self.basic_compute_btn` (`QPushButton` con ID `primaryAction`) en [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L264-L268).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor derecho `result_card` (`QFrame` con `elevated-card`) recibe y dibuja el vector resultante en [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1).
    - *Colores y Tokens:* El botón activa su feedback táctil. El vector se renderiza con corchetes de libro cerrados en `color-text-primary` (`#E0FBFC`) sobre fondo `color-surface-inner` (`#242028`).
    - *Textos y Microcopia:* Label del contenedor: `"Resultado"`. Coeficientes formateados en fracciones exactas (ej. `5/2`, `-1/3`).
    - *Feedback de Carga:* Cero latencia percibida; evaluación matemática local inmediata.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Entrada no numérica o caracteres inválidos en celdas de $u$ o $v$ (ej: letras `abc`, símbolos `##`) | Celdas [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) y Badge Superior `basic_badge` | Borde de la celda en rojo quemado `color-feedback-error` (`#EE6C4D`). Badge superior en rojo con fondo oscuro. Botón `"▶ Calcular"` deshabilitado (`setEnabled(False)`). | **Badge:** `"✕ Hay componentes no numéricas."` (o `"✕ Hay componentes no numéricas en v."` en modo escalar) | Corregir la celda ingresando un número entero, fracción (`a/b`) o decimal válido. |
| Escalar $k$ malformado en modo $k \cdot v$ (ej: cadena vacía, división por cero `1/0`) | Campo `basic_k` y Badge Superior `basic_badge` | Badge en rojo `color-feedback-error`. Botón `"▶ Calcular"` deshabilitado. | **Badge:** `"✕ El escalar k no es un número válido."` | Escribir un escalar válido en el campo $k$. |
| Discrepancia dimensional por manipulación programática o desincronización | Badge Superior `basic_badge` | Badge en rojo. Botón de cálculo bloqueado. | **Badge:** `"✕ [Mensaje de DimensionMismatchError capturado]"` | Restablecer o igualar las dimensiones usando el control `basic_dim`. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Editor de Columna Vectorial (`VectorColumnEditor`)
- **Empty State:** Celdas inicializadas con valor por defecto `"0"`. Sin celdas nulas o no renderizadas.
- **Hover / Focus:** Hover en celda resalta sutilmente el borde; foco selecciona automáticamente el texto completo (`selectAll()`).
- **Disabled:** En operaciones básicas, el editor de $u$ y $v$ no soporta borrado de vector completo (sin botón `×`), garantizando la existencia de los dos operandos.

#### B. Selector Central de Modo (`basic_mid`)
- **Estado Binario:** Muestra `vec_v` en operaciones $u + v$ y $u - v$.
- **Estado Unario/Escalar:** Muestra `scale_card` con campo `basic_k` en operación $k \cdot v$.
- **Transición:** Instantánea mediante `QStackedWidget.setCurrentIndex()`.

#### C. Visor de Resultado (`basic_result` - `BookMatrixWidget`)
- **Empty State:** Cuadro limpio en fondo `color-surface-inner` (`#242028`), sin caracteres basura.
- **Display State:** Corchetes de libro continuos dibujados por `draw_square_brackets()`, escalares centrados con soporte de fracciones apiladas simétricas.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #7 - Flexibilidad y eficiencia de uso]:** No existe un botón de inversión de operandos para la resta ($v - u$), obligando al usuario a reescribir manualmente los valores de ambos vectores si desea evaluar la resta en el orden inverso.
2. **[Nielsen #6 - Reconocimiento antes que recuerdo]:** A diferencia de otros módulos de la suite, esta vista básica no incluye carrusel de pasos explicativo (`AlgorithmStepperCarousel`) que muestre la suma o resta componente a componente ($u_i \pm v_i$), lo cual reduciría la curva de aprendizaje en estudiantes que inician en el álgebra lineal.

---

## [VEC_FLUJO_02] - Métricas Vectoriales y Producto Exterior (‖u‖, ‖v‖, d(u, v), u vᵀ)

### 1. Metadatos Técnicos
- **Objetivo:** Calcular métricas del espacio euclidiano $\mathbb{R}^n$: la norma de un vector ($\|u\|$, $\|v\|$) con cuadrado racional exacto y radical simplificado, la distancia euclidiana ($d(u,v)$), y el producto exterior de rango 1 ($u v^T \in \mathbb{R}^{m \times n}$), acompañados del carrusel de pasos con fórmulas matemáticas en notación de libro.
- **Punto de inicio:** Ruta: Stack Index 2 (`Ctrl+3`), Pestaña `QTabWidget` index 1 (`"Norma y producto exterior"`), componente de vista principal: [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L155).
- **Condiciones previas:** Aplicación abierta en el módulo de Vectores. Dimensiones `dim u` y `dim v` en rango $[1, 10]$ (por defecto 3). Vectores $u$ y $v$ con valores iniciales válidos.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Configuración de dimensiones independientes o carga de presets**
  - **Interacción:** El usuario ajusta las dimensiones de $u$ y $v$ mediante los controles `metric_u_dim` y `metric_v_dim` (`QSpinBox`), o pulsa uno de los tres botones de prueba: `"Ejemplo ‖(3, 4)‖"`, `"Ejemplo distancia"` o `"Ejemplo x xᵀ"`.
  - **Componente:** `metric_u_dim`, `metric_v_dim` y botones preset ([`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L298-L322)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Los editores vectoriales `metric_u` y `metric_v` ajustan el número de filas de forma reactiva.
    - *Colores y Tokens:* Si se pulsa un preset, los datos se cargan automáticamente y se dispara la ejecución de la métrica correspondiente.
    - *Textos y Microcopia:* Botones secundarios: `"Ejemplo ‖(3, 4)‖"`, `"Ejemplo distancia"`, `"Ejemplo x xᵀ"`.
    - *Feedback de Carga:* Instantáneo.

- **Paso 02: Validación dimensional reactiva en badge**
  - **Interacción:** El usuario observa el badge informativo superior `metric_badge` al modificar dimensiones o componentes.
  - **Componente:** `self.metric_badge` ([`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L324-L330)).
  - **Comportamiento visual:**
    - *Colores y Tokens:* Si `dim u == dim v`, badge en verde sage (`#81B29A`) con fondo `color-bg-base` (`#1A181B`). Si difieren, badge en verde informativo indicando que el producto exterior es válido pero la distancia requiere igual dimensión.
    - *Textos y Microcopia:* Con misma dimensión: `"✓ u y v están en ℝⁿ. La norma, la distancia y el producto exterior están definidos."` Con dimensiones distintas: `"✓ El producto exterior u vᵀ es m×n. La distancia pide la misma dimensión."`
    - *Controles asociados:* Si `dim u != dim v`, el botón `"Distancia d(u, v)"` se deshabilita visualmente (`setEnabled(False)`).

- **Paso 03: Edición de componentes vectoriales**
  - **Interacción:** El usuario ingresa números enteros o racionales en las celdas de `metric_u` y `metric_v`.
  - **Componente:** Celdas [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) en `self.metric_u` y `self.metric_v`.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Celdas en `matrix-cell` con texto en `color-text-primary` (`#E0FBFC`). Cada pulsación actualiza el badge y el estado de habilitación de los botones de acción.

- **Paso 04: Selección y ejecución de la métrica deseada**
  - **Interacción:** El usuario hace clic en uno de los 4 botones de acción disponibles:
    1. `"Calcular norma ‖u‖"` (`norm_u_btn`)
    2. `"Calcular norma ‖v‖"` (`norm_v_btn`)
    3. `"Distancia d(u, v)"` (`distance_btn`)
    4. `"Producto exterior u vᵀ"` (`outer_btn`)
  - **Componente:** Botones de acción principal en [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L342-L353).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Se actualizan simultáneamente tres zonas inferiores: la etiqueta de resumen analítico (`metric_summary`), la cuadrícula de resultado (`metric_result`) y el carrusel de trazabilidad (`metric_stepper`).
    - *Colores y Tokens:* Badge se actualiza a `"✓ Cálculo exacto en fracciones."` en verde sage. Botón pulsado muestra estado presionado.

- **Paso 05: Inspección del resultado analítico y carrusel de pasos**
  - **Interacción:** El usuario examina el valor numérico y navega los pasos del cálculo en el carrusel con los botones `"Anterior"` y `"Siguiente"`.
  - **Componente:** `self.metric_summary`, `self.metric_result` (`BookMatrixWidget`) y `self.metric_stepper` (`AlgorithmStepperCarousel`).
  - **Comportamiento visual:**
    - *Textos y Microcopia:* `metric_summary` (22px monospace negrita): ej. `"‖u‖² = 25    ‖u‖ = 5"` o `"d(u, v)² = 25    d(u, v) = 5"` o `"u vᵀ es 3×3. Cada entrada es uᵢ · vⱼ."`.
    - *Carrusel:* Despliega la sumatoria de cuadrados $\sum u_i^2$, la diferencia cuadrática $\sum (u_i - v_i)^2$ o las entradas parciales de la matriz de producto exterior con fórmulas en notación de libro (`latex_to_book_html`).

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Caracteres no numéricos en celdas de $u$ o $v$ | Celdas y Badge Superior `metric_badge` | Celdas con borde rojo `color-feedback-error`. Badge en rojo `#EE6C4D`. Los cuatro botones de cálculo se deshabilitan. | **Badge:** `"✕ Hay componentes no numéricas."` | Corregir los coeficientes no numéricos en las celdas marcadas. |
| Intento de calcular distancia con dimensiones distintas ($n \ne m$) | Botón `distance_btn` y Badge Superior | Botón `"Distancia d(u, v)"` bloqueado con opacidad reducida (`setEnabled(False)`). Cursor estándar (bloquea clics). | **Badge:** `"✓ El producto exterior u vᵀ es m×n. La distancia pide la misma dimensión."` | Igualar los valores de `dim u` y `dim v` mediante los spinboxes superiores. |
| Incompatibilidad dimensional forzada en backend | Badge Superior `metric_badge` | Badge adopta fondo rojo `color-feedback-error`. | **Badge:** `"✕ [Mensaje de DimensionMismatchError]"` | Revisar que ambos vectores posean idéntico número de componentes. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Badge Semántico de Métricas (`metric_badge`)
- **Empty / Idle State:** Fondo `#3A3642`, texto `color-text-primary` (`#E0FBFC`): `"Elige una operación."`
- **Conformable State:** Fondo verde sage `color-feedback-success` (`#81B29A`), texto `#1A181B`.
- **Error State:** Fondo rojo quemado `color-feedback-error` (`#EE6C4D`), texto `#E0FBFC`.

#### B. Botones de Métrica (`norm_u_btn`, `norm_v_btn`, `distance_btn`, `outer_btn`)
- **Normal:** Botones `primaryAction` con fondo `color-interactive-idle` (`#98C1D9`), texto `#1A181B`.
- **Disabled (`distance_btn`):** Opacidad atenuada, fondo `#3A3642`, texto atenuado `color-text-muted`, cursor de bloqueo.

#### C. Carrusel de Métricas (`metric_stepper`)
- **Empty State:** Oculto o vacío sin pasos cargados.
- **Active State:** Contenedor visible con botones `Anterior` / `Siguiente`, selector `Fracciones` / `Decimales`, visualizador de fórmula formateada y matriz del paso.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #8 - Diseño estético y minimalista]:** Cuatro botones de acción primaria (`primaryAction`) alineados en la misma barra generan competencia visual y sobrecarga de decisión (Ley de Hick). Sería preferible un selector segmentado de métrica (`QButtonGroup`) complementado con un único botón de ejecución `"▶ Calcular"`.
2. **[Nielsen #1 - Visibilidad del estado del sistema]:** En el producto exterior $u v^T$, al hacer clic en una celda de la matriz resultante no se resaltan la fila de $u$ ni la columna de $v$ involucradas (a diferencia del inspector celda a celda de $A \cdot B$ en el Módulo 2).

---

## [VEC_FLUJO_03] - Evaluación y Descomposición de Combinación Lineal (Σ cᵢ vᵢ = b)

### 1. Metadatos Técnicos
- **Objetivo:** Determinar formalmente si un vector objetivo $b \in \mathbb{R}^n$ es combinación lineal de una familia finita de vectores generadores $\{v_1, \dots, v_k\} \subset \mathbb{R}^n$, calculando los pesos únicos $c_i$ (SCD), la familia infinita de soluciones paramétricas (SCI), o detectando la contradicción matemática si no es combinación lineal (SI), con verificación exacta componente a componente y carrusel opcional de escalonamiento.
- **Punto de inicio:** Ruta: Stack Index 2 (`Ctrl+3`), Pestaña `QTabWidget` index 2 (`"Combinación lineal"`), componente de vista principal: [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L155).
- **Condiciones previas:** Espacio $\mathbb{R}^n$ con $n \in [2, 10]$ (por defecto 3). Conjunto generador con al menos un vector (por defecto 2 vectores $v_1, v_2$) y un vector objetivo $b$.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección del espacio dimensional y presets**
  - **Interacción:** El usuario ajusta el spinbox `combo_dim` o pulsa `"Ejemplo SCD"` o `"Ejemplo SI"`.
  - **Componente:** `self.combo_dim` (`QSpinBox`), botones `sample_ok`, `sample_si` ([`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L506-L521)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Si se cambia $n$, todos los generadores en `_combo_editors` y el `target_editor` ajustan su altura de cuadrícula simultáneamente.
    - *Textos y Microcopia:* Spinbox con label `"Espacio ℝⁿ   n ="`. Botones: `"Ejemplo SCD"`, `"Ejemplo SI"`.

- **Paso 02: Gestión dinámica de vectores generadores**
  - **Interacción:** El usuario hace clic en `"+  Agregar vector"` para incorporar nuevos vectores al conjunto generador, o pulsa el botón `"×"` en el encabezado de un vector existente para eliminarlo.
  - **Componente:** `add_btn` (`QPushButton` secundario) y `delete_btn` en [`VectorColumnEditor`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L101-L107).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Los vectores se añaden horizontalmente dentro del contenedor deslizable `scroll_gen`.
    - *Textos y Microcopia:* Títulos de los vectores se renumeran automáticamente en orden correlativo: `v1`, `v2`, `v3`, etc. mediante `_retitle_combo_vectors()`.
    - *Restricciones:* Si queda un solo vector generador, el botón de eliminación se oculta o bloquea para evitar dejar el conjunto vacío.

- **Paso 03: Ingreso de componentes del conjunto y del vector objetivo**
  - **Interacción:** El usuario digita coeficientes numéricos en las celdas de los generadores $\{v_i\}$ y en las celdas del vector objetivo $b$.
  - **Componente:** Cuadrículas `DynamicMatrixGrid` de los editores `_combo_editors` y `self.target_editor`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El editor del vector objetivo `target_editor` se distingue visualmente mediante un borde destacado continuo de 2px en `color-interactive-idle` (`#98C1D9`).
    - *Colores y Tokens:* Celdas con texto en `color-text-primary`. Validación en tiempo real.

- **Paso 04: Evaluación de la combinación lineal**
  - **Interacción:** El usuario hace clic en el botón principal `"▶ Evaluar combinación lineal"`.
  - **Componente:** `self.combo_btn` (`QPushButton` con ID `primaryAction`) en [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L560-L564).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El panel inferior de resultados despliega el badge de clasificación, el resumen analítico, el checklist de sustitución y habilita el botón del carrusel de pasos.
    - *Colores y Tokens:*
      - **SCD (Solución Única):** Badge en verde sage `color-feedback-success` (`#81B29A`) con texto `color-bg-base` (`#1A181B`).
      - **SCI (Infinitas Combinaciones):** Badge en amarillo ámbar `color-accent-warning` (`#E9C46A`) con texto `#1A181B`.
      - **SI (Inconsistente):** Badge en rojo quemado `color-feedback-error` (`#EE6C4D`) con texto `color-text-primary` (`#E0FBFC`).

- **Paso 05: Inspección de pesos, solución paramétrica y verificación**
  - **Interacción:** El usuario revisa los pesos calculados $c_i$ y las marcas de verificación de cada componente. Opcionalmente pulsa `"Ver procedimiento de escalonamiento"`.
  - **Componente:** `self.combo_summary`, `self.combo_checklist`, `self.show_steps_btn` y `self.combo_stepper`.
  - **Comportamiento visual:**
    - *Textos y Microcopia:* `combo_summary` (24px monospace negrita): muestra $b = c_1 v_1 + \dots$, lista de pesos `"Pesos: c1 = ..., c2 = ..."`, solución paramétrica o contradicción.
    - *Checklist:* Tarjetas horizontales de 24px en `color-surface-inner` (`#242028`) con marcas `✓` en verde comprobando $\sum c_i v_{i,j} = b_j$. En caso inconsistente, tarjeta roja: `"Contradicción: aparece una fila [0 … 0 | c ≠ 0]."`.
    - *Desplegable de Pasos:* Al conmutar `show_steps_btn`, se despliega suavemente `combo_stepper` mostrando la reducción por filas de la matriz aumentada $[v_1 \dots v_k \mid b]$.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Celdas con caracteres alfabéticos o no válidos en generadores o en $b$ | Diálogo Modal [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L806) | Modal emergente con icono de advertencia (`Warning`) y estilo temático oscuro. El cálculo se detiene. | **Título:** `"Entrada inválida"`<br>**Mensaje:** `"Corrige las componentes no numéricas."` | Pulsar `"Aceptar"` en el modal y corregir las celdas con borde rojo. |
| Incompatibilidad de dimensiones entre vectores y el espacio | Diálogo Modal `QMessageBox` | Modal de advertencia. El cálculo no se efectúa. | **Título:** `"Dimensiones incompatibles"`<br>**Mensaje:** `"[Detalle de la excepción]"` | Ajustar la dimensión de los vectores para que coincidan con $n$. |
| Intento de eliminar cuando queda un solo vector ($k=1$) | Botón de eliminación `×` | La acción no se ejecuta (`len(_combo_editors) <= 1`). El botón no responde o se oculta. | Sin microcopia (protección por lógica de interfaz). | Mantener al menos un vector generador en el conjunto. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Vector Objetivo (`target_editor`)
- **Estilo Permanente:** Borde de 2px sólido en `COLOR_INTERACTIVE_IDLE` (`#98C1D9`), radio de 8px, garantizando distinción física respecto a los generadores.
- **Foco:** Auto-selección completa de la celda al entrar.

#### B. Badge de Diagnóstico (`combo_badge`)
- **Idle State:** Fondo `#3A3642`, texto `color-text-primary`: `"Esperando evaluación"`.
- **SCD State:** Fondo `#81B29A`: `"SÍ ES COMBINACIÓN LINEAL ÚNICA  (SCD)"`.
- **SCI State:** Fondo `#E9C46A`: `"SÍ ES COMBINACIÓN LINEAL  (infinitas combinaciones, SCI)"`.
- **SI State:** Fondo `#EE6C4D`: `"NO ES COMBINACIÓN LINEAL  (SI)"`.

#### C. Botón Desplegable de Escalonamiento (`show_steps_btn`)
- **Disabled State:** Antes de calcular, deshabilitado (`setEnabled(False)`).
- **Active State:** Habilitado tras cálculo. Checkable: cuando está presionado, `combo_stepper.setVisible(True)`.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #5 - Prevención de errores]:** El botón `"+  Agregar vector"` permite añadir vectores indefinidamente sin advertir si se supera la dimensión del espacio ($k > n$), momento en el cual el conjunto se vuelve linealmente dependiente y las combinaciones lineales dejan de ser únicas. Una pequeña advertencia pedagógica antes de evaluar enriquecería la experiencia.
2. **[Nielsen #2 - Coincidencia entre el sistema y el mundo real]:** Cuando el sistema es inconsistente (SI), el checklist solo muestra el texto genérico `"Contradicción: aparece una fila [0 … 0 | c ≠ 0]"` sin indicar en cuál fila específica ocurrió la discrepancia ni mostrar los valores numéricos incongruentes (ej. $0 = 4$).

---

## [VEC_FLUJO_04] - Diagnóstico de Independencia Lineal (L.I. / L.D.) y Demostración Teórica

### 1. Metadatos Técnicos
- **Objetivo:** Evaluar rigurosamente si un conjunto finito de vectores $\{v_1, \dots, v_k\} \subset \mathbb{R}^n$ es Linealmente Independiente (L.I.) o Linealmente Dependiente (L.D.), aplicando teoremas estructurales (Teorema de la Dimensión $k > n$, Teorema del Vector Nulo, rango y pivotes de la matriz formada por los vectores como columnas), presentando justificación teórica formal, escalonamiento por filas y, en caso de ser L.D., la demostración explícita de combinación lineal no trivial nula ($\sum c_i v_i = 0$ con $c \ne 0$).
- **Punto de inicio:** Ruta: Stack Index 2 (`Ctrl+3`), Pestaña `QTabWidget` index 3 (`"Independencia lineal"`), componente de vista principal: [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L155).
- **Condiciones previas:** Dimensión del espacio $\mathbb{R}^n$ con $n \in [1, 10]$ (por defecto 3). Conjunto inicial con 3 vectores $v_1, v_2, v_3$ con entradas numéricas válidas.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección de dimensión o carga de casos teóricos de prueba**
  - **Interacción:** El usuario selecciona la dimensión $n$ en `indep_dim` (`QSpinBox`), o hace clic en alguno de los 4 botones superiores:
    1. `"Ejemplo L.I."`: Carga base canónica en $\mathbb{R}^3$ ($v_1=(1,0,0), v_2=(0,1,0), v_3=(0,0,1)$).
    2. `"Ejemplo L.D."`: Carga vectores linealmente dependientes ($v_3 = v_1 + v_2$).
    3. `"Ejemplo k > n (L.D.)"`: Carga 4 vectores en $\mathbb{R}^3$ para activar el Teorema Fundamental de Dimensión.
    4. `"Teoremas clave"`: Abre el modal pedagógico con los teoremas del módulo.
  - **Componente:** `self.indep_dim` y botones en cabecera ([`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L836-L863)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Si se activa un preset, los editores se recrean y redimensionan de forma transparente y ejecutan la evaluación de inmediato.
    - *Modal de Teoremas:* Si se pulsa `"Teoremas clave"`, se abre un diálogo modal estilizado ([`show_theorems_dialog`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L1093)) con 5 teoremas explicados en HTML de alto contraste.

- **Paso 02: Gestión interactiva de vectores del conjunto**
  - **Interacción:** El usuario añade vectores mediante `"+  Agregar vector"` o los elimina pulsando `"×"`.
  - **Componente:** `add_btn` y editores `_indep_editors` en `self.indep_list_host`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Desplazamiento horizontal fluido en el card de generadores.
    - *Textos y Microcopia:* Encabezados actualizados automáticamente: `v_1`, `v_2`, `v_3`, etc. mediante `_refresh_indep_titles()`.

- **Paso 03: Ejecución de la evaluación de independencia lineal**
  - **Interacción:** El usuario hace clic en el botón principal `"▶ Evaluar Independencia Lineal"`.
  - **Componente:** `self.indep_btn` (`QPushButton` con ID `primaryAction`) en [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L894-L898).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor inferior de resultados despliega el veredicto en el badge semántico, el informe teórico estructurado y la sección de demostración si es L.D.
    - *Colores y Tokens:*
      - **L.I.:** Badge verde sage `color-feedback-success` (`#81B29A`): `"🟢 CONJUNTO LINEALMENTE INDEPENDIENTE (L.I.)"`.
      - **L.D.:** Badge rojo quemado `color-feedback-error` (`#EE6C4D`): `"🔴 CONJUNTO LINEALMENTE DEPENDIENTE (L.D.)"`.

- **Paso 04: Análisis de la justificación teórica y teoremas activos**
  - **Interacción:** El usuario lee el resumen técnico y teórico en `indep_summary`.
  - **Componente:** `self.indep_summary` (`QLabel` con RichText) en [`VectorsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L910-L915).
  - **Comportamiento visual:**
    - *Textos y Microcopia:* Desglose formal:
      - `• Vectores: k = ... en ℝⁿ`
      - `• Número de pivotes (rango de A): r`
      - `• Variables básicas:` lista de $c_i$.
      - `• Variables libres:` lista de $c_i$ o `Ninguna (0)`.
      - **Justificación Teórica:** Explica si el sistema homogéneo tiene solución única trivial ($c=0$) o infinitas no triviales. Si aplica, resalta: `• Teorema Fundamental de Dimensión: k > n` o `• Teorema del Vector Nulo`.

- **Paso 05: Inspección de la demostración no trivial y escalonamiento**
  - **Interacción:** Si el conjunto es L.D., el usuario examina la ecuación no trivial nula en `indep_checklist`. Opcionalmente activa el carrusel de pasos.
  - **Componente:** `self.indep_checklist`, `self.indep_show_steps_btn` y `self.indep_stepper`.
  - **Comportamiento visual:**
    - *Textos y Microcopia:* Muestra el encabezado `Demostración de Combinación Lineal No Trivial Nula:` y la ecuación formal en 22px monospace: ej. `(1)·v₁ + (-1)·v₂ + (0)·v₃ = 0` sobre fondo `color-surface-inner` (`#242028`). Debajo, cada componente muestra la verificación en verde sage: `✓ Componente 1: Σ cᵢ·vᵢ = 0 (coincide con 0)`.
    - *Carrusel:* Al pulsar `indep_show_steps_btn`, se despliega el visor paso a paso con las operaciones elementales de fila aplicadas para escalonar la matriz homogénea.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Valores no numéricos en celdas de algún vector $v_i$ | Diálogo Modal [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L806) | Modal emergente de advertencia (`Warning`). La evaluación no se inicia. | **Título:** `"Entrada inválida"`<br>**Mensaje:** `"El vector v_i contiene valores numéricos no válidos."` | Pulsar `"Aceptar"` y corregir el valor en el vector indicado. |
| Conjunto con más vectores que la dimensión ($k > n$) | Badge y Resumen Teórico | Badge en rojo `L.D.`. El sistema identifica y aplica el teorema inmediatamente sin requerir eliminación innecesaria. | **Resumen:** `"• Teorema Fundamental de Dimensión: k = X > n = Y. En ℝⁿ ningún conjunto de más de Y vectores puede ser L.I."` | Informativo. El usuario comprende que la dependencia es inherente a la dimensión. |
| Conjunto que incluye el vector nulo ($v_i = \mathbf{0}$) | Badge y Resumen Teórico | Badge en rojo `L.D.`. | **Resumen:** `"• Teorema del Vector Nulo: El vector v_i es el vector cero. Todo conjunto con el 0 es L.D."` | Modificar el vector cero si se desea evaluar un conjunto no trivial. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Modal de Teoremas (`show_theorems_dialog`)
- **Presentación:** Ventana modal centrada de PySide6 estilizada con `apply_message_box_theme()`.
- **Estilo:** Fondo `color-surface-elevated` (`#564D65`), texto en `color-text-primary` (`#E0FBFC`), separador `<hr>` y botón estándar `"Aceptar"`.
- **Contenido:** 5 teoremas formativos de álgebra lineal explicados rigurosamente.

#### B. Badge de Estado (`indep_badge`)
- **Idle State:** Fondo `#3A3642`: `"Esperando evaluación"`.
- **L.I. State:** Fondo `#81B29A` (verde sage), texto `#1A181B`: `"🟢 CONJUNTO LINEALMENTE INDEPENDIENTE (L.I.)"`.
- **L.D. State:** Fondo `#EE6C4D` (rojo quemado), texto `#E0FBFC`: `"🔴 CONJUNTO LINEALMENTE DEPENDIENTE (L.D.)"`.

#### C. Checklist de Demostración (`indep_checklist`)
- **L.I. State:** Permanece vacío (no existe combinación no trivial nula).
- **L.D. State:** Despliega bloques elevados con tipografía 22px monospace, destacando los coeficientes de ponderación no nulos y comprobando componente a componente la igualdad a cero.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado del sistema]:** En el modal abierto por `"Teoremas clave"`, el título de la ventana y el encabezado principal dicen textualmente `"TEOREMAS CLAVE — MÓDULO 2: VECTORES E INDEPENDENCIA LINEAL"` y `"Teoremas Clave del Módulo 2"`. En la arquitectura general de la suite, esta vista corresponde al **Módulo 3** (rezago de versiones tempranas). Esto genera disonancia cognitiva en el usuario.
2. **[Nielsen #7 - Flexibilidad y eficiencia de uso]:** No se dispone de una opción para transponer o importar una matriz completa directamente como un conjunto de vectores columna (Copy/Paste por bloque), obligando al estudiante a transcribir celda por celda cada vector cuando trabaja con ejercicios de libros de texto extensos ($k \ge 4$).

---

## Resumen Ejecutivo de la Auditoría del Módulo 3

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[VEC_FLUJO_01] Operaciones Básicas** | **9.0 / 10** | Conmutación instantánea entre operandos vectoriales y escala escalar $k$; renderizado de libro en fracciones exactas. | Ausencia de inversión de operandos ($v - u$) y falta de desglose paso a paso. |
| **[VEC_FLUJO_02] Métricas y Producto Exterior** | **9.2 / 10** | Desglose triple (resumen analítico, matriz resultado y carrusel de pasos); cálculo exacto con radicales simplificados. | Sobrecarga de cuatro botones de acción primaria en la misma barra horizontal. |
| **[VEC_FLUJO_03] Combinación Lineal** | **9.5 / 10** | Detección completa de los 3 casos (SCD, SCI, SI); marco distintivo para el vector objetivo $b$ y checklist de sustitución de 24px. | El scroll horizontal de generadores se congestiona con más de 5 vectores. |
| **[VEC_FLUJO_04] Independencia Lineal** | **9.7 / 10** | Detección automática de Teoremas ($k > n$, vector nulo); demostración explícita no trivial nula cuando es L.D. | Disonancia en título del modal de teoremas (dice "Módulo 2" en vez de "Módulo 3"). |

---

*Fin del reporte técnico del Módulo 3.*


---

# Procede con la auditoría profunda y detallada del módulo: Módulo 4: Ecuaciones Matriciales y Propiedades de A · x

---

## [EQM_FLUJO_01] - Resolución y Verificación de la Ecuación A · x = b

### 1. Metadatos Técnicos
- **Objetivo:** Resolver algebraicamente la ecuación matricial canónica $A \cdot x = b$ con coeficientes racionales arbitrarios ($A \in \mathbb{R}^{m \times n}$, $b \in \mathbb{R}^m$), obteniendo el vector solución $x \in \mathbb{R}^n$, la clasificación analítica (SCD, SCI con solución paramétrica o SI), la traza paso a paso de Gauss-Jordan en la matriz aumentada $[A \mid b]$ y la comprobación explícita mediante multiplicación fila por vector ($A \cdot x = b$).
- **Punto de inicio:** Ruta: Stack Index 3 (`Ctrl+4`), Pestaña principal `QTabWidget` index 0 (`"Ecuación  A · x = b"`), componente de vista principal: [`MatrixEquationsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_equations_view.py#L50).
- **Condiciones previas:** Aplicación abierta en el módulo de Ecuaciones Matriciales. Estado inicial con matriz $A$ de $3 \times 3$, vector de incógnitas $x \in \mathbb{R}^3$, vector de términos independientes $b \in \mathbb{R}^3$ inicializado en ceros.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Exploración dimensional y carga de casos académicos de prueba**
  - **Interacción:** El usuario visualiza la fórmula de conformabilidad en la cabecera o hace clic en alguno de los botones de prueba rápida:
    1. `"Ejemplo SCD (3×3)"`: Carga $A$ invertible ($3 \times 3$) y $b = (4, 4, 3)^T$, con solución única $x = (2, 1, 1)^T$.
    2. `"Ejemplo SCI (2×3)"`: Carga sistema indeterminado con variable libre.
    3. `"Ejemplo SI (3×2)"`: Carga sistema incompatible sin solución.
    4. `"Limpiar"`: Restablece matriz y vectores a ceros.
  - **Componente:** Botones de preset en `header_layout` ([`MatrixEquationsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_equations_view.py#L100-L127)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La cabecera `header_card` mantiene elevación `elevated-card`. La cuadrícula $A$ y el vector $b$ se rellenan inmediatamente.
    - *Colores y Tokens:* Label de fórmula `self.formula_lbl` muestra dimensiones actuales en tipografía Monospace (`Fira Code`) y color `color-interactive-idle` (`#98C1D9`).
    - *Textos y Microcopia:* `formula_lbl`: `"A (3×3)  ·  x (3×1)  =  b (3×1)"`. Tooltips explicativos en cada botón de preset.
    - *Feedback de Carga:* Inmediato; la selección de un preset ejecuta automáticamente la resolución (`solve()`).

- **Paso 02: Edición interactiva de coeficientes en Matriz A y Vector b**
  - **Interacción:** El usuario hace clic en las celdas de la cuadrícula `grid_a` o en el editor `vec_b` para introducir valores numéricos (enteros, fracciones `a/b` o decimales).
  - **Componente:** [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) (`grid_a`) y [`VectorColumnEditor`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L71) (`vec_b`).
  - **Comportamiento visual:**
    - *Sincronización Automática:* Al alterar la cantidad de filas de $A$ mediante celdas fantasma o borrado contextual, la señal `_on_a_changed` ajusta de inmediato la dimensión del vector $b$ para preservar la conformabilidad $m = \text{dim}(b)$.
    - *Badge de Validación:* `self.badge` evalúa en tiempo real la consistencia dimensional y sintáctica. Si es conformable, se ilumina en verde sage `color-feedback-success` (`#81B29A`): `"✓ Ecuación conformable: A (m×n) · x (n×1) = b (m×1)"`.
    - *Contenedor de Incógnita $x$:* La tarjeta `x_card` actualiza su título reactivamente: `x_title` muestra `"x ∈ ℝⁿ"`.

- **Paso 03: Ejecución de la resolución de la ecuación matricial**
  - **Interacción:** El usuario hace clic en el botón principal `"Resolver ecuación matricial  A · x = b"` o en el botón de cabecera `"▶  Resolver A · x = b"`.
  - **Componente:** `self.solve_btn` y `self.header_solve_btn` ([`MatrixEquationsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_equations_view.py#L128-L134), [L216-L222](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_equations_view.py#L216-L222)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor del vector $x$ ([`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1)) dibuja el vector solución. La sección inferior de pestañas `results_tabs` se actualiza y la vista realiza auto-scroll suave asegurando su visibilidad (`ensureWidgetVisible`).
    - *Colores y Tokens:* Si existe solución, el subtítulo de la incógnita cambia de `"Incógnita a resolver"` a `"Solución x (n×1)"`. Si el sistema es inconsistente, muestra `"Sin solución"`.
    - *Feedback de Carga:* Cero latencia percibida; resolución exacta en fracciones estándar de Python.

- **Paso 04: Inspección de la comprobación analítica (Pestaña 1)**
  - **Interacción:** El usuario examina la primera pestaña de resultados: `"✓  Comprobación y Solución"`.
  - **Componente:** [`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80) y tarjeta de comprobación `product_card` con etiqueta `product_label`.
  - **Comportamiento visual:**
    - *Dashboard izquierdo:* Badge de clasificación semántica, variables básicas y libres, y solución analítica/paramétrica.
    - *Tarjeta derecha de comprobación:* Banner verde de alto contraste: `"<span style='font-size:22px; font-weight:700;'>✓ ¡Igualdad exacta comprobada!  A · x = b (igualdad exacta)</span>"`.
    - *Checklist componente a componente:* Cada fila de la multiplicación matricial se desglosa en tamaño grande (22px monospace) contrastando el producto fila por columna $(A \cdot x)_i$ contra el término independiente $b_i$: `✓ Fila i: (A·x)_i = K  =  b_i = K`.

- **Paso 05: Inspección del procedimiento paso a paso (Pestaña 2)**
  - **Interacción:** El usuario hace clic en la segunda pestaña: `"📋  Procedimiento Paso a Paso [A | b]"`, y avanza/retrocede mediante los botones de navegación.
  - **Componente:** `self.stepper` ([`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32)).
  - **Comportamiento visual:**
    - *Carrusel:* Muestra la matriz aumentada $[A \mid b]$ con pivotes resaltados, fórmulas elementales de fila en notación de libro (`latex_to_book_html`), explicación heurística y conmutador entre vista fraccionaria y decimal.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Caracteres alfabéticos o no numéricos en celdas de $A$ o $b$ | Celdas [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) y Badge Superior `self.badge` | Celdas con borde rojo `color-feedback-error` (`#EE6C4D`). Badge superior en rojo. Ambos botones de resolución bloqueados (`setEnabled(False)`). Si se fuerza clic: modal `QMessageBox`. | **Badge:** `"✕ Hay entradas no numéricas en A o en b."`<br>**Modal:** `"Corrige las celdas no numéricas."` | Reemplazar los caracteres inválidos por enteros, fracciones (`a/b`) o decimales. |
| Discrepancia dimensional ($m \ne \text{dim}(b)$) provocada por pegado externo o edición desincronizada | Badge Superior `self.badge` y Botones de Acción | Badge en rojo quemado `color-feedback-error`. Botones de resolución deshabilitados. | **Badge:** `"✕ La ecuación no es conformable: A tiene m filas y b ∈ ℝ^{dim(b)}. Se requiere dim(b) = filas de A."` | Ajustar las filas de $A$ o la dimensión de $b$ para que coincidan exactamente. |
| Sistema incompatible sin solución (SI) | Visor `x_view` y Tarjeta `product_card` | `x_view` se vacía (`clear()`), subtítulo indica `"Sin solución"`. Dashboard muestra badge rojo `color-feedback-error`. `product_label` en texto plano. | **x_subtitle:** `"Sin solución"`<br>**product_label:** `"No hay vector x que satisfaga A x = b (sistema inconsistente)."` | Informativo pedagógico. El usuario puede modificar $b$ o los coeficientes para obtener compatibilidad. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Tarjeta de Ecuación Central (`equation_card`)
- **Organización espacial:** Disposición horizontal continua $[A] \cdot [x] = [b]$ que refleja el modelo mental matemático directo del usuario.
- **Operadores visuales:** Símbolos de multiplicación `·` (34px) e igualdad `=` (30px) renderizados en `color-interactive-idle` (`#98C1D9`).

#### B. Incógnita Vectorial (`x_card` y `x_view`)
- **Empty / Initial State:** Caja elevada interna (`color-surface-inner` `#242028`), título `"x ∈ ℝⁿ"`, subtítulo en cursiva `"Incógnita a resolver"`, visor vacío sin corchetes activos.
- **Solved State:** Subtítulo `"Solución x (n×1)"`, visor [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1) con corchetes cerrados y fracciones simplificadas.

#### C. Tarjeta de Comprobación de Producto (`product_card`)
- **Idle State:** `"Resuelve para verificar el producto matricial."` en texto tenue.
- **Success State:** Contenedor verde translúcido (`rgba(129, 178, 154, 0.12)`), borde verde sage, y filas comparativas de 22px con marcas `✓`.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #1 - Visibilidad del estado del sistema]:** En sistemas indeterminados (SCI), el visor de incógnita $x$ solo muestra la solución particular $p$ (con variables libres en cero), lo cual puede confundir a un estudiante haciéndole creer que esa es la única solución. Aunque el Dashboard y la tarjeta de producto aclaran la forma paramétrica general ($x = p + t_1 v_1$), el visor gráfico de $x$ debería exhibir una insignia visual de *“Solución particular (variables libres = 0)”*.
2. **[Nielsen #7 - Flexibilidad y eficiencia]:** Si el usuario expande la matriz $A$ añadiendo columnas (más incógnitas que ecuaciones), el vector $b$ mantiene su dimensión correcta ($m$), pero el usuario no tiene forma directa de resetear rápidamente a un sistema cuadrado sin borrar celdas una a una o pulsar `"Limpiar"`.

---

## [EQM_FLUJO_02] - Comprobación de Propiedad Distributiva de A · x (A(u + v) = Au + Av)

### 1. Metadatos Técnicos
- **Objetivo:** Demostrar y comprobar rigurosamente la propiedad de linealidad distributiva del producto matriz-vector $A(u + v) = A \cdot u + A \cdot v$ para cualquier matriz $A \in \mathbb{R}^{m \times n}$ y cualquier par de vectores $u, v \in \mathbb{R}^n$, contrastando lado a lado el Miembro Izquierdo (LHS) y el Miembro Derecho (RHS) con desglose algebraico formal paso a paso y verificación de igualdad componente a componente.
- **Punto de inicio:** Ruta: Stack Index 3 (`Ctrl+4`), Pestaña principal index 1 (`"Propiedades del Producto  A · x"`), selector de modo en `"1. Propiedad Distributiva"`, componente: [`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L71).
- **Condiciones previas:** Cuadrícula $A$ configurada en $m \times n$ (inicialmente $2 \times 3$). Vectores $u$ y $v$ en $\mathbb{R}^n$ ($n = 3$). Modo activo: `distributive`.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección del modo distributivo y ajuste de dimensiones**
  - **Interacción:** El usuario hace clic en el botón `"1. Propiedad Distributiva:  A(u + v) = A·u + A·v"` o pulsa `"Distributiva (2×3)"` en la barra de presets.
  - **Componente:** `self.btn_mode_dist` ([`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L173-L178)) y `dim_card` con spinboxes `spin_m`, `spin_n`, `spin_dim_u`, `spin_dim_v`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor central de vectores `vector_controls_stack` conmuta a la página distributiva mostrando $(u + v)$ entre paréntesis envolventes estilizados. La barra de dimensiones muestra el control `dim(v)` (`spin_dim_v`).
    - *Colores y Tokens:* Botón de modo se activa en clase `modeToggle`.
    - *Sincronización:* Botón `"⟳ Sincronizar dimensiones"` ajusta instantáneamente $\text{dim}(u)$ y $\text{dim}(v)$ a la cantidad de columnas $n$ de la matriz $A$.

- **Paso 02: Ingreso de datos en Matriz A y Vectores u, v**
  - **Interacción:** El usuario edita los coeficientes de $A$, $u$ y $v$.
  - **Componente:** `self.grid_a` ([`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1)), `self.vec_u_dist` y `self.vec_v_dist` ([`VectorColumnEditor`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/vectors_view.py#L71)).
  - **Comportamiento visual:**
    - *Validación reactiva:* Al cambiar cualquier valor, `_refresh_validation()` verifica que $\text{dim}(u) = \text{dim}(v) = n$. Si se cumple, el badge superior adopta verde sage `color-feedback-success`: `"✓ Conformable: A (m×n) · (u + v) (n×1) = A·u (m×1) + A·v (m×1). Ambos lados dan un vector en ℝᵐ."`.
    - *Habilitación:* El botón principal `"Verificar Propiedad Distributiva"` y el botón de cabecera `"▶  Verificar Propiedad"` se habilitan.

- **Paso 03: Ejecución de la verificación formal**
  - **Interacción:** El usuario hace clic en `"Verificar Propiedad Distributiva  A(u + v) = A·u + A·v"`.
  - **Componente:** `self.verify_btn` ([`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L290-L296)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Las pestañas de resultados se llenan de forma síncrona y la vista hace auto-scroll asegurando su visualización.
    - *Banner de Igualdad:* `equality_banner` se ilumina en verde sage (`#81B29A`): `"✓ ¡PROPIEDAD DISTRIBUTIVA DEMOSTRADA RIGUROSAMENTE!  A(u + v) = A·u + A·v
Ambos miembros de la ecuación coinciden exactamente en cada componente de ℝᵐ."`.
    - *Símbolo Central:* El indicador central entre columnas cambia de `≟` a `✓ =` en 24px negrita verde.

- **Paso 04: Análisis comparativo lado a lado (Pestaña 1)**
  - **Interacción:** El usuario inspecciona los resultados en la pestaña `"✓  Demostración y Comprobación"`.
  - **Componente:** Columna izquierda `lhs_card`, Columna derecha `rhs_card` y tarjeta inferior `checklist_card`.
  - **Comportamiento visual:**
    - *Columna LHS:* Muestra la suma intermedia $(u + v) \in \mathbb{R}^n$ en `lhs_intermediate_view` y el producto final $A(u + v) \in \mathbb{R}^m$ en `lhs_final_view`.
    - *Columna RHS:* Muestra los productos parciales $Au$ y $Av$ en `rhs_view1` y `rhs_view2`, y su suma final $(Au + Av) \in \mathbb{R}^m$ en `rhs_final_view`.
    - *Checklist componente a componente:* Cada renglón de $\mathbb{R}^m$ se contrasta en 22px monospace con marca `✓` verde: `✓ Fila i: (A·(u + v))_i = K  =  (A·u + A·v)_i = K`.

- **Paso 05: Exploración del desglose matemático riguroso (Pestaña 2)**
  - **Interacción:** El usuario hace clic en la pestaña `"📋  Desglose Matemático Paso a Paso"`.
  - **Componente:** `self.steps_text` dentro de un área con scroll ([`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L559-L571)).
  - **Comportamiento visual:**
    - *Microcopia Matemática:* Renderizado en RichText monospace con desglose por secciones:
      - `--- LADO IZQUIERDO (LHS) ---` con la suma vectorial y el producto fila por columna.
      - `--- LADO DERECHO (RHS) ---` con ambos productos y la adición posterior.
      - `--- CONCLUSIÓN FORMAL ---` con la demostración de sumatoria: $\sum_j A_{ij}(u_j + v_j) = \sum_j A_{ij} u_j + \sum_j A_{ij} v_j$.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Dimensiones de vectores dispares ($	ext{dim}(u) 
e 	ext{dim}(v)$) | Badge Superior `self.badge` | Badge en rojo quemado `color-feedback-error`. Botones de verificación deshabilitados. | **Badge:** `"✕ Vectores no conformables: dim(u) = X ≠ dim(v) = Y. La suma (u + v) requiere vectores de la misma dimensión."` | Igualar los valores de `dim(u)` y `dim(v)` con los spinboxes o pulsar `"⟳ Sincronizar dimensiones"`. |
| Columnas de $A$ distintas a la dimensión de los vectores ($n 
e 	ext{dim}(u)$) | Badge Superior `self.badge` | Badge en rojo. Botones de verificación deshabilitados. | **Badge:** `"✕ Producto no conformable: A tiene n columnas pero u y v tienen dimensión dim(u). Se requiere que dim(u) = dim(v) = n (número de columnas de A)."` | Pulsar `"⟳ Sincronizar dimensiones"` para igualar automáticamente las dimensiones de los vectores al número de columnas de $A$. |
| Celdas con entradas no numéricas en $A$, $u$ o $v$ | Celdas de las cuadrículas y Badge Superior | Celdas con borde rojo. Badge en rojo. Botón de verificación bloqueado. | **Badge:** `"✕ Hay celdas con valores no numéricos en la matriz o los vectores."` | Corregir las celdas afectadas con valores numéricos válidos. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Barra de Control de Dimensiones (`dim_card`)
- **Spinboxes sincronizables:** `spin_m` (filas de $A$, 1-8), `spin_n` (columnas de $A$, 1-8), `spin_dim_u` (1-8), `spin_dim_v` (1-8).
- **Acción Rápida:** Botón `"⟳ Sincronizar dimensiones"` con cursor `PointingHandCursor` que unifica las dimensiones de los vectores con las columnas de $A$.

#### B. Banner de Igualdad (`equality_banner`)
- **Idle State:** Fondo `#242028`: `"Realiza la verificación para comparar ambos lados de la igualdad."`
- **Verified State:** Fondo verde sage `#81B29A`, texto `#1A181B` en negrita 16px.
- **Mismatch State:** Fondo rojo quemado `#EE6C4D` con símbolo `≠` en el divisor central.

#### C. Visores Matriciales de Resultados (`BookMatrixWidget`)
- **LHS:** `lhs_intermediate_view` (vector $u+v$) y `lhs_final_view` (vector $A(u+v)$).
- **RHS:** `rhs_view1` (vector $Au$), `rhs_view2` (vector $Av$) y `rhs_final_view` (vector $Au+Av$).
- **Estilo:** Altura mínima garantizada (110px a 130px), corchetes de libro y fracciones apiladas simétricas.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #7 - Flexibilidad y atajos de eficiencia]:** Aunque el botón `"⟳ Sincronizar dimensiones"` es una excelente solución de usabilidad, sería aún más ergonómico ofrecer un checkbox de *“Bloquear dimensiones sincronizadas (vincular n a vectores)”* para que al alterar las columnas de $A$, los vectores se redimensionen automáticamente sin requerir un clic adicional.
2. **[Nielsen #8 - Claridad visual]:** En pantallas con altura reducida ($< 768\text{ px}$), la disposición vertical con doble fila de visores en el RHS ($Au$, $Av$ arriba y $Au+Av$ abajo) genera una tarjeta muy alta que obliga a hacer scroll vertical continuo para contrastar la comprobación con el checklist.

---

## [EQM_FLUJO_03] - Comprobación de Homogeneidad de A · x (A(c · u) = c(Au))

### 1. Metadatos Técnicos
- **Objetivo:** Demostrar y comprobar formalmente la propiedad de homogeneidad (multiplicación por escalar) del producto matriz-vector $A(c \cdot u) = c \cdot (A \cdot u)$ para cualquier matriz $A \in \mathbb{R}^{m \times n}$, cualquier vector $u \in \mathbb{R}^n$ y cualquier escalar $c \in \mathbb{R}$, evaluando el miembro izquierdo y derecho con verificación exacta en fracciones y desglose analítico de conmutatividad escalar.
- **Punto de inicio:** Ruta: Stack Index 3 (`Ctrl+4`), Pestaña principal index 1 (`"Propiedades del Producto  A · x"`), selector de modo en `"2. Homogeneidad / Escalar"`, componente: [`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L71).
- **Condiciones previas:** Matriz $A$ de $m \times n$, vector $u \in \mathbb{R}^n$, escalar $c$ con valor numérico válido (por defecto `"3"` o `"3/2"` en presets). Modo activo: `homogeneity`.

### 2. Flujo Principal (Happy Path) - Paso a Paso

- **Paso 01: Selección del modo de homogeneidad y carga de presets**
  - **Interacción:** El usuario hace clic en `"2. Homogeneidad / Escalar:  A(c·u) = c·(A·u)"` o pulsa el botón `"Homogeneidad (2×3)"` en la cabecera.
  - **Componente:** `self.btn_mode_homo` ([`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L180-L185)) y botón preset `sample_homo`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El contenedor `vector_controls_stack` conmuta a la página de homogeneidad, mostrando la tarjeta del escalar $c$ y el vector $u$ dentro de paréntesis $(c \cdot u)$.
    - *Barra de Dimensiones:* Los controles de `dim(v)` se ocultan automáticamente (`setVisible(False)`), simplificando la interfaz.
    - *Textos y Microcopia:* Título de entrada: `"Entrada de Datos:  A ∈ M_{m×n},  u ∈ ℝⁿ,  c ∈ ℝ"`. Botón principal: `"Verificar Propiedad de Homogeneidad  A(c·u) = c·(A·u)"`.

- **Paso 02: Ingreso de componentes y definición del escalar c**
  - **Interacción:** El usuario introduce coeficientes en la matriz $A$, en el vector $u$, y un escalar entero, fraccionario o decimal en el campo `input_c` (ej. `3/2`, `-4`, `0.25`).
  - **Componente:** `self.input_c` (`QLineEdit` con ID `scalarField`), `self.grid_a` y `self.vec_u_homo`.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Campo $c$ con fuente Monospace `Fira Code` 14pt centrada. Al modificarlo, se valida mediante `parse_scalar()`.
    - *Badge de Validación:* Si $c$ es válido y $n = \text{dim}(u)$, el badge se ilumina en verde sage: `"✓ Conformable: A (m×n) · (c·u) (n×1) = (c) · (A·u) (m×1). Ambos lados dan un vector en ℝᵐ."`.

- **Paso 03: Ejecución de la comprobación de homogeneidad**
  - **Interacción:** El usuario pulsa `"Verificar Propiedad de Homogeneidad  A(c·u) = c·(A·u)"`.
  - **Componente:** `self.verify_btn` ([`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L735-L742)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Las pestañas de resultados se actualizan y la vista desplaza el scroll suavemente hacia ellas.
    - *Banner de Igualdad:* Se muestra en verde sage (`#81B29A`): `"✓ ¡PROPIEDAD DE HOMOGENEIDAD DEMOSTRADA RIGUROSAMENTE!  A(c·u) = c·(A·u)
Con escalar c = [valor], ambos miembros coinciden en cada componente de ℝᵐ."`.
    - *Símbolo Central:* Cambia a `✓ =` en 24px verde.

- **Paso 04: Inspección comparativa lado a lado (Pestaña 1)**
  - **Interacción:** El usuario examina las columnas LHS y RHS en la pestaña de comprobación.
  - **Componente:** `lhs_card`, `rhs_card` y `checklist_label`.
  - **Comportamiento visual:**
    - *LHS:* `lhs_intermediate_view` muestra el vector escalado $c \cdot u \in \mathbb{R}^n$; `lhs_final_view` muestra $A(c \cdot u) \in \mathbb{R}^m$.
    - *RHS:* `rhs_view1` muestra el producto intermedio $Au \in \mathbb{R}^m$; el segundo visor intermedio `rhs_view2` permanece oculto; `rhs_final_view` muestra el escalado exterior $c(Au) \in \mathbb{R}^m$.
    - *Checklist:* Tarjetas horizontales de 22px monospace con marca `✓` verde: `✓ Fila i: (A·(c·u))_i = K  =  (c·(A·u))_i = K`.

- **Paso 05: Inspección de la demostración formal (Pestaña 2)**
  - **Interacción:** El usuario hace clic en `"📋  Desglose Matemático Paso a Paso"`.
  - **Componente:** `self.steps_text` ([`MatrixVectorPropertiesView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/matrix_vector_properties_view.py#L904-L920)).
  - **Comportamiento visual:**
    - *Demostración Formal:* Muestra la traza aritmética completa para LHS y RHS y la demostración teórica por sumatorias:
      $$(A(c u))_i = \sum_j A_{ij} (c u_j) = c \sum_j A_{ij} u_j = c (Au)_i = (c (Au))_i$$
      concluyendo formalmente que la multiplicación por escalar conmuta con el producto matriz-vector en todo $\mathbb{R}^m$.

---

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Escalar $c$ inválido (ej: texto alfabético `xyz`, división por cero `2/0`, vacío) | Campo `input_c` y Badge Superior `self.badge` | Badge en rojo quemado `color-feedback-error`. Botones de verificación deshabilitados. | **Badge:** `"✕ Escalar c inválido: ingrese un número entero, fracción (a/b) o decimal."` | Escribir un valor escalar válido en el campo $c$. |
| Incompatibilidad entre columnas de $A$ y dimensión de $u$ ($n 
e 	ext{dim}(u)$) | Badge Superior `self.badge` | Badge en rojo. Botón de verificación deshabilitado. | **Badge:** `"✕ Producto no conformable: A tiene n columnas pero u tiene dimensión dim(u). Se requiere que dim(u) = n (número de columnas de A)."` | Ajustar la dimensión de $u$ con `spin_dim_u` o pulsar `"⟳ Sincronizar dimensiones"`. |
| Celdas con entradas no numéricas en $A$ o en $u$ | Celdas de cuadrícula y Badge Superior | Celdas con borde rojo. Badge en rojo. Botones bloqueados. | **Badge:** `"✕ Hay celdas inválidas."` | Corregir las celdas marcadas con borde rojo. |

---

### 4. Matriz de Estados de Componentes Clave

#### A. Campo de Escalar (`input_c`)
- **Estilo:** `QLineEdit` centrado con fondo `color-surface-inner` (`#242028`), texto `color-text-primary` (`#E0FBFC`), fuente Monospace `Fira Code` 14pt.
- **Microcopia de ayuda:** Subtítulo `"c ∈ ℝ (ej. 3, -1/2)"` en tipografía tenue de 12px.
- **Foco:** Auto-selección completa al entrar.

#### B. Tarjeta de Operandos de Homogeneidad (`_build_homogeneity_inputs`)
- **Estructura visual:** Agrupación visual con paréntesis estilizados de 40px en `color-interactive-idle` envolviendo el escalar $c$ y el vector $u$ con el operador `·` central.

#### C. Columna Derecha (RHS) en Modo Homogeneidad
- **Adaptabilidad reactiva:** Oculta limpiamente `rhs_view2` (utilizado solo en distributiva) para evitar mostrar cuadros vacíos, dejando visible únicamente el producto intermedio $Au$ y el resultado final escalado $c(Au)$.

---

### 5. Brechas Heurísticas Identificadas [UX Gaps]

1. **[Nielsen #6 - Reconocimiento antes que recuerdo]:** En el campo del escalar $c$, al escribir un número fraccionario (ej. `3/2`), la interfaz no despliega una pequeña etiqueta con su aproximación decimal equivalente (ej. `≈ 1.5`), lo cual ayudaría a usuarios que verifican ejercicios con calculadoras científicas tradicionales.
2. **[Nielsen #1 - Visibilidad del estado]:** Si el escalar $c$ se define como $0$, la propiedad sigue siendo formalmente válida ($A(0 \cdot u) = 0 \cdot (Au) = \mathbf{0}$), pero la interfaz no ofrece una nota explicativa que destaque el caso particular del vector nulo, perdiendo una valiosa oportunidad didáctica.

---

## Resumen Ejecutivo de la Auditoría del Módulo 4

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[EQM_FLUJO_01] Ecuación A · x = b** | **9.6 / 10** | Disposición matemática continua $[A][x]=[b]$; sincronización reactiva de filas; doble pestaña (dashboard con producto fila por vector y carrusel de pasos). | En sistemas SCI, el visor $x$ solo muestra la solución particular sin rotular explícitamente que las variables libres están en cero. |
| **[EQM_FLUJO_02] Propiedad Distributiva** | **9.4 / 10** | Comparación visual lado a lado (LHS vs RHS); botón de sincronización dimensional rápida; demostración formal por sumatorias. | Falta opción de auto-vincular dimensiones permanentes; altura excesiva de la tarjeta RHS en pantallas pequeñas. |
| **[EQM_FLUJO_03] Homogeneidad** | **9.5 / 10** | Adaptación dinámica del layout ocultando operandos innecesarios; soporte de escalares en fracciones exactas; checklist de 22px. | Falta indicador de valor decimal para fracciones en el escalar $c$; sin nota pedagógica ante $c=0$. |

---

*Fin del reporte técnico del Módulo 4.*


# Procede con la auditoría profunda y detallada del módulo: Módulo 5: Determinantes, Regla de Sarrus, Cofactores y Adjunta

---

## [DET_FLUJO_01] - Evaluación de Determinante por Triangulación / Operaciones Elementales

### 1. Metadatos Técnicos
- **Objetivo:** Calcular el determinante $\det(A)$ de una matriz cuadrada de orden $n \in [1, 8]$ mediante eliminación gaussiana hacia una forma triangular superior, rastreando el impacto de intercambios de fila, escalamientos y operaciones de cizallamiento en el valor del determinante.
- **Punto de inicio:** Ruta: Stack Index 4 (`Ctrl+5`), botón de modo `"Triangulación"` (modo por defecto) en [`DeterminantsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L87).
- **Condiciones previas:** Matriz $A$ cuadrada $n \times n$. Celdas con valores numéricos válidos (enteros, fracciones o decimales). Orden $n$ entre 1 y 8 (`MAX_DETERMINANT_ORDER = 8`).

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01:**
  - **Interacción:** El usuario selecciona el orden deseado mediante los botones `+` o `−` en la barra de acciones superior.
  - **Componente:** `self.order_down_btn`, `self.order_up_btn`, `self.order_value_label` en [`DeterminantsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L134-L152).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La cuadrícula [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) redimensiona su estructura conservando los valores de submatrices previas y rellenando nuevas entradas con `0`.
    - *Colores y Tokens:* `order_value_label` actualiza el texto a `"n = 3"`. Los botones `+` y `−` se habilitan o deshabilitan dinámicamente si se alcanza el límite ($1$ u $8$).
    - *Textos y Microcopia:* Label: `"n = {order}"`. Tooltips o labels: `"Orden n"`.
    - *Feedback de Carga:* Inmediato en hilo de UI.
- **Paso 02:**
  - **Interacción:** El usuario introduce coeficientes numéricos en las celdas de la matriz $A$.
  - **Componente:** [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) dentro de `self.grid`.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Entrada válida conserva fondo `color-surface-inner` (`#242028`) y borde sutil. El badge de estado superior cambia a `"Matriz cuadrada lista para calcular."` sobre fondo `color-surface-inner` con texto `color-text-muted` (`#7A7585`).
    - *Textos y Microcopia:* `compute_btn` (`"Calcular"`) permanece habilitado.
- **Paso 03:**
  - **Interacción:** El usuario hace clic en el botón `"Calcular"`.
  - **Componente:** `self.compute_btn` (`QPushButton` con ID `primaryAction`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El panel central (`self.stepper`) y el panel derecho (`right_card`) se actualizan instantáneamente.
    - *Colores y Tokens:* El badge superior adopta `color-feedback-success` (`#81B29A`) si la matriz no es singular, o `color-feedback-error` (`#EE6C4D`) si es singular ($\det(A)=0$).
    - *Textos y Microcopia:*
      - `det_value_label`: despliega el valor exacto en tamaño grande (28px, negrita, tipografía Monospace): `"det(A) = {valor}"`.
      - `diagnosis_label`: despliega el diagnóstico: `"Matriz no singular (invertible). Rango completo n={order}."` o `"Matriz singular (no invertible). Rango deficiente."`.
      - Badge: `"det(A) = {valor}. Matriz no singular."`.
- **Paso 04:**
  - **Interacción:** El usuario recorre las etapas de triangulación con los botones `"Anterior"` y `"Siguiente"` del carrusel.
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`self.stepper`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La matriz de libro intermedia ([`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1)) ilustra la evolución hacia la forma triangular superior.
    - *Colores y Tokens:* El pivote activo se destaca en color sage `color-feedback-success` (`#81B29A`).
    - *Textos y Microcopia:* La fórmula explica la operación elemental (ej. $F_2 \rightarrow F_2 - \frac{3}{2} F_1$) y aclara si hubo permutación de filas que invirtiera el signo del determinante ($\times (-1)$).

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Entrada no numérica en celda | [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) y `self.badge` | Borde rojo en celda (`#EE6C4D`). Badge superior en `color-feedback-error`. `compute_btn` se deshabilita. | `"Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales."` | Editar el valor de la celda hasta ingresar un número válido. |
| Intento de redimensionar orden con celdas inválidas | Modal nativo [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L689) | Modal emergente con icono de advertencia. | **Título:** `"Entrada inválida"`<br>**Cuerpo:** `"Corrige las celdas antes de cambiar el orden."` | Pulsar `"OK"` en el modal y corregir las celdas erróneas. |
| Matriz rectangular (en caso de inconsistencia de shape) | `self.badge` | Badge superior en fondo rojo de error. Botón `"Calcular"` bloqueado. | `"El determinante solo está definido para matrices cuadradas (n×n). A es {rows}×{cols}."` | Pulsar los botones de orden para forzar cuadratura $n \times n$. |
| Matriz de orden superior a 8 | `self.badge` | Badge superior en fondo rojo de error. | `"El orden n debe estar entre 1 y 8."` | Reducir el orden con el botón `−`. |

### 4. Matriz de Estados de Componentes Clave
- **Botón de Modo Triangulación (`triangulation_mode_btn`):**
  - *Normal:* Fondo tenue `color-surface-inner` (`#242028`), texto `color-text-primary`.
  - *Checked:* Elevado con borde y fondo realzados en `color-interactive-idle` (`#98C1D9`).
- **Botones de Redimensionamiento (`order_down_btn`, `order_up_btn`):**
  - *Habilitado:* Fondo secundario, cursor `PointingHandCursor`, ancho fijo de 36px.
  - *Disabled:* Opacidad reducida cuando $n=1$ (para decremento) o $n=8$ (para incremento). Bloquea clics.
- **Visor de Determinante (`det_value_label`):**
  - *Empty State:* `"det(A) = —"` antes de calcular.
  - *Calculated State:* Texto en 28px, negrita, seleccionable con ratón (`TextSelectableByMouse`).

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #1 - Visibilidad del estado del sistema]:** No existe un paso final en el carrusel que resuma el cálculo explícito del producto de la diagonal principal ($\det(A) = u_{11} \cdot u_{22} \cdots u_{nn} \cdot (-1)^s$). El usuario debe deducir mentalmente el producto al ver la matriz triangular final.
2. **[Nielsen #7 - Flexibilidad y atajos]:** Cambiar de orden $2 \times 2$ a $7 \times 7$ requiere pulsar 5 veces consecutivas el botón `+`. Sería mucho más ergonómico contar con un `QSpinBox` directo de orden en lugar de botones incrementales únicos.

---

## [DET_FLUJO_02] - Evaluación por Regla de Sarrus (3×3)

### 1. Metadatos Técnicos
- **Objetivo:** Evaluar el determinante de una matriz de orden estricto $3 \times 3$ mediante la regla mnemotécnica de Sarrus (ampliación por columnas/filas, suma de productos de las diagonales principales menos suma de productos de las diagonales secundarias).
- **Punto de inicio:** Ruta: Stack Index 4 (`Ctrl+5`), botón de modo `"Sarrus (3×3)"`.
- **Condiciones previas:** La matriz $A$ debe tener dimensiones exactamente iguales a $3 \times 3$. Si el orden es distinto, el cálculo se bloquea.

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01:**
  - **Interacción:** El usuario hace clic en el botón `"Sarrus (3×3)"` en la barra de modos superior, o pulsa el botón de preset `"Ejemplo Sarrus"`.
  - **Componente:** `self.sarrus_mode_btn` o `sample_sarrus` en [`DeterminantsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L111-L191).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Si se pulsó `"Ejemplo Sarrus"`, se carga la matriz académica de la Sesión 11 (Diapositiva 26) y se evalúa automáticamente.
    - *Colores y Tokens:* `sarrus_mode_btn` pasa a estado checked. El panel de Laplace y la caja de propiedades de determinantes se ocultan (`setVisible(False)`).
    - *Textos y Microcopia:* Si la matriz no es $3 \times 3$, el badge advierte la restricción dimensional.
- **Paso 02:**
  - **Interacción:** Si el orden no es 3, el usuario ajusta el orden con los botones `+`/`−` hasta alcanzar `n = 3`.
  - **Componente:** `self.order_up_btn` / `self.order_down_btn`.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Al alcanzar $n=3$, el badge superior pasa a estado neutro `"Matriz cuadrada lista para calcular."` y el botón `"Calcular"` se habilita.
- **Paso 03:**
  - **Interacción:** El usuario hace clic en `"Calcular"`.
  - **Componente:** `self.compute_btn`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El carrusel central se puebla con el desglose algebraico de Sarrus.
    - *Colores y Tokens:* `det_value_label` muestra el resultado (ej. `"det(A) = 36"`). El badge adopta verde o rojo según singularidad.
    - *Textos y Microcopia:* El carrusel detalla el producto de las tres diagonales principales $(+) (a_{11}a_{22}a_{33} + a_{12}a_{23}a_{31} + a_{13}a_{21}a_{32})$ y las tres diagonales secundarias $(-)(a_{13}a_{22}a_{31} + a_{11}a_{23}a_{32} + a_{12}a_{21}a_{33})$.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Selección de Sarrus con orden $n \ne 3$ (ej. $n=2$ o $n=4$) | `self.badge` y `self.compute_btn` | Badge superior en color `color-feedback-error` (`#EE6C4D`). Botón `"Calcular"` inhabilitado (`setEnabled(False)`). | `"La regla de Sarrus solo está definida para matrices 3×3."` | Pulsar los botones de orden hasta fijar $n=3$, o cambiar de método (ej. Triangulación o Laplace). |
| Presencia de celdas no numéricas en matriz 3x3 | `self.grid` y `self.badge` | Borde rojo en celdas inválidas. Badge en error. Botón `"Calcular"` bloqueado. | `"Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales."` | Editar celdas con escalares válidos. |

### 4. Matriz de Estados de Componentes Clave
- **Botón de Modo Sarrus (`sarrus_mode_btn`):**
  - *Checked:* Resaltado activo.
  - *Unchecked:* Modo neutro.
- **Botón Preset Sarrus (`sample_sarrus`):**
  - *Acción:* Ejecuta `load_sarrus_example()`, conmutando el modo a Sarrus, seteando la matriz $\begin{pmatrix} 2 & -1 & 0 \\ -2 & 3 & 4 \\ -5 & 1 & 6 \end{pmatrix}$ y ejecutando el cálculo en un solo clic.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #5 - Prevención de errores]:** Si el usuario se encuentra en orden $n=4$ y hace clic en `"Sarrus (3×3)"`, la interfaz se bloquea y muestra un badge de error. La interfaz debería auto-ajustar el orden a $n=3$ de forma inteligente o advertir mediante un toast antes de bloquear la acción.
2. **[Nielsen #8 - Claridad visual]:** La representación de Sarrus en el carrusel muestra fórmulas en texto, pero carece de un diagrama esquemático con las líneas diagonales continuas y punteadas características del método gráfico de Sarrus.

---

## [DET_FLUJO_03] - Expansión por Cofactores de Laplace (Fila o Columna)

### 1. Metadatos Técnicos
- **Objetivo:** Calcular el determinante mediante el teorema de expansión de Laplace a lo largo de una fila o columna específica seleccionada por el usuario, mostrando la sumatoria ponderada de elementos por sus respectivos cofactores: $\det(A) = \sum_{j=1}^n a_{ij} C_{ij}$.
- **Punto de inicio:** Ruta: Stack Index 4 (`Ctrl+5`), botón de modo `"Cofactores de Laplace"`.
- **Condiciones previas:** Matriz $A$ cuadrada $n \times n$. Selección de eje (Fila o Columna) e índice válido ($1 \le \text{índice} \le n$).

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01:**
  - **Interacción:** El usuario hace clic en el botón `"Cofactores de Laplace"`.
  - **Componente:** `self.laplace_mode_btn` en [`DeterminantsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L112).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La barra de controles secundarios (`self.laplace_box`) se hace visible (`setVisible(True)`).
    - *Colores y Tokens:* Aparecen los botones de eje: `"Fila"` (`laplace_row_btn`) y `"Columna"` (`laplace_col_btn`), junto con el selector numérico `expansion_index`.
    - *Textos y Microcopia:* `expansion_index` muestra el prefijo `"índice 1"`, con rango acotado entre 1 y $n$.
- **Paso 02:**
  - **Interacción:** El usuario elige entre expandir por `"Fila"` o `"Columna"` y ajusta el índice deseado (ej. fila con más ceros para optimizar cálculo).
  - **Componente:** `self.laplace_row_btn`, `self.laplace_col_btn`, `self.expansion_index` (`QSpinBox`).
  - **Comportamiento visual:**
    - *Colores y Tokens:* El botón de eje seleccionado pasa a checked. El spinbox refleja el índice actual.
- **Paso 03:**
  - **Interacción:** El usuario hace clic en `"Calcular"`.
  - **Componente:** `self.compute_btn`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El carrusel de pasos desglosa cada sumando $a_{ij} \cdot C_{ij}$.
    - *Colores y Tokens:* `det_value_label` muestra el valor del determinante.
    - *Textos y Microcopia:* El carrusel muestra la fórmula de cada cofactor: $C_{ij} = (-1)^{i+j} M_{ij}$, renderizando la submatriz del menor complementario $M_{ij}$ y su cálculo intermedio.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Índice de expansión superior al orden actual tras reducción de $n$ | `self.expansion_index` | `_sync_controls` reajusta automáticamente el `maximum` del spinbox al nuevo orden $n$. | Ningún error visible; auto-corrección reactiva en el spinbox. | Transparente para el usuario. |
| Presencia de entradas no numéricas en matriz $A$ | `self.grid` y `self.badge` | Borde rojo en celdas con fallo. Badge superior en error. Botón de cálculo deshabilitado. | `"Corrige las celdas marcadas. Se admiten enteros, fracciones (a/b) y decimales."` | Modificar entradas en la cuadrícula. |

### 4. Matriz de Estados de Componentes Clave
- **Controles de Expansión de Laplace (`laplace_box`):**
  - *Visible:* Exclusivamente en modo `"laplace"`. Oculto en los otros 4 modos.
  - *Botones Fila/Columna:* Exclusivos mediante `axis_group`.
  - *SpinBox `expansion_index`:* Fondo `color-surface-inner` (`#242028`), texto `color-text-primary`, borde `color-interactive-idle`. Rango estrictamente sincronizado con el orden $n$ de la matriz.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #4 - Consistencia y estándares]:** En la cuadrícula de entrada, no se resaltan visualmente la fila o columna seleccionada para la expansión, lo que obliga al usuario a verificar manualmente qué fila corresponde al `"índice 2"`. Un sombreado suave de la fila/columna activa mejoraría notablemente la ergonomía visual.
2. **[Nielsen #2 - Relación entre el sistema y el mundo real]:** La interfaz no sugiere cuál fila o columna contiene la mayor cantidad de ceros (estrategia recomendada en los libros de álgebra lineal para minimizar operaciones).

---

## [DET_FLUJO_04] - Cálculo de Matriz de Menores, Cofactores, Adjunta e Inversa

### 1. Metadatos Técnicos
- **Objetivo:** Construir la matriz completa de menores $M_{ij}$, la matriz de cofactores $C_{ij}$, la matriz adjunta $\operatorname{adj}(A) = C^T$, y calcular la inversa analítica por el método de la adjunta: $A^{-1} = \frac{1}{\det(A)} \operatorname{adj}(A)$ (si $\det(A) \ne 0$).
- **Punto de inicio:** Ruta: Stack Index 4 (`Ctrl+5`), botón de modo `"Matriz Adjunta"`.
- **Condiciones previas:** Matriz $A$ cuadrada $n \times n$. Si $\det(A) = 0$, la adjunta se calcula pero se notifica que no existe inversa.

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01:**
  - **Interacción:** El usuario hace clic en el botón `"Matriz Adjunta"` o pulsa `"Ejemplo Sesión 11"`.
  - **Componente:** `self.adjugate_mode_btn` o `sample_det` en [`DeterminantsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L113-L186).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La sección derecha de adjunta (`adjugate_section`) se prepara para despliegue.
    - *Colores y Tokens:* `adjugate_mode_btn` pasa a estado checked.
- **Paso 02:**
  - **Interacción:** El usuario hace clic en `"Calcular"`.
  - **Componente:** `self.compute_btn`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* En el panel lateral derecho se despliegan simultáneamente 4 tarjetas matriciales en notación de libro ([`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1)):
      1. Matriz de menores $M_{ij}$ (`minors_view`).
      2. Matriz de cofactores $C_{ij}$ (`cofactors_view`).
      3. Matriz adjunta $\operatorname{adj}(A) = C^T$ (`adjugate_view`).
      4. Inversa analítica $A^{-1}$ (`inverse_view`).
    - *Textos y Microcopia:* 
      - Títulos de bloques: `"Matriz de menores Mᵢⱼ"`, `"Matriz de cofactores Cᵢⱼ"`, `"Matriz adjunta adj(A) = Cᵀ"`, `"Inversa por adjunta  A⁻¹ = (1/det A) · adj(A)"`.
      - Readouts: Debajo de cada matriz se incluye una cadena con los valores tabulares (`_matrix_inline`).
      - `diagnosis_label`: `"Matriz no singular (invertible)... La inversa analítica es (1/det A) · adj(A)."`.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Matriz singular ($\det(A) = 0$) | `self.inverse_view` y `self.inverse_readout` | La matriz inversa se limpia (`clear()`). El readout de inversa muestra texto explicativo. Badge en rojo de singularidad. | `inverse_readout`: `"No existe A⁻¹ porque det(A) = 0."`<br>`diagnosis_label`: `"La adjunta está definida, pero no existe A⁻¹."` | Informativo. La adjunta sigue siendo visible para análisis teórico. |
| Matriz no cuadrada | `self.badge` | Badge en color de error. Botón de cálculo bloqueado. | `"El determinante solo está definido para matrices cuadradas (n×n)."` | Ajustar orden con controles de la barra superior. |

### 4. Matriz de Estados de Componentes Clave
- **Sección de Adjunta (`adjugate_section`):**
  - *Visible:* Únicamente en modo `"adjugate"`. Se oculta en los otros 4 modos (`setVisible(False)`).
  - *Visores Matriciales (`minors_view`, `cofactors_view`, `adjugate_view`, `inverse_view`):* Altura mínima de 180px con corchetes de libro y renderizado fraccionario.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #8 - Sobrecarga visual y cognitiva]:** Desplegar 4 matrices completas con sus etiquetas y lecturas en un solo scroll lateral derecho genera una columna excesivamente larga que requiere abundante desplazamiento vertical en pantallas estándar de 1080p. Una distribución en pestañas o acordeones colapsables para Menores / Cofactores / Adjunta / Inversa resultaría mucho más limpia.
2. **[Nielsen #7 - Eficiencia de uso]:** No existe un botón de acción rápida para *"Copiar $A^{-1}$ a la Matriz A"* o enviarla directamente al módulo de Álgebra Matricial.

---

## [DET_FLUJO_05] - Verificación de Propiedades de Determinantes

### 1. Metadatos Técnicos
- **Objetivo:** Comprobar experimentalmente en tiempo real las cuatro propiedades fundamentales de los determinantes contrastando el miembro izquierdo y derecho de cada ley matemática:
  1. Multiplicativa: $\det(AB) = \det(A)\det(B)$.
  2. Transpuesta: $\det(A^T) = \det(A)$.
  3. Inversa: $\det(A^{-1}) = \frac{1}{\det(A)}$ (si $\det(A) \ne 0$).
  4. Escalamiento homogéneo: $\det(kA) = k^n \det(A)$.
- **Punto de inicio:** Ruta: Stack Index 4 (`Ctrl+5`), botón de modo `"Propiedades"`.
- **Condiciones previas:** Matriz $A$ cuadrada $n \times n$, matriz compañera $B$ cuadrada del mismo orden $n \times n$, y escalar $k$ numérico válido.

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01:**
  - **Interacción:** El usuario hace clic en el botón `"Propiedades"` o pulsa `"Ejemplo det(AB)"`.
  - **Componente:** `self.properties_mode_btn` o `sample_properties` en [`DeterminantsView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/determinants_view.py#L114-L192).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La caja de propiedades (`properties_box`) en el panel izquierdo se vuelve visible (`setVisible(True)`), desplegando la segunda cuadrícula para la matriz $B$ (`grid_b`) y el campo para el escalar $k$ (`scalar_k`).
    - *Sincronización:* La matriz $B$ se auto-ajusta para coincidir exactamente con el orden $n$ de la matriz $A$ (`_match_partner_order`).
- **Paso 02:**
  - **Interacción:** El usuario edita las entradas de $A$, $B$ y el escalar $k$.
  - **Componente:** `grid`, `grid_b`, `scalar_k`.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Si todas las entradas son válidas y $A, B$ tienen igual orden, el botón `"Calcular"` permanece habilitado.
- **Paso 03:**
  - **Interacción:** El usuario hace clic en `"Calcular"`.
  - **Componente:** `self.compute_btn`.
  - **Comportamiento visual:**
    - *Cards y Contenedores:* En el panel derecho se activa la lista de verificación `properties_checklist`.
    - *Colores y Tokens:* Cada ley cumplida se muestra en verde `color-feedback-success` (`#81B29A`) con un checkmark `✓`. Si $\det(A)=0$, la propiedad de inversa se muestra en gris atenuado `color-text-muted` (`#7A7585`) con guion `—`.
    - *Textos y Microcopia:* 
      - Badge: `"✓ Las propiedades del determinante se cumplen."`.
      - Fila 1: `"✓  det(AB) = 45 y det(A)·det(B) = 45"`.
      - Fila 2: `"✓  det(Aᵀ) = 9 y det(A) = 9"`.
      - Fila 3: `"✓  det(A⁻¹) = 1/9 y 1/det(A) = 1/9"`.
      - Fila 4: `"✓  det(kA) = 36 = kⁿ det(A), con k = 2"`.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Escalar $k$ con formato inválido (letras, vacío) | `self.badge` y `self.compute_btn` | Badge superior en color de error. Botón de cálculo bloqueado. | `"El escalar k no es un número válido (entero, a/b o decimal)."` | Corregir el valor en el campo `scalar_k`. |
| Celdas inválidas en matriz B | `self.grid_b` y `self.badge` | Celdas en rojo. Badge en error. Botón de cálculo bloqueado. | `"Corrige las celdas de B."` | Rellenar celdas de $B$ con números válidos. |
| Desajuste dimensional entre A y B | `self.badge` | Badge en color de error. | `"A y B deben ser cuadradas del mismo orden para det(AB). A es {rA}×{cA} y B es {rB}×{cB}."` | Redimensionar o usar botón preset. |
| Matriz A singular ($\det(A)=0$) en propiedad inversa | `self.properties_checklist` | Línea de checklist en color gris atenuado con marca `—`. | `"—  det(A⁻¹) no aplica porque det(A) = 0."` | No es un error; es la representación correcta de que no existe inversa. |

### 4. Matriz de Estados de Componentes Clave
- **Caja de Propiedades (`properties_box`):**
  - *Visible:* Exclusivamente en modo `"properties"`.
  - *Campo `scalar_k`:* `QLineEdit` centrado, tipografía monospace, predeterminado `"2"`.
- **Checklist de Propiedades (`properties_checklist`):**
  - *Visible:* Exclusivamente en modo `"properties"`.
  - *Formato:* Bloques HTML dinámicos de 18px con interletraje espaciado y contraste validado.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #1 - Visibilidad del estado del sistema]:** La matriz $B$ se ubica debajo de la matriz $A$ en el panel izquierdo. En órdenes $n \ge 3$, la matriz $B$ queda fuera del viewport visible inmediato, requiriendo scroll para verificar sus entradas.
2. **[Nielsen #6 - Reconocimiento antes que recuerdo]:** En la cuarta propiedad ($\det(kA) = k^n \det(A)$), sería de gran valor didáctico desplegar explícitamente el cálculo de la potencia: $k^n = 2^2 = 4 \implies 4 \cdot 9 = 36$.

---

## Resumen Ejecutivo de la Auditoría del Módulo 5

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[DET_FLUJO_01] Triangulación** | **9.4 / 10** | Trazador de operaciones elementales exhaustivo; diagnóstico automático de singularidad; fracciones exactas. | Falta resumen explícito del producto de la diagonal; redimensionamiento incremental monótono. |
| **[DET_FLUJO_02] Regla de Sarrus** | **9.2 / 10** | Desglose fiel de diagonales principales y secundarias; preset instantáneo de Sesión 11. | Bloqueo estricto ante $n \ne 3$ sin auto-ajuste inteligente; falta diagrama esquemático con líneas diagonales. |
| **[DET_FLUJO_03] Laplace** | **9.5 / 10** | Flexibilidad total de selección de fila/columna e índice; renderizado formal de submatrices de menores. | Sin resaltado visual en la cuadrícula de la fila/columna activa; sin sugerencia de fila óptima con más ceros. |
| **[DET_FLUJO_04] Matriz Adjunta** | **9.0 / 10** | Presentación completa del pipeline analítico ($M_{ij} \to C_{ij} \to \operatorname{adj}(A) \to A^{-1}$); manejo elegante de matrices singulares. | Exceso de longitud vertical en el panel lateral; sin exportación directa de $A^{-1}$ hacia otros módulos. |
| **[DET_FLUJO_05] Propiedades** | **9.6 / 10** | Sincronización automática de matrices compañeras; verificación bilateral robusta; checklist con tratamiento especial para $\det(A)=0$. | Matriz $B$ requiere scroll vertical en pantallas pequeñas; falta desglose de la potencia $k^n$. |

---

*Fin del reporte técnico del Módulo 5.*


# Procede con la auditoría profunda y detallada del módulo: Módulo 6: Factorización LU y Solución en Dos Etapas

---

## [LUF_FLUJO_01] - Descomposición de Matriz A = LU / PA = LU

### 1. Metadatos Técnicos
- **Objetivo:** Descomponer una matriz $A$ de dimensiones $m \times n$ (con $m, n \in [1, 8]$) en el producto de una matriz triangular inferior unitaria $L$ y una matriz escalonada superior $U$ ($A = LU$), o incorporar permutaciones de fila $PA = LU$ mediante una matriz de permutación $P$ cuando se requiera pivoteo parcial por ceros en la diagonal, verificando la identidad analítica $PA = LU$.
- **Punto de inicio:** Ruta: Stack Index 5 (`Ctrl+6`), botón de acción `"Descomponer A = LU"` en el panel superior de [`LUFactorizationView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/lu_factorization_view.py#L103).
- **Condiciones previas:** Matriz $A$ con valores numéricos válidos en todas sus celdas. Dimensiones dentro del rango permitido ($1 \le m, n \le 8$).

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01: Selección dimensional o carga de caso académico**
  - **Interacción:** El usuario ajusta las filas y columnas mediante los botones `+`/`−` en la barra superior (`row_down_btn`, `row_up_btn`, `col_down_btn`, `col_up_btn`), o hace clic en un botón de preajuste:
    - `"Ejemplo 1 (3×3)"` (Sesión 12, diapositivas 6 a 10).
    - `"Ejemplo 2 (4×4)"` (Sesión 12, diapositivas 11 a 15).
    - `"Ejemplo 3 (4×5)"` (Sesión 12, diapositivas 17 a 22, caso rectangular sin pivote completo).
  - **Componente:** Botones de control de tamaño y presets en [`LUFactorizationView`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/lu_factorization_view.py#L125-L160).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La cuadrícula [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1) redimensiona su estructura inmediatamente. La etiqueta `shape_label` muestra la dimensión resultante (ej. `"3 × 3"` o `"4 × 5"`).
    - *Colores y Tokens:* Si se selecciona un preset, las celdas se rellenan y el cálculo de factores se dispara de forma automática y reactiva.
    - *Textos y Microcopia:* `shape_label`: `"{rows} × {cols}"`. Badge superior: `"Matriz lista para descomponer A = LU."`.
- **Paso 02: Ingreso de entradas en matriz A**
  - **Interacción:** El usuario escribe o modifica valores escalares en las celdas de la cuadrícula.
  - **Componente:** [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) dentro de `self.grid`.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Cada celda válida conserva fondo `color-surface-inner` (`#242028`). Al modificar cualquier celda de $A$, se invocan `_clear_results()` y `_sync_b()`, limpiando factores previos para prevenir desincronización de estado.
- **Paso 03: Descomposición factorial**
  - **Interacción:** El usuario hace clic en el botón `"Descomponer A = LU"`.
  - **Componente:** `self.decompose_btn` (`QPushButton` con ID `primaryAction`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El divisor superior (`upper` QSplitter) puebla el carrusel central de construcción y las tarjetas de la columna derecha (`right_card`).
    - *Colores y Tokens:* 
      - El badge superior adopta verde de éxito `color-feedback-success` (`#81B29A`): `"A = LU verificada. Ya se puede resolver Ly = b y Ux = y."` (o `"P · A = L · U verificada..."` si hubo intercambio de filas).
      - `checklist_label` pasa a verde con checkmark: `"✓  L · U = A"` o `"✓  P · A = L · U"`.
    - *Textos y Microcopia:*
      - Tarjeta $P$: muestra la matriz de permutación en [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1). Si no hubo permutaciones, $P = I$.
      - `permutation_note`: `"No se requirieron permutaciones de fila (A = LU)."` o `"Se intercambiaron filas k veces. La identidad es P · A = L · U. Al resolver se usa el vector Pb."`.
      - Tarjeta $L$: matriz triangular inferior con $1$ en la diagonal principal y los multiplicadores $m_{ij} = a_{ij} / a_{jj}$ debajo.
      - Tarjeta $U$: matriz escalonada superior con los pivotes resultantes.
      - `multiplier_label`: `"{count} multiplicadores guardados en L."`.
- **Paso 04: Exploración del procedimiento en el carrusel**
  - **Interacción:** El usuario avanza con `"Siguiente"` en el carrusel de construcción (`factor_stepper`).
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`self.factor_stepper`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Muestra la eliminación progresiva hacia $U$ y cómo se almacenan simultáneamente los multiplicadores de fila en las entradas de $L$.
    - *Colores y Tokens:* Pivotes activos resaltados en sage `color-feedback-success` (`#81B29A`).

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Entrada no numérica en matriz A | [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) y `self.badge` | Borde rojo en celdas (`#EE6C4D`). Badge superior en `color-feedback-error`. Botón `"Descomponer A = LU"` bloqueado. | `"Corrige las celdas de A. Se admiten enteros, fracciones (a/b) y decimales."` | Editar celdas con valores válidos. |
| Intento de redimensionar con celdas no válidas | Modal [`QMessageBox`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/modules/lu_factorization_view.py#L666) | Diálogo modal nativo con icono de advertencia. | **Título:** `"Entrada inválida"`<br>**Cuerpo:** `"Corrige las celdas antes de cambiar el tamaño."` | Pulsar `"OK"` y corregir las celdas marcadas. |
| Matriz con dimensión superior a 8 | `self.badge` | Badge en color de error. | `"Cada dimensión debe estar entre 1 y 8."` | Reducir dimensiones con controles de la barra superior. |
| Pivote cero sin filas inferiores no nulas (matriz singular) | `self.badge` | Badge superior en color de error `color-feedback-error`. La descomposición $A=LU$ se genera, pero se notifica la imposibilidad de solución única. | `"A = LU verificada, pero U tiene un pivote diagonal nulo. Ax = b no tiene solución única por sustitución hacia atrás."` | El botón de resolución en dos etapas (`solve_btn`) permanece inhabilitado. |
| Matriz rectangular (ej. $4 \times 5$, Ejemplo 3) | `self.badge` | Badge en verde indicando verificación exitosa de $A=LU$, pero informando que no aplica solución en dos etapas. | `"A = LU verificada. A es 4×5: la solución única en dos etapas pide una matriz cuadrada."` | `solve_btn` se deshabilita preventivamente. |

### 4. Matriz de Estados de Componentes Clave
- **Botón Descomponer (`decompose_btn`):**
  - *Habilitado:* Fondo interactivo `color-interactive-idle` (`#98C1D9`), texto `color-bg-base` (`#1A181B`).
  - *Disabled:* Opacidad reducida cuando hay celdas no numéricas en $A$. Bloquea clics.
- **Botones de Redimensionamiento (`row_down_btn`, `row_up_btn`, `col_down_btn`, `col_up_btn`):**
  - *Límites:* `row_down_btn` / `col_down_btn` se inhabilitan en 1; `row_up_btn` / `col_up_btn` en 8.
- **Tarjetas de Factores (`p_view`, `l_view`, `u_view`):**
  - *Empty State:* Antes de calcular, se muestran en blanco con altura mínima de 140px.
  - *Populated State:* Corchetes tipográficos de libro, números en fracciones exactas y etiquetas de lectura inline accesibles.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #7 - Flexibilidad y eficiencia de uso]:** La matriz $A$ solo se puede redimensionar mediante los 4 botones de incremento/decremento paso a paso. No existen spinboxes directos para fijar dimensiones arbitrarias de golpe (ej. pasar de $2 \times 2$ a $5 \times 5$ requiere 6 clics manuales).
2. **[Nielsen #1 - Visibilidad del estado]:** Cuando se realiza una permutación de filas, la matriz de permutación $P$ se visualiza en la columna derecha, pero en la matriz original $A$ no se indica cromáticamente qué filas fueron intercambiadas.

---

## [LUF_FLUJO_02] - Resolución en Dos Etapas: Ly = Pb y Ux = y

### 1. Metadatos Técnicos
- **Objetivo:** Resolver el sistema lineal $Ax = b$ desacoplando el problema en dos subsistemas triangulares sucesivos de sustitución directa:
  1. **Etapa 1 (Forward Substitution):** Resolver $Ly = Pb$ mediante sustitución progresiva para hallar el vector intermedio $y$.
  2. **Etapa 2 (Backward Substitution):** Resolver $Ux = y$ mediante sustitución regresiva para hallar el vector solución final $x$.
  3. **Comprobación:** Verificar formalmente la sustitución analítica $A \cdot x = b$.
- **Punto de inicio:** Ruta: Stack Index 5 (`Ctrl+6`), botón de acción `"Resolver Ly = b y Ux = y"` en el panel superior, o ingreso de términos en el panel inferior `"Solución en dos etapas"`.
- **Condiciones previas:** Matriz $A$ cuadrada $n \times n$ con descomposición $PA = LU$ calculada previamente (o auto-ejecutada al pulsar resolver). Matriz $U$ sin pivotes diagonales nulos ($u_{ii} \ne 0$). Vector de términos independientes $b$ de dimensión $n \times 1$ con valores válidos.

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01: Sincronización del vector b**
  - **Interacción:** El usuario observa el panel inferior `"Solución en dos etapas"`. Si la matriz $A$ tiene orden $n$, la cuadrícula `b_grid` se dimensiona automáticamente a $n \times 1$. El usuario ingresa los términos independientes de su sistema en las celdas del vector $b$.
  - **Componente:** `self.b_grid` ([`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L1)) en el panel inferior.
  - **Comportamiento visual:**
    - *Colores y Tokens:* Entrada válida conserva estilo estándar.
    - *Reutilización reactiva:* Si $L$ y $U$ ya estaban calculadas y el usuario edita $b$, se dispara `_on_b_changed()`. El sistema limpia la solución anterior pero conserva los factores $L$ y $U$, actualizando el badge a: `"b cambió. L y U se reutilizan: vuelve a resolver las dos etapas."` sobre fondo neutro.
- **Paso 02: Ejecución de la resolución en dos etapas**
  - **Interacción:** El usuario hace clic en el botón `"Resolver Ly = b y Ux = y"`.
  - **Componente:** `self.solve_btn` (`QPushButton` con ID `primaryAction`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* El panel inferior (`lower` QSplitter) se puebla en sus cuatro columnas:
      1. Vector $b$ cargado (`b_card`).
      2. Carrusel y fórmulas de Etapa 1 (`forward_box`).
      3. Carrusel y fórmulas de Etapa 2 (`backward_box`).
      4. Tarjeta de solución y comprobación (`answer_card`).
    - *Colores y Tokens:* 
      - El badge superior adopta verde de éxito `color-feedback-success` (`#81B29A`): `"x = [x₁,…,xₙ]ᵀ. Se comprobó Ly = Pb, Ux = y y Ax = b."`.
      - `ax_label` muestra `"✓  A · x = b"` en verde bold de 16px.
    - *Textos y Microcopia:*
      - `forward_title`: `"Etapa 1 · Ly = Pb"` si hubo permutaciones o `"Etapa 1 · Ly = b"` si $P=I$.
      - `pb_label`: Muestra la permutación del vector de carga: `"Pb = [...]ᵀ"` o `"P = I, así que Pb = b."`.
      - `forward_steps_label`: Despliega paso a paso las fórmulas algebraicas en HTML de libro con subíndices (ej. $y_1 = b_1$, $y_2 = b_2 - l_{21}y_1$, etc.).
      - `backward_steps_label`: Despliega paso a paso la sustitución hacia atrás (ej. $x_3 = y_3 / u_{33}$, $x_2 = (y_2 - u_{23}x_3)/u_{22}$, etc.).
      - Visores finales: `y_view` muestra el vector columna intermedio $y$; `x_view` muestra el vector columna solución $x$.
- **Paso 03: Inspección de carruseles de sustitución**
  - **Interacción:** El usuario utiliza los botones de carrusel de `forward_stepper` y `backward_stepper` para estudiar cada sustitución de variables.
  - **Componente:** [`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32) (`forward_stepper` y `backward_stepper`).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Las matrices aumentadas $[L \mid Pb]$ y $[U \mid y]$ se van reduciendo progresivamente, mostrando el despeje de cada variable.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Entrada no numérica en vector b | `self.b_grid` y `self.badge` | Borde rojo en celdas de $b$. Badge en `color-feedback-error`. | `"Corrige las celdas del vector b."` | Corregir las componentes no válidas de $b$. |
| Matriz A no cuadrada al intentar resolver | `self.solve_btn` y `self.badge` | `solve_btn` inhabilitado. Badge informa la condición de cuadratura. | `"A = LU verificada. A es m×n: la solución única en dos etapas pide una matriz cuadrada."` | Ajustar $A$ a matriz cuadrada $n \times n$. |
| Cero en la diagonal de U ($u_{ii} = 0$, `LUSingularError`) | `self.badge` y `self.solve_btn` | `solve_btn` bloqueado. Badge en color de error. | `"A = LU verificada, pero U tiene un pivote diagonal nulo. Ax = b no tiene solución única por sustitución hacia atrás."` | No se puede resolver por sustitución triangular; utilizar el Módulo de Sistemas Lineales para clasificar el sistema. |
| Pivote cero irreductible sin permutación válida (`LUPivotZeroError`) | `self.badge` | Badge en color de error. Carrusel hacia atrás refleja la fila singular. | Mensaje de excepción con la etapa exacta donde falló la división por cero. | Modificar la matriz $A$. |
| Falla en la comprobación final $Ax = b$ | `self.ax_label` y `self.badge` | `ax_label` en rojo `color-feedback-error`. Badge alerta la inconsistencia. | `ax_label`: `"A · x no coincide con b"`<br>Badge: `"La sustitución terminó, pero la comprobación A · x = b no cerró."` | Revisar aritmética de precisión o entradas singulares. |

### 4. Matriz de Estados de Componentes Clave
- **Botón Resolver en Dos Etapas (`solve_btn`):**
  - *Habilitado:* Únicamente cuando $A$ está descompuesta, es cuadrada, $U$ no tiene ceros en su diagonal y $b$ es completamente válido.
  - *Disabled:* En cualquier otro caso, permanece deshabilitado evitando clics infructuosos.
- **Cuadrícula del Vector b (`b_grid`):**
  - *Sincronización:* Sincroniza automáticamente su número de filas con el número de filas de $A$. Las entradas se conservan al redimensionar.
- **Visores de Solución (`y_view`, `x_view`):**
  - *Empty State:* Vacíos antes de resolver.
  - *Populated State:* Vector columna renderizado con corchetes vectoriales formales en fuente monospace.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #8 - Sobrecarga en el layout inferior]:** El panel inferior divide horizontalmente 4 columnas (`b_grid`, Etapa 1 con carrusel, Etapa 2 con carrusel, y Solución). En pantallas de 1366x768 o portátiles pequeños, esta división cuádruple comprime severamente el ancho de los carruseles, dificultando la lectura de las fórmulas matemáticas. Una distribución en pestañas (Tab 1: Etapa 1 / Tab 2: Etapa 2 / Tab 3: Solución) resolvería la fatiga visual.
2. **[Nielsen #4 - Consistencia con otros módulos]:** A diferencia del Módulo 1 (Sistemas Lineales) y el Módulo 4 (Ecuaciones Matriciales), este módulo no incluye una tarjeta de clasificación de variables libres (🔑) en caso de que el sistema tenga infinitas soluciones; simplemente inhabilita el solucionador si hay pivotes nulos en $U$.

---

## Resumen Ejecutivo de la Auditoría del Módulo 6

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[LUF_FLUJO_01] Descomposición A = LU / PA = LU** | **9.5 / 10** | Detección automática y transparente de permutaciones ($P \ne I$); soporte de matrices rectangulares; checklist de verificación formal $PA = LU$. | Controles de tamaño de fila/columna incrementales sin entrada directa numérica; falta de resaltado de filas intercambiadas en $A$. |
| **[LUF_FLUJO_02] Solución en Dos Etapas (Ly = Pb y Ux = y)** | **9.3 / 10** | Reutilización reactiva de factores $L$ y $U$ al modificar $b$; doble carrusel para ambas etapas; validación cruzada $Ax = b$. | Layout horizontal cuádruple muy comprimido en pantallas de baja resolución; sin soporte pedagógico para sistemas indeterminados. |

---

*Fin del reporte técnico del Módulo 6.*


# Procede con la auditoría profunda y detallada del módulo: Módulo 7: Componentes Transversales del Sistema de UI/UX (Design System y Core Interactivo)

---

## [SYS_FLUJO_01] - Edición, Ghosting y Navegación por Teclado en Cuadrículas

### 1. Metadatos Técnicos
- **Objetivo:** Proveer un mecanismo universal, ágil y de cero fricción para la entrada matricial en toda la suite, permitiendo edición numérica validada en tiempo real, expansión fluida mediante celdas fantasma (Ghosting Pattern) y navegación integral por teclado sin dependencia del ratón.
- **Punto de inicio:** Transversal a todos los módulos que instancian [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L176) y [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) (Sistemas Lineales, Álgebra Matricial, Vectores, Ecuaciones Matriciales, Determinantes y Factorización LU).
- **Condiciones previas:** Componente montado en el layout de la vista correspondiente. Soporte de modo aumentado (`augmented=True` con barra $[A \mid b]$) o estándar rectangular (`augmented=False`).

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01: Foco inicial y selección de texto**
  - **Interacción:** El usuario hace clic sobre una celda o accede a ella mediante `Tab`.
  - **Componente:** [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63).
  - **Comportamiento visual:**
    - *Colores y Tokens:* La celda adquiere la clase CSS `matrix-cell`. Al recibir el foco (`focusInEvent`), se programa un `QTimer.singleShot(0)` para seleccionar la totalidad del texto existente (`selectAll()`), permitiendo sobrescribir el valor sin requerir pulsar `Backspace`.
    - *Textos y Microcopia:* Valor predeterminado `"0"`. Tipografía de celda: Monospace (`Fira Code`, 12pt). Tamaño fijo ergonómico de 58x38 px.
- **Paso 02: Navegación continua por teclado**
  - **Interacción:** El usuario se desplaza entre celdas contiguas utilizando `Tab`, `Shift+Tab`, `Enter`, `Return` o las flechas de cursor ($\leftarrow, \uparrow, \rightarrow, \downarrow$).
  - **Componente:** `MatrixCellEdit.keyPressEvent` emitiendo la señal `navigate(row, col, direction)` hacia [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L456).
  - **Comportamiento visual:**
    - *Navegación inteligente:* Al presionar `Flecha Derecha` cuando el cursor está al final del texto (o `Flecha Izquierda` al inicio), el foco salta suavemente a la celda adyacente. Al presionar `Enter` o `Flecha Abajo`, el cursor desciende en la misma columna.
- **Paso 03: Expansión de dimensiones mediante Ghosting Pattern**
  - **Interacción:** El usuario sitúa el ratón sobre los márgenes de la cuadrícula o presiona `Tab` en la última celda de la fila.
  - **Componente:** Botones de celda fantasma `ghost_col_btn` y `ghost_row_btn` ([`_make_ghost_button`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L53)).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* La cuadrícula recalcula su tamaño sin parpadeos visuales. Las nuevas celdas se insertan con animación estructural instantánea.
    - *Colores y Tokens:* Botones con clase `ghost-cell` muestran un símbolo `+` en `color-interactive-idle` (`#98C1D9`) con fondo transparente y cursor `PointingHandCursor`.
    - *Textos y Microcopia:* Tooltip contextual: `"Agregar variable"` / `"Agregar ecuación"` en sistemas aumentados; `"Agregar fila"` / `"Agregar columna"` en matrices estándar.
- **Paso 04: Renderizado de corchetes y barra aumentada de libro**
  - **Interacción:** La cuadrícula se repinta ante cambios de tamaño o scroll.
  - **Componente:** `DynamicMatrixGrid.paintEvent` invocando [`draw_square_brackets`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L45) y [`draw_split_bar`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L45).
  - **Comportamiento visual:**
    - *Corchetes:* Se dibujan corchetes rectangulares de 2px de grosor envolviendo todas las celdas en `color-text-primary` (`#E0FBFC`).
    - *Barra divisoria:* Si `augmented=True`, se traza una línea vertical continua en `color-interactive-idle` (`#98C1D9`) a 6px a la izquierda de la columna de términos independientes, emulando la notación física de un libro de texto.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Inserción de caracteres alfanuméricos no escalares (ej. `3a`, `1..0`, `//`) | [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L63) | Borde cambia reactivamente a clase CSS `matrix-cell-error` (`#EE6C4D`, 2px sólido). Propiedad `is_valid` pasa a `False`. | Sin texto de error dentro de la celda; feedback netamente cromático de alto contraste. | Corregir la entrada. Al reconocer formato válido (entero, fracción o decimal), el borde regresa al estado normal. |
| Celda con texto en blanco | [`MatrixCellEdit`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L107) | Si se borra todo el texto, se remueve el estado de error temporalmente, pero `get_value()` devolverá `Fraction(0, 1)` o bloqueará el cálculo según la validación del módulo. | Ninguna microcopia. | Escribir un valor explícito o `"0"`. |
| Desbordamiento de navegación fuera de los límites de la cuadrícula | [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L456) | Si el usuario presiona flecha arriba en la fila 0, o flecha izquierda en la columna 0, el foco permanece en la celda actual sin generar excepciones. | Ninguna. | Comportamiento silencioso y seguro. |

### 4. Matriz de Estados de Componentes Clave
- **Celda Editable (`MatrixCellEdit`):**
  - *Normal:* Fondo `color-surface-inner` (`#242028`), texto `color-text-primary` (`#E0FBFC`), borde tenue.
  - *Focused:* Borde realzado, selección completa de texto.
  - *Error:* Borde sólido `color-feedback-error` (`#EE6C4D`).
  - *Highlighted (Inspector de producto):* Propiedad `highlighted=True`, fondo con tinte interactivo realzado para indicar fila/columna activa en multiplicación.
- **Botones Fantasma (`ghost_cell`):**
  - *Normal:* Opacidad sutil, borde punteado o transparente.
  - *Hover:* Opacidad 100%, fondo interactivo tenue, cursor de mano.
  - *Oculto:* Cuando `row_expandable=False` o `col_expandable=False`, se remueven del layout.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #5 - Prevención de errores]:** Si el usuario introduce una celda vacía por descuido, en algunos módulos se asume silenciosamente como cero, mientras que en otros se bloquea el botón de cálculo. Sería preferible autocompletar con `"0"` al perder el foco (`focusOutEvent`) si la celda queda en blanco.
2. **[Nielsen #7 - Eficiencia de uso]:** No existe una combinación de teclado rápida para eliminar una fila o columna activa (ej. `Ctrl+Delete` o `Alt+Backspace`); la eliminación depende exclusivamente del menú contextual de clic derecho.

---

## [SYS_FLUJO_02] - Sistema de Portapapeles y Menú Contextual (Copy / Paste)

### 1. Metadatos Técnicos
- **Objetivo:** Facilitar la interoperabilidad y el intercambio ágil de matrices completas o celdas individuales entre PrettyCalc y aplicaciones externas (Excel, Google Sheets, Wolfram Alpha, LaTeX, editores de texto plano) o entre distintas vistas internas de la aplicación, mediante el portapapeles del sistema operativo (`QGuiApplication.clipboard()`).
- **Punto de inicio:** Menú contextual disparado por clic derecho sobre cualquier celda o cuadrícula, o atajos de teclado estándar `Ctrl+C` y `Ctrl+V`.
- **Condiciones previas:** Texto copiado en formato reconocible: valores tabulados (TSV), filas separadas por saltos de línea o punto y coma, o sintaxis LaTeX `\begin{matrix}`.

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01: Apertura del menú contextual**
  - **Interacción:** El usuario hace clic derecho sobre una celda específica de la cuadrícula.
  - **Componente:** `MatrixCellEdit.contextMenuEvent` disparando [`DynamicMatrixGrid.show_cell_context_menu`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L377).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Se despliega un menú flotante nativo [`QMenu`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L378) estilizado bajo el Design System oscuro (`color-surface-elevated` `#564D65`, bordes redondeados y texto claro).
    - *Textos y Microcopia:* 
      - `"Copiar matriz"` (atajo visual: `Ctrl+C`).
      - `"Pegar matriz"` (atajo visual: `Ctrl+V`, habilitado si hay datos válidos en el portapapeles).
      - Separador.
      - `"Copiar valor de celda"`.
      - `"Pegar en celda"` (habilitado si hay texto en portapapeles).
      - Separador.
      - `"Eliminar fila"`.
      - `"Eliminar columna"`.
- **Paso 02: Copia inteligente (Matriz completa vs. Subcadena)**
  - **Interacción:** 
    - *Caso A (Atajo Ctrl+C sin selección o con celda completa):* Copia la matriz completa en formato TSV universal (`copy_to_clipboard()`).
    - *Caso B (Atajo Ctrl+C con texto parcial seleccionado en celda):* Copia únicamente el fragmento seleccionado (ej. solo el numerador `1` de `1/2`).
  - **Componente:** [`clipboard.py`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/clipboard.py#L21) (`copy_matrix_to_clipboard`).
  - **Comportamiento visual:**
    - Operación silenciosa y no bloqueante. El texto en el portapapeles queda listo para ser pegado en una hoja de cálculo como celdas tabuladas.
- **Paso 03: Pegado multidimensional transparente**
  - **Interacción:** El usuario pulsa `Ctrl+V` sobre una celda o selecciona `"Pegar matriz"` en el menú contextual.
  - **Componente:** `paste_from_clipboard()` en [`DynamicMatrixGrid`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/matrix_grid.py#L146).
  - **Comportamiento visual:**
    - *Cards y Contenedores:* Si el texto contiene saltos de línea o tabuladores representando una matriz rectangular (ej. $3 \times 4$), la cuadrícula **se redimensiona automáticamente** para ajustarse a las dimensiones de los datos entrantes y puebla todas las celdas con sus valores correspondientes.
    - *Disparo reactivo:* Emite la señal `matrixChanged()`, notificando al módulo padre para refrescar validaciones y badges de conformabilidad.

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Portapapeles vacío o con texto no estructurado | `QMenu` (`paste_action`) | La opción `"Pegar matriz"` aparece deshabilitada en color tenue (`color-interactive-disabled` `#3A3642`). | Ninguna microcopia adicional; control deshabilitado. | Copiar una estructura tabular válida antes de abrir el menú. |
| Intento de eliminar la última fila o columna ($1 \times 1$) | `QMenu` (`delete_row`, `delete_col`) | Las acciones aparecen deshabilitadas con cursor de bloqueo. | Tooltip: `"Debe quedar al menos una fila."` o `"Debe quedar al menos una columna."`. | Conservar la dimensión mínima requerida. |
| Intento de eliminar la columna aumentada $b$ mediante clic derecho | `QMenu` (`delete_col`) | La acción `"Eliminar columna"` se deshabilita específicamente cuando la celda pulsada pertenece a la columna de términos independientes. | Tooltip: `"La columna de términos independientes no se puede eliminar."`. | Eliminar variables del sistema desde las columnas de coeficientes $x_j$. |
| Pegado de matriz no rectangular (filas con diferente número de elementos) | `parse_matrix_text` en core | La operación de pegado se aborta silenciosamente; la cuadrícula conserva su estado previo sin corromper datos. | Ningún error intrusivo. | Formatear la tabla copiada con columnas homogéneas. |

### 4. Matriz de Estados de Componentes Clave
- **Menú Contextual (`QMenu`):**
  - *Estado Activo:* Fondo `#564D65`, bordes limpios, separadores en `color-surface-inner` (`#242028`).
  - *Acciones Habilitadas:* Texto `color-text-primary` (`#E0FBFC`), hover con realce azul `color-interactive-idle` (`#98C1D9`).
  - *Acciones Deshabilitadas:* Texto `color-interactive-disabled` (`#3A3642`), clics bloqueados.

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #1 - Visibilidad del estado]:** Al pegar una matriz grande mediante `Ctrl+V`, la sustitución de celdas ocurre sin una animación sutil de parpadeo (flash feedback) o toast de confirmación (*"Matriz 3×4 pegada exitosamente"*), lo que puede desconcertar al usuario sobre si la operación surtió efecto.
2. **[Nielsen #3 - Control y libertad del usuario]:** El pegado de una matriz sobrescribe de forma destructiva todos los valores existentes sin confirmación ni opción de deshacer (`Ctrl+Z`).

---

## [SYS_FLUJO_03] - Renderizado Tipográfico, Design System y Notación Matemática de Libro

### 1. Metadatos Técnicos
- **Objetivo:** Garantizar máxima coherencia visual, legibilidad cognitiva y fidelidad formal a los textos clásicos de álgebra lineal, transformando cadenas crudas de LaTeX generadas por el motor matemático a HTML enriquecido de libro (`Qt.RichText`), aplicando alineación simétrica y cumpliendo los tokens cromáticos del Design System.
- **Punto de inicio:** Transversal a toda la capa de presentación: carruseles de pasos ([`AlgorithmStepperCarousel`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/stepper_carousel.py#L32)), dashboards ([`ResultsDashboardCard`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/results_dashboard.py#L80)), visores de libro ([`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1)) y etiquetas de propiedades.
- **Condiciones previas:** Tokens oficiales centralizados en [`theme.py`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/theme.py#L1) y reglas de parseo en [`mathtext.py`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/mathtext.py#L1).

### 2. Flujo Principal (Happy Path) - Paso a Paso
- **Paso 01: Invocación del conversor de fórmulas**
  - **Interacción:** El motor matemático emite un paso con fórmula LaTeX (ej. `\det(A)`, `f_2 \rightarrow f_2 - 3f_1`, `\|u\|^2`, `x_1`).
  - **Componente:** [`mathtext.py`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/mathtext.py#L1) (`latex_to_book_html`, `prettify_math_text`, `variable_html`).
  - **Comportamiento visual:**
    - *Transformación sintáctica:* Las macros de LaTeX se convierten a símbolos Unicode y etiquetas HTML nativas de libro sin depender de librerías externas pesadas (como MathJax o WebKit):
      - `f_{2}` $\rightarrow$ $F_2$ con subíndice tipográfico bajado.
      - `\rightarrow` $\rightarrow$ $\rightarrow$ (flecha de transformación).
      - `\text{...}` $\rightarrow$ prosa formal en cursiva.
      - Fracciones $\rightarrow$ formato horizontal limpio o apilado.
- **Paso 02: Renderizado simétrico en `BookMatrixWidget`**
  - **Interacción:** Se actualiza un visor de matrices estáticas (ej. matrices $P, L, U$, matriz transpuesta, inversas o vectores columna).
  - **Componente:** [`BookMatrixWidget`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/book_matrix.py#L1) invocando `paint_book_scalar`.
  - **Comportamiento visual:**
    - *Tipografía y Alineación:* Se utiliza estrictamente fuente **Monospace** (`Fira Code` / `Roboto Mono`). Los signos negativos, numeradores y denominadores quedan centrados geométricamente de forma simétrica entre corchetes rectangulares continuos.
    - *Fracciones apiladas:* Si una celda contiene una fracción racional (ej. `3/4`), se pinta la barra horizontal de fracción con el numerador arriba y el denominador abajo con fuente de tamaño adaptativo.
- **Paso 03: Aplicación del Design System Cromático**
  - **Interacción:** Despliegue de estados de éxito, advertencia, error y superficies.
  - **Componente:** Tokens oficiales de [`theme.py`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/theme.py#L50-L65):
    - `COLOR_BG_BASE`: `#1A181B` (Shadow Grey, fondo base de absorción de luz).
    - `COLOR_SURFACE_ELEVATED`: `#564D65` (Vintage Grape, tarjetas y dashboards elevados).
    - `COLOR_SURFACE_INNER`: `#242028` (Superficies internas oscuras para celdas y visores).
    - `COLOR_TEXT_PRIMARY`: `#E0FBFC` (Light Cyan, tipografía de alto contraste).
    - `COLOR_TEXT_MUTED`: `#7A7585` (Muted Purple-Grey, textos tenues informativos).
    - `COLOR_INTERACTIVE_IDLE`: `#98C1D9` (Powder Blue, acentos interactivos, bordes y barras aumentadas).
    - `COLOR_INTERACTIVE_DISABLED`: `#3A3642` (Dimmed Grape, controles deshabilitados).
    - `COLOR_FEEDBACK_ERROR`: `#EE6C4D` (Burnt Peach, estados de inconsistencia y bordes de error).
    - `COLOR_FEEDBACK_SUCCESS`: `#81B29A` (Muted Sage, checkmarks de validación y resaltado de pivotes).
    - `COLOR_ACCENT_WARNING`: `#E9C46A` (Warm Ochre, variables libres y sistemas indeterminados).

### 3. Matriz de Errores, Validaciones y Casos Límite (Edge Cases)

| Disparador de Falla | Componente Visual | Comportamiento UI (Bordes, Iconos, Colores) | Microcopia Exacta Mostrada | Mecanismo de Recuperación (CTA) |
|---|---|---|---|---|
| Comando LaTeX desconocido o no soportado en la especificación | `latex_to_book_html` en [`mathtext.py`](file:///home/ro/Projects/PrettyCalc/prettycalc/ui/mathtext.py#L1) | Sanitiza el texto mediante `html.escape()`, reemplaza barras invertidas y presenta la cadena de forma segura sin romper el layout del QLabel. | Cadena de texto escapada legible. | Transparente para el usuario; previene fallos de renderizado HTML. |
| Denominador cero o fracción infinita | `format_scalar` | El motor maneja excepciones de división y el formateador emite `"indefinido"` o cadena nula. | `"indefinido"` | Corregir la operación matemática. |
| Texto de fórmula excesivamente largo para el ancho del carrusel | `QLabel.setWordWrap(True)` en carrusel | El contenedor expande su altura verticalmente sin recortar los bordes laterales de la fórmula. | Fórmulas completas en multilínea. | Ajustar el divisor del splitter si se requiere mayor ancho horizontal. |

### 4. Matriz de Estados de Componentes Clave
- **Badges Semánticos:**
  - *Éxito (`color-feedback-success` `#81B29A`):* Fondo verde tenue, texto oscuro de alto contraste, bordes suaves de 6px.
  - *Advertencia (`color-accent-warning` `#E9C46A`):* Fondo ámbar para sistemas indeterminados o variables libres.
  - *Error (`color-feedback-error` `#EE6C4D`):* Fondo durazno/coral quemado para inconsistencias o singularidad.
- **Tarjetas Elevadas (`elevated-card`):**
  - Fondo `color-surface-elevated` (`#564D65`), bordes redondeados (8px), márgenes internos estandarizados (14px).

### 5. Brechas Heurísticas Identificadas [UX Gaps]
1. **[Nielsen #8 - Accesibilidad cromática y contraste WCAG AA]:** En algunos textos de notas o subíndices, el color `color-text-muted` (`#7A7585`) sobre el fondo `color-surface-elevated` (`#564D65`) presenta una relación de contraste aproximada de 3.2:1, lo cual se sitúa por debajo del umbral mínimo de 4.5:1 exigido por las pautas WCAG 2.1 AA para texto de cuerpo normal.
2. **[Nielsen #7 - Flexibilidad y personalización]:** No existe un selector de tema (Modo Claro / Modo Oscuro) o ajuste de escala de fuentes para usuarios con baja visión o preferencias de accesibilidad visual.

---

## Resumen Ejecutivo de la Auditoría del Módulo 7

| Flujo Auditado | Calificación Ergonomía | Puntos Fuertes UI/UX | Puntos Críticos a Mejorar |
| :--- | :---: | :--- | :--- |
| **[SYS_FLUJO_01] Edición y Ghosting** | **9.6 / 10** | Navegación por teclado completa (Tab, Flechas, Enter); selección de celda inmediata; corchetes de libro de 2px impecables. | Sin autocompletado a cero al perder foco en celda vacía; sin atajo de teclado para eliminar filas/columnas. |
| **[SYS_FLUJO_02] Sistema de Portapapeles** | **9.5 / 10** | Detección automática y transparente entre matriz completa y fragmento de celda; redimensionamiento automático al pegar TSV. | Falta feedback visual de confirmación (toast) al pegar; sin función de deshacer (Ctrl+Z) ante pegado destructivo. |
| **[SYS_FLUJO_03] Design System y MathText** | **9.7 / 10** | Notación matemática de libro en RichText nativo sin dependencias web; paleta de colores coherente y sobria; fracciones apiladas. | Contraste de texto atenuado (`#7A7585`) al límite de la norma WCAG AA; sin soporte para alternar a tema de alto contraste o tema claro. |

---

*Fin del reporte técnico del Módulo 7.*
