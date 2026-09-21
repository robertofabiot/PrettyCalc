"""Tipos de datos fundamentales y manejo de aritmética exacta para PrettyCalc.

Restricción: 100% Python estándar (sin NumPy/SciPy).
"""

from __future__ import annotations
from fractions import Fraction
from typing import Sequence, Any, Tuple, List, Union, Optional


Scalar = Union[Fraction, int, float]


class DimensionMismatchError(ValueError):
    """Dimensiones incompatibles para una operación algebraica.

    El mensaje describe la regla violada (misma dimensión, mismas filas/columnas
    o conformabilidad del producto) para que la UI y el CLI expliquen el error
    sin lanzar una excepción genérica.
    """

    def __init__(
        self,
        message: str,
        left_shape: Optional[Tuple[int, ...]] = None,
        right_shape: Optional[Tuple[int, ...]] = None,
        operation: Optional[str] = None,
    ) -> None:
        self.left_shape = left_shape
        self.right_shape = right_shape
        self.operation = operation
        super().__init__(message)


def parse_scalar(value: Any) -> Fraction:
    """Convierte una entrada numérica o cadena a un objeto Fraction exacto.

    Soporta:
    - Enteros: 5, -3
    - Cadenas de enteros: "5", "-3", "+7"
    - Cadenas de fracciones: "3/4", "-1/2", "+2/5"
    - Cadenas decimales: "0.75", "-1.5", ".5"
    - Números de punto flotante: 0.75, -2.5
    - Instancias existentes de Fraction

    Lanza:
        ValueError: Si el valor no tiene formato numérico válido o hay división por cero.
        TypeError: Si el tipo de dato no es soportado.
    """
    if isinstance(value, Fraction):
        return value

    if isinstance(value, int):
        return Fraction(value, 1)

    if isinstance(value, float):
        # Convertir float a Fraction de forma limpia
        return Fraction(str(value)).limit_denominator(1_000_000)

    if isinstance(value, str):
        cleaned = value.strip().replace(" ", "")
        if not cleaned:
            raise ValueError("No se puede convertir una cadena vacía a escalar numérico.")

        # Manejo de fracciones tipo "a/b"
        if "/" in cleaned:
            parts = cleaned.split("/")
            if len(parts) != 2:
                raise ValueError(f"Formato de fracción inválido: '{value}' (se esperaba 'a/b').")
            num_str, den_str = parts[0], parts[1]
            try:
                num = int(num_str)
                den = int(den_str)
            except ValueError as e:
                raise ValueError(f"El numerador y denominador deben ser enteros en '{value}'.") from e

            if den == 0:
                raise ValueError(f"División por cero en la fracción: '{value}'.")
            return Fraction(num, den)

        # Manejo de decimales o enteros en cadena
        try:
            return Fraction(cleaned)
        except Exception as e:
            raise ValueError(f"No se pudo interpretar '{value}' como número o fracción.") from e

    raise TypeError(f"Tipo de dato no soportado para escalar: {type(value).__name__}")


def format_scalar(val: Fraction, mode: str = "fraction") -> str:
    """Formatea un escalar exacto según el modo solicitado.

    Modos disponibles:
    - 'fraction': Formato texto fraccionario ('3/4', '-1/2', '5', '0').
    - 'decimal': Formato decimal ('0.75', '5.0', '-0.5').
    - 'latex': Formato LaTeX ('\\frac{3}{4}', '-\\frac{1}{2}', '5', '0').
    """
    if val.denominator == 1:
        return str(val.numerator)

    if mode == "decimal":
        float_val = float(val)
        # Formatear con precisión limpia (remover ceros redundantes)
        return f"{float_val:.4f}".rstrip("0").rstrip(".")

    if mode == "latex":
        if val.numerator < 0:
            return f"-\\frac{{{abs(val.numerator)}}}{{{val.denominator}}}"
        return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

    # Default 'fraction'
    return f"{val.numerator}/{val.denominator}"


class Matrix:
    """Representación bidimensional de una matriz sobre el cuerpo de los racionales (Fraction).

    Garantiza cálculos exactos sin pérdida de precisión por redondeo flotante.
    """

    def __init__(self, data: Sequence[Sequence[Any]]):
        """Inicializa la matriz a partir de una lista anidada de datos escalares.

        Args:
            data: Lista 2D de filas conteniendo enteros, flotantes, cadenas o Fractions.

        Raises:
            ValueError: Si la matriz está vacía o las filas tienen longitudes desiguales.
        """
        if not data or len(data) == 0:
            raise ValueError("No se puede crear una matriz vacía (0 filas).")

        num_rows = len(data)
        if not data[0] or len(data[0]) == 0:
            raise ValueError("No se puede crear una matriz con columnas vacías.")

        num_cols = len(data[0])
        parsed_data: List[List[Fraction]] = []

        for r_idx, row in enumerate(data):
            if len(row) != num_cols:
                raise ValueError(
                    f"Matriz irregular: la fila {r_idx} tiene {len(row)} columnas "
                    f"pero la primera fila tiene {num_cols}."
                )
            parsed_row = [parse_scalar(val) for val in row]
            parsed_data.append(parsed_row)

        self._data: List[List[Fraction]] = parsed_data
        self._rows: int = num_rows
        self._cols: int = num_cols

    @classmethod
    def zeros(cls, rows: int, cols: int) -> Matrix:
        """Crea una matriz nula de dimensiones rows x cols."""
        if rows <= 0 or cols <= 0:
            raise ValueError(f"Dimensiones inválidas para matriz nula: {rows}x{cols}")
        data = [[Fraction(0, 1) for _ in range(cols)] for _ in range(rows)]
        return cls(data)

    @classmethod
    def identity(cls, n: int) -> Matrix:
        """Crea una matriz identidad de orden n x n."""
        if n <= 0:
            raise ValueError(f"Orden inválido para matriz identidad: {n}")
        data = [
            [Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n)]
            for i in range(n)
        ]
        return cls(data)

    @classmethod
    def from_flat_list(cls, values: Sequence[Any], rows: int, cols: int) -> Matrix:
        """Construye una matriz a partir de una lista plana y sus dimensiones."""
        if len(values) != rows * cols:
            raise ValueError(
                f"Cantidad de elementos ({len(values)}) no coincide con {rows}x{cols}={rows*cols}."
            )
        nested = [
            values[i * cols : (i + 1) * cols]
            for i in range(rows)
        ]
        return cls(nested)

    @property
    def rows(self) -> int:
        """Número de filas de la matriz."""
        return self._rows

    @property
    def cols(self) -> int:
        """Número de columnas de la matriz."""
        return self._cols

    @property
    def shape(self) -> Tuple[int, int]:
        """Tupla (filas, columnas)."""
        return (self._rows, self._cols)

    def dimensions(self) -> Tuple[int, int]:
        """Retorna las dimensiones (filas, columnas)."""
        return (self._rows, self._cols)

    def get(self, r: int, c: int) -> Fraction:
        """Obtiene el elemento exacto en la posición (r, c) (índices 0-based)."""
        self._validate_indices(r, c)
        return self._data[r][c]

    def set(self, r: int, c: int, value: Any) -> None:
        """Establece el elemento en la posición (r, c) convirtiéndolo a Fraction."""
        self._validate_indices(r, c)
        self._data[r][c] = parse_scalar(value)

    def get_row(self, r: int) -> List[Fraction]:
        """Retorna una copia de la fila r."""
        if r < 0 or r >= self._rows:
            raise IndexError(f"Índice de fila fuera de rango: {r} (matriz de {self._rows} filas).")
        return list(self._data[r])

    def set_row(self, r: int, row_values: Sequence[Any]) -> None:
        """Sobrescribe la fila r con los valores proporcionados."""
        if r < 0 or r >= self._rows:
            raise IndexError(f"Índice de fila fuera de rango: {r}")
        if len(row_values) != self._cols:
            raise ValueError(f"Longitud de fila ({len(row_values)}) no coincide con columnas ({self._cols}).")
        self._data[r] = [parse_scalar(v) for v in row_values]

    def get_col(self, c: int) -> List[Fraction]:
        """Retorna una lista con los elementos de la columna c."""
        if c < 0 or c >= self._cols:
            raise IndexError(f"Índice de columna fuera de rango: {c} (matriz de {self._cols} columnas).")
        return [self._data[r][c] for r in range(self._rows)]

    def copy(self) -> Matrix:
        """Retorna una copia profunda e independiente de la matriz."""
        copied_data = [[val for val in row] for row in self._data]
        return Matrix(copied_data)

    def augment(self, other: Union[Matrix, Sequence[Any]]) -> Matrix:
        """Crea una nueva matriz aumentada concatenando otra matriz o vector columna a la derecha.

        Args:
            other: Otra matriz con el mismo número de filas, o lista/vector de longitud rows.
        """
        if isinstance(other, Matrix):
            if other.rows != self._rows:
                raise ValueError(
                    f"No se pueden aumentar matrices con diferente número de filas: "
                    f"{self._rows} vs {other.rows}."
                )
            new_data = [
                self._data[r] + other._data[r]
                for r in range(self._rows)
            ]
            return Matrix(new_data)

        # Si es una secuencia (vector columna)
        if len(other) != self._rows:
            raise ValueError(
                f"La longitud del vector a aumentar ({len(other)}) no coincide con las filas ({self._rows})."
            )
        new_data = [
            self._data[r] + [parse_scalar(other[r])]
            for r in range(self._rows)
        ]
        return Matrix(new_data)

    def split_augmented(self, split_col: int) -> Tuple[Matrix, Matrix]:
        """Divide la matriz en dos submatrices en la columna split_col (ej. [A | b])."""
        if split_col <= 0 or split_col >= self._cols:
            raise ValueError(f"Columna de partición inválida: {split_col} para {self._cols} columnas.")

        left_data = [row[:split_col] for row in self._data]
        right_data = [row[split_col:] for row in self._data]
        return (Matrix(left_data), Matrix(right_data))

    def to_list(self) -> List[List[Fraction]]:
        """Retorna los datos como lista anidada de Fractions."""
        return [[val for val in row] for row in self._data]

    def to_float_list(self) -> List[List[float]]:
        """Retorna los datos como lista anidada de flotantes."""
        return [[float(val) for val in row] for row in self._data]

    def to_str_list(self, mode: str = "fraction") -> List[List[str]]:
        """Retorna los datos como cadenas de texto formateadas."""
        return [[format_scalar(val, mode=mode) for val in row] for row in self._data]

    def to_latex(self, split_col: Optional[int] = None) -> str:
        """Genera el código LaTeX formal para la matriz.

        Si split_col está definido, renderiza una matriz aumentada [A | b] con línea vertical.
        """
        if split_col is not None and 1 <= split_col < self._cols:
            left_cols = "c" * split_col
            right_cols = "c" * (self._cols - split_col)
            col_spec = f"{left_cols}|{right_cols}"
            lines = [f"\\left[\\begin{{array}}{{{col_spec}}}"]
        else:
            lines = ["\\begin{bmatrix}"]

        for row in self._data:
            row_str = " & ".join(format_scalar(val, mode="latex") for val in row)
            lines.append(f"  {row_str} \\\\")

        if split_col is not None and 1 <= split_col < self._cols:
            lines.append("\\end{array}\\right]")
        else:
            lines.append("\\end{bmatrix}")

        return "\n".join(lines)

    def _validate_indices(self, r: int, c: int) -> None:
        if r < 0 or r >= self._rows:
            raise IndexError(f"Índice de fila fuera de rango: {r} (0..{self._rows-1}).")
        if c < 0 or c >= self._cols:
            raise IndexError(f"Índice de columna fuera de rango: {c} (0..{self._cols-1}).")

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, tuple):
            r, c = key
            return self.get(r, c)
        if isinstance(key, int):
            if key < 0 or key >= self._rows:
                raise IndexError(f"Índice de fila fuera de rango: {key} (0..{self._rows-1}).")
            return list(self._data[key])
        raise TypeError(f"Índice inválido: {key}")

    def __setitem__(self, key: Tuple[int, int], value: Any) -> None:
        if isinstance(key, tuple) and len(key) == 2:
            r, c = key
            self.set(r, c, value)
        else:
            raise TypeError(f"Se requiere una tupla (r, c) para asignar celdas: {key}")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return False
        if self.shape != other.shape:
            return False
        for r in range(self._rows):
            for c in range(self._cols):
                if self._data[r][c] != other._data[r][c]:
                    return False
        return True

    def __repr__(self) -> str:
        rows_str = ", ".join(
            "[" + ", ".join(f"Fraction({v.numerator}, {v.denominator})" for v in row) + "]"
            for row in self._data
        )
        return f"Matrix([{rows_str}])"

    def __str__(self) -> str:
        """Formato visual monospace alineado por columnas."""
        str_cells = self.to_str_list(mode="fraction")
        col_widths = [
            max(len(str_cells[r][c]) for r in range(self._rows))
            for c in range(self._cols)
        ]
        lines = []
        for r in range(self._rows):
            formatted_row = "  ".join(
                str_cells[r][c].rjust(col_widths[c]) for c in range(self._cols)
            )
            lines.append(f"│  {formatted_row}  │")
        return "\n".join(lines)


class Vector:
    """Vector columna en ℝⁿ sobre el cuerpo de los racionales (`Fraction`).

    Las componentes se almacenan en una lista unidimensional de fracciones
    exactas. Un vector de dimensión n equivale a una matriz columna n×1,
    pero el acceso es unidimensional: `v[i]` en lugar de `v[i, 0]`.
    """

    def __init__(self, components: Sequence[Any]):
        """Inicializa el vector a partir de una secuencia de escalares.

        Args:
            components: Enteros, fracciones (`"3/4"`), decimales o `Fraction`.

        Raises:
            ValueError: Si la secuencia está vacía.
        """
        if components is None or len(components) == 0:
            raise ValueError("No se puede crear un vector vacío (dimensión 0).")

        self._components: List[Fraction] = [parse_scalar(val) for val in components]
        self._dimension: int = len(self._components)

    @classmethod
    def zeros(cls, n: int) -> Vector:
        """Crea el vector nulo de ℝⁿ."""
        if n <= 0:
            raise ValueError(f"Dimensión inválida para vector nulo: {n}")
        return cls([Fraction(0, 1) for _ in range(n)])

    @classmethod
    def from_column_matrix(cls, matrix: Matrix) -> Vector:
        """Construye un vector a partir de una matriz columna n×1."""
        if matrix.cols != 1:
            raise ValueError(
                f"Se esperaba una matriz columna n×1, se recibió {matrix.rows}×{matrix.cols}."
            )
        return cls(matrix.get_col(0))

    @property
    def dimension(self) -> int:
        """Número de componentes (n de ℝⁿ)."""
        return self._dimension

    @property
    def components(self) -> List[Fraction]:
        """Copia de las componentes exactas."""
        return list(self._components)

    def to_list(self) -> List[Fraction]:
        """Retorna las componentes como lista de `Fraction`."""
        return list(self._components)

    def to_column_matrix(self) -> Matrix:
        """Representación matricial equivalente: columna n×1."""
        return Matrix([[comp] for comp in self._components])

    def copy(self) -> Vector:
        """Copia profunda e independiente."""
        return Vector(list(self._components))

    def to_latex(self) -> str:
        """Código LaTeX del vector como matriz columna."""
        lines = ["\\begin{bmatrix}"]
        for val in self._components:
            lines.append(f"  {format_scalar(val, mode='latex')} \\\\")
        lines.append("\\end{bmatrix}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return self._dimension

    def __getitem__(self, index: int) -> Fraction:
        if index < 0 or index >= self._dimension:
            raise IndexError(
                f"Índice de componente fuera de rango: {index} (0..{self._dimension - 1})."
            )
        return self._components[index]

    def __setitem__(self, index: int, value: Any) -> None:
        if index < 0 or index >= self._dimension:
            raise IndexError(
                f"Índice de componente fuera de rango: {index} (0..{self._dimension - 1})."
            )
        self._components[index] = parse_scalar(value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Vector):
            return False
        if self._dimension != other._dimension:
            return False
        return self._components == other._components

    def __iter__(self):
        return iter(self._components)

    def __repr__(self) -> str:
        inner = ", ".join(
            f"Fraction({v.numerator}, {v.denominator})" for v in self._components
        )
        return f"Vector([{inner}])"

    def __str__(self) -> str:
        width = max(len(format_scalar(v, mode="fraction")) for v in self._components)
        lines = [
            f"│  {format_scalar(v, mode='fraction').rjust(width)}  │"
            for v in self._components
        ]
        return "\n".join(lines)
