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
from prettycalc.ui.navigation_bar import ModularNavigationBar
from prettycalc.ui.platform_setup import configure_high_dpi, prepare_application
from prettycalc.ui.preferences_dialog import (
    PreferencesDialog,
    ShortcutsDialog,
    restart_application,
)
from prettycalc.ui.theme import (
    load_appearance,
    get_global_stylesheet,
    get_app_palette,
    COLOR_BG_BASE,
    COLOR_SURFACE_ELEVATED,
    COLOR_TEXT_PRIMARY,
    COLOR_INTERACTIVE_IDLE,
)

_MODULE_SUBTITLES = (
    "Sistemas de ecuaciones lineales  ·  eliminación por filas",
    "Álgebra matricial  ·  A ± B, k·A, A·B y Aᵀ",
    "Vectores en ℝⁿ  ·  operaciones y combinación lineal",
    "Ecuaciones matriciales  ·  A x = b y propiedades de A · x",
    "Determinantes  ·  Sarrus, triangulación, cofactores y adjunta",
    "Factorización LU  ·  A = LU, Ly = b y Ux = y",
)



class MainWindow(QMainWindow):
    """Shell multi-módulo: navegación segmentada y seis vistas persistentes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrettyCalc — Álgebra lineal")
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

    def _setup_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("rootWidget")
        self.setCentralWidget(root_widget)

        main_layout = QVBoxLayout(root_widget)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("PrettyCalc")
        title_lbl.setObjectName("appTitle")
        title_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: 600; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.02em;"
        )
        self.subtitle_lbl = QLabel(_MODULE_SUBTITLES[0])
        self.subtitle_lbl.setStyleSheet(f"font-size: 15px; color: {COLOR_INTERACTIVE_IDLE};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        header_layout.addLayout(title_box)

        self.nav_bar = ModularNavigationBar()
        self.nav_bar.module_changed.connect(self._on_module_changed)
        header_layout.addWidget(self.nav_bar, stretch=1, alignment=Qt.AlignVCenter)

        self.shortcuts_btn = QPushButton("?")
        self.shortcuts_btn.setObjectName("headerTool")
        self.shortcuts_btn.setAccessibleName("Atajos de teclado")
        self.shortcuts_btn.setToolTip("Atajos de teclado (F1)")
        self.shortcuts_btn.setFixedWidth(40)
        self.shortcuts_btn.setCursor(Qt.PointingHandCursor)
        self.shortcuts_btn.clicked.connect(self.show_shortcuts)
        header_layout.addWidget(self.shortcuts_btn, 0, Qt.AlignVCenter)

        self.appearance_btn = QPushButton("Aa")
        self.appearance_btn.setObjectName("headerTool")
        self.appearance_btn.setAccessibleName("Apariencia y accesibilidad")
        self.appearance_btn.setToolTip("Tema, alto contraste y tamaño de la interfaz (Ctrl+,)")
        self.appearance_btn.setFixedWidth(46)
        self.appearance_btn.setCursor(Qt.PointingHandCursor)
        self.appearance_btn.clicked.connect(self.show_preferences)
        header_layout.addWidget(self.appearance_btn, 0, Qt.AlignVCenter)
        main_layout.addLayout(header_layout)

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
        main_layout.addWidget(self.module_stack, stretch=1)
        self.determinants_view.inverseExported.connect(self._send_inverse_to_matrices)

    def _send_inverse_to_matrices(self, matrix) -> None:
        """Determinantes → Matrices: abre el Módulo 2 con A⁻¹ en la página de la inversa."""
        self.set_module(1)
        self.matrix_operations_view.receive_inverse(matrix)

    def _setup_shortcuts(self) -> None:
        for index in range(6):
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
            self.subtitle_lbl.setText(_MODULE_SUBTITLES[index])

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
    configure_high_dpi()
    app = QApplication(sys.argv)
    app.setOrganizationName("PrettyCalc")
    app.setApplicationName("PrettyCalc")
    prepare_application(app)
    palette = get_app_palette()
    if palette is not None:
        app.setPalette(palette)
    app.setStyleSheet(get_global_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
