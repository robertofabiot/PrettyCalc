"""Clasificación canónica de sistemas de ecuaciones lineales según el Teorema de Rouché-Frobenius.

Categorías:
1. Consistente Determinado (SCD) -> Solución única
2. Consistente Indeterminado (SCI) -> Infinitas soluciones (Variables libres y parametrización)
3. Inconsistente (SI) -> Sin solución ([0 ... 0 | c] con c != 0)

100% Python estándar (sin dependencias externas).
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import List, Optional, Tuple, Dict, Union, Any

from prettycalc.core.types import Matrix, format_scalar
from prettycalc.core.elimination import gauss_jordan_elimination


class SystemType(Enum):
    """Tipos canónicos de sistemas de ecuaciones lineales."""
    CONSISTENT_DETERMINED = "Consistente Determinado"
    CONSISTENT_INDETERMINED = "Consistente Indeterminado"
    INCONSISTENT = "Inconsistente"


@dataclass(frozen=True)
class ParametricExpression:
    """Expresión paramétrica para una variable básica: x_i = constant + sum(coeff_j * x_j)."""
    constant: Fraction
    free_var_coeffs: Dict[int, Fraction]  # var_index -> coefficient

    def to_string(self, var_names: Optional[List[str]] = None) -> str:
        """Genera representación en texto de la expresión (ej: '2 - 3*x3')."""
        terms = []
        if self.constant != Fraction(0, 1) or not self.free_var_coeffs:
            terms.append(format_scalar(self.constant, mode="fraction"))

        for var_idx, coeff in sorted(self.free_var_coeffs.items()):
            v_name = var_names[var_idx] if var_names and var_idx < len(var_names) else f"x{var_idx+1}"
            c_str = format_scalar(coeff, mode="fraction")
            if coeff == Fraction(1, 1):
                term = f"+ {v_name}" if terms else v_name
            elif coeff == Fraction(-1, 1):
                term = f"- {v_name}"
            elif coeff > 0:
                term = f"+ {c_str}*{v_name}" if terms else f"{c_str}*{v_name}"
            else:
                term = f"- {format_scalar(abs(coeff), mode='fraction')}*{v_name}"
            terms.append(term)

        return " ".join(terms) if terms else "0"


@dataclass(frozen=True)
class SystemAnalysis:
    """Resultado del análisis y clasificación formal de un sistema lineal Ax = b."""
    system_type: SystemType
    rank_a: int
    rank_augmented: int
    num_variables: int
    num_equations: int
    basic_variables: List[int]
    free_variables: List[int]
    unique_solution: Optional[List[Fraction]]
    parametric_solutions: Optional[Dict[int, ParametricExpression]]
    inconsistent_row: Optional[int]
    summary_message: str
    pivot_columns: Optional[List[int]] = None
    has_augmented_pivot: bool = False

    def __post_init__(self):
        if self.pivot_columns is None:
            object.__setattr__(self, "pivot_columns", list(self.basic_variables))

    @property
    def pivot_columns_1based(self) -> List[int]:
        """Retorna los índices de columnas con pivote en base 1 (1..n)."""
        return [c + 1 for c in (self.pivot_columns or [])]

    @property
    def basic_variables_names(self) -> List[str]:
        """Retorna los nombres de las variables básicas (ej: ['x1', 'x2'])."""
        return [f"x{c + 1}" for c in self.basic_variables]

    @property
    def free_variables_names(self) -> List[str]:
        """Retorna los nombres de las variables libres (ej: ['x3'])."""
        return [f"x{c + 1}" for c in self.free_variables]



def classify_system(matrix: Matrix, split_col: Optional[int] = None) -> SystemAnalysis:
    """Analiza y clasifica un sistema de ecuaciones lineales a partir de su matriz aumentada [A | b].

    Args:
        matrix: Matriz aumentada [A | b].
        split_col: Columna donde se divide A de b (por defecto matrix.cols - 1).

    Returns:
        SystemAnalysis con la clasificación completa, rangos, variables libres y solución.
    """
    effective_split = split_col if split_col is not None else matrix.cols - 1
    num_equations, total_cols = matrix.shape
    num_variables = effective_split

    if effective_split <= 0 or effective_split >= total_cols:
        raise ValueError(
            f"Columna divisoria {effective_split} no es válida para una matriz de {total_cols} columnas."
        )

    # Obtenemos la forma escalonada reducida (RREF)
    rref, _ = gauss_jordan_elimination(matrix, split_col=effective_split)

    # 1. Detección de inconsistencia y cálculo de rangos
    rank_a = 0
    rank_augmented = 0
    inconsistent_row = None

    pivot_cols_in_a: List[int] = []
    pivot_row_map: Dict[int, int] = {}  # col -> row

    for r in range(num_equations):
        # Buscar primer elemento no nulo en la parte de coeficientes A
        first_non_zero_a_col = None
        for c in range(num_variables):
            if rref.get(r, c) != Fraction(0, 1):
                first_non_zero_a_col = c
                break

        # Revisar término independiente b
        b_val = rref.get(r, effective_split)
        has_non_zero_b = (b_val != Fraction(0, 1))

        if first_non_zero_a_col is not None:
            rank_a += 1
            rank_augmented += 1
            if first_non_zero_a_col not in pivot_cols_in_a:
                pivot_cols_in_a.append(first_non_zero_a_col)
                pivot_row_map[first_non_zero_a_col] = r
        else:
            # La fila en A es completamente cero
            if has_non_zero_b:
                rank_augmented += 1
                if inconsistent_row is None:
                    inconsistent_row = r

    # Identificación de variables básicas y libres
    basic_vars = sorted(pivot_cols_in_a)
    free_vars = [c for c in range(num_variables) if c not in basic_vars]

    # 2. Clasificación según Teorema de Rouché-Frobenius
    if rank_a < rank_augmented or inconsistent_row is not None:
        # Sistema Inconsistente (SI)
        inc_r_disp = (inconsistent_row + 1) if inconsistent_row is not None else 1
        return SystemAnalysis(
            system_type=SystemType.INCONSISTENT,
            rank_a=rank_a,
            rank_augmented=rank_augmented,
            num_variables=num_variables,
            num_equations=num_equations,
            basic_variables=basic_vars,
            free_variables=free_vars,
            unique_solution=None,
            parametric_solutions=None,
            inconsistent_row=inconsistent_row,
            summary_message=(
                f"Sistema Inconsistente (Sin Solución). "
                f"Rango(A) = {rank_a} != Rango(A|b) = {rank_augmented}. "
                f"Fila {inc_r_disp} contradictoria (0 = c con c != 0)."
            ),
            pivot_columns=basic_vars,
            has_augmented_pivot=True,
        )

    if rank_a == num_variables:
        # Sistema Consistente Determinado (SCD)
        solution = [Fraction(0, 1)] * num_variables
        for var_idx in basic_vars:
            row_idx = pivot_row_map[var_idx]
            solution[var_idx] = rref.get(row_idx, effective_split)

        return SystemAnalysis(
            system_type=SystemType.CONSISTENT_DETERMINED,
            rank_a=rank_a,
            rank_augmented=rank_augmented,
            num_variables=num_variables,
            num_equations=num_equations,
            basic_variables=basic_vars,
            free_variables=[],
            unique_solution=solution,
            parametric_solutions=None,
            inconsistent_row=None,
            summary_message=(
                f"Sistema Consistente Determinado (Solución Única). "
                f"Rango(A) = Rango(A|b) = {rank_a} = número de incógnitas."
            ),
            pivot_columns=basic_vars,
            has_augmented_pivot=False,
        )

    # Sistema Consistente Indeterminado (SCI)
    parametric_solutions: Dict[int, ParametricExpression] = {}
    for basic_var in basic_vars:
        row_idx = pivot_row_map[basic_var]
        const_val = rref.get(row_idx, effective_split)
        free_coeffs: Dict[int, Fraction] = {}
        for free_var in free_vars:
            c_val = rref.get(row_idx, free_var)
            if c_val != Fraction(0, 1):
                # Despeje: pasa con signo contrario
                free_coeffs[free_var] = - c_val
        parametric_solutions[basic_var] = ParametricExpression(
            constant=const_val,
            free_var_coeffs=free_coeffs,
        )

    # Solución particular asignando 0 a todas las variables libres
    particular_sol = [Fraction(0, 1)] * num_variables
    for basic_var, expr in parametric_solutions.items():
        particular_sol[basic_var] = expr.constant

    free_vars_str = ", ".join(f"x{v+1}" for v in free_vars)
    return SystemAnalysis(
        system_type=SystemType.CONSISTENT_INDETERMINED,
        rank_a=rank_a,
        rank_augmented=rank_augmented,
        num_variables=num_variables,
        num_equations=num_equations,
        basic_variables=basic_vars,
        free_variables=free_vars,
        unique_solution=particular_sol,
        parametric_solutions=parametric_solutions,
        inconsistent_row=None,
        summary_message=(
            f"Sistema Consistente Indeterminado (Infinitas Soluciones). "
            f"Rango(A) = Rango(A|b) = {rank_a} < {num_variables} incógnitas. "
            f"Variables libres: {free_vars_str}."
        ),
        pivot_columns=basic_vars,
        has_augmented_pivot=False,
    )
