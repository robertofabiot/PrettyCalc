"""Campo escalar validado en vivo, con pista decimal y atajos de valores frecuentes.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10. Unifica los campos k y c de todos los módulos: el borde se pone en
rojo igual que una celda inválida (Nielsen #4, consistencia), la etiqueta
inferior explica el error o muestra ``≈ 1.5`` para una fracción (Nielsen #6) y
los chips cargan escalares canónicos de un clic (Nielsen #7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

try:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
    from PySide6.QtCore import Qt, Signal
except ImportError:  # pragma: no cover
    QLineEdit = object  # type: ignore
    QWidget = object  # type: ignore
    Signal = lambda *args: None  # type: ignore

from prettycalc.core.input_diagnostics import ScalarDiagnosis, decimal_hint, diagnose_scalar_text
from prettycalc.core.types import parse_scalar
from prettycalc.ui.theme import (
    COLOR_FEEDBACK_ERROR,
    COLOR_TEXT_MUTED,
    apply_widget_class,
    repolish,
    ui_font,
)

#: Escalares canónicos de los ejercicios: opuesta, anulación, mitad y doble.
CANONICAL_SCALARS: Tuple[Tuple[str, str, str], ...] = (
    ("−1", "-1", "k = −1: matriz o vector opuesto"),
    ("0", "0", "k = 0: anulación (resultado nulo)"),
    ("½", "1/2", "k = 1/2: mitad"),
    ("2", "2", "k = 2: doble"),
)


class ScalarField(QLineEdit):
    """``QLineEdit`` que se marca inválido (borde rojo + tooltip) si el texto no es un escalar."""

    validityChanged = Signal(bool)

    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        *,
        object_name: str = "scalarField",
        allow_empty: bool = False,
        base_tooltip: str = "",
    ) -> None:
        super().__init__(text, parent)
        self.setObjectName(object_name)
        if object_name != "scalarField":
            apply_widget_class(self, "scalar-field")
        self.setFont(ui_font(19, mono=True))
        self.setAlignment(Qt.AlignCenter)
        self._allow_empty = allow_empty
        self._base_tooltip = base_tooltip
        self._valid = True
        self.setAccessibleName("Escalar")
        self.textChanged.connect(self._revalidate)
        self._revalidate(self.text())

    def diagnosis(self) -> ScalarDiagnosis:
        return diagnose_scalar_text(self.text(), allow_empty=self._allow_empty)

    def is_valid(self) -> bool:
        return self._valid

    def value(self) -> Optional[Fraction]:
        """Valor exacto, o ``None`` si está vacío o es inválido."""
        text = self.text().strip()
        if not text or not self._valid:
            return None
        return parse_scalar(text)

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        self.selectAll()

    def _revalidate(self, _text: str = "") -> None:
        diagnosis = self.diagnosis()
        valid = diagnosis.is_valid
        self.setProperty("invalid", not valid)
        repolish(self)
        self.setToolTip(diagnosis.message if not valid else self._base_tooltip)
        changed = valid != self._valid
        self._valid = valid
        if changed:
            self.validityChanged.emit(valid)


class ScalarInput(QWidget):
    """Campo escalar + línea de ayuda (error o ``≈ decimal``) + chips opcionales."""

    def __init__(
        self,
        field: ScalarField,
        *,
        presets: Sequence[Tuple[str, str, str]] = (),
        help_text: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.field = field
        self._help_text = help_text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(field)
        self.hint_label = QLabel("")
        self.hint_label.setObjectName("scalarHint")
        self.hint_label.setWordWrap(True)
        apply_widget_class(self.hint_label, "field-hint")
        layout.addWidget(self.hint_label)
        self.chip_buttons: List[QPushButton] = []
        if presets:
            chips = QHBoxLayout()
            chips.setSpacing(4)
            for label, value, tooltip in presets:
                chip = QPushButton(label)
                apply_widget_class(chip, "chip")
                chip.setToolTip(tooltip)
                chip.setCursor(Qt.PointingHandCursor)
                chip.setFocusPolicy(Qt.TabFocus)
                chip.clicked.connect(lambda _checked=False, v=value: self.field.setText(v))
                chips.addWidget(chip)
                self.chip_buttons.append(chip)
            chips.addStretch(1)
            layout.addLayout(chips)
        field.textChanged.connect(self._refresh_hint)
        self._refresh_hint()

    def hint_text(self) -> str:
        return self.hint_label.text()

    def _refresh_hint(self, _text: str = "") -> None:
        diagnosis = self.field.diagnosis()
        if not diagnosis.is_valid:
            self.hint_label.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-size: 13px; font-weight: 600;"
            )
            self.hint_label.setText(diagnosis.message)
            return
        self.hint_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        approx = decimal_hint(self.field.text())
        self.hint_label.setText(approx or self._help_text)
