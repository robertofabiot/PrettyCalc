# Definición del Problema - PrettyCalc

## 1. Contexto y Justificación
El aprendizaje y aplicación del álgebra lineal en niveles universitarios (ingenierías, ciencias exactas, computación) exige tanto la verificación rápida de resultados como la comprensión del procedimiento paso a paso (ej. transformaciones elementales de fila, escalonamiento, pivoteo, sustitución). 

Las herramientas convencionales suelen presentar interfaces áridas y confusas: abren cuadrículas gigantescas vacías que intimidan al usuario, ocultan el vector de términos independientes $b$ rompiendo el modelo mental de transcribir una ecuación ($Ax = b$), obligan al uso exhaustivo del ratón para introducir números celda por celda, o arrojan pergaminos infinitos de matrices sin destacar visualmente qué fila mutó o qué celda actuó como pivote.

## 2. Declaración del Problema
Los estudiantes universitarios necesitan una herramienta de escritorio interactiva, intuitiva y visualmente refinada que:
1. Elimine la fricción y ansiedad en la introducción de datos matriciales iniciando directamente en una matriz accesible de **$2 \times 2$ con vector $b$ visible**, permitiendo el crecimiento dinámico orgánico mediante **celdas fantasma (Ghosting)** accionables al pasar el cursor (`+`) y navegación 100% fluida por teclado.
2. Desglose los procedimientos paso a paso mediante un **controlador de pasos (Stepper/Carrusel)** interactivo que resalte los elementos pivote y explique la heurística de cada transformación.
3. Clasifique y valide rigurosamente los resultados mediante un **Dashboard de Resultados** con identificación de variables libres y verificación automática por sustitución exacta (✓).

## 3. Objetivos del Proyecto

### 3.1. Objetivos Principales
1. **Desarrollar una aplicación de escritorio en PySide6 (Python)** moderna, estética y libre de dependencias externas de cálculo (NumPy/SciPy/SymPy).
2. **Implementar inicio directo en $2 \times 2 (+ b)$ con Crecimiento Dinámico:** Cuadrícula interactiva con celdas fantasma que reaccionan con un botón `+` en hover para expandir filas/columnas sin necesidad de configuraciones previas ni memorización de atajos.
3. **Visibilidad Continua de la Matriz Aumentada $[A \mid b]$:** Separación visual elegante mediante línea divisoria en la columna de términos independientes desde el primer milisegundo.
4. **Optimizar la cuadrícula de entrada (Grid Affordance):** Navegación completa por teclado (`Tab`, flechas) con validación en tiempo real y prevención de errores (borde en `color-feedback-error` para entradas inválidas).
5. **Visualizador de Algoritmos en Carrusel/Stepper:** Navegación paso a paso (`[ ◀ Anterior ]`, `[ Siguiente ▶ ]`) con resaltado visual del pivote activo y texto explicativo de la heurística.
6. **Dashboard de Resultados y Verificación:** Panel lateral/modal con badges de estado (Consistente Determinado, Consistente Indeterminado, Inconsistente), diferenciación de variables libres con icono (🔑) y checklist de validación por sustitución (✓).

### 3.2. Objetivos Secundarios
1. Aritmética exacta por defecto basada en `fractions.Fraction`, con alternancia opcional a formato decimal.
2. Alineación tipográfica perfecta de matrices utilizando fuentes Monospace dedicadas.

## 4. Usuarios Objetivo y Casos de Uso
* **Perfil:** Estudiantes universitarios de carreras STEM.
* **Casos de Uso Principales:**
  * **CU-01 (Entrada Inmediata y Crecimiento):** Comenzar a escribir en la matriz $2 \times 2 (+ b)$ y expandirla dinámicamente con un clic en `+` o mediante teclado según el tamaño de su ejercicio.
  * **CU-02 (Exploración del Procedimiento):** Recorrer el carrusel de pasos analizando cada pivote y la operación elemental de fila aplicada.
  * **CU-03 (Revisión de Solución y Checklist):** Verificar el tipo de sistema en el Dashboard y constatar la validez de la solución con el checklist de sustitución.

## 5. Alcance General (Scope)

### 5.1. Dentro del Alcance (In-Scope)
* Aplicación de escritorio nativa multiplataforma (Linux, Windows, macOS).
* Motor matemático en Python puro con trazador de pasos y verificador de ecuaciones.
* Componentes de UI especializados: DynamicMatrixGrid con Ghosting, AugmentedMatrixDelegate, Stepper Carousel, Results Dashboard.

### 5.2. Fuera del Alcance (Out-of-Scope)
* Uso de librerías externas de álgebra lineal para el cálculo.
* Entornos web o móviles en esta fase.
* Despliegue en servidores o bases de datos externas.

## 6. Restricciones Técnicas
* Python 3.10+ y PySide6.
* Cero librerías externas para el motor matemático (`prettycalc.core`).
