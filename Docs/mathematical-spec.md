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
  * La norma euclidiana se guarda como \(\|v\|^2 = \sum v_i^2 \in \mathbb{Q}\) y se muestra como radical simplificado \(a\sqrt{b}/c\), obtenido por factorización de enteros. La distancia es \(d(u, v) = \|u - v\|\).
  * El producto exterior \(u v^T\) es la matriz \(m \times n\) con entradas \(u_i v_j\).

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

### 4.3. Forma Vectorial Paramétrica de un SCI
Si el sistema es consistente indeterminado, además de los despejes escalares se construye

\[
x = p + \sum_k t_k v_k
\]

donde \(p\) es la solución particular con cada variable libre igual a 0, y cada \(v_k\) es el vector de la base del núcleo asociado a esa variable libre (1 en su posición y el coeficiente de despeje en las variables básicas).

---

## 5. Inversa por Gauss-Jordan

Para \(A\) de orden \(n \times n\):

1. Se forma la matriz super-aumentada \([A \mid I_n]\).
2. Se calcula su forma escalonada reducida con las mismas operaciones elementales de fila del resto del motor.
3. Si el bloque izquierdo es \(I_n\), el bloque derecho es \(A^{-1}\). Se comprueba \(A \cdot A^{-1} = I_n\) y \(A^{-1} \cdot A = I_n\) en aritmética exacta.
4. Si alguna fila del bloque izquierdo queda en ceros, \(A\) es singular: no existe \(A^{-1}\) (Teorema de la Matriz Invertible, \(\det(A) = 0\)).
5. Si \(A\) no es cuadrada, la inversa no está definida.

Con \(A\) invertible, el sistema \(Ax = b\) también puede resolverse como \(x = A^{-1} b\).

---

## 6. Determinantes, adjunta y Regla de Cramer

El determinante de una matriz cuadrada se calcula en aritmética exacta, sin escalar los pivotes cuando el método es la triangulación:

1. **2×2:** \(\det(A) = ad - bc\).
2. **Sarrus (3×3):** suma de las diagonales principales menos las secundarias.
3. **Triangulación:** intercambiar filas multiplica por \(-1\); sumar un múltiplo de una fila a otra no cambia el determinante. Al quedar triangular, \(\det(A) = (-1)^k \prod u_{ii}\). Si falta un pivote, \(\det(A) = 0\).
4. **Laplace:** \(\det(A) = \sum a_{ij} C_{ij}\) por cualquier fila o columna, con \(C_{ij} = (-1)^{i+j} M_{ij}\). Cada menor se evalúa por triangulación. El menor de una matriz \(1\times 1\) vale 1 por convención.

La matriz de cofactores \(C\) y la adjunta \(\operatorname{adj}(A) = C^T\) están definidas aunque \(A\) sea singular. La inversa analítica

\[
A^{-1} = \frac{1}{\det(A)}\operatorname{adj}(A)
\]

solo se construye cuando \(\det(A) \neq 0\).

La Regla de Cramer resuelve \(Ax = b\) cuando \(A\) es \(n\times n\) y \(\det(A) \neq 0\):

\[
x_i = \frac{\det(A_i(b))}{\det(A)}
\]

\(A_i(b)\) es \(A\) con la columna \(i\) sustituida por \(b\). Si \(\det(A) = 0\), Cramer no aplica y el sistema se clasifica con Gauss-Jordan.

---

## 7. Factorización LU y resolución en dos etapas

Para \(A\) de tamaño \(m \times n\):

1. \(L\) es \(m \times m\), triangular inferior unitaria: unos en la diagonal y, debajo, los multiplicadores de la eliminación.
2. \(U\) es \(m \times n\) y es la forma escalonada de \(A\). Solo se usan reemplazos \(f_i \to f_i + k f_j\) con \(i > j\). No hay intercambios de fila.
3. El multiplicador de la fila \(i\) bajo el pivote \(p\) es \(\ell = a_{ij}/p\). Se guarda en \(L\) y se anula en \(U\).
4. Si una columna es cero desde la fila actual hacia abajo, no tiene pivote y se pasa a la siguiente. Así se factoriza el ejemplo \(4 \times 5\) de la sesión, cuya tercera columna queda sin pivote.
5. Si el candidato a pivote es 0 y debajo hay una entrada distinta de cero, no existe \(A = LU\). `lu_decompose` lanza `LUPivotZeroError`. `plu_decompose` sí construye la permutación.

### 7.1. Factorización \(PA = LU\)

\(P\) empieza como \(I_m\). Cuando el pivote de la fila actual es 0 y una fila inferior tiene una entrada distinta de cero, se intercambia con la primera de esas filas. El mismo intercambio se aplica a \(P\) y a los multiplicadores ya guardados en las columnas anteriores de \(L\). La comprobación es \(P A = L U\). Si no hubo intercambios, \(P = I\) y los factores coinciden con \(A = LU\).

Cuando \(A\) es cuadrada y la diagonal de \(U\) no tiene ceros, \(Ax = b\) se resuelve en dos etapas, reutilizando los mismos factores para cada vector de carga:

1. Sustitución hacia adelante: \(Ly = b\) si \(P = I\), o \(Ly = Pb\) si hubo permutación.
2. Sustitución hacia atrás: \(Ux = y\).

La comprobación exige \(LU = A\) (o \(PA = LU\)), \(Ly = Pb\), \(Ux = y\) y \(Ax = b\) en aritmética exacta. Si \(U\) tiene un cero en la diagonal, la factorización puede existir igual y el sistema no tiene solución única.

---

## 8. Aplicaciones de sistemas lineales

El asistente arma la matriz aumentada. El estudiante no la transcribe.

### 8.1. Balanceo químico
Cada elemento es una ecuación homogénea: átomos en los reactivos menos átomos en los productos. Con un solo grado de libertad, el generador del núcleo se convierte en enteros positivos mínimos: se multiplica por el mínimo común múltiplo de los denominadores y se divide por el máximo común divisor. El propano queda \(1\,C_3H_8 + 5\,O_2 \rightarrow 3\,CO_2 + 4\,H_2O\).

### 8.2. Modelo cerrado de Leontief
\(C\) es la tabla de consumo. En el modelo cerrado cada columna suma 1. Los precios de equilibrio resuelven \((I - C)p = 0\). La última variable libre se normaliza en 1. Para carbón, electricidad y acero el vector relativo es \(\left(\frac{31}{33}, \frac{28}{33}, 1\right)\), que la diapositiva redondea a \(0.94\), \(0.85\) y \(1\).

### 8.3. Dieta
\(Ax = b\) con una columna por alimento y una fila por nutriente. Una componente negativa no es una mezcla realizable. La dieta Cambridge, con la grasa del suero en \(\frac{11}{10}\), tiene solución única; cada unidad son 100 g.

### 8.4. Redes de flujo
Cada nodo conserva el flujo. En una calle de un solo sentido, \(x_i \ge 0\). Con una variable libre, esas desigualdades recortan un intervalo. En la red de Baltimore la libre es \(x_5\) y el intervalo es \([0, 500]\): \(x_4 = 500 - x_5\) no puede ser negativa, y el resto de las calles queda dentro de un rango cerrado. Con más de una variable libre se escribe la solución general y no se cierran las cotas por símplex.
