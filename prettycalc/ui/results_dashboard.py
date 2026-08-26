"""Dashboard de Resultados y Verificación con tipografía de alto contraste (#E0FBFC) y espaciado generoso."""

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
    FONT_FAMILY_SANS,
)


class ResultsDashboardCard(QFrame):
    """Panel lateral que despliega el estado del sistema, variables destacadas y checklist con respiro."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "elevated-card")
        self.setMinimumWidth(320)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Encabezado del Dashboard
        title = QLabel("📊 Resultados")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY_SANS};")
        layout.addWidget(title)

        # 2. Badge de Estado del Sistema
        self.status_badge = QLabel("Esperando cálculo...")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet(f"""
            background-color: #3A3642;
            color: {COLOR_TEXT_PRIMARY};
            font-weight: bold;
            font-size: 14px;
            padding: 10px 14px;
            border-radius: 6px;
        """)
        layout.addWidget(self.status_badge)

        # 3. Resumen descriptivo
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(f"color: {COLOR_INTERACTIVE_IDLE}; font-size: 13px; margin-bottom: 6px;")
        layout.addWidget(self.summary_label)

        # 4. Sección de Variables
        var_title = QLabel("🔢 Solución del Sistema")
        var_title.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {COLOR_TEXT_PRIMARY}; margin-top: 4px;")
        layout.addWidget(var_title)

        self.var_container = QVBoxLayout()
        self.var_container.setSpacing(8)
        layout.addLayout(self.var_container)

        # 5. Sección de Validación por Sustitución
        check_title = QLabel("✅ Comprobación de Igualdad")
        check_title.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {COLOR_TEXT_PRIMARY}; margin-top: 8px;")
        layout.addWidget(check_title)

        self.checklist_container = QVBoxLayout()
        self.checklist_container.setSpacing(8)
        layout.addLayout(self.checklist_container)

        layout.addStretch(1)

    def display_results(
        self,
        analysis: SystemAnalysis,
        verifications: Optional[List[EquationVerification]] = None,
    ) -> None:
        # 1. Configurar Badge de Estado
        if analysis.system_type == SystemType.CONSISTENT_DETERMINED:
            badge_color = COLOR_FEEDBACK_SUCCESS
            badge_text = "🟢 Consistente Determinado"
            text_color = "#1A181B"
        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            badge_color = COLOR_ACCENT_WARNING
            badge_text = "🟡 Consistente Indeterminado"
            text_color = "#1A181B"
        else:
            badge_color = COLOR_FEEDBACK_ERROR
            badge_text = "🔴 Sistema Inconsistente"
            text_color = "#E0FBFC"

        self.status_badge.setText(badge_text)
        self.status_badge.setStyleSheet(f"""
            background-color: {badge_color};
            color: {text_color};
            font-weight: bold;
            font-size: 14px;
            padding: 10px 14px;
            border-radius: 6px;
        """)

        self.summary_label.setText(analysis.summary_message)

        # 2. Limpiar variables anteriores
        while self.var_container.count():
            item = self.var_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rellenar variables con alta legibilidad y Light Cyan (#E0FBFC)
        if analysis.system_type == SystemType.CONSISTENT_DETERMINED and analysis.unique_solution:
            for idx, val in enumerate(analysis.unique_solution):
                v_name = f"x{idx+1}"
                val_str = format_scalar(val, mode="fraction")
                dec_str = format_scalar(val, mode="decimal")

                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: #242028;
                        border: 1px solid {COLOR_SURFACE_ELEVATED};
                        border-radius: 6px;
                        padding: 8px 12px;
                    }}
                """)
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 8, 10, 8)

                var_lbl = QLabel(f"<span style='color:{COLOR_INTERACTIVE_IDLE}; font-size:16px; font-weight:bold;'>{v_name}</span> = <span style='color:{COLOR_TEXT_PRIMARY}; font-size:17px; font-weight:bold; font-family:{FONT_FAMILY_MONO};'>{val_str}</span> <span style='color:#A09BA8; font-size:12px;'> (≈ {dec_str})</span>")
                var_lbl.setTextFormat(Qt.RichText)
                card_layout.addWidget(var_lbl)

                self.var_container.addWidget(card)

        elif analysis.system_type == SystemType.CONSISTENT_INDETERMINED:
            if analysis.parametric_solutions:
                for basic_var, expr in analysis.parametric_solutions.items():
                    v_name = f"x{basic_var+1}"
                    expr_str = expr.to_string()

                    card = QFrame()
                    card.setStyleSheet(f"""
                        QFrame {{
                            background-color: #242028;
                            border: 1px solid {COLOR_SURFACE_ELEVATED};
                            border-radius: 6px;
                            padding: 8px 12px;
                        }}
                    """)
                    card_layout = QHBoxLayout(card)
                    card_layout.setContentsMargins(10, 8, 10, 8)

                    lbl = QLabel(f"<span style='color:{COLOR_INTERACTIVE_IDLE}; font-size:15px; font-weight:bold;'>{v_name}</span> = <span style='color:{COLOR_TEXT_PRIMARY}; font-size:16px; font-weight:bold; font-family:{FONT_FAMILY_MONO};'>{expr_str}</span>")
                    lbl.setTextFormat(Qt.RichText)
                    card_layout.addWidget(lbl)
                    self.var_container.addWidget(card)

            for free_var in analysis.free_variables:
                v_name = f"x{free_var+1}"
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: #242028;
                        border: 1px dashed {COLOR_ACCENT_WARNING};
                        border-radius: 6px;
                        padding: 8px 12px;
                    }}
                """)
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 8, 10, 8)

                lbl = QLabel(f"🔑 <span style='color:{COLOR_ACCENT_WARNING}; font-size:15px; font-weight:bold;'>{v_name}</span> <span style='color:{COLOR_TEXT_PRIMARY}; font-size:13px;'>es Variable Libre</span>")
                lbl.setTextFormat(Qt.RichText)
                card_layout.addWidget(lbl)
                self.var_container.addWidget(card)
        else:
            lbl = QLabel("Sin valores definidos (sistema inconsistente).")
            lbl.setStyleSheet(f"color: {COLOR_FEEDBACK_ERROR}; font-style: italic; font-size: 13px;")
            self.var_container.addWidget(lbl)

        # 3. Limpiar checklist anterior
        while self.checklist_container.count():
            item = self.checklist_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rellenar checklist con respiro y padding
        if verifications and analysis.system_type != SystemType.INCONSISTENT:
            for v in verifications:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: #242028;
                        border-left: 3px solid {COLOR_FEEDBACK_SUCCESS if v.is_valid else COLOR_FEEDBACK_ERROR};
                        border-radius: 4px;
                        padding: 6px 10px;
                    }}
                """)
                row_layout = QHBoxLayout(card)
                row_layout.setContentsMargins(8, 6, 8, 6)
                row_layout.setSpacing(10)

                icon_lbl = QLabel("✓" if v.is_valid else "✗")
                icon_color = COLOR_FEEDBACK_SUCCESS if v.is_valid else COLOR_FEEDBACK_ERROR
                icon_lbl.setStyleSheet(f"color: {icon_color}; font-size: 18px; font-weight: bold;")
                row_layout.addWidget(icon_lbl)

                desc_lbl = QLabel(f"<span style='color:{COLOR_TEXT_PRIMARY}; font-size:13px;'>Ec. {v.equation_index+1}:</span> <span style='color:{COLOR_INTERACTIVE_IDLE}; font-family:{FONT_FAMILY_MONO}; font-size:13px;'>{v.equation_str}</span>")
                desc_lbl.setTextFormat(Qt.RichText)
                row_layout.addWidget(desc_lbl, stretch=1)

                self.checklist_container.addWidget(card)
        elif analysis.system_type == SystemType.INCONSISTENT:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #3E2426;
                    border: 1px solid {COLOR_FEEDBACK_ERROR};
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)
            card_layout = QHBoxLayout(card)
            lbl = QLabel(f"⚠️ <span style='color:{COLOR_FEEDBACK_ERROR}; font-weight:bold; font-size:13px;'>Contradicción: 0 = c (c ≠ 0)</span>")
            lbl.setTextFormat(Qt.RichText)
            card_layout.addWidget(lbl)
            self.checklist_container.addWidget(card)
