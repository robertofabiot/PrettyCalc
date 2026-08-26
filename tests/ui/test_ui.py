"""Pruebas de interfaz gráfica con pytest-qt."""

import pytest
from prettycalc.ui.main_window import MainWindow
from prettycalc.core.types import Matrix


def test_main_window_init(qtbot):
    """Verifica que la ventana principal inicialice correctamente en formato 2x2."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.matrix_grid.num_rows == 2
    assert window.matrix_grid.num_vars == 2
    assert window.windowTitle() == "PrettyCalc - Calculadora de Álgebra Lineal"


def test_main_window_solve_sample_case1(qtbot):
    """Verifica la carga y resolución del Caso 1 (Solución Única)."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.load_sample_case1()

    # Verificar que el badge indique Consistente Determinado
    assert "Consistente Determinado" in window.dashboard_card.status_badge.text()
    # Verificar que haya pasos en el carrusel
    assert len(window.stepper_carousel._steps) > 0


def test_main_window_reset(qtbot):
    """Verifica que el botón de reinicio devuelva la matriz a 2x2 limpia."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.load_sample_case1()
    window.reset_matrix()

    assert window.matrix_grid.num_rows == 2
    assert window.matrix_grid.num_vars == 2
    assert len(window.stepper_carousel._steps) == 0
