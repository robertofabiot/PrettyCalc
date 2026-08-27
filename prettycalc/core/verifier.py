"""Verificador automático de soluciones por sustitución en sistemas de ecuaciones lineales.

Comprueba que: sum(A_ij * x_j) == b_i para cada ecuación i con aritmética exacta.
100% Python estándar (sin dependencias externas).
"""

from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Sequence, Optional, Any

from prettycalc.core.types import Matrix, parse_scalar, format_scalar


@dataclass(frozen=True)
class EquationVerification:
    """Resultado de la verificación de una ecuación individual del sistema.

    Attributes:
        equation_index: Índice 0-based de la ecuación.
        lhs_value: Valor calculado del lado izquierdo tras sustitución.
        rhs_value: Valor esperado del término independiente (lado derecho).
        is_valid: True si lhs_value == rhs_value exactamente.
        equation_str: Representación de la ecuación original (ej: '2*x1 + 3*x2 = 5').
        substitution_str: Expresión con los valores sustituidos (ej: '2*(1) + 3*(1) = 5').
    """
    equation_index: int
    lhs_value: Fraction
    rhs_value: Fraction
    is_valid: bool
    equation_str: str
    substitution_str: str


class SolutionVerifier:
    """Servicio de verificación de soluciones mediante sustitución exacta."""

    @staticmethod
    def verify(
        augmented_matrix: Matrix,
        solution_vector: Sequence[Any],
        split_col: Optional[int] = None,
        var_names: Optional[List[str]] = None,
    ) -> List[EquationVerification]:
        """Verifica el vector solución contra cada fila de la matriz aumentada original.

        Args:
            augmented_matrix: Matriz aumentada [A | b] original del sistema.
            solution_vector: Vector de valores asignados a cada variable (longitud = split_col).
            split_col: Índice de la columna b (por defecto matrix.cols - 1).
            var_names: Nombres opcionales de las variables (ej: ['x', 'y', 'z']).

        Returns:
            Lista de EquationVerification por cada fila/ecuación del sistema.
        """
        effective_split = split_col if split_col is not None else augmented_matrix.cols - 1
        num_equations = augmented_matrix.rows
        num_variables = effective_split

        if len(solution_vector) != num_variables:
            raise ValueError(
                f"La longitud del vector solución ({len(solution_vector)}) no coincide "
                f"con el número de variables ({num_variables})."
            )

        parsed_solution = [parse_scalar(val) for val in solution_vector]
        verifications: List[EquationVerification] = []

        for r in range(num_equations):
            lhs_total = Fraction(0, 1)
            eq_terms = []
            sub_terms = []

            for c in range(num_variables):
                coeff = augmented_matrix.get(r, c)
                x_val = parsed_solution[c]
                lhs_total += coeff * x_val

                v_name = var_names[c] if var_names and c < len(var_names) else f"x{c+1}"
                coeff_str = format_scalar(coeff, mode="fraction")
                x_str = format_scalar(x_val, mode="fraction")

                if coeff != Fraction(0, 1):
                    eq_terms.append(f"{coeff_str}*{v_name}")
                    sub_terms.append(f"{coeff_str}*({x_str})")

            rhs_expected = augmented_matrix.get(r, effective_split)
            rhs_str = format_scalar(rhs_expected, mode="fraction")

            eq_display = (" + ".join(eq_terms) if eq_terms else "0") + f" = {rhs_str}"
            sub_display = (" + ".join(sub_terms) if sub_terms else "0") + f" = {format_scalar(lhs_total, mode='fraction')} (Esperado: {rhs_str})"

            is_valid = (lhs_total == rhs_expected)

            verifications.append(
                EquationVerification(
                    equation_index=r,
                    lhs_value=lhs_total,
                    rhs_value=rhs_expected,
                    is_valid=is_valid,
                    equation_str=eq_display,
                    substitution_str=sub_display,
                )
            )

        return verifications
