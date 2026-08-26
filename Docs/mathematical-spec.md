# Especificación Matemática - PrettyCalc

## 1. Tipos de Datos y Aritmética Numérica
* **Aritmética Exacta por Defecto:** Todo el motor de cálculo opera internamente utilizando el módulo estándar `fractions.Fraction` de Python.
  * Los números enteros y racionales se almacenan como fracciones exactas irreducible ($p/q$), garantizando que operaciones como $1/3 \times 3 = 1$ sin pérdida por punto flotante.
* **Modo Decimal / Flotante:** La capa de presentación y el motor permiten convertir y proyectar los resultados en formato decimal con precisión configurable según preferencia del usuario.
* **Escalares Mixtos Admitidos:** Admisión de entradas como enteros (`-5`), fracciones (`3/4`, `-1/2`) y decimales (`0.75`).

## 2. Estructuras Algebraicas y Dimensiones
* **Matrices ($N \times M$):**
  * Soporte para dimensiones arbitrarias ($1 \times 1, 2 \times 2, 3 \times 3, \dots, N \times M$).
  * Matrices cuadradas y rectangulares.
* **Vectores ($n$-dimensionales):**
  * Tratados algebraicamente como matrices columna ($n \times 1$) o fila ($1 \times n$).

## 3. Operaciones Elementales y Registro de Heurísticas

### 3.1. Operaciones Elementales de Fila
El motor matemático implementa de forma pura las tres operaciones elementales de fila, asociando a cada una su representación en LaTeX formal y su texto heurístico descriptivo:

| Operación Elemental | Notación Formal (LaTeX) | Heurística Descriptiva |
| :--- | :--- | :--- |
| **Combinación Lineal** | $f_i \underset{\sim}\rightarrow k \cdot f_j + f_i$ | *"Se multiplicó la Fila $j$ por $k$ y se sumó a la Fila $i$."* |
| **Intercambio de Filas** | $f_i \leftrightarrow f_j$ | *"Se intercambió la Fila $i$ con la Fila $j$."* |
| **Escalamiento de Fila** | $f_i \underset{\sim}\rightarrow k \cdot f_i$ | *"Se multiplicó la Fila $i$ por el escalar $k$."* |

### 3.2. Estructura de Datos de cada Paso (`CalculationStep`)
Cada paso registrado por el algoritmo incluye:
1. `matrix_state`: Estado de la matriz en ese instante.
2. `pivot_position`: Coordenadas `(row, col)` de la celda pivote activa.
3. `latex_formula`: Expresión formal de la operación.
4. `heuristic_text`: Explicación en texto claro de qué fila mutó y cómo.

---

## 4. Resolución, Clasificación y Verificación de Sistemas ($Ax = b$)

### 4.1. Clasificación Canónica del Sistema
1. **Consistente Determinado (SCD):**
   * Badge semántico: `color-feedback-success` (`#81B29A` - *Muted Sage*).
   * Solución única ($rango(A) = rango(A|b) = n$).
   * Todas las variables son básicas.
2. **Consistente Indeterminado (SCI):**
   * Badge semántico: Tono de advertencia / atención.
   * Infinitas soluciones ($rango(A) = rango(A|b) < n$).
   * Desglose explícito de **variables básicas** vs **variables libres** (identificadas con el ícono 🔑).
   * Expresión de la solución en forma vectorial paramétrica.
3. **Inconsistente (SI):**
   * Badge semántico: `color-feedback-error` (`#EE6C4D` - *Burnt Peach*).
   * Sin solución ($rango(A) < rango(A|b)$).
   * Identificación de la fila conflictiva ($0 = c$ con $c \neq 0$).

### 4.2. Algoritmo de Verificación por Sustitución (Checklist de Validación)
Para sistemas consistentes (determinados o soluciones particulares en indeterminados):
1. El motor realiza la multiplicación del vector solución calculado contra cada fila $i$ del sistema original:
   $$\sum_{j=1}^n A_{i, j} \cdot x_j \stackrel{?}{=} b_i$$
2. Utiliza aritmética de fracciones exactas para garantizar que la igualdad sea absoluta ($LHS - RHS = 0$).
3. Genera el resultado booleano que alimenta el checklist visual con el icono (**✓**) coloreado en `color-feedback-success` (`#81B29A`) al lado de cada ecuación original.
