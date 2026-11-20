# UNIVERSIDAD AMERICANA (UAM)
## Facultad de Ingeniería y Arquitectura (FIA)
### Asignatura: Álgebra Lineal (MTM0120) — II Semestre 2026
### Proyecto Integrador — Entrega Programa 8

---

# INFORME TÉCNICO: INTEGRACIÓN DE MÉTODOS ITERATIVOS (JACOBI Y GAUSS-SEIDEL) A LA CALCULADORA DE ÁLGEBRA LINEAL, ANÁLISIS DE CONVERGENCIA Y GUÍA DE DEFENSA INDIVIDUAL

* **Cátedra:** Álgebra Lineal (MTM0120)
* **Integrantes del Grupo 4:**
  * Roberto Fabio Tercero Morán (Carnet / Correo: `rftercerom@uamv.edu.ni`)
  * Steven Alexander Flores Obregón (Carnet / Correo: `safloreso@uamv.edu.ni`)
  * Kellys Bellanger (Carnet / Correo: `kbbellanger@uamv.edu.ni`)
  * Raúl Valverde Ruiz (Carnet / Correo: `raulvruiz@uamv.edu.ni`)
* **Carrera:** Ingeniería en Sistemas de Información / Ingeniería de Software
* **Fecha:** Noviembre de 2026
* **Semestre:** 4.° Semestre

---

## 1. Introducción y Objetivos del Proyecto

El presente proyecto corresponde al **Octavo Programa** de la asignatura Álgebra Lineal (MTM0120) de la Universidad Americana (UAM). En esta entrega, el Grupo 4 integra formalmente los **métodos iterativos de Jacobi y Gauss-Seidel** a la calculadora de Álgebra Lineal desarrollada a lo largo del curso.

### Objetivos Principales:
1. **Implementación Rigurosa y Didáctica:** Desarrollar los algoritmos de Jacobi y Gauss-Seidel en **Python estándar (100% puro)** utilizando la clase `fractions.Fraction` para aritmética exacta, garantizando que el único error visible en las iteraciones provenga del truncamiento de la serie iterativa y no de la pérdida de dígitos por punto flotante.
2. **Diagnóstico Teórico Previo:** Implementar comprobaciones automáticas de **Dominancia Diagonal Estricta**, cálculo del **Polinomio Característico** mediante el método de Faddeev-LeVerrier, raíces complejas mediante **Durand-Kerner**, y estimación del **Radio Espectral $\rho(T)$**, así como el criterio de Sylvester para **matrices simétricas definidas positivas**.
3. **Casos de Prueba Demostrativos:** Demostrar numéricamente, mediante 6 casos de prueba controlados, la aproximación de soluciones de sistemas de ecuaciones lineales $A\mathbf{x} = \mathbf{b}$, la comparación de tasas de convergencia entre ambos métodos, y la identificación certera de escenarios donde los métodos divergen o donde el reordenamiento de ecuaciones restaura la convergencia.
4. **Defensa Individual del Trabajo:** Documentar las decisiones de diseño y proporcionar un compendio estructurado de preguntas conceptuales para que cada integrante comprenda a fondo los algoritmos, justifique el código desarrollado y defienda con éxito su trabajo ante la cátedra.

---

## 2. Fundamentación Teórica y Modelado Matemático

### 2.1. Descomposición Canónica de la Matriz de Coeficientes
Sea un sistema de $n$ ecuaciones lineales con $n$ incógnitas expresado matricialmente como $A\mathbf{x} = \mathbf{b}$, donde la matriz de coeficientes $A \in \mathbb{R}^{n \times n}$ posee elementos diagonales no nulos ($a_{ii} \neq 0$ para todo $i = 1, \dots, n$).

Se descompone aditivamente la matriz $A$ en la suma canónica:
$$A = D + L + U$$

Donde:
* $D = \text{diag}(a_{11}, a_{22}, \dots, a_{nn})$ es la matriz diagonal principal.
* $L$ es la matriz triangular inferior estricta con ceros en la diagonal ($l_{ij} = a_{ij}$ si $i > j$, y $0$ si $i \le j$).
* $U$ es la matriz triangular superior estricta con ceros en la diagonal ($u_{ij} = a_{ij}$ si $i < j$, y $0$ si $i \ge j$).

---

### 2.2. Método Iterativo de Jacobi (Desplazamiento Simultáneo)
En el método de Jacobi, cada incógnita $x_i$ se despeja de la $i$-ésima ecuación del sistema:
$$x_i^{(k+1)} = \frac{1}{a_{ii}} \left( b_i - \sum_{j=1, j \neq i}^{n} a_{ij} x_j^{(k)} \right), \quad i = 1, 2, \dots, n$$

**Propiedad distintiva:** Todas las componentes del nuevo vector $\mathbf{x}^{(k+1)}$ se evalúan utilizando **exclusivamente** los valores de la iteración inmediatamente anterior $\mathbf{x}^{(k)}$. Por este motivo, se conoce como método de **desplazamientos simultáneos** y es naturalmente paralelizable en arquitecturas multihilo.

**Formulación Matricial:**
$$(D + L + U)\mathbf{x} = \mathbf{b} \implies D\mathbf{x} = \mathbf{b} - (L + U)\mathbf{x}$$
$$\mathbf{x}^{(k+1)} = -D^{-1}(L + U)\mathbf{x}^{(k)} + D^{-1}\mathbf{b}$$

Definiendo la **Matriz de Iteración de Jacobi** ($T_J$) y el vector de traslación ($\mathbf{c}_J$):
$$T_J = -D^{-1}(L + U), \quad \mathbf{c}_J = D^{-1}\mathbf{b} \implies \mathbf{x}^{(k+1)} = T_J \mathbf{x}^{(k)} + \mathbf{c}_J$$

---

### 2.3. Método Iterativo de Gauss-Seidel (Desplazamiento Sucesivo)
En el método de Gauss-Seidel, las componentes ya calculadas de la iteración en curso $x_1^{(k+1)}, \dots, x_{i-1}^{(k+1)}$ se sustituyen **de forma inmediata** en la ecuación para determinar $x_i^{(k+1)}$:
$$x_i^{(k+1)} = \frac{1}{a_{ii}} \left( b_i - \sum_{j=1}^{i-1} a_{ij} x_j^{(k+1)} - \sum_{j=i+1}^{n} a_{ij} x_j^{(k)} \right), \quad i = 1, 2, \dots, n$$

**Propiedad distintiva:** Se denomina método de **desplazamientos sucesivos**. No requiere duplicar el vector en memoria (puede realizarse la actualización *in-place*), y en una gran variedad de matrices prácticas acelera la velocidad de convergencia respecto a Jacobi.

**Formulación Matricial:**
$$(D + L)\mathbf{x}^{(k+1)} + U\mathbf{x}^{(k)} = \mathbf{b} \implies (D + L)\mathbf{x}^{(k+1)} = \mathbf{b} - U\mathbf{x}^{(k)}$$
$$\mathbf{x}^{(k+1)} = -(D + L)^{-1} U \mathbf{x}^{(k)} + (D + L)^{-1}\mathbf{b}$$

Definiendo la **Matriz de Iteración de Gauss-Seidel** ($T_{GS}$) y su traslación ($\mathbf{c}_{GS}$):
$$T_{GS} = -(D + L)^{-1} U, \quad \mathbf{c}_{GS} = (D + L)^{-1}\mathbf{b} \implies \mathbf{x}^{(k+1)} = T_{GS} \mathbf{x}^{(k)} + \mathbf{c}_{GS}$$

---

### 2.4. Teoremas y Criterios de Convergencia

#### A. Condición Suficiente: Dominancia Diagonal Estricta por Filas
Una matriz $A \in \mathbb{R}^{n \times n}$ es **estrictamente diagonal dominante por filas** si el valor absoluto de cada elemento diagonal es estrictamente mayor que la suma de los valores absolutos de los demás elementos de su misma fila:
$$|a_{ii}| > \sum_{j=1, j \neq i}^{n} |a_{ij}| \quad \forall i \in \{1, 2, \dots, n\}$$

* **Teorema de Convergencia:** Si $A$ es estrictamente diagonal dominante por filas, entonces **TANTO Jacobi COMO Gauss-Seidel CONVERGEN** a la solución única $\mathbf{x}^* = A^{-1}\mathbf{b}$ para cualquier vector inicial $\mathbf{x}^{(0)} \in \mathbb{R}^n$.
* **Naturaleza lógica:** Es una condición **suficiente**, pero **NO necesaria**. Si no se cumple, el método aún puede converger.

#### B. Condición Necesaria y Suficiente: Radio Espectral $\rho(T)$
Para cualquier esquema iterativo lineal estacionario de la forma $\mathbf{x}^{(k+1)} = T\mathbf{x}^{(k)} + \mathbf{c}$:
* Sea $\rho(T) = \max_i |\lambda_i|$ el **radio espectral** de la matriz de iteración $T$, donde $\lambda_i$ son los autovalores de $T$.
* **Teorema Fundamental:** El esquema iterativo converge para cualquier vector de inicio $\mathbf{x}^{(0)}$ si y solo si:
$$\rho(T) < 1$$
* **Velocidad Asintótica de Convergencia:** La rapidez con la que el error tiende a cero está gobernada por $R = -\ln(\rho(T))$. Cuanto más cercano a cero sea $\rho(T)$, menor cantidad de iteraciones serán necesarias.

#### C. Criterio de Ostrowski-Reich (Matrices Simétricas Definidas Positivas)
Si $A$ es una matriz simétrica ($A = A^T$) con elementos diagonales positivos ($a_{ii} > 0$), y es **definida positiva** (lo cual se verifica formalmente mediante el Criterio de Sylvester, evaluando que todos los menores principales directos tengan determinante positivo: $\det(A_k) > 0$), entonces:
$$\rho(T_{GS}) < 1$$
Es decir, el método de **Gauss-Seidel converge garantizado** para cualquier $\mathbf{x}^{(0)}$, aun cuando la matriz no sea diagonal dominante.

#### D. Teorema de Stein-Rosenberg y Desmitificación de Superioridad
Si todos los elementos fuera de la diagonal son no positivos ($a_{ij} \le 0$ para todo $i \neq j$) y $a_{ii} > 0$:
1. Si $\rho(T_J) < 1$, entonces $\rho(T_{GS}) < \rho(T_J) < 1$ (Gauss-Seidel converge más rápido que Jacobi).
2. Si $\rho(T_J) \ge 1$, entonces $\rho(T_{GS}) \ge \rho(T_J) \ge 1$ (ambos divergen).

> [!IMPORTANT]
> **Ruptura de mito docente:** Si la matriz contiene elementos de signos mixtos fuera de la diagonal, la hipótesis de Stein-Rosenberg no se cumple. **Gauss-Seidel NO siempre es superior a Jacobi**. Existen matrices donde Jacobi converge y Gauss-Seidel diverge (como se demuestra en el Caso de Prueba 3).

---

### 2.5. Criterios de Paro Numérico y Control de Divergencia

El programa evalúa en cada iteración la norma infinito del paso $\Delta \mathbf{x}^{(k)} = \mathbf{x}^{(k)} - \mathbf{x}^{(k-1)}$:
$$\|\Delta \mathbf{x}^{(k)}\|_\infty = \max_{1 \le i \le n} |x_i^{(k)} - x_i^{(k-1)}|$$

1. **Criterio de Paro Absoluto:** Se detiene cuando $\|\Delta \mathbf{x}^{(k)}\|_\infty < \varepsilon$.
2. **Criterio de Paro Relativo:** Se detiene cuando $\dfrac{\|\Delta \mathbf{x}^{(k)}\|_\infty}{\|\mathbf{x}^{(k)}\|_\infty} < \varepsilon$.
3. **Cota de Iteraciones ($k_{\max}$):** Previene ciclos infinitos en sistemas divergentes o de convergencia muy lenta.
4. **Detección Temprana de Divergencia (Norm Divergence Guard):** Si en cualquier iteración $\|\mathbf{x}^{(k)}\|_\infty > 10^8 \cdot \max(\|\mathbf{x}^{(0)}\|_\infty, \|\mathbf{b}\|_\infty, 1)$, el programa aborta y declara **DIVERGENCIA EXPLOSIVA**, ahorrando tiempo computacional y reportando el fallo de forma inmediata.

---

## 3. Decisiones de Arquitectura e Implementación

### 3.1. Cumplimiento del Contrato Didáctico (100% Python Estándar)
* Se descartaron bibliotecas de álgebra lineal como `numpy` y `scipy` para los cálculos numéricos e iterativos de la entrega.
* Todos los coeficientes, operaciones elementales y deltas se computan sobre instancias de la clase `fractions.Fraction`.
* **Beneficio didáctico:** El estudiante y el docente observan exactamente las fracciones reducidas y los valores numéricos sin el "ruido" de la mantisa flotante de IEEE 754.

### 3.2. Polinomio Característico Exacto y Raíces Complejas
* Para determinar $\rho(T)$ sin NumPy, se programó el algoritmo clásico de **Faddeev-LeVerrier**, el cual obtiene los coeficientes analíticos de $p(\lambda) = \det(\lambda I - T)$ en aritmética de fracciones exactas.
* Las raíces del polinomio característico se aproximan mediante el algoritmo de **Durand-Kerner (Weierstrass)** en el espacio de números complejos $\mathbb{C}$, garantizando la localización de todos los autovalores y el cálculo exacto de $\rho(T) = \max_i |\lambda_i|$.

### 3.3. Algoritmo de Reordenamiento de Ecuaciones (`reorder_for_dominance`)
Cuando un sistema contiene ceros en la diagonal ($a_{ii} = 0$) o no es diagonal dominante, el sistema explora las permutaciones de filas para ubicar los coeficientes de mayor magnitud en la diagonal principal. Si existe una permutación que vuelva al sistema estrictamente diagonal dominante, el programa la detecta, permuta el sistema y logra la convergencia.

### 3.4. Estructura de Entregables del Proyecto
El proyecto se organizó en tres frentes integrados:
1. `Programa 8_Grupo4.py` (en la raíz): Script interactivo 100% autónomo de consola, listo para evaluación individual o en grupo.
2. `Calculadora_Algebra_Lineal/modulos/modulo_iterativos.py`: Módulo 5 integrado a la suite modular del proyecto, con enlaces en `main.py` y `resumen_teoremas.py`.
3. `prettycalc/ui/modules/iterative_methods_view.py`: Módulo 10 de la aplicación gráfica PrettyCalc en PySide6, con gráfica de convergencia logarítmica y medidor espectral.

---

## 4. Demostración y Casos de Prueba Didácticos

El software incorpora un menú guiado de **6 casos de prueba preconfigurados** que demuestran todos los teoremas descritos:

```text
==============================================================================
🧪 CASOS DE PRUEBA DIDÁCTICOS PRECONFIGURADOS
==============================================================================
1. Caso 1: Matriz Estrictamente Diagonal Dominante (Burden & Faires 4x4)
2. Caso 2: Solo Gauss-Seidel Converge (ρ(T_J) > 1 y ρ(T_GS) < 1)
3. Caso 3: Solo Jacobi Converge (¡Gauss-Seidel NO siempre es mejor!)
4. Caso 4: Divergencia de Ambos Métodos (No Diagonal Dominante 2x2)
5. Caso 5: Reordenamiento Exitoso de Ecuaciones (Restaura Dominancia)
6. Caso 6: Cero en la Diagonal Principal (a₁₁ = 0 y división por cero)
==============================================================================
```

---

### Caso 1: Matriz Estrictamente Diagonal Dominante ($4 \times 4$)
* **Origen:** Burden & Faires, *Análisis Numérico*, Ejemplo clásico de Jacobi y Gauss-Seidel.
* **Sistema de Ecuaciones:**
  $$\begin{bmatrix} 10 & -1 & 2 & 0 \\ -1 & 11 & -1 & 3 \\ 2 & -1 & 10 & -1 \\ 0 & 3 & -1 & 8 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \\ x_3 \\ x_4 \end{bmatrix} = \begin{bmatrix} 6 \\ 25 \\ -11 \\ 15 \end{bmatrix}$$
* **Solución Exacta:** $\mathbf{x}^* = (1, 2, -1, 1)^T$.
* **Diagnóstico Previo:**
  * Fila 1: $|10| > 1 + 2 + 0 = 3$ (Cumple)
  * Fila 2: $|11| > 1 + 1 + 3 = 5$ (Cumple)
  * Fila 3: $|10| > 2 + 1 + 1 = 4$ (Cumple)
  * Fila 4: $|8| > 0 + 3 + 1 = 4$ (Cumple)
  * **Conclusión:** Estrictamente diagonal dominante. Se garantiza convergencia de ambos.
* **Resultados Numéricos ($\varepsilon = 10^{-4}$):**
  * **Jacobi:** Converge en **13 iteraciones** ($\rho(T_J) \approx 0.4449$).
  * **Gauss-Seidel:** Converge en **6 iteraciones** ($\rho(T_{GS}) \approx 0.1251$).
  * **Conclusión Didáctica:** Gauss-Seidel converge en menos de la mitad de iteraciones que Jacobi gracias a la rápida reducción del radio espectral ($\rho(T_{GS}) \approx \rho(T_J)^2$).

---

### Caso 2: Solo Gauss-Seidel Converge ($3 \times 3$)
* **Sistema de Ecuaciones:**
  $$\begin{bmatrix} 2 & -1 & 1 \\ 2 & 2 & 2 \\ -1 & -1 & 2 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \\ x_3 \end{bmatrix} = \begin{bmatrix} -1 \\ 4 \\ -5 \end{bmatrix}$$
* **Solución Exacta:** $\mathbf{x}^* = (1, 2, -1)^T$.
* **Diagnóstico Previo:**
  * No es diagonal dominante (ej. Fila 2: $|2| \ngtr 2 + 2 = 4$).
  * Radio espectral de Jacobi: $\rho(T_J) = \dfrac{\sqrt{5}}{2} \approx 1.1180 > 1$.
  * Radio espectral de Gauss-Seidel: $\rho(T_{GS}) = 0.5000 < 1$.
* **Resultados Numéricos ($\varepsilon = 10^{-4}$):**
  * **Jacobi:** **DIVERGE** (las aproximaciones oscilan y se alejan de la solución).
  * **Gauss-Seidel:** **CONVERGE** en **19 iteraciones** a $(1.0000, 2.0000, -1.0000)^T$.
  * **Conclusión Didáctica:** Demuestra que la dominancia diagonal NO es condición necesaria; Gauss-Seidel converge porque $\rho(T_{GS}) < 1$.

---

### Caso 3: Solo Jacobi Converge ($3 \times 3$ — Contraejemplo Teórico)
* **Sistema de Ecuaciones:**
  $$\begin{bmatrix} 1 & 2 & -2 \\ 1 & 1 & 1 \\ 2 & 2 & 1 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \\ x_3 \end{bmatrix} = \begin{bmatrix} 7 \\ 2 \\ 5 \end{bmatrix}$$
* **Solución Exacta:** $\mathbf{x}^* = (1, 2, -1)^T$.
* **Diagnóstico Previo:**
  * Matriz de iteración de Jacobi: $T_J$ es una matriz nilpotente de grado 3 ($T_J^3 = \mathbf{0}$).
  * Radio espectral de Jacobi: $\rho(T_J) = 0 < 1$.
  * Radio espectral de Gauss-Seidel: $\rho(T_{GS}) = 2.0000 > 1$.
* **Resultados Numéricos:**
  * **Jacobi:** **CONVERGE** en **4 iteraciones** a la solución exacta.
  * **Gauss-Seidel:** **DIVERGE EXPLOSIVAMENTE** ($\|\mathbf{x}^{(k)}\|_\infty$ se duplica en cada iteración y supera $10^8$ en la iteración 25).
  * **Conclusión Didáctica:** Rompe el mito común de que Gauss-Seidel siempre es mejor que Jacobi. Como la matriz no cumple las condiciones de Stein-Rosenberg, Jacobi resulta rotundamente superior.

---

### Caso 4 y 5: Divergencia y Reordenamiento Exitoso de Filas ($2 \times 2$)
* **Sistema Original (Caso 4):**
  $$\begin{bmatrix} 1 & -5 \\ 7 & -1 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \end{bmatrix} = \begin{bmatrix} -4 \\ 6 \end{bmatrix}$$
  * Diagnóstico: Ninguna fila tiene elemento diagonal mayor que el restante. $\rho(T_J) = \sqrt{35} \approx 5.916 > 1$, $\rho(T_{GS}) = 35 > 1$.
  * Comportamiento: **AMBOS MÉTODOS DIVERGEN** en pocas iteraciones (la norma supera $10^8$ en las iteraciones 12 y 6).
* **Sistema Reordenado (Caso 5 — Intercambio $E_1 \leftrightarrow E_2$):**
  $$\begin{bmatrix} 7 & -1 \\ 1 & -5 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \end{bmatrix} = \begin{bmatrix} 6 \\ -4 \end{bmatrix}$$
  * Diagnóstico: Fila 1: $|7| > 1$. Fila 2: $|-5| > 1$. **¡Estrictamente diagonal dominante!**
  * Radios espectrales: $\rho(T_J) \approx 0.1690 < 1$, $\rho(T_{GS}) \approx 0.0286 < 1$.
  * Resultados: **AMBOS CONVERGEN** de inmediato a $\mathbf{x}^* = (1, 1)^T$ (Jacobi en 7 iteraciones, Gauss-Seidel en 5 iteraciones).
  * **Conclusión Didáctica:** Un sistema que no converge puede transformarse en convergente simplemente permutando el orden de las ecuaciones para concentrar la masa numérica en la diagonal principal.

---

### Caso 6: Cero en la Diagonal Principal ($a_{ii} = 0$)
* **Sistema de Ecuaciones:**
  $$\begin{bmatrix} 0 & 2 \\ 3 & 1 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \end{bmatrix} = \begin{bmatrix} 4 \\ 5 \end{bmatrix}$$
* **Diagnóstico:** El coeficiente $a_{11} = 0$. Al intentar despejar $x_1$, la fórmula exigiría dividir entre $0$, lo cual es una indeterminación matemática.
* **Acción del Programa:** Detecta automáticamente el cero diagonal, emite la alerta teórica y aplica `reorder_for_dominance`, permutando a $\begin{bmatrix} 3 & 1 \\ 0 & 2 \end{bmatrix} \mathbf{x} = \begin{bmatrix} 5 \\ 4 \end{bmatrix}$. Resuelve de inmediato obteniendo $x_1 = 1, x_2 = 2$.

---

## 5. Guía de Preguntas y Respuestas para la Defensa Individual

Cada integrante del equipo debe dominar las siguientes preguntas conceptuales ante el docente o evaluador:

### P1: ¿Cuál es la diferencia algorítmica fundamental entre Jacobi y Gauss-Seidel?
> **Respuesta:**
> Jacobi calcula todo el vector nuevo $\mathbf{x}^{(k+1)}$ usando exclusivamente el vector anterior $\mathbf{x}^{(k)}$ (desplazamiento simultáneo), lo que requiere reservar memoria para dos vectores independientes. Gauss-Seidel utiliza las componentes recién actualizadas $x_1^{(k+1)}, \dots, x_{i-1}^{(k+1)}$ en cuanto están disponibles para calcular las siguientes incógnitas en la misma iteración (desplazamiento sucesivo), permitiendo trabajar *in-place*.

### P2: ¿Por qué la dominancia diagonal es condición suficiente pero no necesaria?
> **Respuesta:**
> Es suficiente porque garantiza mediante el Teorema de Círculos de Gershgorin que todos los autovalores de la matriz de iteración $T$ caen estrictamente dentro del círculo unitario $|\lambda| < 1$, asegurando $\rho(T) < 1$. No es necesaria porque existen matrices no diagonal dominantes cuyos autovalores igualmente satisfacen $|\lambda_i| < 1$, como se probó empíricamente en el Caso 2.

### P3: ¿Por qué el radio espectral $\rho(T) < 1$ es la condición necesaria y suficiente de convergencia?
> **Respuesta:**
> Porque el error en la iteración $k$ está dado por $\mathbf{e}^{(k)} = T^k \mathbf{e}^{(0)}$. Por el teorema de la descomposición de Jordan o espectral, la matriz $T^k \to \mathbf{0}$ cuando $k \to \infty$ si y solo si el módulo del autovalor más grande en valor absoluto es estrictamente menor que 1 ($\rho(T) < 1$).

### P4: ¿Es Gauss-Seidel siempre más rápido o superior a Jacobi?
> **Respuesta:**
> No. Si la matriz cumple las hipótesis del Teorema de Stein-Rosenberg ($a_{ij} \le 0$ para $i \neq j$), Gauss-Seidel converge el doble de rápido. Pero si la matriz contiene signos mixtos, Gauss-Seidel puede diverger mientras Jacobi converge, como evidenció el Caso 3 donde Jacobi convergió en 4 iteraciones y Gauss-Seidel divergió exponencialmente.

### P5: ¿Por qué se utilizó `fractions.Fraction` en vez de `float`?
> **Respuesta:**
> Porque los flotantes estándar de IEEE 754 introducen errores de redondeo en cada división y producto, lo que contamina el cálculo en matrices mal condicionadas. Al utilizar `fractions.Fraction`, la aritmética es exacta y el único error presente es el de truncamiento del método numérico.

### P6: ¿Qué hace el programa si encuentra un cero en la diagonal?
> **Respuesta:**
> En lugar de provocar un error no controlado de división por cero, detecta la fila con $a_{ii} = 0$ y ejecuta la heurística de pivoteo `reorder_for_dominance`, buscando una permutación de ecuaciones que coloque coeficientes no nulos y dominantes en la diagonal principal.

---

## 6. Instrucciones para Ejecución y Entrega Oficial

### Ejecución Directa del Script Autónomo:
```bash
python3 "Programa 8_Grupo4.py"
```

### Ejecución de la Suite Modular Completa:
```bash
python3 Calculadora_Algebra_Lineal/main.py
```

### Ejecución de Pruebas Automatizadas con PyTest:
```bash
pytest tests/core/test_iterative_methods.py tests/core/test_programa8_standalone.py -v
```

---

## 7. Conclusiones

1. Se integraron con éxito los métodos de Jacobi y Gauss-Seidel tanto en un script autónomo de consola (`Programa 8_Grupo4.py`) como en la suite modular (`Calculadora_Algebra_Lineal/`) y en la aplicación gráfica PySide6.
2. Se demostró mediante evidencia computacional y teórica el papel del radio espectral $\rho(T)$ y la dominancia diagonal estricta en la convergencia de ambos métodos.
3. El equipo cuenta con todo el respaldo conceptual, el código validado al 100% mediante 27 pruebas automáticas y la guía de defensa para justificar las decisiones de implementación tomadas.
