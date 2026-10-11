"""Dashboard de resultados con notación de libro: variables, rangos y comprobación."""

from __future__ import annotations
from typing import Optional, List

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QFrame,
    )
    from PySide6.QtCore import Qt, QRect, QTimer
    from PySide6.QtGui import QPainter, QColor, QFont, QPaintEvent
except ImportError:
    QFrame = object  # type: ignore

from prettycalc.core.classifier import ParametricVectorSolution, SystemAnalysis, SystemType
from prettycalc.core.verifier import EquationVerification
from prettycalc.core.types import Vector, format_scalar
from prettycalc.ui.book_matrix import draw_square_brackets, paint_book_scalar
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
    COLOR_TEXT_MUTED,
    COLOR_SURFACE_INNER,
    COLOR_BG_BASE,
    FONT_FAMILY_MONO,
    FONT_FAMILY_SANS,
    apply_widget_class,
)


class _ColumnVectorWidget(QWidget):
    """Vector columna compacto, con corchetes de libro y fracciones apiladas."""

    def __init__(self, vector: Vector, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._values = [format_scalar(value, mode="fraction") for value in vector.components]
        self._row_h = 40
        self.setFixedSize(112, self._row_h * len(self._values) + 16)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(COLOR_SURFACE_INNER))
        rows = len(self._values)
        top = 4
        bracket = QRect(2, top, self.width() - 4, rows * self._row_h)
        draw_square_brackets(painter, bracket, QColor(COLOR_TEXT_PRIMARY), thickness=2)
        font = QFont()
        font.setFamily(FONT_FAMILY_MONO.split(",")[0].strip())
        font.setPointSize(11)
        font.setBold(True)
        for index, text in enumerate(self._values):
            cell = QRect(
                bracket.left() + 14,
                bracket.top() + index * self._row_h,
                bracket.width() - 28,
                self._row_h,
            )
            paint_book_scalar(painter, cell, text, QColor(COLOR_TEXT_PRIMARY), font)


class ResultsDashboardCard(QFrame):
    """Panel de clasificación, solución y comprobación por sustitución."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        apply_widget_class(self, "elevated-card")
        self.setMinimumWidth(320)
        self.parametric_solution: Optional[ParametricVectorSolution] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
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

    def clear(self) -> None:
        """Restablece el panel al estado vacío inicial."""
        self.status_badge.setText("Esperando cálculo")
        self.status_badge.setStyleSheet(self._badge_style("#3A3642", COLOR_TEXT_PRIMARY))
        self.summary_label.setText("")
        self.parametric_solution = None
        self._clear_layout(self.structure_layout)
        self._clear_layout(self.var_container)
        self._clear_layout(self.checklist_container)
        self._fit_minimum_height()
        QTimer.singleShot(0, self._fit_minimum_height)

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
        self.parametric_solution = analysis.parametric_vector_solution

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
            if analysis.parametric_vector_solution is not None:
                self._append_parametric_form(analysis.parametric_vector_solution)
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
        self._fit_minimum_height()
        QTimer.singleShot(0, self._fit_minimum_height)

    def _fit_minimum_height(self) -> None:
        """Impide que el splitter aplaste el panel y superponga la solución con la comprobación."""
        layout = self.layout()
        if layout is None:
            return
        layout.activate()
        needed = max(layout.sizeHint().height(), layout.minimumSize().height())
        if needed <= 0:
            return
        self.setMinimumHeight(needed)
        self.setMinimumWidth(max(320, layout.minimumSize().width()))
        self.updateGeometry()

    def _append_parametric_form(self, solution: ParametricVectorSolution) -> None:
        """Muestra x = p + Σ t_k v_k con vectores columna de libro."""
        title = QLabel("Forma vectorial paramétrica")
        title.setObjectName("parametricVectorTitle")
        title.setStyleSheet(
            f"font-weight: 600; font-size: 18px; color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;"
        )
        self.var_container.addWidget(title)

        host = QWidget()
        host.setObjectName("parametricVectorForm")
        row = QHBoxLayout(host)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(6)

        equals = QLabel("x  =")
        equals.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-family: {FONT_FAMILY_MONO}; font-weight: 700;"
        )
        row.addWidget(equals, 0, Qt.AlignVCenter)
        row.addWidget(self._vector_term(solution.particular_vector, "particular p"), 0, Qt.AlignVCenter)

        for free_idx in sorted(solution.null_basis_vectors):
            plus = QLabel("+")
            plus.setStyleSheet(
                f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 22px; font-weight: 700;"
            )
            row.addWidget(plus, 0, Qt.AlignVCenter)
            name = QLabel(variable_html(free_idx, sub_size_px=14))
            name.setTextFormat(Qt.RichText)
            name.setStyleSheet(
                f"color: {COLOR_ACCENT_WARNING}; font-size: 20px; font-family: {FONT_FAMILY_MONO}; font-weight: 700;"
            )
            row.addWidget(name, 0, Qt.AlignVCenter)
            caption = f"base de {variable_symbol(free_idx)}"
            row.addWidget(
                self._vector_term(solution.null_basis_vectors[free_idx], caption),
                0,
                Qt.AlignVCenter,
            )
        row.addStretch(1)
        host.layout().activate()
        host.setMinimumWidth(host.sizeHint().width())
        self.var_container.addWidget(host)

        equation = QLabel(solution.to_plain_equation())
        equation.setObjectName("parametricVectorEquation")
        equation.setWordWrap(True)
        equation.setTextInteractionFlags(Qt.TextSelectableByMouse)
        equation.setToolTip(solution.to_latex_equation())
        equation.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-family: {FONT_FAMILY_MONO}; "
            f"padding: 4px 0 8px 0;"
        )
        self.var_container.addWidget(equation)

    def _vector_term(self, vector: Vector, caption: str) -> QWidget:
        """Vector columna dibujado con corchetes de libro y un pie de figura."""
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(_ColumnVectorWidget(vector), 0, Qt.AlignHCenter)
        foot = QLabel(caption)
        foot.setAlignment(Qt.AlignCenter)
        foot.setStyleSheet(
            f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 13px; font-family: {FONT_FAMILY_SANS};"
        )
        layout.addWidget(foot)
        return box

    def _equation_line(self, text: str, tag: str = "") -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-family: {FONT_FAMILY_MONO}; "
            f"font-weight: 600; padding: 6px 2px;"
        )
        if tag:
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(
                f"<span style='color:{COLOR_TEXT_PRIMARY}; font-size:22px; font-family:{FONT_FAMILY_MONO}; font-weight:600;'>{text}</span>"
                f"&nbsp;&nbsp;<span style='color:{COLOR_INTERACTIVE_IDLE}; font-size:16px; font-style:italic;'>({tag})</span>"
            )
        else:
            lbl.setText(text)
        return lbl

    def _free_var_line(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet(
            f"color: {COLOR_ACCENT_WARNING}; font-size: 20px; font-family:{FONT_FAMILY_MONO}; "
            f"font-weight: 600; padding: 6px 2px;"
        )
        return lbl

    def _info_line(self, label: str, value: str, value_color: str) -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet("padding: 4px 0px;")
        lbl.setText(
            f"<span style='color:{COLOR_INTERACTIVE_IDLE}; font-weight:600; font-size:17px;'>{label}:</span>&nbsp;&nbsp;"
            f"<span style='color:{value_color}; font-family:{FONT_FAMILY_MONO}; font-size:18px; font-weight:600;'>{value}</span>"
        )
        return lbl

    def _verification_block(self, v: EquationVerification) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: transparent; }}")
        col = QVBoxLayout(card)
        col.setContentsMargins(0, 4, 0, 4)
        col.setSpacing(4)

        mark = "✓" if v.is_valid else "✗"
        mark_color = COLOR_FEEDBACK_SUCCESS if v.is_valid else COLOR_FEEDBACK_ERROR
        eq = format_equation_book(v.equation_str)
        eq_html = to_html_subscripts(eq, sub_size_px=14)
        sub = format_substitution_book(v.substitution_str)
        sub_html = to_html_subscripts(sub, sub_size_px=14)

        head = QLabel(f"{mark}   ({v.equation_index + 1})   {eq}")
        head.setWordWrap(True)
        head.setTextFormat(Qt.RichText)
        head.setText(
            f"<span style='color:{mark_color}; font-weight:bold; font-size:24px;'>{mark}</span>"
            f"&nbsp;&nbsp;<span style='color:{COLOR_INTERACTIVE_IDLE}; font-size:22px;'>({v.equation_index + 1})</span>"
            f"&nbsp;&nbsp;<span style='color:{COLOR_TEXT_PRIMARY}; font-size:22px; font-weight:600; font-family:{FONT_FAMILY_MONO};'>{eq_html}</span>"
        )
        col.addWidget(head)

        sub_lbl = QLabel(sub)
        sub_lbl.setTextFormat(Qt.RichText)
        sub_lbl.setText(
            f"<span style='color:{COLOR_TEXT_PRIMARY}; font-size:22px; font-weight:600; "
            f"font-family:{FONT_FAMILY_MONO};'>{sub_html}</span>"
        )
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 600; "
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
