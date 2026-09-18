# Casos de prueba académicos — Sprint 2 (Programa 3, MTM0120)

Material de apoyo para el informe PDF `Informe_Programa 3_Grupo 4.pdf`.
Todos los cálculos usan aritmética exacta (`fractions.Fraction`); no hay redondeo flotante.

---

## 1. Multiplicación matricial exitosa (producto conformable)

**Enunciado.** Calcular \(C = A \cdot B\) con

\[
A = \begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{bmatrix}_{2\times 3}
\qquad
B = \begin{bmatrix} 7 & 8 \\ 9 & 10 \\ 11 & 12 \end{bmatrix}_{3\times 2}
\]

**Conformabilidad.** Columnas de \(A\) (3) = filas de \(B\) (3). El resultado es \(2\times 2\).

**Algoritmo (tres bucles anidados).** Para cada \(i\in\{1,2\}\), \(j\in\{1,2\}\):

\[
C_{ij} = \sum_{k=1}^{3} A_{ik}\, B_{kj}
\]

| Celda | Sumatoria | Valor |
| --- | --- | --- |
| \(C_{11}\) | \((1)(7)+(2)(9)+(3)(11)\) | \(58\) |
| \(C_{12}\) | \((1)(8)+(2)(10)+(3)(12)\) | \(64\) |
| \(C_{21}\) | \((4)(7)+(5)(9)+(6)(11)\) | \(139\) |
| \(C_{22}\) | \((4)(8)+(5)(10)+(6)(12)\) | \(154\) |

\[
C = \begin{bmatrix} 58 & 64 \\ 139 & 154 \end{bmatrix}
\]

**Dónde reproducirlo**
- GUI: módulo *Álgebra Matricial* → botón «Ejemplo 2×3 · 3×2». Pulsar una celda de \(C\) abre el inspector (fila de \(A\) y columna de \(B\)).
- CLI: opción `3` → `4` de `Programa 3_Grupo4.py`.

**No conmutatividad.** \(A\cdot B\) es \(2\times 2\); \(B\cdot A\) sería \(3\times 3\). El producto no conmuta en general.

---

## 2. Error de dimensiones incompatibles

**Enunciado.** Intentar \(A_{2\times 3} \cdot B_{2\times 2}\).

\[
A = \begin{bmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{bmatrix}
\qquad
B = \begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}
\]

**Regla violada.** El producto \(A_{m\times n}\cdot B_{n\times p}\) exige que las columnas de \(A\) igualen las filas de \(B\). Aquí \(n_A = 3 \neq 2 = m_B\).

**Comportamiento esperado (sin caída de la aplicación)**
- El motor lanza `DimensionMismatchError` con el mensaje:
  *«columnas de A (3) ≠ filas de B (2)»*.
- La GUI muestra un badge en `#EE6C4D` y **deshabilita** el botón Calcular.
- El CLI imprime el mismo diagnóstico y vuelve al menú.

**Dónde reproducirlo**
- GUI: *Álgebra Matricial* → «Ejemplo incompatible».
- CLI: opción `3` → `4` con \(n_A=3\) y \(n_B=2\).

---

## 3. Combinación lineal afirmativa (SCD)

**Enunciado.** ¿Es \(b = (2,\,-1/2,\,3)\) combinación lineal de la base canónica de \(\mathbb{R}^3\)?

\[
v_1 = e_1 = \begin{bmatrix}1\\0\\0\end{bmatrix},
\quad
v_2 = e_2 = \begin{bmatrix}0\\1\\0\end{bmatrix},
\quad
v_3 = e_3 = \begin{bmatrix}0\\0\\1\end{bmatrix}
\]

El sistema \(A c = b\) con columnas de \(A\) iguales a \(v_j\) es ya la identidad:

\[
\begin{bmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix}
\begin{bmatrix} c_1 \\ c_2 \\ c_3 \end{bmatrix}
=
\begin{bmatrix} 2 \\ -1/2 \\ 3 \end{bmatrix}
\]

**Resultado.** SCD: sí es combinación lineal única, con pesos

\[
c_1 = 2,\quad c_2 = -\tfrac{1}{2},\quad c_3 = 3
\]

es decir \(b = 2 v_1 - \tfrac{1}{2} v_2 + 3 v_3\).

**Comprobación (✓ `#81B29A`)**

| Componente | \(\sum c_i (v_i)_k\) | \(b_k\) |
| --- | --- | --- |
| 1 | \(2\) | \(2\) |
| 2 | \(-1/2\) | \(-1/2\) |
| 3 | \(3\) | \(3\) |

**Dónde reproducirlo:** GUI *Vectores en ℝⁿ* → subpestaña Combinación lineal → «Ejemplo SCD». CLI: opción `2`.

---

## 4. Combinación lineal inconsistente (SI)

**Enunciado.** Vectores en el plano \(xy\) y un objetivo con componente \(z\) no nula:

\[
v_1 = \begin{bmatrix}1\\0\\0\end{bmatrix},
\quad
v_2 = \begin{bmatrix}0\\1\\0\end{bmatrix},
\quad
b = \begin{bmatrix}0\\0\\1\end{bmatrix}
\]

La matriz aumentada \([v_1\ v_2 \mid b]\) produce, tras Gauss-Jordan, una fila contradictoria \([0\ 0 \mid 1]\), es decir \(0 = 1\).

**Resultado.** SI: \(b\) **no** pertenece a \(\operatorname{span}\{v_1,v_2\}\). No es combinación lineal.

**Dónde reproducirlo:** GUI → «Ejemplo SI». CLI: opción `2` con los mismos vectores.

---

## 5. Ecuación matricial \(A x = b\) (solución única)

\[
A = \begin{bmatrix} 1 & 1 & 1 \\ 2 & -1 & 1 \\ 1 & 2 & -1 \end{bmatrix},
\qquad
b = \begin{bmatrix} 4 \\ 4 \\ 3 \end{bmatrix}
\]

**RREF de \([A\mid b]\)**

\[
\left[\begin{array}{ccc|c}
1 & 0 & 0 & 2 \\
0 & 1 & 0 & 1 \\
0 & 0 & 1 & 1
\end{array}\right]
\]

**Solución.** SCD: \(x = (2,\,1,\,1)^\top\).

**Comprobación por producto** \(A\cdot x \stackrel{?}{=} b\) (mismos tres bucles):

\[
A x = \begin{bmatrix} 4 \\ 4 \\ 3 \end{bmatrix} = b
\]

**Dónde reproducirlo:** GUI *Ecuaciones Matriciales* → «Ejemplo 3×3». CLI: opción `4`.

---

## 6. Capturas sugeridas para el informe

1. Producto \(2\times 3 \cdot 3\times 2\) con el inspector abierto sobre \(C_{11}\) o \(C_{21}\).
2. Badge de incompatibilidad en Burnt Peach (`#EE6C4D`) y botón Calcular deshabilitado.
3. Dashboard SCD de combinación lineal con pesos y checklist ✓.
4. Dashboard SI («NO ES COMBINACIÓN LINEAL») con la fila contradictoria.
5. Vista \(A x = b\) con el vector \(x\) y la comprobación \(A\cdot x = b\).

Atajos de la GUI: `Ctrl+1` sistemas, `Ctrl+2` matrices, `Ctrl+3` vectores, `Ctrl+4` ecuaciones.
