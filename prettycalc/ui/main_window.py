"""Ventana principal de PrettyCalc en PySide6."""

from __future__ import annotations
import os
import sys

try:
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QApplication,
        QStackedWidget,
        QPushButton,
    )
    from PySide6.QtGui import QAction, QKeySequence, QColor, QPalette
    from PySide6.QtCore import Qt
except ImportError:
    QMainWindow = object  # type: ignore

from prettycalc.ui.modules.linear_systems_view import LinearSystemsView
from prettycalc.ui.modules.matrix_operations_view import MatrixOperationsView
from prettycalc.ui.modules.vectors_view import VectorsView
from prettycalc.ui.modules.matrix_equations_view import MatrixEquationsView
from prettycalc.ui.modules.determinants_view import DeterminantsView
from prettycalc.ui.modules.lu_factorization_view import LUFactorizationView
from prettycalc.ui.modules.linear_transformations_view import LinearTransformationsView
from prettycalc.ui.modules.vector_spaces_view import VectorSpacesView
from prettycalc.ui.navigation_bar import ModularNavigationBar, brand_icon
from prettycalc.ui.platform_setup import (
    apply_title_bar_theme,
    configure_high_dpi,
    configure_platform_environment,
    prepare_application,
)
from prettycalc.ui.preferences_dialog import (
    PreferencesDialog,
    ShortcutsDialog,
    restart_application,
)
from prettycalc.ui.theme import (
    ACTIVE_THEME,
    load_appearance,
    get_global_stylesheet,
    get_app_palette,
    COLOR_BG_BASE,
    COLOR_SURFACE_ELEVATED,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
    COLOR_TEXT_MUTED,
)

_MODULE_SUBTITLES = (
    "Sistemas de ecuaciones lineales  ·  eliminación por filas",
    "Álgebra matricial  ·  A ± B, k·A, A·B y Aᵀ",
    "Vectores en ℝⁿ  ·  operaciones y combinación lineal",
    "Ecuaciones matriciales  ·  A x = b y propiedades de A · x",
    "Determinantes  ·  Sarrus, triangulación, cofactores y adjunta",
    "Factorización LU  ·  A = LU, Ly = b y Ux = y",
    "Transformaciones Lineales  ·  T(v) = A·v, nu T, im T y rango",
    "Espacios Vectoriales  ·  Conjuntos Generadores, Bases y Dimensión",
)

#: Por debajo de este ancho de ventana la barra lateral se pliega a un riel
#: (en una pantalla de 1366 px el contenido conserva así casi todo el ancho).
_COMPACT_NAV_BELOW = 1600


def _page_header_html(subtitle: str) -> str:
    """Encabezado de página: nombre del módulo destacado y descripción tenue."""
    title, _sep, detail = subtitle.partition("  ·  ")
    html = (
        f"<span style='font-size:22px; font-weight:600; color:{COLOR_TEXT_PRIMARY};'>{title}</span>"
    )
    if detail:
        html += (
            f"<span style='font-size:15px; color:{COLOR_TEXT_MUTED};'>"
            f"&nbsp;&nbsp;&nbsp;{detail}</span>"
        )
    return html



class MainWindow(QMainWindow):
    """Shell multi-módulo: barra lateral de navegación y ocho vistas persistentes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrettyCalc — Álgebra lineal")
        self.setWindowIcon(brand_icon())
        self.setMinimumSize(1080, 680)
        self.resize(1380, 800)
        app = QApplication.instance()
        if app is not None:
            prepare_application(app)
        palette = get_app_palette()
        if palette is not None:
            if app is not None:
                app.setPalette(palette)
            self.setPalette(palette)
        self.setStyleSheet(get_global_stylesheet())
        self._setup_ui()
        self._setup_shortcuts()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.nav_bar.set_compact(self.width() < _COMPACT_NAV_BELOW)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        # Windows pinta la barra de título blanca aunque el tema sea oscuro.
        apply_title_bar_theme(self, dark=ACTIVE_THEME != "light")

    def _setup_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("rootWidget")
        self.setCentralWidget(root_widget)

        shell = QHBoxLayout(root_widget)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.nav_bar = ModularNavigationBar()
        self.nav_bar.module_changed.connect(self._on_module_changed)
        shell.addWidget(self.nav_bar)

        self.shortcuts_btn = self.nav_bar.add_footer_item("?", "Atajos de teclado", "Atajos")
        self.shortcuts_btn.setToolTip("Atajos de teclado (F1)")
        self.shortcuts_btn.clicked.connect(self.show_shortcuts)

        self.appearance_btn = self.nav_bar.add_footer_item("Aa", "Apariencia", "Apariencia")
        self.appearance_btn.setAccessibleName("Apariencia y accesibilidad")
        self.appearance_btn.setToolTip("Tema, alto contraste y tamaño de la interfaz (Ctrl+,)")
        self.appearance_btn.clicked.connect(self.show_preferences)

        content = QWidget()
        content.setObjectName("contentArea")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(22, 16, 22, 16)
        main_layout.setSpacing(12)
        shell.addWidget(content, stretch=1)

        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("pageHeader")
        self.subtitle_lbl.setTextFormat(Qt.RichText)
        self.subtitle_lbl.setText(_page_header_html(_MODULE_SUBTITLES[0]))
        main_layout.addWidget(self.subtitle_lbl)

        self.module_stack = QStackedWidget()
        self.linear_systems_view = LinearSystemsView()
        self.matrix_operations_view = MatrixOperationsView()
        self.vectors_view = VectorsView()
        self.matrix_equations_view = MatrixEquationsView()
        self.determinants_view = DeterminantsView()
        self.lu_view = LUFactorizationView()
        self.module_stack.addWidget(self.linear_systems_view)
        self.module_stack.addWidget(self.matrix_operations_view)
        self.module_stack.addWidget(self.vectors_view)
        self.module_stack.addWidget(self.matrix_equations_view)
        self.module_stack.addWidget(self.determinants_view)
        self.module_stack.addWidget(self.lu_view)
        self.linear_transformations_view = LinearTransformationsView()
        self.module_stack.addWidget(self.linear_transformations_view)
        self.vector_spaces_view = VectorSpacesView()
        self.module_stack.addWidget(self.vector_spaces_view)
        main_layout.addWidget(self.module_stack, stretch=1)
        self.determinants_view.inverseExported.connect(self._send_inverse_to_matrices)

    def _send_inverse_to_matrices(self, matrix) -> None:
        """Determinantes → Matrices: abre el Módulo 2 con A⁻¹ en la página de la inversa."""
        self.set_module(1)
        self.matrix_operations_view.receive_inverse(matrix)

    def _setup_shortcuts(self) -> None:
        for index in range(8):  # Ctrl+1 … Ctrl+8 (incluyendo Espacios Vectoriales)
            action = QAction(self)
            action.setShortcut(QKeySequence(f"Ctrl+{index + 1}"))
            action.triggered.connect(lambda _checked=False, i=index: self.set_module(i))
            self.addAction(action)
        help_action = QAction(self)
        help_action.setShortcut(QKeySequence(Qt.Key_F1))
        help_action.triggered.connect(self.show_shortcuts)
        self.addAction(help_action)
        prefs_action = QAction(self)
        prefs_action.setShortcut(QKeySequence("Ctrl+,"))
        prefs_action.triggered.connect(self.show_preferences)
        self.addAction(prefs_action)

    def show_shortcuts(self) -> None:
        """Hoja de atajos de teclado (F1)."""
        dialog = ShortcutsDialog(self)
        dialog.exec()

    def show_preferences(self) -> None:
        """Tema y escala; ofrece reiniciar para aplicarlos."""
        dialog = PreferencesDialog(self)
        if dialog.exec() and dialog.restart_requested:
            restart_application()

    def set_module(self, index: int) -> None:
        """Conmuta el módulo visible y sincroniza la barra de navegación."""
        self.nav_bar.set_current_index(index, emit=False)
        self._on_module_changed(index)

    def _on_module_changed(self, index: int) -> None:
        if index < 0 or index >= self.module_stack.count():
            return
        self.module_stack.setCurrentIndex(index)
        if 0 <= index < len(_MODULE_SUBTITLES):
            self.subtitle_lbl.setText(_page_header_html(_MODULE_SUBTITLES[index]))

    @property
    def matrix_grid(self):
        return self.linear_systems_view.matrix_grid

    @property
    def solve_btn(self):
        return self.linear_systems_view.solve_btn

    @property
    def reset_btn(self):
        return self.linear_systems_view.reset_btn

    @property
    def dashboard_card(self):
        return self.linear_systems_view.dashboard_card

    @property
    def stepper_carousel(self):
        return self.linear_systems_view.stepper_carousel

    def solve_system(self) -> None:
        self.linear_systems_view.solve_system()

    def reset_matrix(self) -> None:
        self.linear_systems_view.reset_matrix()

    def load_sample_case1(self) -> None:
        self.set_module(0)
        self.linear_systems_view.load_sample_case1()

    def load_sample_case2(self) -> None:
        self.set_module(0)
        self.linear_systems_view.load_sample_case2()

    def load_sample_case3(self) -> None:
        self.set_module(0)
        self.linear_systems_view.load_sample_case3()


def apply_scale_environment() -> float:
    """Aplica la escala guardada vía ``QT_SCALE_FACTOR`` antes de crear la aplicación.

    Respeta un ``QT_SCALE_FACTOR`` puesto por el usuario; solo lo administra si
    lo puso PrettyCalc (marca ``PRETTYCALC_SCALE_APPLIED``), para que un
    reinicio desde Preferencias tome la escala nueva.
    """
    _theme, scale = load_appearance()
    user_owned = "QT_SCALE_FACTOR" in os.environ and "PRETTYCALC_SCALE_APPLIED" not in os.environ
    if user_owned:
        return scale
    if abs(scale - 1.0) > 1e-6:
        os.environ["QT_SCALE_FACTOR"] = f"{scale:g}"
        os.environ["PRETTYCALC_SCALE_APPLIED"] = "1"
    else:
        os.environ.pop("QT_SCALE_FACTOR", None)
        os.environ.pop("PRETTYCALC_SCALE_APPLIED", None)
    return scale


def run_app():
    """Arranque de la aplicación GUI (misma apariencia en Windows, Linux y macOS)."""
    apply_scale_environment()
    configure_platform_environment()
    configure_high_dpi()
    app = QApplication(sys.argv)
    app.setOrganizationName("PrettyCalc")
    app.setApplicationName("PrettyCalc")
    prepare_application(app)
    app.setWindowIcon(brand_icon())
    palette = get_app_palette()
    if palette is not None:
        app.setPalette(palette)
    app.setStyleSheet(get_global_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
