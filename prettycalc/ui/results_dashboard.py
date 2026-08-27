"""Dashboard de resultados con notación de libro: variables, rangos y comprobación."""

from __future__ import annotations
from typing import Optional, List

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QFrame,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QFrame = object  # type: ignore

from prettycalc.core.classifier import SystemAnalysis, SystemType
from prettycalc.core.verifier import EquationVerification
from prettycalc.core.types import format_scalar
from prettycalc.ui.mathtext import (
    variable_symbol,
    format_equation_book,
    format_substitution_book,
    prettify_math_text,
)
from prettycalc.ui.theme import (
    COLOR_FEEDBACK_SUCCESS,
    COLOR_FEEDBACK_ERROR,
    COLOR_ACCENT_WARNING,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    COLOR_BG_BASE,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
    apply_widget_class,
)


class ResultsDashboardCard(QFrame):
    """Panel de clasificación, solución y comprobación por sustitución."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self.setMinimumWidth(300)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Resultados")
        title.setProperty("class", "section-title")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 600; letter-spacing: 0.08em; "
            f"color: {COLOR_INTERACTIVE_IDLE};"
        )
        layout.addWidget(title)

        self.status_badge = QLabel("Esperando cálculo")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet(self._badge_style("#3A3642", COLOR_TEXT_PRIMARY))
        layout.addWidget(self.status_badge)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 12px; font-style: italic;"
        )
        layout.addWidget(self.summary_label)

        var_title = QLabel("Solución")
        var_title.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: {COLOR_TEXT_PRIMARY}; margin-top: 4px;"
        )
        layout.addWidget(var_title)

        self.var_container = QVBoxLayout()
        self.var_container.setSpacing(4)
        layout.addLayout(self.var_container)

        check_title = QLabel("Comprobación")
        check_title.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;"
        )
        layout.addWidget(check_title)

        self.checklist_container = QVBoxLayout()
        self.checklist_container.setSpacing(6)
        layout.addLayout(self.checklist_container)

        layout.addStretch(1)

    def clear(self) -> None:
        """Restablece el panel al estado vacío inicial."""
        self.status_badge.setText("Esperando cálculo")
        self.status_badge.setStyleSheet(self._badge_style("#3A3642", COLOR_TEXT_PRIMARY))
        self.summary_label.setText("")
        self._clear_layout(self.var_container)
        self._clear_layout(self.checklist_container)

    def display_results(
        self,
        analysis: SystemAnalysis,
        verifications: Optional[List[EquationVerification]] = None,
    ) -> None:
        if analysis.system_type == SystemType.CONSISTENT_DETERMINED:
            badge_color = COLOR_FEEDBACK_SUCCESS
            badge_text = "Consistente determinado"
            text_color = COLOR_BG_BASE
        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            badge_color = COLOR_ACCENT_WARNING
            badge_text = "Consistente indeterminado"
            text_color = COLOR_BG_BASE
        else:
            badge_color = COLOR_FEEDBACK_ERROR
            badge_text = "Sistema inconsistente"
            text_color = COLOR_TEXT_PRIMARY

        self.status_badge.setText(badge_text)
        self.status_badge.setStyleSheet(self._badge_style(badge_color, text_color))
        self.summary_label.setText(prettify_math_text(analysis.summary_message))

        self._clear_layout(self.var_container)

        if analysis.system_type == SystemType.CONSISTENT_DETERMINED and analysis.unique_solution:
            for idx, val in enumerate(analysis.unique_solution):
                val_str = format_scalar(val, mode="fraction")
                self.var_container.addWidget(
                    self._equation_line(f"{variable_symbol(idx)}  =  {val_str}")
                )

        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            if analysis.parametric_solutions:
                for basic_var, expr in analysis.parametric_solutions.items():
                    expr_str = prettify_math_text(expr.to_string())
                    self.var_container.addWidget(
                        self._equation_line(f"{variable_symbol(basic_var)}  =  {expr_str}")
                    )

            if analysis.free_variables:
                names = ", ".join(variable_symbol(v) for v in analysis.free_variables)
                free_lbl = QLabel(f"{names}  libres")
                free_lbl.setStyleSheet(
                    f"color: {COLOR_ACCENT_WARNING}; font-size: 13px; font-style: italic; "
                    f"font-family: {FONT_FAMILY_SANS}; padding: 4px 2px;"
                )
                self.var_container.addWidget(free_lbl)
        else:
            lbl = QLabel("No hay solución (el sistema es incompatible).")
            lbl.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-style: italic; font-size: 13px;"
            )
            self.var_container.addWidget(lbl)

        self._clear_layout(self.checklist_container)

        if verifications and analysis.system_type != SystemType.INCONSISTENT:
            for v in verifications:
                self.checklist_container.addWidget(self._verification_block(v))
        elif analysis.system_type == SystemType.INCONSISTENT:
            lbl = QLabel("Contradicción:  0 = c  con  c ≠ 0")
            lbl.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-size: 13px; font-style: italic; "
                f"padding: 8px; background-color: {COLOR_SURFACE_INNER};"
            )
            self.checklist_container.addWidget(lbl)

    def _equation_line(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-family: {FONT_FAMILY_MONO}; "
            f"padding: 4px 2px;"
        )
        return lbl

    def _verification_block(self, v: EquationVerification) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: transparent; }}")
        col = QVBoxLayout(card)
        col.setContentsMargins(0, 2, 0, 2)
        col.setSpacing(2)

        mark = "✓" if v.is_valid else "✗"
        mark_color = COLOR_FEEDBACK_SUCCESS if v.is_valid else COLOR_FEEDBACK_ERROR
        eq = format_equation_book(v.equation_str)
        sub = format_substitution_book(v.substitution_str)

        head = QLabel(f"{mark}   ({v.equation_index + 1})   {eq}")
        head.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-family: {FONT_FAMILY_MONO};"
        )
        # Color only the mark via rich text
        head.setTextFormat(Qt.RichText)
        head.setText(
            f"<span style='color:{mark_color}; font-weight:bold;'>{mark}</span>"
            f"&nbsp;&nbsp;<span style='color:{COLOR_TEXT_MUTED};'>({v.equation_index + 1})</span>"
            f"&nbsp;&nbsp;<span style='color:{COLOR_TEXT_PRIMARY}; font-family:{FONT_FAMILY_MONO};'>{eq}</span>"
        )
        col.addWidget(head)

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 12px; font-style: italic; "
            f"font-family: {FONT_FAMILY_MONO}; padding-left: 28px;"
        )
        col.addWidget(sub_lbl)
        return card

    @staticmethod
    def _badge_style(bg: str, fg: str) -> str:
        return f"""
            background-color: {bg};
            color: {fg};
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.03em;
            padding: 10px 12px;
            border-radius: 4px;
        """

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
