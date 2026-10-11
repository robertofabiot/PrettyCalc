# PrettyCalc

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#instalación--getting-started)
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](#instalación--getting-started)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/robertofabiot/PrettyCalc)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Calculadora de escritorio para sistemas de ecuaciones lineales. Resuelve por eliminación de Gauss y Gauss-Jordan, muestra cada transformación de fila y comprueba la solución por sustitución.

## Descripción

PrettyCalc está pensada para estudiantes de álgebra lineal que necesitan ver *cómo* se obtiene el resultado, no solo el vector final. Abre una matriz aumentada $[A \mid b]$ lista para escribir, crece con celdas fantasma `+` y recorre el procedimiento paso a paso con el pivote y las filas involucradas resaltados. El motor matemático (`prettycalc.core`) usa `fractions.Fraction` y no depende de NumPy, SciPy ni SymPy: la aritmética es exacta y el mismo código se puede probar o reutilizar fuera de la interfaz.

## Tabla de contenidos

- [Descripción](#descripción)
- [Instalación / Getting Started](#instalación--getting-started)
- [Uso](#uso)
- [Licencia](#licencia)

## Instalación / Getting Started

**Requisitos previos**

- Python 3.10 o superior
- pip
- Entorno gráfico de escritorio (la interfaz usa PySide6 / Qt 6)

**Clonar e instalar**

```bash
git clone https://github.com/robertofabiot/PrettyCalc.git
cd PrettyCalc

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e .
pip install -r requirements.txt
```

`pip install -e .` instala la aplicación y PySide6. `requirements.txt` añade `pytest`, `pytest-qt` y `pytest-cov` para las pruebas.

**Levantar el proyecto**

```bash
python run.py
```

Tras la instalación editable también puedes usar:

```bash
prettycalc
```

**Comprobar que las pruebas pasan**

```bash
pytest
```

En un entorno sin pantalla (CI o SSH):

```bash
QT_QPA_PLATFORM=offscreen pytest
```

## Uso

### Interfaz gráfica

1. La ventana abre en $2 \times 2$ con la columna $b$ visible: transcribe el sistema como matriz aumentada.
2. Pulsa `+` para añadir filas o variables. Clic derecho en una celda para eliminar fila o columna (el mínimo es $1 \times 1$).
3. Se admiten enteros, fracciones (`3/4`) y decimales. Una celda inválida se marca en el momento.
4. **Resolver sistema** ejecuta Gauss-Jordan, llena el carrusel de pasos y el panel de Resultados.
5. En **Procedimiento**, avanza con Anterior / Siguiente. **Fracciones** es un interruptor entre vista racional y decimal.
6. **Resultados** clasifica el sistema (solución única, infinitas soluciones o inconsistente) y, si hay solución única, muestra la comprobación por sustitución. Si el sistema es indeterminado, el panel escribe la forma vectorial paramétrica $x = p + t_1 v_1 + \dots$ con el vector particular y una base del núcleo.
7. En **Álgebra Matricial**, el modo **A⁻¹ (Inversa)** reduce $[A \mid I_n]$ por Gauss-Jordan, muestra $A^{-1}$ y comprueba $A \cdot A^{-1} = I_n$. Si $A$ no es cuadrada, el cálculo queda deshabilitado. Si $A$ es singular, el panel explica que no existe inversa.
8. En **Determinantes**, el orden n va de 1 a 8. Se puede calcular por triangulación, por Sarrus (solo 3×3), por cofactores de Laplace o pedir la matriz de cofactores, la adjunta y la inversa \(A^{-1} = \frac{1}{\det A}\operatorname{adj}(A)\).
9. En **Sistemas Lineales**, el selector de método incluye la **Regla de Cramer** para sistemas n×n con determinante distinto de cero. El panel muestra det(A), cada matriz columna reemplazada y \(x_i = \det(A_i(b)) / \det(A)\).
10. En **Factorización LU**, **Descomponer A = LU** muestra \(L\) y \(U\) y comprueba \(L \cdot U = A\). Con \(A\) cuadrada, **Resolver** hace la sustitución hacia adelante \(Ly = b\) y hacia atrás \(Ux = y\). Si cambia \(b\), se reutilizan los mismos factores. Un pivote nulo que exigiría intercambiar filas se explica como caso PLU, fuera de esta sesión.
11. En **Sistemas Lineales**, **V · Aplicaciones** abre el asistente de la sesión 8. No hace falta armar la matriz aumentada a mano:
    - **Química** escribe reactivos y productos (`C3H8 + O2` y `CO2 + H2O`) y devuelve los enteros mínimos, con esos coeficientes resaltados.
    - **Leontief** lee la matriz de consumo \(C\) y resuelve \((I - C)p = 0\). El ejemplo de carbón, electricidad y acero normaliza el precio del acero en 1.
    - **Dieta** carga la tabla Cambridge y muestra las unidades exactas y los gramos.
    - **Tráfico** carga la red de Baltimore y las cotas \(x_i \ge 0\).

Hay casos de prueba en la columna izquierda: solución única, infinitas soluciones, sin solución, Cramer y el asistente de aplicaciones.

### Motor matemático (Python)

El núcleo no necesita Qt. Ejemplo con el caso de solución única $x=2$, $y=1$, $z=1$:

```python
from prettycalc.core import (
    Matrix,
    gauss_jordan_elimination,
    classify_system,
    SolutionVerifier,
)

aumentada = Matrix([
    [1,  1,  1, 4],
    [2, -1,  1, 4],
    [1,  2, -1, 3],
])

rref, tracer = gauss_jordan_elimination(aumentada, split_col=3)
analisis = classify_system(aumentada, split_col=3)

print(analisis.system_type.value)
# Consistente Determinado
print(analisis.unique_solution)
# [Fraction(2, 1), Fraction(1, 1), Fraction(1, 1)]

for paso in tracer:
    print(paso.step_number, paso.heuristic_text)

comprobacion = SolutionVerifier.verify(
    aumentada, analisis.unique_solution, split_col=3
)
assert all(eq.is_valid for eq in comprobacion)
```

`gaussian_elimination` deja la forma escalonada (REF). `gauss_jordan_elimination` reduce hasta RREF. `split_col` es el índice donde empieza $b$ en $[A \mid b]$.

La inversa y la resolución por inversa viven en `prettycalc.core.matrix_inversion` (también reexportadas desde `matrix_ops` y `prettycalc.core`):

```python
from prettycalc.core import Matrix, Vector, classify_system, matrix_inverse, solve_via_inverse

A = Matrix([[2, 3], [-1, 1]])
inversa = matrix_inverse(A)
assert inversa.identity_check_passed
x, _ = solve_via_inverse(A, Vector([8, 1]))

analisis = classify_system(Matrix([
    [3, 5, -4, 0],
    [-3, -2, 4, 0],
    [6, 1, -8, 0],
]))
print(analisis.parametric_vector_solution.to_plain_equation())
# x = [0, 0, 0] + x3*[4/3, 0, 1]
```

El determinante, la adjunta y Cramer están en `prettycalc.core.determinants`, `adjugate` y `cramer`:

```python
from prettycalc.core import (
    Matrix,
    Vector,
    DeterminantMethod,
    matrix_determinant,
    calculate_adjugate_and_inverse,
    solve_cramer,
)

A = Matrix([[1, 3, -3], [2, 0, 1], [-1, 4, -2]])
assert matrix_determinant(A, DeterminantMethod.SARRUS_3X3).value == -19
adjunta = calculate_adjugate_and_inverse(A)
assert adjunta.det_A == -19

solucion = solve_cramer(Matrix([[3, -2], [2, 5]]), Vector([7, 11]))
assert solucion.solution == [3, 1]
```

La factorización LU y las dos sustituciones están en `prettycalc.core.lu_decomposition`:

```python
from prettycalc.core import Matrix, Vector, lu_decompose, solve_many_via_lu

A = Matrix([[3, -7, -2], [-3, 5, 1], [6, -4, 0]])
factores = lu_decompose(A)
assert factores.is_valid

primero, segundo = solve_many_via_lu(A, [Vector([-7, 5, 2]), Vector([0, 0, 0])])
assert primero.factorization is segundo.factorization
assert primero.x_solution == Vector([3, 4, -6])
```

Las aplicaciones de la sesión 8 están en `prettycalc.core.applied_models`:

```python
from prettycalc.core import (
    balance_chemical_equation,
    solve_leontief_exchange,
    solve_nutrition_mix,
    analyze_network_flow,
    coal_electric_steel_consumption,
    cambridge_diet,
    baltimore_traffic_network,
)

propano = balance_chemical_equation("C3H8 + O2 → CO2 + H2O")
assert propano.stoichiometric_coefficients == [1, 5, 3, 4]

precios = solve_leontief_exchange(coal_electric_steel_consumption())
assert precios.degrees_of_freedom == 1

composicion, requerimiento = cambridge_diet()
dieta = solve_nutrition_mix(composicion, requerimiento)
assert dieta.is_feasible

red = analyze_network_flow(baltimore_traffic_network())
assert red.parameter_range == (0, 500)
```

## Licencia

PrettyCalc se distribuye bajo la [licencia MIT](LICENSE). Puedes usar, copiar, modificar y redistribuir el código, con o sin fines comerciales, siempre que conserves el aviso de copyright y la licencia.
