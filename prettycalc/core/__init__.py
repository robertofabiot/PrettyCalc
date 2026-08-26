"""Motor matemático puro de PrettyCalc (Cero dependencias externas)."""

from prettycalc.core.types import Matrix, parse_scalar, format_scalar, Scalar
from prettycalc.core.operations import (
    swap_rows,
    scale_row,
    add_row_multiple,
    get_swap_metadata,
    get_scale_metadata,
    get_add_multiple_metadata,
)
from prettycalc.core.tracer import CalculationStep, StepTracer

__all__ = [
    "Matrix",
    "parse_scalar",
    "format_scalar",
    "Scalar",
    "swap_rows",
    "scale_row",
    "add_row_multiple",
    "get_swap_metadata",
    "get_scale_metadata",
    "get_add_multiple_metadata",
    "CalculationStep",
    "StepTracer",
]
