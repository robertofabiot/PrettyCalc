"""Asistente de las aplicaciones de sistemas lineales (Sesión 8)."""

from __future__ import annotations

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
    ChemicalBalanceResult,
    ChemicalFormulaError,
    LeontiefModelResult,
    NetworkFlowResult,
    NutritionMixResult,
    analyze_network_flow,
    balance_chemical_reaction,
    baltimore_traffic_network,
    cambridge_diet,
    parse_chemical_side,
    solve_leontief_exchange,
    solve_nutrition_mix,
)
from prettycalc.core.types import Matrix, format_scalar
from prettycalc.ui.theme import (
    COLOR_ACCENT_WARNING,
    COLOR_FEEDBACK_ERROR,
    COLOR_FEEDBACK_SUCCESS,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_INNER,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY_MONO,
    apply_widget_class,
)


_FIELD_STYLE = f"""
QLineEdit {{
    background-color: {COLOR_SURFACE_INNER};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_INTERACTIVE_IDLE};
    border-radius: 6px;
    padding: 6px 10px;
    font-family: {FONT_FAMILY_MONO};
    font-size: 14px;
    selection-background-color: {COLOR_INTERACTIVE_IDLE};
    selection-color: {COLOR_SURFACE_INNER};
}}
"""

_COAL_TEXT = "0, 0.4, 0.6; 0.6, 0.1, 0.2; 0.4, 0.5, 0.2"


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
    edit.setStyleSheet(_FIELD_STYLE)
    edit.setClearButtonEnabled(False)
    return edit


def _hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
    return label


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

        self.result_label = QLabel("Elige una aplicación y calcula. La matriz aumentada se carga sola.")
        self.result_label.setObjectName("appliedResult")
        self.result_label.setWordWrap(True)
        self.result_label.setTextFormat(Qt.RichText)
        self.result_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px;")
        layout.addWidget(self.result_label)

    def _chemical_form(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        form = QVBoxLayout(page)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        form.addWidget(_hint("Reactivos y productos, sin coeficientes. Ejemplo de la sesión: propano."))
        form.addWidget(QLabel("Reactivos"))
        self.reactants_edit = _field("C3H8 + O2", "chemicalReactants")
        form.addWidget(self.reactants_edit)
        form.addWidget(QLabel("Productos"))
        self.products_edit = _field("CO2 + H2O", "chemicalProducts")
        form.addWidget(self.products_edit)
        self.balance_btn = QPushButton("Balancear reacción")
        self.balance_btn.setObjectName("balanceChemicalButton")
        apply_widget_class(self.balance_btn, "primaryAction")
        self.balance_btn.clicked.connect(self.balance_reaction)
        form.addWidget(self.balance_btn)
        return page

    def _leontief_form(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        form = QVBoxLayout(page)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        form.addWidget(_hint(
            "Matriz de consumo C. Cada fila va separada por punto y coma y cada columna debe sumar 1."
        ))
        self.consumption_edit = _field(_COAL_TEXT, "leontiefConsumption")
        form.addWidget(self.consumption_edit)
        actions = QHBoxLayout()
        self.leontief_example_btn = QPushButton("Carbón, electricidad y acero")
        self.leontief_example_btn.setObjectName("leontiefExampleButton")
        apply_widget_class(self.leontief_example_btn, "secondaryAction")
        self.leontief_example_btn.clicked.connect(self.load_coal_example)
        actions.addWidget(self.leontief_example_btn)
        self.leontief_btn = QPushButton("Precios de equilibrio")
        self.leontief_btn.setObjectName("leontiefButton")
        apply_widget_class(self.leontief_btn, "primaryAction")
        self.leontief_btn.clicked.connect(self.solve_leontief)
        actions.addWidget(self.leontief_btn)
        form.addLayout(actions)
        return page

    def _diet_form(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        form = QVBoxLayout(page)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        form.addWidget(_hint(
            "Dieta Cambridge: leche descremada, harina de soya y suero. "
            "Cada unidad son 100 g y se cubren proteínas, carbohidratos y grasa."
        ))
        self.diet_btn = QPushButton("Resolver dieta Cambridge")
        self.diet_btn.setObjectName("dietButton")
        apply_widget_class(self.diet_btn, "primaryAction")
        self.diet_btn.clicked.connect(self.solve_cambridge_diet)
        form.addWidget(self.diet_btn)
        return page

    def _traffic_form(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        form = QVBoxLayout(page)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        form.addWidget(_hint(
            "Red de un solo sentido en Baltimore. El balance de los nodos se carga solo "
            "y las cotas evitan un flujo en contra del sentido (xᵢ ≥ 0)."
        ))
        self.traffic_btn = QPushButton("Analizar red de Baltimore")
        self.traffic_btn.setObjectName("trafficButton")
        apply_widget_class(self.traffic_btn, "primaryAction")
        self.traffic_btn.clicked.connect(self.solve_baltimore)
        form.addWidget(self.traffic_btn)
        return page

    def _show_form(self, index: int) -> None:
        self.forms.setCurrentIndex(index)

    def show_mode(self, index: int) -> None:
        """Selecciona Química, Leontief, Dieta o Tráfico."""
        button = self.mode_group.button(index)
        if button is not None:
            button.setChecked(True)
        self.forms.setCurrentIndex(index)

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

    def load_coal_example(self) -> None:
        """Rellena C con la tabla de carbón, electricidad y acero."""
        self.consumption_edit.setText(_COAL_TEXT)
        self.solve_leontief()

    def solve_leontief(self) -> None:
        """Resuelve (I − C) p = 0 con la matriz escrita en el formulario."""
        try:
            consumption = parse_consumption_text(self.consumption_edit.text())
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

    def solve_cambridge_diet(self) -> None:
        """Carga la tabla de la dieta y resuelve la mezcla."""
        composition, requirements = cambridge_diet()
        result = solve_nutrition_mix(
            composition,
            requirements,
            ingredient_names=["leche descremada", "harina de soya", "suero de leche"],
            nutrient_names=["proteínas", "carbohidratos", "grasa"],
        )
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
            self._show_message(f"Mezcla exacta de la dieta Cambridge.<br>{lines}", error=False)
        else:
            self._show_message(result.summary, error=True)
        self.model_ready.emit(result)

    def solve_baltimore(self) -> None:
        """Carga el balance de nodos y calcula las cotas de un solo sentido."""
        result = analyze_network_flow(baltimore_traffic_network())
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
        self.result_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.result_label.setText(text)


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
