"""Asistente de las aplicaciones de sistemas lineales (Sesión 8).

Sprint 10 (auditoría UI/UX, SEL_FLUJO_04):

- La matriz de consumo de Leontief se edita en una cuadrícula n×n (con suma
  de columnas en vivo) en lugar de una línea de texto con punto y coma.
- La dieta y la red de tráfico ya no son ejemplos fijos: la tabla de
  nutrientes y el balance de nodos son editables, con el ejemplo de la
  sesión precargado y un botón para restaurarlo.
- Ejemplos químicos de un clic.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QLineEdit,
        QStackedWidget,
        QButtonGroup,
        QFrame,
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.applied_models import (
    AppliedModelError,
    ChemicalBalanceResult,
    ChemicalFormulaError,
    LeontiefModelResult,
    NetworkFlowResult,
    NutritionMixResult,
    analyze_network_flow,
    balance_chemical_reaction,
    baltimore_traffic_network,
    cambridge_diet,
    coal_electric_steel_consumption,
    parse_chemical_side,
    solve_leontief_exchange,
    solve_nutrition_mix,
)
from prettycalc.core.types import DimensionMismatchError, Matrix, Vector, format_scalar
from prettycalc.ui.matrix_grid import DynamicMatrixGrid
from prettycalc.ui.size_control import MatrixSizeControl
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_TEXT_PRIMARY,
    apply_widget_class,
)


_COAL_TEXT = "0, 0.4, 0.6; 0.6, 0.1, 0.2; 0.4, 0.5, 0.2"

_CAMBRIDGE_INGREDIENTS = ["leche descremada", "harina de soya", "suero de leche"]
_CAMBRIDGE_NUTRIENTS = ["proteínas", "carbohidratos", "grasa"]

#: Reacciones de ejemplo: (rótulo, reactivos, productos).
_CHEMICAL_EXAMPLES = (
    ("Propano", "C3H8 + O2", "CO2 + H2O"),
    ("Fotosíntesis", "CO2 + H2O", "C6H12O6 + O2"),
    ("Óxido de hierro", "Fe + O2", "Fe2O3"),
)


def parse_consumption_text(text: str) -> Matrix:
    """Lee ``0, 0.4, 0.6; 0.6, 0.1, 0.2; ...`` como matriz de consumo."""
    rows = []
    for raw_row in text.split(";"):
        cells = raw_row.replace(",", " ").split()
        if cells:
            rows.append(cells)
    if not rows:
        raise ValueError("Escribe la matriz de consumo, con una fila entre cada punto y coma.")
    return Matrix(rows)


def _field(text: str, object_name: str) -> QLineEdit:
    edit = QLineEdit(text)
    edit.setObjectName(object_name)
    apply_widget_class(edit, "text-field")
    edit.setClearButtonEnabled(True)
    return edit


def _hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
    return label


def _secondary(text: str, name: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName(name)
    apply_widget_class(button, "secondaryAction")
    return button


def _primary(text: str, name: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName(name)
    apply_widget_class(button, "primaryAction")
    return button


class AppliedModelsPanel(QFrame):
    """Formularios de química, Leontief, dieta y redes. No arma la matriz a mano."""

    model_ready = Signal(object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self.setObjectName("appliedModelsPanel")
        self.last_chemical: ChemicalBalanceResult | None = None
        self.last_leontief: LeontiefModelResult | None = None
        self.last_nutrition: NutritionMixResult | None = None
        self.last_network: NetworkFlowResult | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Aplicaciones de SEL")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};"
        )
        layout.addWidget(title)

        modes = QHBoxLayout()
        modes.setSpacing(6)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        labels = (
            ("chemicalMode", "Química"),
            ("leontiefMode", "Leontief"),
            ("dietMode", "Dieta"),
            ("trafficMode", "Tráfico"),
        )
        for index, (name, text) in enumerate(labels):
            button = QPushButton(text)
            button.setObjectName(name)
            button.setCheckable(True)
            apply_widget_class(button, "modeToggle")
            self.mode_group.addButton(button, index)
            modes.addWidget(button)
        self.mode_group.button(0).setChecked(True)
        self.mode_group.idClicked.connect(self._show_form)
        layout.addLayout(modes)

        self.forms = QStackedWidget()
        self.forms.setObjectName("appliedForms")
        self.forms.setStyleSheet("background: transparent;")
        self.forms.addWidget(self._chemical_form())
        self.forms.addWidget(self._leontief_form())
        self.forms.addWidget(self._diet_form())
        self.forms.addWidget(self._traffic_form())
        layout.addWidget(self.forms)

        self.result_label = QLabel(
            "Elige una aplicación y calcula. La matriz aumentada se carga sola en la cuadrícula de arriba."
        )
        self.result_label.setObjectName("appliedResult")
        self.result_label.setWordWrap(True)
        self.result_label.setTextFormat(Qt.RichText)
        self.result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.result_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        layout.addWidget(self.result_label)

    # ------------------------------------------------------------------
    # Formularios
    # ------------------------------------------------------------------

    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        form = QVBoxLayout(page)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        return page, form

    def _chemical_form(self) -> QWidget:
        page, form = self._page()
        form.addWidget(_hint("Reactivos y productos, sin coeficientes. Separa las especies con +."))
        examples = QHBoxLayout()
        examples.setSpacing(4)
        self.chemical_example_buttons: List[QPushButton] = []
        for label, reactants, products in _CHEMICAL_EXAMPLES:
            chip = QPushButton(label)
            apply_widget_class(chip, "chip")
            chip.setToolTip(f"{reactants} → {products}")
            chip.clicked.connect(
                lambda _checked=False, r=reactants, p=products: self.load_chemical_example(r, p)
            )
            examples.addWidget(chip)
            self.chemical_example_buttons.append(chip)
        examples.addStretch(1)
        form.addLayout(examples)
        form.addWidget(QLabel("Reactivos"))
        self.reactants_edit = _field("C3H8 + O2", "chemicalReactants")
        self.reactants_edit.returnPressed.connect(self.balance_reaction)
        form.addWidget(self.reactants_edit)
        form.addWidget(QLabel("Productos"))
        self.products_edit = _field("CO2 + H2O", "chemicalProducts")
        self.products_edit.returnPressed.connect(self.balance_reaction)
        form.addWidget(self.products_edit)
        self.balance_btn = _primary("Balancear reacción", "balanceChemicalButton")
        self.balance_btn.clicked.connect(self.balance_reaction)
        form.addWidget(self.balance_btn)
        return page

    def _leontief_form(self) -> QWidget:
        page, form = self._page()
        form.addWidget(_hint(
            "Matriz de consumo C: la columna j dice cómo reparte su producción el sector j. "
            "Cada columna debe sumar 1."
        ))
        self.consumption_grid = DynamicMatrixGrid(
            initial_rows=3,
            initial_cols=3,
            augmented=False,
            row_expandable=False,
            col_expandable=False,
        )
        self.consumption_grid.setObjectName("leontiefConsumption")
        self.consumption_grid.set_matrix(coal_electric_steel_consumption(), record=False)
        self.consumption_grid.matrixChanged.connect(self._refresh_column_sums)
        self.consumption_grid.submitRequested.connect(self.solve_leontief)
        self.sectors_control = MatrixSizeControl(
            self.consumption_grid, square=True, order_label="Sectores n", minimum=2, maximum=8
        )
        form.addWidget(self.sectors_control)
        form.addWidget(self.consumption_grid)
        self.column_sums_label = QLabel("")
        self.column_sums_label.setObjectName("leontiefColumnSums")
        self.column_sums_label.setWordWrap(True)
        form.addWidget(self.column_sums_label)
        actions = QHBoxLayout()
        self.leontief_example_btn = _secondary("Carbón, electricidad y acero", "leontiefExampleButton")
        self.leontief_example_btn.clicked.connect(self.load_coal_example)
        actions.addWidget(self.leontief_example_btn)
        self.leontief_btn = _primary("Precios de equilibrio", "leontiefButton")
        self.leontief_btn.clicked.connect(self.solve_leontief)
        actions.addWidget(self.leontief_btn)
        form.addLayout(actions)
        self._refresh_column_sums()
        return page

    def _diet_form(self) -> QWidget:
        page, form = self._page()
        form.addWidget(_hint(
            "Filas: nutrientes. Columnas: alimentos (cantidad por porción de 100 g). "
            "Columna b: requerimiento diario. Precargada con la dieta Cambridge."
        ))
        composition, requirements = cambridge_diet()
        self.diet_grid = DynamicMatrixGrid(initial_rows=3, initial_cols=3, augmented=True)
        self.diet_grid.setObjectName("dietTable")
        self.diet_grid.set_matrix(composition.augment(requirements.components), record=False)
        self.diet_grid.submitRequested.connect(self.solve_cambridge_diet)
        self.diet_size = MatrixSizeControl(
            self.diet_grid,
            rows_label="Nutrientes",
            cols_label="Alimentos",
            caption="Nutrientes × alimentos",
            minimum=1,
            maximum=6,
        )
        form.addWidget(self.diet_size)
        form.addWidget(self.diet_grid)
        actions = QHBoxLayout()
        self.diet_example_btn = _secondary("Dieta Cambridge", "dietExampleButton")
        self.diet_example_btn.clicked.connect(self.load_cambridge_example)
        actions.addWidget(self.diet_example_btn)
        self.diet_btn = _primary("Resolver mezcla", "dietButton")
        self.diet_btn.clicked.connect(self.solve_cambridge_diet)
        actions.addWidget(self.diet_btn)
        form.addLayout(actions)
        return page

    def _traffic_form(self) -> QWidget:
        page, form = self._page()
        form.addWidget(_hint(
            "Cada fila es un nodo: lo que entra = lo que sale. Pasa todos los xᵢ a la izquierda "
            "(1 o −1) y el flujo externo a b. Las cotas evitan un flujo en contra del sentido (xᵢ ≥ 0). "
            "Precargada con la red de Baltimore."
        ))
        self.traffic_grid = DynamicMatrixGrid(initial_rows=5, initial_cols=5, augmented=True)
        self.traffic_grid.setObjectName("trafficNetwork")
        self.traffic_grid.set_matrix(baltimore_traffic_network(), record=False)
        self.traffic_grid.submitRequested.connect(self.solve_baltimore)
        self.traffic_size = MatrixSizeControl(
            self.traffic_grid,
            rows_label="Ecuaciones",
            cols_label="Tramos",
            caption="Nodos × tramos",
            minimum=1,
            maximum=8,
        )
        form.addWidget(self.traffic_size)
        form.addWidget(self.traffic_grid)
        actions = QHBoxLayout()
        self.traffic_example_btn = _secondary("Red de Baltimore", "trafficExampleButton")
        self.traffic_example_btn.clicked.connect(self.load_baltimore_example)
        actions.addWidget(self.traffic_example_btn)
        self.traffic_btn = _primary("Analizar red", "trafficButton")
        self.traffic_btn.clicked.connect(self.solve_baltimore)
        actions.addWidget(self.traffic_btn)
        form.addLayout(actions)
        return page

    def _show_form(self, index: int) -> None:
        self.forms.setCurrentIndex(index)

    def show_mode(self, index: int) -> None:
        """Selecciona Química, Leontief, Dieta o Tráfico."""
        button = self.mode_group.button(index)
        if button is not None:
            button.setChecked(True)
        self.forms.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Química
    # ------------------------------------------------------------------

    def load_chemical_example(self, reactants: str, products: str) -> None:
        self.reactants_edit.setText(reactants)
        self.products_edit.setText(products)
        self.balance_reaction()

    def balance_reaction(self) -> None:
        """Balancea los dos lados escritos en el formulario."""
        try:
            reactant_labels, reactants = parse_chemical_side(self.reactants_edit.text())
            product_labels, products = parse_chemical_side(self.products_edit.text())
            result = balance_chemical_reaction(
                reactants,
                products,
                reactant_labels=reactant_labels,
                product_labels=product_labels,
            )
        except ChemicalFormulaError as exc:
            self._show_message(str(exc), error=True)
            return
        self.last_chemical = result
        if result.is_valid:
            self._show_message(_chemical_html(result), error=False)
        else:
            self._show_message(result.summary, error=True)
        self.model_ready.emit(result)

    # ------------------------------------------------------------------
    # Leontief
    # ------------------------------------------------------------------

    @property
    def consumption_text(self) -> str:
        """La matriz de consumo actual en el formato «a, b; c, d»."""
        return "; ".join(", ".join(row) for row in self.consumption_grid.get_raw_strings())

    def _refresh_column_sums(self) -> None:
        if not self.consumption_grid.is_all_valid():
            self.column_sums_label.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 13px;")
            self.column_sums_label.setText("Corrige las celdas marcadas para ver la suma de cada columna.")
            return
        matrix = self.consumption_grid.get_matrix()
        sums = [sum((matrix.get(r, c) for r in range(matrix.rows)), Fraction(0)) for c in range(matrix.cols)]
        ok = all(value == 1 for value in sums)
        shown = ", ".join(format_scalar(value) for value in sums)
        color = COLOR_FEEDBACK_SUCCESS if ok else COLOR_ACCENT_WARNING
        verdict = "cada columna suma 1." if ok else "alguna columna no suma 1 (el modelo cerrado lo exige)."
        self.column_sums_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")
        self.column_sums_label.setText(f"Suma por columna: ({shown}) — {verdict}")

    def load_coal_example(self) -> None:
        """Rellena C con la tabla de carbón, electricidad y acero."""
        self.consumption_grid.set_matrix(coal_electric_steel_consumption())
        self.solve_leontief()

    def solve_leontief(self) -> None:
        """Resuelve (I − C) p = 0 con la matriz de la cuadrícula."""
        if not self.consumption_grid.is_all_valid():
            self._show_message(
                "Corrige la matriz de consumo: " + self.consumption_grid.validation_message(),
                error=True,
            )
            return
        try:
            consumption = self.consumption_grid.get_matrix()
            result = solve_leontief_exchange(consumption)
        except (ValueError, ZeroDivisionError) as exc:
            self._show_message(str(exc), error=True)
            return
        self.last_leontief = result
        prices = ", ".join(
            format_scalar(component) for component in result.equilibrium_price_vector.components
        )
        approx = ", ".join(
            f"{float(component):.2f}" for component in result.equilibrium_price_vector.components
        )
        self._show_message(
            f"{result.summary}<br>Vector exacto: ({prices}). "
            f"Aproximación a dos decimales, como en la diapositiva: ({approx}).",
            error=not result.columns_sum_to_one and result.degrees_of_freedom == 0,
        )
        self.model_ready.emit(result)

    # ------------------------------------------------------------------
    # Dieta
    # ------------------------------------------------------------------

    def load_cambridge_example(self) -> None:
        composition, requirements = cambridge_diet()
        self.diet_grid.set_matrix(composition.augment(requirements.components))
        self.solve_cambridge_diet()

    def solve_cambridge_diet(self) -> None:
        """Resuelve la mezcla con la tabla de la cuadrícula (Cambridge por defecto)."""
        if not self.diet_grid.is_all_valid():
            self._show_message("Corrige la tabla: " + self.diet_grid.validation_message(), error=True)
            return
        table = self.diet_grid.get_matrix()
        split = table.cols - 1
        composition, requirement_matrix = table.split_augmented(split)
        requirements = Vector.from_column_matrix(requirement_matrix)
        cambridge_composition, cambridge_requirements = cambridge_diet()
        is_cambridge = composition == cambridge_composition and requirements == cambridge_requirements
        try:
            result = solve_nutrition_mix(
                composition,
                requirements,
                ingredient_names=_CAMBRIDGE_INGREDIENTS if is_cambridge else None,
                nutrient_names=_CAMBRIDGE_NUTRIENTS if is_cambridge else None,
            )
        except (AppliedModelError, DimensionMismatchError, ValueError) as exc:
            self._show_message(str(exc), error=True)
            return
        self.last_nutrition = result
        if result.is_feasible:
            lines = "<br>".join(
                f"{name}: {format_scalar(amount)} unidades "
                f"≈ {float(amount):.3f} "
                f"({float(grams):.1f} g)"
                for name, amount, grams in zip(
                    result.ingredient_names, result.amounts, result.gram_amounts
                )
            )
            heading = "Mezcla exacta de la dieta Cambridge." if is_cambridge else "Mezcla exacta de la dieta."
            self._show_message(f"{heading}<br>{lines}", error=False)
        else:
            self._show_message(result.summary, error=True)
        self.model_ready.emit(result)

    # ------------------------------------------------------------------
    # Tráfico
    # ------------------------------------------------------------------

    def load_baltimore_example(self) -> None:
        self.traffic_grid.set_matrix(baltimore_traffic_network())
        self.solve_baltimore()

    def solve_baltimore(self) -> None:
        """Analiza la red de la cuadrícula: solución general y cotas de un solo sentido."""
        if not self.traffic_grid.is_all_valid():
            self._show_message("Corrige la red: " + self.traffic_grid.validation_message(), error=True)
            return
        try:
            result = analyze_network_flow(self.traffic_grid.get_matrix())
        except (AppliedModelError, ValueError) as exc:
            self._show_message(str(exc), error=True)
            return
        self.last_network = result
        ranges = "<br>".join(
            f"{name} ∈ {_interval_text(lower, upper)}"
            for name, (lower, upper) in result.valid_ranges.items()
        )
        flows = ", ".join(f"{name} = {text}" for name, text in result.general_flow_solution.items())
        self._show_message(
            f"{result.summary}<br>Solución general: {flows}.<br>{ranges}",
            error=not result.is_feasible,
        )
        self.model_ready.emit(result)

    def _show_message(self, text: str, *, error: bool) -> None:
        color = COLOR_FEEDBACK_ERROR if error else COLOR_FEEDBACK_SUCCESS
        self.result_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; border-left: 3px solid {color}; "
            f"padding-left: 8px;"
        )
        mark = "✕" if error else "✓"
        self.result_label.setText(
            f"<span style='color:{color}; font-weight:700;'>{mark}</span>&nbsp; {text}"
        )


def _interval_text(lower, upper) -> str:
    if upper is None:
        return f"[{format_scalar(lower)}, ∞)"
    if lower == upper:
        return format_scalar(lower)
    return f"[{format_scalar(lower)}, {format_scalar(upper)}]"


def _chemical_html(result: ChemicalBalanceResult) -> str:
    """Ecuación balanceada con los enteros resaltados."""
    split = len(result.reactants)
    coefficients = result.stoichiometric_coefficients

    def _side(labels, coeffs) -> str:
        terms = []
        for coeff, label in zip(coeffs, labels):
            terms.append(
                f"<span style='color:{COLOR_ACCENT_WARNING}; font-weight:700;'>{coeff}</span> {label}"
            )
        return " + ".join(terms)

    equation = (
        _side(result.reactants, coefficients[:split])
        + " → "
        + _side(result.products, coefficients[split:])
    )
    return f"Ecuación balanceada:<br>{equation}"
