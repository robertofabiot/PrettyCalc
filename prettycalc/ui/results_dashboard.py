"""Dashboard de resultados con notación de libro: variables, rangos y comprobación."""

from __future__ import annotations
from typing import Optional, List

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QFrame,
        QScrollArea,
    )
    from PySide6.QtCore import Qt
except ImportError:
    QFrame = object  # type: ignore

from prettycalc.core.classifier import SystemAnalysis, SystemType
from prettycalc.core.verifier import EquationVerification
from prettycalc.core.types import format_scalar
from prettycalc.ui.mathtext import (
    variable_symbol,
    variable_html,
    to_html_subscripts,
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
        self.setMinimumWidth(320)
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        outer.addWidget(scroll)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(10, 10, 12, 10)
        layout.setSpacing(14)

        title = QLabel("Resultados")
        title.setProperty("class", "section-title")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: 600; letter-spacing: 0.04em; "
            f"color: {COLOR_TEXT_PRIMARY};"
        )
        layout.addWidget(title)

        self.status_badge = QLabel("Esperando cálculo")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setWordWrap(True)
        self.status_badge.setStyleSheet(self._badge_style("#3A3642", COLOR_TEXT_PRIMARY))
        layout.addWidget(self.status_badge)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px;"
        )
        layout.addWidget(self.summary_label)

        struct_title = QLabel("Estructura de Variables y Pivotes")
        struct_title.setStyleSheet(
            f"font-weight: 600; font-size: 18px; color: {COLOR_TEXT_PRIMARY}; margin-top: 6px;"
        )
        layout.addWidget(struct_title)

        self.structure_layout = QVBoxLayout()
        self.structure_layout.setSpacing(4)
        layout.addLayout(self.structure_layout)

        var_title = QLabel("Solución")
        var_title.setStyleSheet(
            f"font-weight: 600; font-size: 18px; color: {COLOR_TEXT_PRIMARY}; margin-top: 6px;"
        )
        layout.addWidget(var_title)

        self.var_container = QVBoxLayout()
        self.var_container.setSpacing(6)
        layout.addLayout(self.var_container)

        check_title = QLabel("Comprobación")
        check_title.setStyleSheet(
            f"font-weight: 600; font-size: 18px; color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;"
        )
        layout.addWidget(check_title)

        self.checklist_container = QVBoxLayout()
        self.checklist_container.setSpacing(8)
        layout.addLayout(self.checklist_container)

        layout.addStretch(1)
        scroll.setWidget(inner)

    def clear(self) -> None:
        """Restablece el panel al estado vacío inicial."""
        self.status_badge.setText("Esperando cálculo")
        self.status_badge.setStyleSheet(self._badge_style("#3A3642", COLOR_TEXT_PRIMARY))
        self.summary_label.setText("")
        self._clear_layout(self.structure_layout)
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

        self._clear_layout(self.structure_layout)

        # 1. Columnas con pivote
        if analysis.basic_variables:
            cols_str = ", ".join(
                f"Columna {c + 1} ({variable_html(c, sub_size_px=11)})"
                for c in analysis.basic_variables
            )
            if analysis.has_augmented_pivot or analysis.inconsistent_row is not None:
                cols_str += f" · Columna {analysis.num_variables + 1} (b, pivote en [A|b])"
        else:
            if analysis.has_augmented_pivot or analysis.inconsistent_row is not None:
                cols_str = f"Columna {analysis.num_variables + 1} (b, pivote en [A|b])"
            else:
                cols_str = "Ninguna"

        self.structure_layout.addWidget(
            self._info_line("Columnas con pivote", cols_str, COLOR_TEXT_PRIMARY)
        )

        # 2. Variables básicas
        if analysis.basic_variables:
            basic_str = ", ".join(
                variable_html(c, sub_size_px=11) for c in analysis.basic_variables
            )
            basic_color = COLOR_FEEDBACK_SUCCESS
        else:
            basic_str = "Ninguna"
            basic_color = COLOR_TEXT_MUTED

        self.structure_layout.addWidget(
            self._info_line("Variables básicas", basic_str, basic_color)
        )

        # 3. Variables libres
        if analysis.free_variables:
            free_names = ", ".join(
                variable_html(c, sub_size_px=11) for c in analysis.free_variables
            )
            count = len(analysis.free_variables)
            free_str = f"{free_names}  ({count} libre{'s' if count > 1 else ''})"
            free_color = COLOR_ACCENT_WARNING
        else:
            free_str = "Ninguna (0 variables libres)"
            free_color = COLOR_INTERACTIVE_IDLE

        self.structure_layout.addWidget(
            self._info_line("Variables libres", free_str, free_color)
        )

        self._clear_layout(self.var_container)

        if analysis.system_type == SystemType.CONSISTENT_DETERMINED and analysis.unique_solution:
            for idx, val in enumerate(analysis.unique_solution):
                val_str = format_scalar(val, mode="fraction")
                v_html = variable_html(idx, sub_size_px=12)
                self.var_container.addWidget(
                    self._equation_line(f"{v_html}  =  {val_str}", tag="básica")
                )

        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            if analysis.parametric_solutions:
                for basic_var, expr in analysis.parametric_solutions.items():
                    expr_str = prettify_math_text(expr.to_string())
                    expr_html = to_html_subscripts(expr_str, sub_size_px=12)
                    v_html = variable_html(basic_var, sub_size_px=12)
                    self.var_container.addWidget(
                        self._equation_line(f"{v_html}  =  {expr_html}", tag="básica")
                    )

            if analysis.free_variables:
                for free_var in analysis.free_variables:
                    v_html = variable_html(free_var, sub_size_px=11)
                    self.var_container.addWidget(
                        self._free_var_line(f"{v_html}  libre (parámetro)")
                    )
        else:
            lbl = QLabel("No hay solución (el sistema es incompatible).")
            lbl.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-style: italic; font-size: 16px;"
            )
            self.var_container.addWidget(lbl)
            if analysis.inconsistent_row is not None:
                inc_lbl = QLabel(f"La fila {analysis.inconsistent_row + 1} genera contradicción 0 = c con c ≠ 0.")
                inc_lbl.setStyleSheet(
                    f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; padding-top: 4px;"
                )
                self.var_container.addWidget(inc_lbl)

        self._clear_layout(self.checklist_container)

        if verifications and analysis.system_type != SystemType.INCONSISTENT:
            for v in verifications:
                self.checklist_container.addWidget(self._verification_block(v))
        elif analysis.system_type == SystemType.INCONSISTENT:
            lbl = QLabel("Contradicción:  0 = c  con  c ≠ 0")
            lbl.setStyleSheet(
                f"color: {COLOR_FEEDBACK_ERROR}; font-size: 16px; font-style: italic; "
                f"padding: 10px; background-color: {COLOR_SURFACE_INNER};"
            )
            self.checklist_container.addWidget(lbl)

    def _equation_line(self, text: str, tag: str = "") -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if tag:
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(
                f"<span style='color:{COLOR_TEXT_PRIMARY}; font-size:22px; font-family:{FONT_FAMILY_MONO};'>{text}</span>"
                f"&nbsp;&nbsp;<span style='color:{COLOR_INTERACTIVE_IDLE}; font-size:14px; font-style:italic;'>({tag})</span>"
            )
        else:
            lbl.setText(text)
            lbl.setStyleSheet(
                f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-family: {FONT_FAMILY_MONO}; "
                f"padding: 6px 2px;"
            )
        lbl.setStyleSheet("padding: 4px 2px;")
        return lbl

    def _free_var_line(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet(
            f"color: {COLOR_ACCENT_WARNING}; font-size: 18px; font-family:{FONT_FAMILY_MONO}; "
            f"font-weight: 600; padding: 4px 2px;"
        )
        return lbl

    def _info_line(self, label: str, value: str, value_color: str) -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet("padding: 2px 0px;")
        lbl.setText(
            f"<span style='color:{COLOR_INTERACTIVE_IDLE}; font-weight:600; font-size:15px;'>{label}:</span>&nbsp;&nbsp;"
            f"<span style='color:{value_color}; font-family:{FONT_FAMILY_MONO}; font-size:15px; font-weight:600;'>{value}</span>"
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
        eq_html = to_html_subscripts(eq, sub_size_px=11)
        sub = format_substitution_book(v.substitution_str)
        sub_html = to_html_subscripts(sub, sub_size_px=11)

        head = QLabel(f"{mark}   ({v.equation_index + 1})   {eq}")
        head.setWordWrap(True)
        head.setTextFormat(Qt.RichText)
        head.setText(
            f"<span style='color:{mark_color}; font-weight:bold; font-size:18px;'>{mark}</span>"
            f"&nbsp;&nbsp;<span style='color:{COLOR_INTERACTIVE_IDLE}; font-size:17px;'>({v.equation_index + 1})</span>"
            f"&nbsp;&nbsp;<span style='color:{COLOR_TEXT_PRIMARY}; font-size:17px; font-family:{FONT_FAMILY_MONO};'>{eq_html}</span>"
        )
        col.addWidget(head)

        sub_lbl = QLabel(sub)
        sub_lbl.setTextFormat(Qt.RichText)
        sub_lbl.setText(f"<span style='color:{COLOR_TEXT_PRIMARY}; font-size:17px; font-family:{FONT_FAMILY_MONO};'>{sub_html}</span>")
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 17px; "
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
            font-size: 17px;
            letter-spacing: 0.02em;
            padding: 12px 14px;
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
