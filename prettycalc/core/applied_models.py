"""Aplicaciones de sistemas lineales de la Sesión 8.

Cuatro modelos, todos en aritmética exacta:

* Balanceo químico: conservación de átomos y coeficientes enteros mínimos.
* Economía de Leontief cerrada: ``(I - C) p = 0``.
* Dieta: mezcla ``A x = b`` con cantidades no negativas.
* Redes de flujo: conservación en los nodos y cotas ``x_i >= 0``.

Sin NumPy, SciPy ni SymPy.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from prettycalc.core.classifier import (
    SystemAnalysis,
    SystemType,
    classify_system,
)
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.matrix_ops import matrix_sub
from prettycalc.core.matrix_vector_ops import matrix_vector_multiply
from prettycalc.core.tracer import StepTracer
from prettycalc.core.types import (
    DimensionMismatchError,
    Matrix,
    Vector,
    format_scalar,
    parse_scalar,
)


class AppliedModelError(ValueError):
    """El modelo aplicado no se puede formular con los datos recibidos."""


class ChemicalFormulaError(AppliedModelError):
    """La fórmula química no sigue la notación de la sesión (C3H8, Ca(OH)2, ...)."""


_ELEMENT = re.compile(r"([A-Z][a-z]?)(\d*)")
_ARROW = re.compile(r"\s*(?:→|->|=>|=)\s*")


def parse_chemical_formula(formula: str) -> Dict[str, int]:
    """Cuenta los átomos de una fórmula.

    Acepta elementos, subíndices y grupos entre paréntesis: ``C3H8``, ``CO2``,
    ``Ca(OH)2``. No acepta un coeficiente estequiométrico delante: ese número
    es la incógnita del balanceo.

    Raises:
        ChemicalFormulaError: Si queda texto sin leer o la fórmula está vacía.
    """
    cleaned = formula.strip().replace(" ", "")
    if not cleaned:
        raise ChemicalFormulaError("La fórmula está vacía.")
    if cleaned[0].isdigit():
        raise ChemicalFormulaError(
            f"'{formula}' empieza por un coeficiente. Escribe solo la fórmula; "
            "el balanceo calcula los enteros."
        )
    counts, index = _parse_formula_group(cleaned, 0, stop_at_paren=False)
    if index != len(cleaned):
        raise ChemicalFormulaError(
            f"No se pudo leer '{formula}' a partir de '{cleaned[index:]}'."
        )
    if not counts:
        raise ChemicalFormulaError(f"'{formula}' no contiene ningún elemento.")
    return counts


def _parse_formula_group(
    text: str,
    index: int,
    *,
    stop_at_paren: bool,
) -> Tuple[Dict[str, int], int]:
    """Lee un fragmento de fórmula y devuelve el índice donde se detuvo."""
    counts: Dict[str, int] = {}
    while index < len(text):
        char = text[index]
        if char == "(":
            inner, index = _parse_formula_group(text, index + 1, stop_at_paren=True)
            if index >= len(text) or text[index] != ")":
                raise ChemicalFormulaError(f"Falta cerrar un paréntesis en '{text}'.")
            index += 1
            multiplier, index = _read_count(text, index)
            for element, amount in inner.items():
                counts[element] = counts.get(element, 0) + amount * multiplier
            continue
        if char == ")":
            if stop_at_paren:
                return counts, index
            raise ChemicalFormulaError(f"Paréntesis sin abrir en '{text}'.")
        match = _ELEMENT.match(text, index)
        if match is None:
            raise ChemicalFormulaError(
                f"No se pudo leer '{text}' a partir de '{text[index:]}'."
            )
        element = match.group(1)
        amount = int(match.group(2)) if match.group(2) else 1
        counts[element] = counts.get(element, 0) + amount
        index = match.end()
    return counts, index


def _read_count(text: str, index: int) -> Tuple[int, int]:
    """Lee un subíndice entero. Si no hay dígitos, el grupo aparece una vez."""
    start = index
    while index < len(text) and text[index].isdigit():
        index += 1
    if start == index:
        return 1, index
    return int(text[start:index]), index


def parse_chemical_side(text: str) -> Tuple[List[str], List[Dict[str, int]]]:
    """Separa ``C3H8 + O2`` en etiquetas y conteos atómicos.

    Raises:
        ChemicalFormulaError: Si el lado está vacío o alguna fórmula es inválida.
    """
    pieces = [piece.strip() for piece in text.split("+")]
    pieces = [piece for piece in pieces if piece]
    if not pieces:
        raise ChemicalFormulaError("Falta al menos una sustancia en este lado de la reacción.")
    labels: List[str] = []
    formulas: List[Dict[str, int]] = []
    for piece in pieces:
        labels.append(piece.replace(" ", ""))
        formulas.append(parse_chemical_formula(piece))
    return labels, formulas


def parse_chemical_equation(equation: str) -> Tuple[List[str], List[Dict[str, int]], List[str], List[Dict[str, int]]]:
    """Parte ``C3H8 + O2 → CO2 + H2O`` en reactivos y productos."""
    sides = _ARROW.split(equation.strip(), maxsplit=1)
    if len(sides) != 2 or not sides[0].strip() or not sides[1].strip():
        raise ChemicalFormulaError(
            "Escribe la reacción con una flecha, por ejemplo C3H8 + O2 → CO2 + H2O."
        )
    reactant_labels, reactants = parse_chemical_side(sides[0])
    product_labels, products = parse_chemical_side(sides[1])
    return reactant_labels, reactants, product_labels, products


def integer_balanced_coefficients(components: Sequence[Fraction]) -> List[int]:
    """Convierte un vector racional del núcleo en enteros positivos mínimos.

    Multiplica por el mínimo común múltiplo de los denominadores y divide por
    el máximo común divisor. Si el vector apunta al semiespacio negativo, se
    invierte el signo: los coeficientes de una reacción se leen en sentido
    positivo.

    Raises:
        ValueError: Si el vector es nulo o cambia de signo y no admite una
            combinación no negativa en esa sola dirección.
    """
    values = [parse_scalar(component) for component in components]
    if not values:
        raise ValueError("No hay coeficientes que convertir a enteros.")
    if all(value == 0 for value in values):
        raise ValueError("El vector nulo no determina coeficientes de balanceo.")

    first_nonzero = next(value for value in values if value != 0)
    if first_nonzero < 0:
        values = [-value for value in values]
    if any(value < 0 for value in values):
        raise ValueError(
            "Esta dirección del núcleo toma signos opuestos. "
            "No hay coeficientes no negativos en ese rayo."
        )

    multiplier = 1
    for value in values:
        multiplier = math.lcm(multiplier, value.denominator)
    integers = [(value.numerator * multiplier) // value.denominator for value in values]
    divisor = 0
    for number in integers:
        divisor = math.gcd(divisor, abs(number))
    if divisor == 0:
        raise ValueError("El vector nulo no determina coeficientes de balanceo.")
    return [number // divisor for number in integers]


@dataclass(frozen=True)
class ChemicalBalanceResult:
    """Coeficientes enteros mínimos de una reacción y la matriz de conservación."""

    reactants: List[str]
    products: List[str]
    stoichiometric_coefficients: List[int]
    balanced_equation_text: str
    augmented_matrix: Matrix
    is_valid: bool
    elements: List[str]
    summary: str
    tracer: StepTracer


def _element_order(formulas: Sequence[Dict[str, int]]) -> List[str]:
    """Orden de aparición: así las filas coinciden con el orden del enunciado."""
    ordered: List[str] = []
    seen = set()
    for formula in formulas:
        for element in formula:
            if element not in seen:
                seen.add(element)
                ordered.append(element)
    return ordered


def atom_conservation_matrix(
    reactant_formulas: Sequence[Dict[str, int]],
    product_formulas: Sequence[Dict[str, int]],
) -> Tuple[Matrix, List[str]]:
    """Matriz aumentada homogénea: átomos a la izquierda menos átomos a la derecha.

    Cada fila es un elemento. Las columnas son reactivos, luego productos, y
    una columna de ceros porque la conservación es ``Ax = 0``.
    """
    formulas = list(reactant_formulas) + list(product_formulas)
    elements = _element_order(formulas)
    if not elements:
        raise ChemicalFormulaError("La reacción no menciona ningún elemento.")
    rows: List[List[int]] = []
    product_offset = len(reactant_formulas)
    for element in elements:
        row = [formula.get(element, 0) for formula in reactant_formulas]
        row.extend(-formula.get(element, 0) for formula in product_formulas)
        if len(row) != product_offset + len(product_formulas):
            raise ChemicalFormulaError("Las fórmulas no armaron una fila rectangular.")
        row.append(0)
        rows.append(row)
    return Matrix(rows), elements


def _format_balanced_equation(
    reactants: Sequence[str],
    products: Sequence[str],
    coefficients: Sequence[int],
) -> str:
    """``1 C3H8 + 5 O2 → 3 CO2 + 4 H2O``."""

    def _side(labels: Sequence[str], coeffs: Sequence[int]) -> str:
        return " + ".join(f"{coeff} {label}" for coeff, label in zip(coeffs, labels))

    split = len(reactants)
    left = _side(reactants, coefficients[:split])
    right = _side(products, coefficients[split:])
    return f"{left} → {right}"


def balance_chemical_reaction(
    reactant_formulas: Sequence[Dict[str, int]],
    product_formulas: Sequence[Dict[str, int]],
    reactant_labels: Optional[Sequence[str]] = None,
    product_labels: Optional[Sequence[str]] = None,
) -> ChemicalBalanceResult:
    """Formula la conservación atómica y calcula los enteros positivos mínimos.

    El sistema es homogéneo. Con un solo grado de libertad se toma el generador
    del núcleo, se limpia de denominadores y se divide por el mcd. Si el núcleo
    es trivial o tiene más de una dirección libre, la reacción no queda
    determinada por una sola tupla de enteros mínimos.

    Raises:
        ChemicalFormulaError: Si falta algún lado de la reacción.
    """
    if not reactant_formulas or not product_formulas:
        raise ChemicalFormulaError("Hacen falta reactivos y productos.")

    reactants = list(reactant_labels) if reactant_labels is not None else [
        _formula_label(formula, index) for index, formula in enumerate(reactant_formulas)
    ]
    products = list(product_labels) if product_labels is not None else [
        _formula_label(formula, index) for index, formula in enumerate(product_formulas)
    ]
    if len(reactants) != len(reactant_formulas) or len(products) != len(product_formulas):
        raise ChemicalFormulaError("Cada fórmula necesita exactamente una etiqueta.")

    augmented, elements = atom_conservation_matrix(reactant_formulas, product_formulas)
    species = reactants + products
    description = (
        "Conservación de átomos de "
        + ", ".join(elements)
        + ". Columnas: "
        + ", ".join(species)
        + ". El sistema es homogéneo: lo que entra de cada elemento sale igual."
    )
    _rref, tracer = gauss_jordan_elimination(
        augmented,
        split_col=augmented.cols - 1,
        initial_description=description,
        initial_latex=r"(I)\ \text{conservación atómica}",
    )
    analysis = classify_system(augmented, split_col=augmented.cols - 1)

    if (
        analysis.system_type != SystemType.CONSISTENT_INDETERMINED
        or len(analysis.free_variables) != 1
        or analysis.parametric_vector_solution is None
    ):
        reason = _chemical_failure_reason(analysis)
        tracer.record_step(
            matrix=augmented,
            latex_formula=r"\text{sin enteros mínimos únicos}",
            heuristic_text=reason,
        )
        return ChemicalBalanceResult(
            reactants=reactants,
            products=products,
            stoichiometric_coefficients=[],
            balanced_equation_text="",
            augmented_matrix=augmented,
            is_valid=False,
            elements=elements,
            summary=reason,
            tracer=tracer,
        )

    free_index = analysis.free_variables[0]
    generator = analysis.parametric_vector_solution.null_basis_vectors[free_index]
    try:
        coefficients = integer_balanced_coefficients(generator.components)
    except ValueError as exc:
        tracer.record_step(
            matrix=augmented,
            latex_formula=r"\text{núcleo sin semirrecta positiva}",
            heuristic_text=str(exc),
        )
        return ChemicalBalanceResult(
            reactants=reactants,
            products=products,
            stoichiometric_coefficients=[],
            balanced_equation_text="",
            augmented_matrix=augmented,
            is_valid=False,
            elements=elements,
            summary=str(exc),
            tracer=tracer,
        )

    reactant_positive = any(coeff > 0 for coeff in coefficients[: len(reactants)])
    product_positive = any(coeff > 0 for coeff in coefficients[len(reactants) :])
    if not reactant_positive or not product_positive:
        reason = "El núcleo no usa a la vez reactivos y productos."
        return ChemicalBalanceResult(
            reactants=reactants,
            products=products,
            stoichiometric_coefficients=coefficients,
            balanced_equation_text="",
            augmented_matrix=augmented,
            is_valid=False,
            elements=elements,
            summary=reason,
            tracer=tracer,
        )

    equation = _format_balanced_equation(reactants, products, coefficients)
    free_name = f"x{free_index + 1}"
    summary = (
        f"Hay una variable libre ({free_name}). "
        f"El generador del núcleo, escrito con enteros positivos mínimos, es "
        f"{coefficients}. Ecuación balanceada: {equation}."
    )
    tracer.record_step(
        matrix=augmented,
        latex_formula=equation.replace("→", r"\rightarrow"),
        heuristic_text=summary,
    )
    return ChemicalBalanceResult(
        reactants=reactants,
        products=products,
        stoichiometric_coefficients=coefficients,
        balanced_equation_text=equation,
        augmented_matrix=augmented,
        is_valid=True,
        elements=elements,
        summary=summary,
        tracer=tracer,
    )


def _formula_label(formula: Dict[str, int], index: int) -> str:
    """Etiqueta de respaldo cuando el llamador no pasó el texto de la fórmula."""
    body = "".join(
        element if amount == 1 else f"{element}{amount}"
        for element, amount in formula.items()
    )
    return body or f"especie{index + 1}"


def _chemical_failure_reason(analysis: SystemAnalysis) -> str:
    if analysis.system_type == SystemType.INCONSISTENT:
        return "La conservación de átomos es inconsistente: la reacción no se puede balancear."
    if not analysis.free_variables:
        return (
            "La única solución es la trivial (todos los coeficientes en cero). "
            "La reacción no conserva los átomos con cantidades positivas."
        )
    names = ", ".join(analysis.free_variables_names)
    return (
        f"El núcleo tiene {len(analysis.free_variables)} direcciones libres ({names}). "
        "No hay una sola tupla de enteros mínimos."
    )


def balance_chemical_equation(equation: str) -> ChemicalBalanceResult:
    """Atajo de ``balance_chemical_reaction`` a partir del texto de la reacción."""
    reactants, reactant_formulas, products, product_formulas = parse_chemical_equation(equation)
    return balance_chemical_reaction(
        reactant_formulas,
        product_formulas,
        reactant_labels=reactants,
        product_labels=products,
    )


@dataclass(frozen=True)
class LeontiefModelResult:
    """Precios de equilibrio del modelo cerrado ``(I - C) p = 0``."""

    consumption_matrix_C: Matrix
    system_matrix: Matrix
    equilibrium_price_vector: Vector
    degrees_of_freedom: int
    augmented_matrix: Matrix
    columns_sum_to_one: bool
    summary: str
    tracer: StepTracer


def _column_sums(matrix: Matrix) -> List[Fraction]:
    return [
        sum((matrix.get(row, col) for row in range(matrix.rows)), Fraction(0))
        for col in range(matrix.cols)
    ]


def _relative_price_vector(analysis: SystemAnalysis) -> Vector:
    """Un vector de precios con la última variable libre igual a 1.

    El generador del núcleo ya trae un 1 en esa variable libre, así que la
    escala coincide con la normalización de la sesión.
    """
    if analysis.system_type == SystemType.CONSISTENT_DETERMINED:
        assert analysis.unique_solution is not None
        return Vector(analysis.unique_solution)
    if analysis.parametric_vector_solution is None or not analysis.free_variables:
        raise AppliedModelError("El modelo de Leontief no produjo precios relativos.")
    free_index = analysis.free_variables[-1]
    return analysis.parametric_vector_solution.null_basis_vectors[free_index]


def solve_leontief_exchange(C: Matrix) -> LeontiefModelResult:
    """Resuelve el modelo cerrado de intercambio ``(I - C) p = 0``.

    Cada columna de ``C`` debería sumar 1: el sector reparte toda su producción.
    Los precios quedan relativos a la última variable libre, normalizada en 1,
    que es como la sesión escribe ``p = p_S (31/33, 28/33, 1)``.

    Raises:
        AppliedModelError: Si ``C`` no es cuadrada.
    """
    if C.rows != C.cols:
        raise AppliedModelError(
            f"La matriz de consumo debe ser cuadrada; se recibió {C.rows}×{C.cols}."
        )
    order = C.rows
    system = matrix_sub(Matrix.identity(order), C)
    augmented = system.augment([0] * order)
    sums = _column_sums(C)
    columns_sum_to_one = all(total == 1 for total in sums)
    column_note = (
        "Cada columna de C suma 1: el modelo de intercambio está cerrado."
        if columns_sum_to_one
        else "Alguna columna de C no suma 1. El modelo cerrado pide que cada sector "
        "reparta el total de su producción. Aun así se resuelve (I - C) p = 0."
    )
    _rref, tracer = gauss_jordan_elimination(
        augmented,
        split_col=order,
        initial_description=(
            "Sistema de precios de equilibrio (I - C) p = 0. " + column_note
        ),
        initial_latex=r"(I - C)\,p = 0",
    )
    analysis = classify_system(augmented, split_col=order)
    prices = _relative_price_vector(analysis)
    degrees = len(analysis.free_variables)
    rendered = ", ".join(format_scalar(component) for component in prices.components)
    if degrees == 0:
        summary = (
            "El sistema solo admite el vector de precios nulo. "
            + column_note
        )
    else:
        free_name = f"p{analysis.free_variables[-1] + 1}"
        summary = (
            f"Hay {degrees} grado{'s' if degrees != 1 else ''} de libertad. "
            f"Con {free_name} = 1, los precios relativos son ({rendered}). "
            + column_note
        )
    tracer.record_step(
        matrix=augmented,
        latex_formula=rf"p = ({rendered})",
        heuristic_text=summary,
    )
    return LeontiefModelResult(
        consumption_matrix_C=C,
        system_matrix=system,
        equilibrium_price_vector=prices,
        degrees_of_freedom=degrees,
        augmented_matrix=augmented,
        columns_sum_to_one=columns_sum_to_one,
        summary=summary,
        tracer=tracer,
    )


@dataclass(frozen=True)
class NutritionMixResult:
    """Mezcla que cubre requerimientos exactos de nutrientes."""

    ingredient_names: List[str]
    nutrient_names: List[str]
    amounts: List[Fraction]
    gram_amounts: List[Fraction]
    augmented_matrix: Matrix
    is_feasible: bool
    portion_grams: Fraction
    summary: str
    failure_reason: Optional[str]
    tracer: StepTracer


def solve_nutrition_mix(
    composition: Matrix,
    requirements: Vector,
    ingredient_names: Optional[Sequence[str]] = None,
    nutrient_names: Optional[Sequence[str]] = None,
    portion_grams: Fraction | int = 100,
) -> NutritionMixResult:
    """Resuelve la mezcla ``A x = b``.

    ``composition`` tiene una fila por nutriente y una columna por alimento.
    ``requirements`` es la dieta objetivo, en las mismas unidades. Una solución
    con alguna cantidad negativa no es realizable: no se puede usar una masa
    negativa de alimento.

    Raises:
        DimensionMismatchError: Si el número de nutrientes no coincide con ``b``.
    """
    if composition.rows != requirements.dimension:
        raise DimensionMismatchError(
            "Cada nutriente de la tabla necesita un requerimiento. "
            f"La matriz es {composition.rows}×{composition.cols} y b tiene "
            f"dimensión {requirements.dimension}.",
            left_shape=composition.shape,
            right_shape=(requirements.dimension,),
            operation="dieta nutritiva",
        )
    portion = parse_scalar(portion_grams)
    if portion <= 0:
        raise AppliedModelError("La porción de referencia debe ser positiva.")

    ingredients = list(ingredient_names) if ingredient_names is not None else [
        f"alimento {index + 1}" for index in range(composition.cols)
    ]
    nutrients = list(nutrient_names) if nutrient_names is not None else [
        f"nutriente {index + 1}" for index in range(composition.rows)
    ]
    if len(ingredients) != composition.cols or len(nutrients) != composition.rows:
        raise AppliedModelError("Los nombres no coinciden con las filas o las columnas de la tabla.")

    augmented = composition.augment(requirements.components)
    _rref, tracer = gauss_jordan_elimination(
        augmented,
        split_col=composition.cols,
        initial_description=(
            "Mezcla de alimentos. Filas: "
            + ", ".join(nutrients)
            + ". Columnas: "
            + ", ".join(ingredients)
            + ". Se busca A x = b con cantidades no negativas."
        ),
        initial_latex=r"Ax = b",
    )
    analysis = classify_system(augmented, split_col=composition.cols)
    if analysis.system_type == SystemType.INCONSISTENT or analysis.unique_solution is None:
        reason = analysis.summary_message
        tracer.record_step(
            matrix=augmented,
            latex_formula=r"\text{sin mezcla}",
            heuristic_text=reason,
        )
        return NutritionMixResult(
            ingredient_names=ingredients,
            nutrient_names=nutrients,
            amounts=[],
            gram_amounts=[],
            augmented_matrix=augmented,
            is_feasible=False,
            portion_grams=portion,
            summary=reason,
            failure_reason=reason,
            tracer=tracer,
        )

    amounts = list(analysis.unique_solution)
    grams = [amount * portion for amount in amounts]
    negative = [ingredients[index] for index, amount in enumerate(amounts) if amount < 0]
    if negative:
        if analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            reason = (
                "La solución particular, con las variables libres en 0, pide una cantidad "
                "negativa de "
                + ", ".join(negative)
                + ". Esa mezcla no es realizable."
            )
        else:
            reason = (
                "La solución exacta pide una cantidad negativa de "
                + ", ".join(negative)
                + ". No es una mezcla realizable."
            )
        tracer.record_step(
            matrix=augmented,
            latex_formula=r"x \not\geq 0",
            heuristic_text=reason,
        )
        return NutritionMixResult(
            ingredient_names=ingredients,
            nutrient_names=nutrients,
            amounts=amounts,
            gram_amounts=grams,
            augmented_matrix=augmented,
            is_feasible=False,
            portion_grams=portion,
            summary=reason,
            failure_reason=reason,
            tracer=tracer,
        )

    details = ", ".join(
        f"{ingredients[index]}: {format_scalar(amounts[index])} unidades "
        f"({format_scalar(grams[index])} g si la unidad son {format_scalar(portion)} g)"
        for index in range(len(amounts))
    )
    if analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
        summary = (
            "Hay infinitas mezclas. La solución particular, con las variables libres en 0, "
            f"es no negativa: {details}."
        )
    else:
        summary = f"Mezcla única y no negativa. {details}."
    tracer.record_step(
        matrix=augmented,
        latex_formula=r"x \geq 0",
        heuristic_text=summary,
    )
    return NutritionMixResult(
        ingredient_names=ingredients,
        nutrient_names=nutrients,
        amounts=amounts,
        gram_amounts=grams,
        augmented_matrix=augmented,
        is_feasible=True,
        portion_grams=portion,
        summary=summary,
        failure_reason=None,
        tracer=tracer,
    )


@dataclass(frozen=True)
class NetworkFlowResult:
    """Solución general de una red y cotas para que ningún flujo cambie de sentido."""

    general_flow_solution: Dict[str, str]
    valid_ranges: Dict[str, Tuple[Fraction, Optional[Fraction]]]
    is_feasible: bool
    augmented_matrix: Matrix
    bounds_are_exact: bool
    parameter_range: Optional[Tuple[Fraction, Optional[Fraction]]]
    summary: str
    tracer: StepTracer


def _affine_expressions(
    analysis: SystemAnalysis,
) -> List[Tuple[Fraction, Dict[int, Fraction]]]:
    """Cada variable como constante más combinación de las variables libres."""
    expressions: List[Tuple[Fraction, Dict[int, Fraction]]] = []
    for index in range(analysis.num_variables):
        if analysis.system_type == SystemType.CONSISTENT_DETERMINED:
            assert analysis.unique_solution is not None
            expressions.append((analysis.unique_solution[index], {}))
        elif index in analysis.free_variables:
            expressions.append((Fraction(0), {index: Fraction(1)}))
        else:
            assert analysis.parametric_solutions is not None
            expression = analysis.parametric_solutions[index]
            expressions.append((expression.constant, dict(expression.free_var_coeffs)))
    return expressions


def _solution_strings(analysis: SystemAnalysis) -> Dict[str, str]:
    """Texto de cada flujo: ``600 - x5``, ``x5``, ``400``."""
    rendered: Dict[str, str] = {}
    if analysis.system_type == SystemType.CONSISTENT_DETERMINED:
        assert analysis.unique_solution is not None
        for index, value in enumerate(analysis.unique_solution):
            rendered[f"x{index + 1}"] = format_scalar(value)
        return rendered
    assert analysis.parametric_solutions is not None
    for index in range(analysis.num_variables):
        name = f"x{index + 1}"
        if index in analysis.free_variables:
            rendered[name] = name
        else:
            rendered[name] = analysis.parametric_solutions[index].to_string()
    return rendered


def _single_parameter_bounds(
    expressions: Sequence[Tuple[Fraction, Dict[int, Fraction]]],
    free_index: int,
    capacities: Dict[int, Fraction],
) -> Tuple[bool, Fraction, Optional[Fraction], Dict[str, Tuple[Fraction, Optional[Fraction]]]]:
    """Cotas de ``t`` para un solo parámetro libre y calles de un solo sentido.

    ``x_i = c_i + m_i t``, con ``t`` igual a la variable libre y ``t >= 0``.
    Cada ``x_i >= 0`` y, si se declaró, ``x_i <=`` capacidad recorta el intervalo.
    """
    lowers: List[Fraction] = [Fraction(0)]
    uppers: List[Fraction] = []

    for index, (constant, coeffs) in enumerate(expressions):
        slope = coeffs.get(free_index, Fraction(0))
        extra = {key: value for key, value in coeffs.items() if key != free_index}
        if extra:
            raise AppliedModelError("La cota de un solo parámetro recibió otra variable libre.")
        if slope == 0:
            if constant < 0 or (index in capacities and constant > capacities[index]):
                return False, Fraction(0), None, {}
            continue
        if slope > 0:
            lowers.append((-constant) / slope)
        else:
            uppers.append((-constant) / slope)
        if index in capacities:
            room = capacities[index] - constant
            if slope > 0:
                uppers.append(room / slope)
            else:
                lowers.append(room / slope)

    parameter_min = max(lowers)
    parameter_max = min(uppers) if uppers else None
    if parameter_max is not None and parameter_min > parameter_max:
        return False, parameter_min, parameter_max, {}

    ranges: Dict[str, Tuple[Fraction, Optional[Fraction]]] = {}
    for index, (constant, coeffs) in enumerate(expressions):
        slope = coeffs.get(free_index, Fraction(0))
        name = f"x{index + 1}"
        if slope == 0:
            ranges[name] = (constant, constant)
            continue
        if slope > 0:
            lower_value = constant + slope * parameter_min
            upper_value = None if parameter_max is None else constant + slope * parameter_max
        else:
            if parameter_max is None:
                return False, parameter_min, None, {}
            lower_value = constant + slope * parameter_max
            upper_value = constant + slope * parameter_min
        ranges[name] = (lower_value, upper_value)
    return True, parameter_min, parameter_max, ranges


def _format_interval(lower: Fraction, upper: Optional[Fraction]) -> str:
    if upper is None:
        return f"[{format_scalar(lower)}, ∞)"
    if lower == upper:
        return format_scalar(lower)
    return f"[{format_scalar(lower)}, {format_scalar(upper)}]"


def analyze_network_flow(
    node_equations: Matrix,
    capacities: Optional[Dict[int, Fraction]] = None,
) -> NetworkFlowResult:
    """Conservación en los nodos y cotas para flujos de un solo sentido.

    ``node_equations`` es la matriz aumentada del balance (entra = sale, pasado
    todo a la izquierda). Las capacidades, si se dan, son cotas superiores
    ``x_i <= capacidad`` con índice de variable en base 0.

    Con una variable libre las cotas son exactas. Con más de una, el curso no
    usa símplex: se entrega la solución general y ``bounds_are_exact`` queda
    en falso. ``is_feasible`` es entonces verdadero solo si la solución
    particular (variables libres en 0) ya es no negativa.

    Raises:
        AppliedModelError: Si la matriz no trae la columna de términos independientes.
    """
    if node_equations.cols < 2:
        raise AppliedModelError(
            "La red se escribe como matriz aumentada [A | b] del balance en los nodos."
        )
    limits = {
        index: parse_scalar(limit)
        for index, limit in (capacities or {}).items()
    }
    for index, limit in limits.items():
        if index < 0 or index >= node_equations.cols - 1:
            raise AppliedModelError(
                f"La capacidad de x{index + 1} no corresponde a una rama de la red."
            )
        if limit < 0:
            raise AppliedModelError("Una capacidad de flujo no puede ser negativa.")

    split_col = node_equations.cols - 1
    _rref, tracer = gauss_jordan_elimination(
        node_equations,
        split_col=split_col,
        initial_description=(
            "Conservación en los nodos: el flujo que entra es el flujo que sale. "
            "Las calles de un solo sentido exigen x_i ≥ 0."
        ),
        initial_latex=r"\text{balance de nodos}",
    )
    analysis = classify_system(node_equations, split_col=split_col)
    if analysis.system_type == SystemType.INCONSISTENT:
        summary = "La red es inconsistente: no hay patrón de flujo que conserve todos los nodos."
        tracer.record_step(
            matrix=node_equations,
            latex_formula=r"\text{red inconsistente}",
            heuristic_text=summary,
        )
        return NetworkFlowResult(
            general_flow_solution={},
            valid_ranges={},
            is_feasible=False,
            augmented_matrix=node_equations,
            bounds_are_exact=True,
            parameter_range=None,
            summary=summary,
            tracer=tracer,
        )

    expressions = _affine_expressions(analysis)
    solution = _solution_strings(analysis)
    free_count = len(analysis.free_variables)

    if free_count == 0:
        ranges = {
            f"x{index + 1}": (value, value)
            for index, (value, _coeffs) in enumerate(expressions)
        }
        feasible = all(lower >= 0 for lower, _upper in ranges.values()) and all(
            expressions[index][0] <= limit for index, limit in limits.items()
        )
        summary = (
            "El flujo queda determinado. "
            + (", ".join(f"{name} = {text}" for name, text in solution.items()))
            + (". Todos los flujos respetan el sentido de la calle." if feasible
               else ". Algún flujo es negativo o supera su capacidad: el sentido indicado no se sostiene.")
        )
        tracer.record_step(
            matrix=node_equations,
            latex_formula=r"x \geq 0",
            heuristic_text=summary,
        )
        return NetworkFlowResult(
            general_flow_solution=solution,
            valid_ranges=ranges,
            is_feasible=feasible,
            augmented_matrix=node_equations,
            bounds_are_exact=True,
            parameter_range=None,
            summary=summary,
            tracer=tracer,
        )

    if free_count == 1:
        free_index = analysis.free_variables[0]
        feasible, lower, upper, ranges = _single_parameter_bounds(expressions, free_index, limits)
        parameter = (lower, upper) if feasible else None
        free_name = f"x{free_index + 1}"
        if feasible:
            interval = _format_interval(lower, upper)
            pieces = ", ".join(
                f"{name} ∈ {_format_interval(start, end)}" for name, (start, end) in ranges.items()
            )
            summary = (
                f"La variable libre es {free_name}, con {free_name} ∈ {interval} "
                f"para que ningún flujo sea negativo. Cotas: {pieces}."
            )
        else:
            ranges = {}
            summary = (
                f"No hay un valor de {free_name} que mantenga todos los flujos en el sentido "
                "de la calle y dentro de las capacidades."
            )
        tracer.record_step(
            matrix=node_equations,
            latex_formula=rf"{free_name} \geq 0",
            heuristic_text=summary,
        )
        return NetworkFlowResult(
            general_flow_solution=solution,
            valid_ranges=ranges,
            is_feasible=feasible,
            augmented_matrix=node_equations,
            bounds_are_exact=True,
            parameter_range=parameter,
            summary=summary,
            tracer=tracer,
        )

    particular = analysis.unique_solution or []
    feasible = all(value >= 0 for value in particular) and all(
        particular[index] <= limit for index, limit in limits.items()
    )
    summary = (
        "Hay más de una variable libre. La solución general queda escrita, pero las cotas "
        "cerradas de una red con varios parámetros no se calculan por símplex. "
        "La solución particular, con las libres en 0, "
        + ("ya es no negativa." if feasible else "tiene algún flujo negativo.")
    )
    tracer.record_step(
        matrix=node_equations,
        latex_formula=r"x = p + \sum t_k v_k",
        heuristic_text=summary,
    )
    return NetworkFlowResult(
        general_flow_solution=solution,
        valid_ranges={},
        is_feasible=feasible,
        augmented_matrix=node_equations,
        bounds_are_exact=False,
        parameter_range=None,
        summary=summary,
        tracer=tracer,
    )


def coal_electric_steel_consumption() -> Matrix:
    """Tabla de la sesión 8, diapositivas 3 a 6: carbón, electricidad y acero.

    Las columnas son el reparto de la producción de cada sector y suman 1.
    """
    return Matrix([
        [0, "0.4", "0.6"],
        ["0.6", "0.1", "0.2"],
        ["0.4", "0.5", "0.2"],
    ])


def baltimore_traffic_network() -> Matrix:
    """Balance de la red de Baltimore, sesión 8, diapositivas 17 a 21.

    Variables ``x1`` … ``x5`` en el orden de la figura. La última fila fija
    ``x3 = 400`` por el balance global de la red.
    """
    return Matrix([
        [1, 1, 0, 0, 0, 800],
        [0, 1, -1, 1, 0, 300],
        [0, 0, 0, 1, 1, 500],
        [1, 0, 0, 0, 1, 600],
        [0, 0, 1, 0, 0, 400],
    ])


def cambridge_diet() -> Tuple[Matrix, Vector]:
    """Tabla de leche, harina de soya y suero, sesión 8, diapositivas 11 a 15.

    La grasa del suero es 1.1 g, guardada como ``11/10``.
    """
    composition = Matrix([
        [36, 51, 13],
        [52, 34, 74],
        [0, 7, Fraction(11, 10)],
    ])
    requirements = Vector([33, 45, 3])
    return composition, requirements


def leontief_prices_reproduce_zero(result: LeontiefModelResult) -> bool:
    """Comprueba ``(I - C) p = 0`` con el vector de precios devuelto."""
    image = matrix_vector_multiply(result.system_matrix, result.equilibrium_price_vector)
    return all(component == 0 for component in image.components)
