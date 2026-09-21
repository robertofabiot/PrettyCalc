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
6. **Resultados** clasifica el sistema (solución única, infinitas soluciones o inconsistente) y, si hay solución única, muestra la comprobación por sustitución.

Hay tres casos de prueba en la columna izquierda: solución única, infinitas soluciones y sin solución.

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

## Licencia

PrettyCalc se distribuye bajo la [licencia MIT](LICENSE). Puedes usar, copiar, modificar y redistribuir el código, con o sin fines comerciales, siempre que conserves el aviso de copyright y la licencia.
