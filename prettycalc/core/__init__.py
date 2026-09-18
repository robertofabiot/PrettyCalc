"""Motor matemático puro de PrettyCalc (Cero dependencias externas)."""

from prettycalc.core.types import (
    Matrix,
    Vector,
    DimensionMismatchError,
    parse_scalar,
    format_scalar,
    Scalar,
)
from prettycalc.core.vector_ops import (
    vector_add,
    vector_sub,
    vector_scale,
    vector_dot,
)
from prettycalc.core.matrix_ops import (
    matrix_add,
    matrix_sub,
    matrix_scale,
    matrix_multiply,
    matrix_multiply_with_details,
    MultiplicationStepDetail,
)
from prettycalc.core.linear_combination import (
    LinearCombinationResult,
    evaluate_linear_combination,
    format_combination_equation,
)
from prettycalc.core.operations import (
    swap_rows,
    scale_row,
    add_row_multiple,
    get_swap_metadata,
    get_scale_metadata,
    get_add_multiple_metadata,
)
from prettycalc.core.tracer import CalculationStep, StepTracer
from prettycalc.core.elimination import (
    gaussian_elimination,
    gauss_jordan_elimination,
)
from prettycalc.core.classifier import (
    SystemType,
    SystemAnalysis,
    ParametricExpression,
    classify_system,
)
from prettycalc.core.verifier import (
    EquationVerification,
    SolutionVerifier,
)

__all__ = [
    "Matrix",
    "Vector",
    "DimensionMismatchError",
    "parse_scalar",
    "format_scalar",
    "Scalar",
    "vector_add",
    "vector_sub",
    "vector_scale",
    "vector_dot",
    "matrix_add",
    "matrix_sub",
    "matrix_scale",
    "matrix_multiply",
    "matrix_multiply_with_details",
    "MultiplicationStepDetail",
    "LinearCombinationResult",
    "evaluate_linear_combination",
    "format_combination_equation",
    "swap_rows",
    "scale_row",
    "add_row_multiple",
    "get_swap_metadata",
    "get_scale_metadata",
    "get_add_multiple_metadata",
    "CalculationStep",
    "StepTracer",
    "gaussian_elimination",
    "gauss_jordan_elimination",
    "SystemType",
    "SystemAnalysis",
    "ParametricExpression",
    "classify_system",
    "EquationVerification",
    "SolutionVerifier",
]
