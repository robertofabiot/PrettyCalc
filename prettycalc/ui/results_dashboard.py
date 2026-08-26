"""Dashboard de Resultados y Verificación para PrettyCalc."""

from __future__ import annotations
from typing import Optional, List

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
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
from prettycalc.ui.theme import (
    COLOR_FEEDBACK_SUCCESS,
    COLOR_FEEDBACK_ERROR,
    COLOR_ACCENT_WARNING,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
    COLOR_SURFACE_ELEVATED,
    FONT_FAMILY_MONO,
)


class ResultsDashboardCard(QFrame):
    """Panel lateral o card que despliega el estado del sistema, variables y checklist de validación."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "elevated-card")
        self.setMinimumWidth(320)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Título del Dashboard
        title = QLabel("📊 Resultados y Clasificación")
        title.setProperty("class", "title")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(title)

        # 2. Badge de Estado del Sistema
        self.status_badge = QLabel("Esperando cálculo...")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet(f"""
            background-color: #3A3642;
            color: {COLOR_TEXT_PRIMARY};
            font-weight: bold;
            font-size: 13px;
            padding: 8px 12px;
            border-radius: 6px;
        """)
        layout.addWidget(self.status_badge)

        # 3. Resumen descriptivo
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 12px;")
        layout.addWidget(self.summary_label)

        # 4. Sección de Valores de Variables
        var_title = QLabel("🔢 Valores de las Variables")
        var_title.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;")
        layout.addWidget(var_title)

        self.var_container = QVBoxLayout()
        self.var_container.setSpacing(4)
        layout.addLayout(self.var_container)

        # 5. Checklist de Verificación por Sustitución (✓)
        check_title = QLabel("✅ Comprobación de Ecuaciones")
        check_title.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;")
        layout.addWidget(check_title)

        self.checklist_container = QVBoxLayout()
        self.checklist_container.setSpacing(4)
        layout.addLayout(self.checklist_container)

        layout.addStretch(1)

    def display_results(
        self,
        analysis: SystemAnalysis,
        verifications: Optional[List[EquationVerification]] = None,
    ) -> None:
        """Actualiza el dashboard con los datos del análisis y la verificación."""
        # 1. Configurar Badge de Estado
        if analysis.system_type == SystemType.CONSISTENT_DETERMINED:
            badge_color = COLOR_FEEDBACK_SUCCESS
            badge_text = "🟢 Consistente Determinado (Solución Única)"
            text_color = "#1A181B"
        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            badge_color = COLOR_ACCENT_WARNING
            badge_text = "🟡 Consistente Indeterminado (Infinitas Soluciones)"
            text_color = "#1A181B"
        else:
            badge_color = COLOR_FEEDBACK_ERROR
            badge_text = "🔴 Inconsistente (Sin Solución)"
            text_color = "#E0FBFC"

        self.status_badge.setText(badge_text)
        self.status_badge.setStyleSheet(f"""
            background-color: {badge_color};
            color: {text_color};
            font-weight: bold;
            font-size: 13px;
            padding: 8px 12px;
            border-radius: 6px;
        """)

        # 2. Resumen
        self.summary_label.setText(analysis.summary_message)

        # 3. Limpiar variables anteriores
        while self.var_container.count():
            item = self.var_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rellenar variables
        if analysis.system_type == SystemType.CONSISTENT_DETERMINED and analysis.unique_solution:
            for idx, val in enumerate(analysis.unique_solution):
                v_name = f"x{idx+1}"
                val_str = format_scalar(val, mode="fraction")
                dec_str = format_scalar(val, mode="decimal")
                lbl = QLabel(f"• <b>{v_name}</b> = <span style='color:{COLOR_TEXT_PRIMARY}; font-family:{FONT_FAMILY_MONO}'>{val_str}</span> (≈ {dec_str})")
                lbl.setTextFormat(Qt.RichText)
                self.var_container.addWidget(lbl)

        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            # Variables básicas parametrizadas
            if analysis.parametric_solutions:
                for basic_var, expr in analysis.parametric_solutions.items():
                    v_name = f"x{basic_var+1}"
                    expr_str = expr.to_string()
                    lbl = QLabel(f"• <b>{v_name}</b> = <span style='color:{COLOR_TEXT_PRIMARY}; font-family:{FONT_FAMILY_MONO}'>{expr_str}</span>")
                    lbl.setTextFormat(Qt.RichText)
                    self.var_container.addWidget(lbl)

            # Variables libres con icono de llave 🔑
            for free_var in analysis.free_variables:
                v_name = f"x{free_var+1}"
                lbl = QLabel(f"• 🔑 <b>{v_name}</b> = Variable libre (t ∈ ℝ)")
                lbl.setStyleSheet(f"color: {COLOR_ACCENT_WARNING};")
                self.var_container.addWidget(lbl)
        else:
            lbl = QLabel("No existen valores para las variables.")
            lbl.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-style: italic;")
            self.var_container.addWidget(lbl)

        # 4. Limpiar checklist anterior
        while self.checklist_container.count():
            item = self.checklist_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rellenar checklist de verificación
        if verifications and analysis.system_type != SystemType.INCONSISTENT:
            for v in verifications:
                row_layout = QHBoxLayout()
                icon_lbl = QLabel("✓" if v.is_valid else "✗")
                icon_color = COLOR_FEEDBACK_SUCCESS if v.is_valid else COLOR_FEEDBACK_ERROR
                icon_lbl.setStyleSheet(f"color: {icon_color}; font-size: 16px; font-weight: bold;")
                row_layout.addWidget(icon_lbl)

                desc_lbl = QLabel(f"Ec. {v.equation_index+1}: {v.equation_str}")
                desc_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_PRIMARY};")
                row_layout.addWidget(desc_lbl, stretch=1)

                row_widget = QWidget()
                row_widget.setLayout(row_layout)
                self.checklist_container.addWidget(row_widget)
        elif analysis.system_type == SystemType.INCONSISTENT:
            lbl = QLabel("⚠️ Sistema contradictorio (Lado Izquierdo = 0 ≠ Lado Derecho)")
            lbl.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-size: 12px;")
            self.checklist_container.addWidget(lbl)
