# Reglas y Principios de Diseño - PrettyCalc

## 1. Filosofía Visual y Experiencia de Usuario ("PrettyCalc")
La aplicación prioriza la elegancia, la claridad cognitiva y la eliminación total de fricción. Las matemáticas son ordenadas y la interfaz debe reflejarlo mediante principios de **Carga Progresiva Natural**, **Visibilidad del Estado del Sistema (Nielsen)**, **Prevención de Errores** y un **Design System Cromático** de alto contraste.

---

## 2. Design System: Especificaciones Cromáticas y Tokens Visuales

| Token Semántico | Nombre del Tono | Valor HEX | Uso Estricto en la Interfaz |
| :--- | :--- | :--- | :--- |
| `color-bg-base` | **Shadow Grey** | `#17151A` (antes `#1A181B`) | **Lienzo de fondo principal** de la ventana. Absorbe la luz y da protagonismo a los paneles de datos. |
| `color-surface-elevated` | **Graphite Grape** | `#2F2A37` (pulido UI; antes `#4A4257` y `#564D65`) | **Superficies elevadas y contenedores:** Fondos de Cards laterales (Dashboard de resultados) y contenedor de la cuadrícula de la matriz. |
| `color-text-primary` | **Light Cyan** | `#E0FBFC` | **Tipografía de alto contraste:** Títulos, etiquetas de ejes, texto de botones principales y coeficientes de las matrices. |
| `color-interactive-idle` | **Powder Blue** | `#98C1D9` | **Interacción secundaria:** Bordes de celdas en reposo, botones secundarios (`[ ◀ Paso Anterior ]`), texto tenue de fórmulas ($f_2 \rightarrow f_2 - 3f_1$) y **línea divisoria vertical de la matriz aumentada**. |
| `color-interactive-disabled` | **Dimmed Grape** | `#3C3646` | **Controles inactivos / deshabilitados:** Botón "Paso Anterior" en el Paso 1 para evitar clics inválidos. |
| `color-feedback-error` | **Burnt Peach** | `#EE6C4D` | **Feedback de Error / Inconsistencia:** Badge de *"Sistema Inconsistente"*, borde de celda ante entradas inválidas (letras) y alertas. |
| `color-feedback-success` | **Muted Sage** | `#81B29A` | **Feedback de Éxito:** Badge de *"Sistema Consistente"*, checkmarks (**✓**) de validación y resaltado de pivote/fila escalonada. |
| `color-surface-inner` | **Ink Grape** | `#1F1C24` | Fondos de visores de matriz, campos y bloques de fórmula. |
| `color-text-muted` | **Lilac Mist** | `#C9C3D6` | Texto secundario. Contraste ≥ 4.5:1 sobre `color-surface-elevated` (WCAG AA). |
| `color-text-disabled` | **Faded Lilac** | `#A8A3B2` | Texto de controles deshabilitados. |
| `color-interactive-hover` | **Sky Wash** | `#B3D4E6` | Hover de botones secundarios. |
| `color-accent-warning` | **Saffron** | `#E9C46A` | SCI, filas permutadas, avisos pedagógicos (k > n, c = 0). |

**Escala de superficies.** Fondo, pozo y tarjeta suben en saltos suaves (`#17151A` → `#1F1C24` → `#2F2A37`): la elevación se lee por el tono y por un borde tenue (`interactive-idle` al 12 %), no por un bloque de color. Las tarjetas redondean a 12 px.

**Sprint 10.** Los tokens viven en `prettycalc/ui/theme.py` (`PALETTES`) con tres temas: oscuro (predeterminado), alto contraste y claro, elegibles en *Apariencia* (Ctrl+,). El texto de cada badge se elige con `readable_text_on()` para cumplir 4.5:1. Ningún módulo escribe colores sueltos: todos importan los tokens.

---

## 2.1. Navegación y estructura de la ventana

* **Barra lateral.** Logotipo arriba, los ocho módulos con su marca tipográfica (`[A|b]`, `A·B`, `ℝⁿ`, `Ax`, `det`, `LU`, `T(v)`, `EV`) y, en el pie, Atajos y Apariencia. El módulo activo lleva tinte y una pastilla de acento a la izquierda.
* **Riel en portátiles.** Bajo 1600 px de ancho la barra se pliega a un riel de 96 px con la marca y el rótulo corto debajo; el nombre completo queda en el tooltip. Ningún rótulo se recorta en ninguno de los dos modos.
* **Encabezado de página.** Una sola línea: nombre del módulo destacado y su descripción en tono tenue.
* **Anillo de foco** solo al llegar con el teclado (Tab), nunca por el foco inicial ni por un clic.
* **Icono de la ventana**: el mismo logotipo (corchetes de matriz sobre el degradado de los dos acentos), dibujado por la app.

## 2.2. Avisos de estado

* **Avisos** (éxito, error, atención, información): tinte del color al 20 %, borde y franja izquierda del mismo color y texto primario. Se leen de un vistazo sin competir con las matrices.
* **Veredictos** (el badge del tablero de resultados): sólidos, porque son la conclusión.
* **Paneles laterales** dentro de un divisor nunca quedan más angostos que su contenido (`track_content_width`): el ancho se le quita a la columna del procedimiento.
* **Tres columnas que no caben** (Sistemas, Determinantes, LU): el panel de resultados baja a todo el ancho debajo de las otras dos (`StackingSplitterHost`) y vuelve a su columna al ensanchar la ventana. La cabecera de Ecuaciones pasa sus botones a una segunda línea.
* **Sin desplazamiento horizontal** en ninguna vista desde la ventana mínima (1080 × 680) hasta 1920 px; `tests/ui/test_responsive_layout.py` lo comprueba con los ejemplos cargados.

## 3. Flujo de Inicialización y Crecimiento Dinámico (Ghosting Pattern)
* **Inicio Inmediato sin Fricción:**
  * La aplicación inicia directamente mostrando un sistema base de **$2 \times 2$ coeficientes más el vector de términos independientes $b$**. No se interrumpe al usuario con modales ni formularios de configuración de tamaño inicial.
* **Mecanismo de Expansión por Celdas Fantasma (Ghosting):**
  * Cuando la matriz se llena o el cursor llega a los límites, se despliega una **fila y columna extra con opacidad reducida** en los bordes.
* **Descubrimiento y Asequibilidad Visual (Heurística de Visibilidad de Nielsen):**
  * Prohibido depender exclusivamente de atajos de teclado ocultos para agregar filas/columnas.
  * Al pasar el cursor (**Hover**) sobre la fila o columna fantasma, se muestra un **icono sutil de `+`**.
  * Al hacer clic en el área fantasma (o seleccionarla por teclado), la matriz se expande formalmente de manera fluida y suave.

---

## 4. Cuadrícula de Entrada y Matriz Aumentada $[A \mid b]$
* **Visibilidad Permanente del Vector de Términos Independientes ($b$):**
  * En álgebra lineal, el sistema $Ax = b$ requiere que la igualdad esté presente desde el primer milisegundo para respetar el modelo mental del usuario que transcribe su cuaderno (ej. $2x + 3y = 5$).
  * **Partición Visual con Delegado en PySide6:** Mediante un `QStyledItemDelegate` personalizado, se intercepta el método `paint()` para dibujar una **línea vertical sólida** con `color-interactive-idle` (`#98C1D9` - *Powder Blue*) en el borde izquierdo de la columna $b$, simulando la barra divisoria $[A \mid b]$ con acabado profesional.
* **Navegabilidad Total por Teclado:**
  * El usuario **DEBE** poder navegar entre todas las celdas de la matriz (incluyendo la columna $b$) usando **`Tab`**, **`Shift+Tab`** o las **`Flechas del Teclado`** ($\leftarrow, \rightarrow, \uparrow, \downarrow$). El mouse es estrictamente opcional.
* **Validación en Tiempo Real (Prevención de Errores):**
  * Si el usuario escribe caracteres no numéricos (ej. letras), la celda aplica inmediatamente un borde en `color-feedback-error` (`#EE6C4D`) y bloquea la entrada.
  * Formatos válidos por celda: enteros (`-5`), fracciones (`3/4`, `-1/2`) y decimales (`0.75`).

---

## 5. Visualización del Algoritmo (Patrón Stepper / Carrusel)
* **Estructura de Visualización:**
  * **Prohibido:** Scroll vertical infinito con decenas de matrices apiladas.
  * **Componente Obligatorio:** **Carrusel / Stepper** con navegación controlada:
    * Botón **`‹ Anterior`** (inactivo en el Paso 1).
    * Indicador de progreso (*3 / 8*, con «inicial» o «final» en tono tenue).
    * Botón **`Siguiente ›`**.
    * Debajo, cuando hay pasos: deslizador «Ir al paso», interruptor Fracciones/Decimales y Exportar.
* **Atención Visual y Resaltado:**
  * **Pivote Activo y Fila Mutada:** La celda pivote de la iteración se resalta visualmente con un acento suave o badge de color `color-feedback-success` (`#81B29A`).
  * **Fórmula en notación de libro:** El `QLabel` de la fórmula usa `Qt.RichText` y `latex_to_book_html`. No se muestra el LaTeX crudo del `StepTracer` (`\det`, `_{ }`, `^`, `\text{...}`). El contrato está en [latex-rendering-spec.md](latex-rendering-spec.md).
* **Explicación de Heurística:** Debajo de la matriz, se muestra la fórmula formal en `color-interactive-idle` y un texto en cursiva explicando la mutación ocurrida:
    $$\text{Paso: } f_2 \underset{\sim}\rightarrow -3f_1 + f_2$$
    *“Se multiplicó la Fila 1 por -3 y se sumó a la Fila 2.”*

---

## 6. Tipografía y Jerarquía Visual
* **Números de Matrices (Alineación Perfecta):**
  * Fuente **Monospace** `Fira Code` (respaldo `DejaVu Sans`) en `color-text-primary`. Signos, dígitos y fracciones ocupan el mismo ancho y las columnas quedan alineadas.
* **Interfaz General (UI Chrome):**
  * Fuente **Sans-serif** `Inter` (respaldo `DejaVu Sans`) para títulos, botones, etiquetas y diálogos.
* **Misma apariencia en Windows y Linux (Sprint 10):**
  * Las tres familias van **empaquetadas** en `prettycalc/ui/assets/fonts/` (licencias OFL/Bitstream incluidas) y se registran al arrancar; nunca se usa una fuente del sistema.
  * Los tamaños se fijan en **píxeles** (`ui_font(px)`), no en puntos, y sin *hinting*: el mismo texto mide lo mismo con 96 o 144 ppp.
  * Estilo **Fusion** en todas las plataformas, iconos de los diálogos dibujados por la app, diálogo de archivos no nativo y **sin emojis** (dependen de la fuente de color del sistema).
  * En Windows el texto se rasteriza con FreeType (`windows:fontengine=freetype`), el mismo motor que en Linux, en lugar de DirectWrite.
  * La barra de título la dibuja el sistema operativo; en Windows 10/11 se pide oscura con los temas oscuro y de alto contraste, y un AppUserModelID propio hace que la barra de tareas muestre el icono de PrettyCalc y no el de Python.
  * El wheel incluye las diez fuentes, sus licencias y los SVG (`[tool.setuptools.package-data]`).

---

## 7. Dashboard de Resultados
Al alcanzar el paso final de la resolución, la UI despliega un Card lateral o Modal estilizado sobre `color-surface-elevated` (`#564D65`):

1. **Identificador de Estado (Badge Semántico de Color):**
   * **Consistente Determinado:** Badge con `color-feedback-success` (`#81B29A`).
   * **Consistente Indeterminado:** Badge de atención (Amarillo / Acento).
   * **Inconsistente:** Badge con `color-feedback-error` (`#EE6C4D`).
2. **Desglose de Variables:**
   * Separación visual entre variables básicas y **variables libres**.
   * Las variables libres se distinguen con color de acento y la etiqueta «libre (parámetro)»; no se usan emojis.
3. **Checklist de Validación de la Solución:**
   * Verificación visual de sustitución en el sistema original.
   * Icono de confirmación en `color-feedback-success` (**✓** `#81B29A`) al lado de cada ecuación original confirmando que la igualdad matemática es exacta.

---

## 8. Patrones de interacción (Sprint 10)

* **Una acción primaria por vista.** Un solo botón «Calcular / Resolver / Verificar»; Ctrl+Enter lo dispara desde cualquier celda.
* **Errores en línea, sin modales.** El badge nombra la matriz, la fila y la columna (o la componente) y el motivo: «A, fila 2, columna 3: divide entre cero».
* **Todo cambio masivo se puede deshacer.** Reiniciar, pegar, cargar un ejemplo, intercambiar operandos o quitar un vector muestran un aviso con «Deshacer» (y Ctrl+Z en la cuadrícula).
* **Resultados desactualizados.** Si los datos cambian después de calcular, el veredicto se retira y se pide recalcular; nunca queda un resultado que no corresponde a lo que se ve.
* **Tamaños directos.** Spinboxes `m × n` (u orden `n`) en lugar de botones ±; atajos «Hacer cuadrada», «Ajustar a 3×3», «Igualar a n».
* **Inspectores.** Hacer clic en una entrada de un producto resalta la fila y la columna que la producen.
* **Escalares.** Campo común con borde rojo si es inválido, pista `≈ 1.5` para fracciones y chips −1, 0, ½, 2.
* **Responsive.** A 1366×768 ninguna vista tiene desplazamiento horizontal: las filas de tarjetas se apilan y los conjuntos de vectores saltan de línea.

---

## 9. Movimiento

El movimiento es parte del sistema de diseño, igual que la paleta. Vive en `prettycalc/ui/motion.py` (tokens, interruptor y ayudantes), `prettycalc/ui/choreography.py` (valores que viajan entre widgets) y `prettycalc/core/step_diff.py` (qué operación hizo cada paso). Ningún módulo escribe duraciones ni curvas sueltas.

### 9.1. Principios

* **Cada animación responde una pregunta:** qué cambió (una fila, una celda, un veredicto), de dónde vino (la fila pivote, la columna reemplazada) o a dónde fue (la vista se desplazó, el panel apareció, el resultado quedó desactualizado). Si no responde ninguna, no se agrega.
* **El estado cambia de inmediato; la animación decora.** Texto, señales, visibilidad, valores y resultados se actualizan de forma síncrona. Si una animación nunca corriera, la app se vería y se comportaría igual en su estado final.
* **El fotograma final carga todo el significado.** La franja de la fila afectada, el anillo del pivote, el ocre de las filas permutadas y el término de Sarrus quedan pintados después de la animación.
* **Nunca bloquea ni se encola.** Ningún botón se deshabilita mientras algo anima. Un disparador nuevo lleva el anterior a su estado final y empieza el suyo.
* **Navegar rápido es tan ágil como sin animaciones.** Mantener → o pulsarla antes de que termine la secuencia usa la versión corta (fundido de lo que cambió). Lo vistoso es para quien avanza y mira.
* **Nunca números intermedios.** Un valor cambia con fundido cruzado o resaltado, jamás interpolando el número. Un valor puede viajar porque sigue siendo el valor correcto mientras se mueve.
* **El movimiento nunca miente.** Un valor solo viaja de A a B si el valor de A es, literalmente, el que termina en B; cada correspondencia se comprueba con aritmética exacta antes de volar. Por eso L no "sale" de A en LU (L guarda multiplicadores) y el multiplicador no viaja a L (la fila lleva −ℓ y L guarda ℓ): ahí se resalta. Ante la duda, se resalta en vez de mover.
* **Sobrio en el adorno, ambicioso en la coreografía.** Sin rebotes, elásticos, partículas ni movimiento en reposo.

### 9.2. Tokens

| Token | Duración | Uso |
| :--- | :--- | :--- |
| `FAST` | 120 ms | Hover, fundidos pequeños, retroceder o saltar un paso, veredicto que se retira |
| `BASE` | 180 ms | Entrada de avisos, cambio de módulo, asentamiento del badge, paneles que aparecen |
| `SLOW` | 260 ms | Recorrido del pivote, desplazamiento suave |
| `EMPHASIS` | 600 ms | Destellos y pulsos de una sola vez |
| `SIGNATURE` | 680 ms | La operación de un paso, la matriz que entra al procedimiento, la transpuesta |
| `STAGGER` | 50 ms por elemento, 300 ms en total | Revelados escalonados |
| `PULSE_CYCLE` | 400 ms | Pulsos repetidos (2.5 por segundo) |

Curvas: `OutCubic` para entrar, `InCubic` para salir, `InOutCubic` para desplazarse y viajar. No se usan `OutBounce`, `OutElastic` ni `OutBack`.

`PRETTYCALC_MOTION_SCALE=4` multiplica todas las duraciones para revisarlas a ojo.

### 9.3. Qué se anima

* **El procedimiento.** Avanzar un paso reproduce su operación: en `Fᵢ → Fᵢ + k·Fⱼ` una copia de la fila `j` viaja con la etiqueta `× k` hasta la fila `i` y se funde con ella; en `Fᵢ ↔ Fⱼ` las filas se cruzan en arco (una por delante, realzada; otra por detrás, atenuada); en `Fᵢ → k·Fᵢ` la etiqueta aterriza y el pivote pulsa al quedar en 1. Solo las entradas que cambiaron pasan del valor viejo al nuevo, el pivote se desliza, y en `Aᵢ(b)` la columna `i` baja mientras `b` entra desde la derecha. Retroceder o saltar solo funde lo que cambió.
* **La forma final.** Al llegar avanzando, los pivotes se encienden en orden y las cabeceras quedan en verde (básicas) u ocre (libres). En Sistemas, cada valor de la columna `b` viaja a su línea `xᵢ = …` del tablero; con infinitas soluciones responde la forma paramétrica; en `[0 … 0 | c]` los ceros se atenúan y `c` queda en el color de error.
* **Reproducir el procedimiento.** Recorre los pasos con su coreografía y un tiempo de lectura según el texto, a ½×, 1× o 2× (Espacio con el carrusel enfocado). Se detiene al final, ante cualquier interacción con el carrusel, al cambiar de módulo y si cambian los pasos.
* **Valores que viajan.** La matriz de entrada viaja a su lugar en el paso inicial (solo si cambió desde el último cálculo); en Aᵀ cada entrada va de `(i, j)` a `(j, i)` y la diagonal pulsa sin cruzar; el bloque derecho de `[Iₙ | A⁻¹]` viaja a la tarjeta de A⁻¹. Solo vuelan si origen y destino se ven enteros.
* **Resultados.** El badge se asienta (fundido y 6 px) y las secciones entran en orden de lectura; si el resultado no cambió, el badge pulsa. Al editar después de calcular, el veredicto viejo se desvanece encima del estado nuevo.
* **Orientación.** Avisos que entran, salen y cuentan el tiempo para deshacer (pausa con el cursor encima); desplazamiento suave hasta los resultados; indicador del módulo activo que se desliza; fundido entre módulos y pestañas; paneles que entran con un fundido.
* **Entrada.** Los corchetes crecen o se contraen desde su tamaño anterior y las celdas nuevas llegan teñidas; el destello de pegar o deshacer es un tinte que decae; al intentar calcular con celdas inválidas, la primera pulsa dos veces en rojo.
* **Momentos por módulo.** Sarrus traza su diagonal y escribe el término; el inspector de A·B enciende los pares `(aᵢₖ, bₖⱼ)` por `k`; LU pulsa las filas que P permutó y muestra `y` antes que `x`; T(v) se arma fila por fila; las columnas pivote se encienden con la base de im(T) y las libres con la de nu(T); en un conjunto dependiente cada coeficiente aparece junto a su vector.

### 9.4. Qué no se anima

* Hover, presión y `:checked` de botones con QSS (solo lo pintado a mano, como la barra lateral).
* El cambio a riel de la barra al redimensionar, ni nada durante un redimensionamiento: lo pendiente salta al final.
* El foco entre celdas, la escritura y la aparición del error en una celda.
* Diálogos, combos y tooltips (quedan nativos de Qt por paridad entre plataformas).
* La geometría de widgets dentro de layouts: la geometría final se aplica de inmediato y se anima la pintura o la opacidad.
* El cambio de tema (requiere reiniciar).
* Nada en bucle ni en reposo.

### 9.5. Reglas técnicas

* Se anima lo pintado (`paintEvent`) o una capa encima; nunca `setStyleSheet` ni `repolish` por fotograma.
* Lo que viaja entre widgets se pinta en una sola capa por ventana, oculta mientras no hay nada en vuelo y transparente al ratón. Se cancela ante un redimensionamiento, un desplazamiento de las áreas de origen o destino y un cambio de módulo.
* Un solo efecto gráfico por widget y nunca anidado; los efectos temporales se quitan al terminar. Las páginas grandes se funden por instantánea, no con efecto.
* Cada animación es hija del widget que anima y sus callbacks toleran objetos ya borrados.
* `finish_all()` lleva todo a su estado final (las pruebas lo usan al terminar).

### 9.6. Reducir animaciones

*Apariencia* (Ctrl+,) tiene «Reducir animaciones», guardada en `appearance/reduce_motion` y aplicada sin reiniciar; `PRETTYCALC_REDUCE_MOTION=1` la fuerza. En Windows, si el usuario nunca la eligió, se toma la preferencia del sistema. Con ella activa no hay desplazamientos, vuelos, escalas, trazos progresivos ni escalonados: cada realce se muestra como estado final estático, el desplazamiento a un widget es instantáneo y la reproducción del procedimiento sigue disponible, sin movimiento.

Ningún destello se repite más de 3 veces por segundo (WCAG 2.3.1) y las animaciones no tocan los tokens ni el contraste del estado final. Los tintes animados usan un alfa más alto en el tema claro para seguir viéndose.
