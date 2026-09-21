# Reglas y Principios de Diseño - PrettyCalc

## 1. Filosofía Visual y Experiencia de Usuario ("PrettyCalc")
La aplicación prioriza la elegancia, la claridad cognitiva y la eliminación total de fricción. Las matemáticas son ordenadas y la interfaz debe reflejarlo mediante principios de **Carga Progresiva Natural**, **Visibilidad del Estado del Sistema (Nielsen)**, **Prevención de Errores** y un **Design System Cromático** de alto contraste.

---

## 2. Design System: Especificaciones Cromáticas y Tokens Visuales

| Token Semántico | Nombre del Tono | Valor HEX | Uso Estricto en la Interfaz |
| :--- | :--- | :--- | :--- |
| `color-bg-base` | **Shadow Grey** | `#1A181B` | **Lienzo de fondo principal** de la ventana. Absorbe la luz y da protagonismo a los paneles de datos. |
| `color-surface-elevated` | **Vintage Grape** | `#564D65` | **Superficies elevadas y contenedores:** Fondos de Cards laterales (Dashboard de resultados) y contenedor de la cuadrícula de la matriz. |
| `color-text-primary` | **Light Cyan** | `#E0FBFC` | **Tipografía de alto contraste:** Títulos, etiquetas de ejes, texto de botones principales y coeficientes de las matrices. |
| `color-interactive-idle` | **Powder Blue** | `#98C1D9` | **Interacción secundaria:** Bordes de celdas en reposo, botones secundarios (`[ ◀ Paso Anterior ]`), texto tenue de fórmulas ($f_2 \rightarrow f_2 - 3f_1$) y **línea divisoria vertical de la matriz aumentada**. |
| `color-interactive-disabled` | **Dimmed Grape** | `#3A3642` | **Controles inactivos / deshabilitados:** Botón "Paso Anterior" en el Paso 1 para evitar clics inválidos. |
| `color-feedback-error` | **Burnt Peach** | `#EE6C4D` | **Feedback de Error / Inconsistencia:** Badge de *"Sistema Inconsistente"*, borde de celda ante entradas inválidas (letras) y alertas. |
| `color-feedback-success` | **Muted Sage** | `#81B29A` | **Feedback de Éxito:** Badge de *"Sistema Consistente"*, checkmarks (**✓**) de validación y resaltado de pivote/fila escalonada. |

---

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
    * Botón **`[ ◀ Paso Anterior ]`** (inactivo con `color-interactive-disabled` (`#3A3642`) en el Paso 1).
    * Indicador de progreso (ej. *Paso 3 de 8*).
    * Botón **`[ Siguiente Paso ▶ ]`**.
* **Atención Visual y Resaltado:**
  * **Pivote Activo y Fila Mutada:** La celda pivote de la iteración se resalta visualmente con un acento suave o badge de color `color-feedback-success` (`#81B29A`).
  * **Explicación de Heurística:** Debajo de la matriz, se muestra la fórmula formal en `color-interactive-idle` y un texto en cursiva explicando la mutación ocurrida:
    $$\text{Paso: } f_2 \underset{\sim}\rightarrow -3f_1 + f_2$$
    *“Se multiplicó la Fila 1 por -3 y se sumó a la Fila 2.”*

---

## 6. Tipografía y Jerarquía Visual
* **Números de Matrices (Alineación Perfecta):**
  * Uso estricto de fuente **Monospace** (`Fira Code`, `Roboto Mono` o `Courier New`) en color `color-text-primary` (`#E0FBFC`). Esto garantiza que signos negativos, dígitos y fracciones ocupen exactamente el mismo ancho visual, manteniendo columnas perfectamente alineadas.
* **Interfaz General (UI Chrome):**
  * Fuente limpia **Sans-serif** (`Inter` o `Segoe UI`) para títulos, botones, etiquetas y modales.

---

## 7. Dashboard de Resultados
Al alcanzar el paso final de la resolución, la UI despliega un Card lateral o Modal estilizado sobre `color-surface-elevated` (`#564D65`):

1. **Identificador de Estado (Badge Semántico de Color):**
   * **Consistente Determinado:** Badge con `color-feedback-success` (`#81B29A`).
   * **Consistente Indeterminado:** Badge de atención (Amarillo / Acento).
   * **Inconsistente:** Badge con `color-feedback-error` (`#EE6C4D`).
2. **Desglose de Variables:**
   * Separación visual entre variables básicas y **variables libres**.
   * Las variables libres se distinguen con un ícono explícito (ej. 🔑 o `*`).
3. **Checklist de Validación de la Solución:**
   * Verificación visual de sustitución en el sistema original.
   * Icono de confirmación en `color-feedback-success` (**✓** `#81B29A`) al lado de cada ecuación original confirmando que la igualdad matemática es exacta.
