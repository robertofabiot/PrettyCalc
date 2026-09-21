# Estándares de Código y Desarrollo - PrettyCalc

## 1. Principios Generales de Desarrollo
1. **Regla de Cero Dependencias Matemáticas Externas:** Queda estrictamente prohibido el uso de librerías como `numpy`, `scipy` o `sympy` para los cálculos. Toda la lógica matricial y de vectores debe residir en el módulo `core` utilizando Python estándar.
2. **Inmutabilidad y Pureza Funcional:** Las operaciones matemáticas deben retornar nuevas instancias de matrices en lugar de mutar las de entrada inesperadamente, a menos que sea un método elemental interno explícito.
3. **Tipado Estricto (Type Hinting):** Todo el código debe utilizar anotaciones de tipo (`typing.List`, `typing.Optional`, `typing.Union`, `typing.Tuple`, etc.).

## 2. Convenciones de Nombrado y Estilo
* **Clases:** `PascalCase` (ej. `Matrix`, `Vector`, `StepTracer`, `CalculationStep`).
* **Funciones y Métodos:** `snake_case` (ej. `gaussian_elimination()`, `determinant()`, `swap_rows()`).
* **Variables matemáticas:** 
  * Matrices: Mayúsculas estándar ($A, B, M$).
  * Vectores: Minúsculas con nombres claros o prefijos (`v_vector`, `b_vector`).
  * Escalares / Índices: Letras minúsculas (`i`, `j`, `k`, `scalar`).
* **Constantes:** `UPPER_SNAKE_CASE` (ej. `DEFAULT_TOLERANCE`, `MAX_MATRIX_SIZE`).

## 3. Estructura y Organización de Módulos

```text
prettycalc/
├── core/                  # Motor matemático 100% Python puro (sin dependencias GUI)
│   ├── types.py           # Scalar, Fraction, Matrix, Vector
│   ├── operations.py      # Operaciones básicas (+, -, *, transpuesta)
│   ├── algorithms.py      # Gauss, Gauss-Jordan, Determinante, Inversa
│   └── tracer.py          # Registro de pasos intermedios
├── app/                   # Capa de aplicación y controladores
│   ├── state.py           # Gestión del estado de la sesión
│   └── formatters.py      # Formateadores de texto/LaTeX de matrices
├── ui/                    # Interfaz gráfica de escritorio
│   ├── components/        # Grillas de matrices, visores de pasos
│   └── windows/           # Ventana principal y diálogos
└── tests/                 # Pruebas con pytest
```

## 4. Manejo de Errores y Validaciones
* Definir excepciones de dominio específicas:
  * `DimensionMismatchError` (dimensiones incompatibles para suma o multiplicación).
  * `SingularMatrixError` (matriz no invertible o determinante cero).
  * `InvalidMatrixFormatError` (filas con diferente número de columnas, datos no numéricos).
* Ningún error matemático debe provocar un cierre inesperado de la aplicación (crash de la GUI); todos deben capturarse y presentarse de manera clara al usuario.

## 5. Control de Versiones (Git)
* Formato de commits: **Conventional Commits** (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
